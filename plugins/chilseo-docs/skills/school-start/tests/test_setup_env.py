import contextlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "setup_env.py"
spec = importlib.util.spec_from_file_location("setup_env", SCRIPT)
setup_env = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup_env)


class SetupEnvTests(unittest.TestCase):
    def test_invalid_option_has_korean_guidance(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--home"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("옵션을 확인해 주세요", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_broken_venv_does_not_abort_check(self):
        with tempfile.TemporaryDirectory() as temp:
            python = setup_env.venv_python(Path(temp))
            python.parent.mkdir(parents=True)
            python.write_text("broken", encoding="utf-8")
            python.chmod(0o755)
            result = subprocess.run([sys.executable, str(SCRIPT), "--check", "--home", temp], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0 if all(setup_env.current_packages()) else 1)
            self.assertIn("없거나 사용할 수 없어요", result.stdout)
            self.assertNotIn("Traceback", result.stderr)

    def test_empty_chilseo_home_uses_default(self):
        with mock.patch.dict(os.environ, {"CHILSEO_HOME": ""}), \
             mock.patch.object(setup_env, "current_packages", return_value=(True, True)), \
             mock.patch.object(setup_env, "venv_packages", return_value=None) as check, \
             mock.patch.object(setup_env, "node_text", return_value="없어요"), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(setup_env.run(["--check"]), 0)
            check.assert_called_once_with(setup_env.venv_python(Path.home() / ".chilseo"))

    def test_venv_python_paths(self):
        home = Path("example")
        self.assertEqual(setup_env.venv_python(home, "posix"), home / "venv" / "bin" / "python")
        self.assertEqual(setup_env.venv_python(home, "nt"), home / "venv" / "Scripts" / "python.exe")

    def test_check_does_not_create_home(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "absent"
            result = subprocess.run([sys.executable, str(SCRIPT), "--check", "--home", str(home)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0 if all(setup_env.current_packages()) else 1)
            self.assertFalse(home.exists())
            for heading in ("Python:", "현재 Python의 문서 도구:", "준비 폴더:", "Node.js:", "→ "):
                self.assertIn(heading, result.stdout)

    def test_install_uses_venv_python_and_verifies(self):
        calls = []
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            python = setup_env.venv_python(home)

            def runner(command, **kwargs):
                calls.append(command)
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            output = io.StringIO()
            with mock.patch.object(setup_env, "current_packages", return_value=(False, False)), \
                 mock.patch.object(setup_env, "venv_packages", side_effect=[None, (True, True)]), \
                 mock.patch.object(setup_env, "node_text", return_value="없음"), \
                 mock.patch.object(setup_env.subprocess, "run", side_effect=runner), \
                 contextlib.redirect_stdout(output):
                self.assertEqual(setup_env.run(["--home", str(home)]), 0)
            self.assertEqual(calls[0], [sys.executable, "-m", "venv", str(home / "venv")])
            self.assertEqual(calls[1], [str(python), "-m", "pip", "install", "--disable-pip-version-check", "lxml>=5", "python-hwpx>=6.6"])
            self.assertIn("→ 준비 끝", output.getvalue())
            self.assertFalse(home.exists())

    def test_install_network_failure_guidance(self):
        failure = subprocess.CompletedProcess([], 1, stdout="", stderr="connection timed out")
        with mock.patch.object(setup_env, "current_packages", return_value=(False, False)), \
             mock.patch.object(setup_env, "venv_packages", return_value=(False, False)), \
             mock.patch.object(setup_env, "node_text", return_value="없음"), \
             mock.patch.object(setup_env.subprocess, "run", return_value=failure), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(setup_env.run(["--home", "example"]), 1)
            self.assertIn("정보 담당자", output.getvalue())
            self.assertIn("python.org와 pypi.org", output.getvalue())


if __name__ == "__main__":
    unittest.main()
