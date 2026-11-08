import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / 'scripts/gate.py'
OTHER_GATE = ROOT.parent / ('school-newsletter' if ROOT.name == 'school-plan-hwpx' else 'school-plan-hwpx') / 'scripts/gate.py'


class GateExitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.valid = Path(cls.temp.name) / 'valid.hwpx'
        result = subprocess.run(
            [sys.executable, str(ROOT / 'scripts/build_newsletter.py'),
             str(ROOT / 'examples/sample_museum_trip.json'), '-o', str(cls.valid)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
        cls.invalid = Path(cls.temp.name) / 'invalid.hwpx'
        with zipfile.ZipFile(cls.valid) as source:
            entries = [(info, source.read(info)) for info in source.infolist()]
        with zipfile.ZipFile(cls.invalid, 'w') as target:
            for info, data in entries[1:2] + entries[:1] + entries[2:]:
                target.writestr(info, data)

    def gate(self, *paths):
        return subprocess.run([sys.executable, str(GATE), *map(str, paths)],
                              capture_output=True, text=True)

    def test_valid_document(self):
        result = self.gate(self.valid)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('통과', result.stdout)

    def test_blocking_finding(self):
        result = self.gate(self.valid, self.invalid)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('⛔', result.stdout)

    def test_missing_file(self):
        result = self.gate(self.invalid, Path(self.temp.name) / 'missing.hwpx')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('파일을 열 수 없어요', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_wrong_arguments(self):
        for args in ((), ('--wrong',)):
            with self.subTest(args=args):
                result = self.gate(*args)
                self.assertEqual(result.returncode, 2)
                self.assertIn('파일', result.stderr)
                self.assertNotIn('Traceback', result.stderr)

    def test_gate_scripts_are_identical(self):
        self.assertEqual(GATE.read_bytes(), OTHER_GATE.read_bytes())


if __name__ == '__main__':
    unittest.main()
