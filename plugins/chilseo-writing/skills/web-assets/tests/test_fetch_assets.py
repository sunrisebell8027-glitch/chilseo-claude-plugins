import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'fetch_assets.py'
spec = importlib.util.spec_from_file_location('fetch_assets', SCRIPT)
fetch_assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch_assets)


class FetchAssetsTests(unittest.TestCase):
    def test_icon_names_cannot_escape_vendor_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            vendor = project / 'assets' / 'vendor'
            notices = fetch_assets.Notices(project)
            with patch.object(fetch_assets, 'download', return_value=True) as download:
                fetch_assets.fetch_icons(vendor, notices, 'lucide', ['users', '../escape', 'a/b', ''])
            icon_calls = [call for call in download.call_args_list
                          if call.args[1].suffix == '.svg']
            self.assertEqual(len(icon_calls), 1)
            self.assertEqual(icon_calls[0].args[1], vendor / 'lucide' / 'users.svg')
            self.assertFalse((project / 'assets' / 'escape.svg').exists())

    def test_offline_download_failure_is_reported_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'asset.svg'
            with patch.object(fetch_assets.urllib.request, 'urlopen', side_effect=OSError('offline')):
                self.assertFalse(fetch_assets.download('https://example.invalid/file', dest))
            self.assertFalse(dest.exists())

    def test_list_works_with_korean_and_spaced_project_path(self):
        with tempfile.TemporaryDirectory(prefix='학교 앱 ') as tmp:
            from unittest.mock import patch
            import contextlib
            import io
            with patch('sys.argv', ['fetch_assets.py', tmp, '--list']), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(fetch_assets.main(), 0)

    def test_missing_project_is_reported_without_traceback(self):
        with tempfile.TemporaryDirectory(prefix='없는 학교 앱 ') as tmp:
            missing = str(Path(tmp) / '없는 폴더')
            from unittest.mock import patch
            import contextlib
            import io
            stderr = io.StringIO()
            with patch('sys.argv', ['fetch_assets.py', missing, '--list']), \
                    contextlib.redirect_stderr(stderr):
                self.assertEqual(fetch_assets.main(), 1)
            self.assertIn('프로젝트 폴더가 없어요', stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
