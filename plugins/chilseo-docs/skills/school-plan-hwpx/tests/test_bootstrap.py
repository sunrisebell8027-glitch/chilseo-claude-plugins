import os
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath
from unittest import mock

SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = sorted((SKILL / 'scripts').glob('*.py'))
SCRIPTS = [p for p in SCRIPTS if p.name in ('build.py', 'build_newsletter.py', 'clean_template.py', 'gate.py')]


class BootstrapTests(unittest.TestCase):
    def test_gate_copies_match(self):
        other = 'school-newsletter' if SKILL.name == 'school-plan-hwpx' else 'school-plan-hwpx'
        self.assertEqual((SKILL / 'scripts/gate.py').read_bytes(),
                         (SKILL.parent / other / 'scripts/gate.py').read_bytes())

    def test_paths_and_candidate_order(self):
        for script in SCRIPTS:
            with self.subTest(script=script.name):
                namespace = runpy.run_path(str(script))
                with mock.patch.object(os, 'name', 'posix'):
                    self.assertEqual(namespace['_venv_python'](PurePosixPath('/env')), PurePosixPath('/env/bin/python'))
                with mock.patch.object(os, 'name', 'nt'):
                    self.assertEqual(namespace['_venv_python'](PurePosixPath('/env')), PurePosixPath('/env/Scripts/python.exe'))
                with tempfile.TemporaryDirectory() as tmp:
                    with mock.patch.dict(os.environ, {'CHILSEO_PYTHON': 'chosen-python', 'CHILSEO_HOME': tmp}):
                        candidates = namespace['_python_candidates']()
                    self.assertEqual(candidates, ['chosen-python', namespace['_venv_python'](Path(tmp) / 'venv'),
                                                 namespace['_venv_python'](SKILL / '.venv'),
                                                 namespace['_venv_python'](Path.cwd() / '.venv')])

    def test_missing_dependency_exits_with_help(self):
        with tempfile.TemporaryDirectory() as tmp:
            shadow = Path(tmp) / 'lxml'
            shadow.mkdir()
            (shadow / '__init__.py').write_text('')
            env = os.environ.copy()
            env.update(PYTHONPATH=tmp, CHILSEO_HOME=tmp, PATH='')
            env.pop('CHILSEO_PYTHON', None)
            env.pop('CHILSEO_BOOTSTRAPPED', None)
            for script in SCRIPTS:
                with self.subTest(script=script.name):
                    result = subprocess.run([sys.executable, str(script)], cwd=tmp, env=env, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 2)
                    for phrase in ('lxml과 python-hwpx가 필요해요', '시작하기', 'school-start',
                                   'python3 -m pip install -r ' + str(SKILL / 'requirements.txt'),
                                   'externally-managed-environment', '별도 설치 폴더'):
                        self.assertIn(phrase, result.stderr)
                    self.assertNotIn('Traceback', result.stderr)

    def test_candidate_reexecutes_and_propagates_status(self):
        for script in SCRIPTS:
            with self.subTest(script=script.name):
                ns = runpy.run_path(str(script))
                calls = []
                def run(args, **kwargs):
                    calls.append((args, kwargs))
                    return subprocess.CompletedProcess(args, 0 if len(calls) == 1 else 7)
                with mock.patch.dict(os.environ, {'CHILSEO_PYTHON': '/candidate/python'}, clear=True), \
                     mock.patch.object(ns['_bootstrap'].__globals__['shutil'], 'which', return_value='/candidate/python'), \
                     mock.patch.object(subprocess, 'run', side_effect=run):
                    with self.assertRaises(SystemExit) as result:
                        ns['_bootstrap']()
                self.assertEqual(result.exception.code, 7)
                self.assertEqual(calls[0][0], ['/candidate/python', '-c', 'import lxml'])
                self.assertEqual(calls[1][0], ['/candidate/python', *sys.argv])
                self.assertEqual(calls[1][1]['env']['CHILSEO_BOOTSTRAPPED'], '1')

    @unittest.skipIf(os.name == 'nt', 'Executable wrapper requires POSIX')
    def test_real_candidate_is_launched(self):
        with tempfile.TemporaryDirectory() as tmp:
            shadow = Path(tmp) / 'lxml'
            shadow.mkdir()
            (shadow / '__init__.py').write_text('')
            wrapper = Path(tmp) / 'candidate'
            marker = Path(tmp) / 'called'
            wrapper.write_text('#!' + sys.executable + "\nimport pathlib, sys\n"
                               + "if sys.argv[1] == '-c': sys.exit(0)\n"
                               + 'pathlib.Path(' + repr(str(marker)) + ").write_text('called')\nsys.exit(7)\n")
            wrapper.chmod(0o755)
            env = os.environ.copy()
            env.update(PYTHONPATH=tmp, CHILSEO_HOME=tmp, CHILSEO_PYTHON=str(wrapper))
            env.pop('CHILSEO_BOOTSTRAPPED', None)
            for script in SCRIPTS:
                with self.subTest(script=script.name):
                    marker.unlink(missing_ok=True)
                    result = subprocess.run([sys.executable, str(script)], cwd=tmp, env=env, capture_output=True)
                    self.assertEqual(result.returncode, 7)
                    self.assertEqual(marker.read_text(), 'called')

    def test_bootstrap_guard_does_not_retry(self):
        for script in SCRIPTS:
            with self.subTest(script=script.name):
                ns = runpy.run_path(str(script))
                with mock.patch.dict(os.environ, {'CHILSEO_BOOTSTRAPPED': '1'}), \
                     mock.patch.object(subprocess, 'run') as run, \
                     mock.patch('sys.stderr'):
                    with self.assertRaises(SystemExit) as result:
                        ns['_bootstrap']()
                self.assertEqual(result.exception.code, 2)
                run.assert_not_called()

    def test_clean_missing_file_has_korean_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, str(SKILL / 'scripts/clean_template.py'),
                                     str(Path(tmp) / '없는 파일.hwpx'), '-o', str(Path(tmp) / '결과.hwpx')],
                                    capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('입력 파일', result.stderr)
        self.assertNotIn('Traceback', result.stderr)
