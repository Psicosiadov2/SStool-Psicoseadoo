import unittest
from pathlib import Path
from unittest.mock import patch
import build_support


class BuildTests(unittest.TestCase):
    def test_build_script_disables_pip_cache(self):
        script = Path("BUILD_EXE.bat").read_text(encoding="utf-8")
        self.assertIn('set "PIP_NO_CACHE_DIR=1"', script)
        self.assertGreaterEqual(script.count("--no-cache-dir"), 2)

    def test_rejects_313_before_compiler(self):
        with patch.object(build_support.sys, 'platform', 'win32'), patch.object(build_support.sys, 'version_info', (3, 13)), patch.object(build_support.subprocess, 'call') as call:
            self.assertEqual(build_support.main(), 1)
            call.assert_not_called()

    def test_passes_paths_with_spaces_as_single_arguments(self):
        with patch.object(build_support.sys, 'platform', 'win32'), patch.object(build_support.sys, 'version_info', (3, 12)), patch.object(build_support.sys, 'argv', ['build_support.py', '--mode=onefile', 'main.py']), patch.object(build_support.struct, 'calcsize', return_value=8), patch.object(build_support, 'discover_tk', return_value=(Path('C:/Program Files/tcl'), Path('C:/Program Files/tk'))), patch.object(build_support.subprocess, 'call', return_value=0) as call:
            self.assertEqual(build_support.main(), 0)
            args = call.call_args.args[0]
            tcl_arg = next(value for value in args if value.startswith('--tcl-library-dir='))
            tk_arg = next(value for value in args if value.startswith('--tk-library-dir='))
            self.assertEqual(Path(tcl_arg.split('=', 1)[1]), Path('C:/Program Files/tcl'))
            self.assertEqual(Path(tk_arg.split('=', 1)[1]), Path('C:/Program Files/tk'))
            self.assertEqual(args[-1], 'main.py')
