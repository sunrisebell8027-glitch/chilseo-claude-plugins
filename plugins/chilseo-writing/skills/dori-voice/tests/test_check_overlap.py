import subprocess
import sys
import tempfile
import time
import random
import unittest
from unittest import mock
import importlib.util
import io
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/check_overlap.py'
sys.path.insert(0, str(SCRIPT.parent))
spec = importlib.util.spec_from_file_location('check_overlap', SCRIPT)
overlap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(overlap)


class OverlapTests(unittest.TestCase):
    def run_check(self, left, right, *args):
        with tempfile.TemporaryDirectory(prefix='비교 공간 ') as tmp:
            first, second = Path(tmp) / '검사.txt', Path(tmp) / '원고.md'
            first.write_text(left, encoding='utf-8')
            second.write_text(right, encoding='utf-8')
            return subprocess.run([sys.executable, str(SCRIPT), str(first), '--against', str(second), *args], capture_output=True, text=True)

    def test_overlap_ignores_punctuation_and_space(self):
        result = self.run_check('가나다라 마바사아, 자차카타파하.', '가나다라마바사아자차카타파하')
        self.assertEqual(result.returncode, 1)
        self.assertIn('가나다라마바사아자차카타파하', result.stdout)
        self.assertIn(':1:1', result.stdout)

    def test_no_overlap(self):
        self.assertEqual(self.run_check('가나다라마바사아자차카타파', '가나다라마바사아자차카타파').returncode, 0)

    def test_long_text_finishes_quickly(self):
        rng = random.Random(123)
        text = ''.join(rng.choices('가나다라마바사아자차카타파하', k=200_000))
        start = time.monotonic()
        result = self.run_check(text, text, '--min', '14')
        self.assertLess(time.monotonic() - start, 10)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(len(result.stdout.splitlines()), 1)
        self.assertIn(text, result.stdout)

    def test_separate_runs_and_positions(self):
        result = self.run_check('가나다라X마바사아', '가나다라Y마바사아', '--min', '4')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(len(result.stdout.splitlines()), 2)
        self.assertIn(':1:6', result.stdout)

    def test_overlapping_runs_are_not_skipped(self):
        result = self.run_check('abcde', 'abcXbcde', '--min', '3')
        self.assertIn('abc', result.stdout)
        self.assertIn('bcde', result.stdout)

    def test_timeout_skips_comparison_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / '원고.txt'
            slow = Path(tmp) / '느린 파일.txt'
            other = Path(tmp) / '비교.txt'
            for path in (target, slow, other):
                path.touch()
            def read(path):
                if path == slow:
                    raise TimeoutError()
                return '가나다라마바사아자차카타파하'
            args = ['check_overlap.py', str(target), '--against', str(slow), str(other)]
            with mock.patch.object(overlap, 'read_text', side_effect=read), mock.patch.object(sys, 'argv', args), mock.patch('sys.stderr', new_callable=io.StringIO) as err, mock.patch('sys.stdout', new_callable=io.StringIO) as out:
                self.assertEqual(overlap.main(), 2)
                self.assertIn('느린 파일.txt', err.getvalue())
                self.assertIn('비교.txt', out.getvalue())

    def test_invalid_minimum(self):
        result = self.run_check('가', '가', '--min', '0')
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
