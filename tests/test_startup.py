import ast
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from customtkinter.windows.widgets.appearance_mode.appearance_mode_base_class import CTkAppearanceModeBaseClass
from core import theme
from core.startup_errors import report_error


class StartupTests(unittest.TestCase):
    def test_language_selector_uses_supported_colors(self):
        source = Path(__file__).resolve().parents[1] / 'ui' / 'titlebar.py'
        tree = ast.parse(source.read_text(encoding='utf-8'))
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Attribute)
                 and node.func.attr == 'CTkSegmentedButton']
        self.assertEqual(len(calls), 1)
        for keyword in calls[0].keywords:
            if keyword.arg.endswith('_color'):
                value = keyword.value
                color = getattr(theme, value.attr) if isinstance(value, ast.Attribute) else ast.literal_eval(value)
                CTkAppearanceModeBaseClass._check_color_type(color)

    def test_error_log_survives_hidden_console(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict('os.environ', {'LOCALAPPDATA': directory}), patch('core.startup_errors.sys.platform', 'linux'), patch('core.startup_errors.sys.stderr', None):
                report_error(ValueError, ValueError('startup test'), None)
            log = Path(directory) / 'PsicoseadoSSTool' / 'startup-error.log'
            self.assertIn('startup test', log.read_text(encoding='utf-8'))
