import os
import shutil
import base64
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from core.data import CATEGORIES
from core.launcher import _download_tool, _tool_command


class ZimmermanTests(unittest.TestCase):
    def test_full_official_catalogue_with_isolated_dependencies(self):
        tools = next(c for c in CATEGORIES if c['id'] == 'ericzimmerman')['tools']
        self.assertEqual(len(tools), 26)
        self.assertEqual(len({t['path'].split('/')[0] for t in tools}), 26)
        for t in tools:
            self.assertTrue(t['run_as_admin'])
            self.assertTrue(t['archive'])
            self.assertTrue(t['url'].startswith('https://download.ericzimmermanstools.com/'))

    def test_srum_console_collects_required_parameters(self):
        command = _tool_command(r'C:\Tools\SrumECmd.exe', {'name': 'SrumECmd', 'runner': 'zimmerman_cli'})
        self.assertIn('-NoExit', command)
        script = base64.b64decode(command[-1]).decode('utf-16-le')
        self.assertIn('if ($true)', script)
        self.assertIn("@('-f', $source, '--csv', $destination)", script)
        self.assertIn("@('-r', $registry)", script)
        self.assertIn('CommandLineToArgvW("tool " + text', script)
        self.assertNotIn('Invoke-Expression', script)

    def test_nested_zip_extracted_at_package_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / 'download.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('App/App.exe', b'MZ-test')
                z.writestr('App/helper.dll', b'dependency')
            target = root / 'isolated' / 'App' / 'App.exe'
            tool = dict(name='App', path='isolated/App/App.exe', archive=True,
                        archive_entry='App/App.exe', url='https://example.test/tool.zip')
            with patch('core.launcher._download_to_temp', return_value=str(archive)):
                self.assertEqual(_download_tool('ericzimmerman', tool, str(target)), str(target))
            self.assertTrue(target.is_file())
            self.assertEqual((target.parent / 'helper.dll').read_bytes(), b'dependency')
            self.assertFalse((target.parent / 'App').exists())


class ZimmermanLocateTests(unittest.TestCase):
    def setUp(self):
        from core import zimmerman_fetch
        patcher = patch.object(zimmerman_fetch, 'EXTERNAL_METHODS', ())
        patcher.start()
        self.addCleanup(patcher.stop)

    def _tool(self, name, path, entry):
        return dict(name=name, path=path, archive=True, archive_entry=entry,
                    url='https://download.ericzimmermanstools.com/net9/%s.zip' % name)

    def _install(self, files, tool, target):
        with tempfile.TemporaryDirectory() as zdir:
            archive = Path(zdir) / 'x.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                for name, data in files.items():
                    z.writestr(name, data)
            with patch('core.launcher._download_to_temp', return_value=str(archive)):
                return _download_tool('ericzimmerman', tool, str(target))

    def test_executable_found_by_name_when_zip_layout_differs_from_catalogue(self):
        with tempfile.TemporaryDirectory() as directory:
            # Catalogue expects Pkg/Pkg/Pkg.exe but the ZIP is flat and differently cased.
            tool = self._tool('Pkg', 'Pkg/Pkg/Pkg.exe', 'Pkg/Pkg.exe')
            target = Path(directory) / 'Pkg' / 'Pkg' / 'Pkg.exe'
            result = self._install({'PKG.EXE': b'MZ-flat', 'x.dll': b'd'}, tool, target)
            self.assertEqual(Path(result).read_bytes(), b'MZ-flat')
            self.assertTrue(Path(result).is_relative_to(Path(directory) / 'Pkg'))
            self.assertTrue((Path(result).parent / 'x.dll').is_file())

    def test_executable_found_in_unexpected_subfolder(self):
        with tempfile.TemporaryDirectory() as directory:
            tool = self._tool('Pkg', 'Pkg/Pkg.exe', 'Pkg.exe')
            target = Path(directory) / 'Pkg' / 'Pkg.exe'
            result = self._install({'Deep/er/pkg.exe': b'MZ-deep', 'Deep/er/a.dll': b'd'}, tool, target)
            self.assertEqual(Path(result).name.lower(), 'pkg.exe')
            self.assertEqual(Path(result).read_bytes(), b'MZ-deep')

    def test_missing_executable_reports_clear_error(self):
        from core.launcher import ToolDownloadError
        with tempfile.TemporaryDirectory() as directory:
            tool = self._tool('Pkg', 'Pkg/Pkg.exe', 'Pkg.exe')
            target = Path(directory) / 'Pkg' / 'Pkg.exe'
            with self.assertRaises(ToolDownloadError):
                self._install({'other.txt': b'x'}, tool, target)

    def test_official_mirror_used_when_primary_fails(self):
        from core.launcher import ToolDownloadError
        with tempfile.TemporaryDirectory() as directory:
            tool = self._tool('Pkg', 'Pkg/Pkg.exe', 'Pkg.exe')
            target = Path(directory) / 'Pkg' / 'Pkg.exe'
            archive = Path(directory) / 'x.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('Pkg.exe', b'MZ-mirror')
            calls = []

            def fake(url, *a, **k):
                calls.append(url)
                if 'download.ericzimmermanstools.com' in url:
                    raise ToolDownloadError('primary down')
                return str(archive)
            with patch('core.launcher._download_to_temp', side_effect=fake):
                _download_tool('ericzimmerman', tool, str(target))
            self.assertEqual(len(calls), 2)
            self.assertTrue(calls[1].startswith('https://f001.backblazeb2.com/file/EricZimmermanTools/net9/'))
            self.assertEqual(target.read_bytes(), b'MZ-mirror')


class ZimmermanDiscoveryTests(unittest.TestCase):
    def setUp(self):
        from core import zimmerman_fetch
        patcher = patch.object(zimmerman_fetch, 'EXTERNAL_METHODS', ())
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_live_official_link_used_when_static_urls_fail_and_all_errors_reported(self):
        from core.launcher import ToolDownloadError
        tool = dict(name='Pkg', path='Pkg/Pkg.exe', archive=True, archive_entry='Pkg.exe',
                    url='https://download.ericzimmermanstools.com/net9/Pkg.zip')
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / 'x.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('Pkg.exe', b'MZ-live')
            page = '| Pkg | [2.2](https://download.ericzimmermanstools.com/net9/Pkg.zip) &vert; [x](https://download.ericzimmermanstools.com/net9/Other.zip) |'
            live = 'https://download.ericzimmermanstools.com/net9/pkg.zip'
            calls = []

            def fake(url, *a, **k):
                calls.append(url)
                raise ToolDownloadError('HTTP Error 404')
            with patch('core.launcher._download_to_temp', side_effect=fake), \
                 patch('core.launcher._read_small_page', return_value=page):
                with self.assertRaises(ToolDownloadError) as ctx:
                    _download_tool('ericzimmerman', tool, str(Path(directory) / 'Pkg' / 'Pkg.exe'))
            message = str(ctx.exception)
            self.assertIn('download.ericzimmermanstools.com [python]: HTTP Error 404', message)
            self.assertIn('_manual_zips', message)
            log = (Path(directory) / 'ultimo_error_descarga.log').read_text(encoding='utf-8')
            self.assertIn('f001.backblazeb2.com [python]: HTTP Error 404', log)
            self.assertIn('chocolatey [python]: HTTP Error 404', log)
            self.assertEqual(len(calls), 3)  # oficial, mirror, chocolatey (el enlace descubierto es el mismo)

    def test_discovered_different_link_is_tried(self):
        from core.launcher import _discover_zimmerman_urls
        tool = dict(url='https://download.ericzimmermanstools.com/net9/TimelineExplorer.zip')
        page = ('[2.1](https://f001.backblazeb2.com/file/EricZimmermanTools/net9/TimelineExplorer.zip) '
                '[old](https://download.ericzimmermanstools.com/net6/TimelineExplorer.zip) '
                '[n](https://download.ericzimmermanstools.com/net9/TimelineExplorer.zip)')
        with patch('core.launcher._read_small_page', return_value=page):
            self.assertEqual(_discover_zimmerman_urls(tool),
                             ['https://download.ericzimmermanstools.com/net9/TimelineExplorer.zip'])


class ZimmermanFetchMethodsTests(unittest.TestCase):
    def _zip(self, directory, name='Pkg.zip', exe=b'MZ-ok'):
        archive = Path(directory) / name
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr('Pkg.exe', exe)
        return archive

    def test_curl_used_when_python_fails(self):
        from core import zimmerman_fetch as zf
        with tempfile.TemporaryDirectory() as d:
            source = self._zip(d)
            target = Path(d) / 'pkg'

            def fake_curl(url, dest):
                shutil.copyfile(source, dest)
            with patch.object(zf, 'EXTERNAL_METHODS', (('curl', fake_curl),)):
                path = zf.fetch_zip(['https://x.test/net9/Pkg.zip'], 'Pkg.zip', str(target),
                                    python_download=lambda url: (_ for _ in ()).throw(OSError('403')))
            self.assertTrue(zipfile.is_zipfile(path))

    def test_html_error_page_is_rejected_and_next_method_used(self):
        from core import zimmerman_fetch as zf
        with tempfile.TemporaryDirectory() as d:
            source = self._zip(d)
            target = Path(d) / 'pkg'

            def html_python(url):
                fd, p = tempfile.mkstemp(dir=target)
                os.write(fd, b'<html>blocked</html>'); os.close(fd)
                return p

            def good(url, dest):
                shutil.copyfile(source, dest)
            with patch.object(zf, 'EXTERNAL_METHODS', (('ps', good),)):
                path = zf.fetch_zip(['https://x.test/Pkg.zip'], 'Pkg.zip', str(target), python_download=html_python)
            self.assertTrue(zipfile.is_zipfile(path))

    def test_chocolatey_package_inner_zip_is_extracted(self):
        from core import zimmerman_fetch as zf
        with tempfile.TemporaryDirectory() as d:
            inner = self._zip(d)
            nupkg = Path(d) / 'pkg.nupkg'
            with zipfile.ZipFile(nupkg, 'w') as z:
                z.write(inner, 'tools/Pkg.zip')
                z.writestr('pkg.nuspec', '<x/>')
            target = Path(d) / 'pkg'

            def python_download(url):
                if 'chocolatey.org' in url:
                    return str(shutil.copyfile(nupkg, Path(d) / 'tmp.nupkg'))
                raise OSError('404')
            with patch.object(zf, 'EXTERNAL_METHODS', ()):
                path = zf.fetch_zip(['https://x.test/Pkg.zip'], 'Pkg.zip', str(target), python_download=python_download)
            with zipfile.ZipFile(path) as z:
                self.assertEqual(z.read('Pkg.exe'), b'MZ-ok')

    def test_manual_zip_and_log(self):
        from core import zimmerman_fetch as zf
        with tempfile.TemporaryDirectory() as d:
            manual = Path(d) / '_manual_zips'
            manual.mkdir()
            self._zip(manual, 'pkg.ZIP')
            log = Path(d) / 'err.log'
            fail = lambda url: (_ for _ in ()).throw(OSError('nope'))
            with patch.object(zf, 'EXTERNAL_METHODS', ()):
                path = zf.fetch_zip(['https://x.test/Pkg.zip'], 'Pkg.zip', str(Path(d) / 'pkg'),
                                    python_download=fail, manual_dir=str(manual), log_path=str(log))
                self.assertTrue(zipfile.is_zipfile(path))
                (manual / 'pkg.ZIP').unlink()
                with self.assertRaises(zf.FetchError):
                    zf.fetch_zip(['https://x.test/Pkg.zip'], 'Pkg.zip', str(Path(d) / 'pkg'),
                                 python_download=fail, manual_dir=str(manual), log_path=str(log))
            self.assertIn('x.test [python]: nope', log.read_text(encoding='utf-8'))
