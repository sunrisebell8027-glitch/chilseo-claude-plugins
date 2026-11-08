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
            fetch_assets.list_assets(Path(tmp))


if __name__ == '__main__':
    unittest.main()
