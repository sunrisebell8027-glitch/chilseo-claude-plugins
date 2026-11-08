#!/usr/bin/env python3
import argparse
import importlib
import os
from pathlib import Path
import shutil
import subprocess
import sys


PACKAGES = ("lxml", "hwpx")


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "→ 입력한 옵션을 확인해 주세요. --check와 --home 폴더경로를 쓸 수 있어요.\n")


def venv_python(home, platform=None):
    if (platform or os.name) in ("nt", "win32"):
        return Path(home) / "venv" / "Scripts" / "python.exe"
    return Path(home) / "venv" / "bin" / "python"


def current_packages():
    found = []
    for name in PACKAGES:
        try:
            importlib.import_module(name)
            found.append(True)
        except ImportError:
            found.append(False)
    return tuple(found)


def venv_packages(python):
    if not python.is_file():
        return None
    code = ("import importlib\n"
            "for name in ('lxml', 'hwpx'):\n"
            " try:\n  importlib.import_module(name)\n  print('1')\n"
            " except ImportError:\n  print('0')\n")
    try:
        result = subprocess.run([str(python), "-c", code], capture_output=True, text=True)
    except OSError:
        return None
    if result.returncode != 0 or result.stdout.splitlines() not in (
        ['0', '0'], ['0', '1'], ['1', '0'], ['1', '1']
    ):
        return None
    return tuple(value == '1' for value in result.stdout.splitlines())


def package_text(found):
    return ", ".join(f"{name}: {'있어요' if ok else '없어요'}"
                     for name, ok in zip(("lxml", "python-hwpx"), found))


def node_text():
    node = shutil.which("node")
    if node:
        try:
            result = subprocess.run([node, "--version"], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except OSError:
            pass
    return "없어요 (한글 미리보기 kordoc을 쓸 때만 필요해요)"


def run(args=None):
    parser = Parser(add_help=False)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--home", type=Path, default=Path(os.environ.get("CHILSEO_HOME") or Path.home() / ".chilseo"))
    options = parser.parse_args(args)
    home = options.home.expanduser()
    python = venv_python(home)
    current = current_packages()
    prepared = venv_packages(python)
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")
    print(f"현재 Python의 문서 도구: {package_text(current)}")
    if prepared is None:
        print(f"준비 폴더: 없거나 사용할 수 없어요 ({python.parent.parent})")
    else:
        print(f"준비 폴더: 있어요 ({python.parent.parent}), {package_text(prepared)}")
    print(f"Node.js: {node_text()}")

    if all(current) or (prepared is not None and all(prepared)):
        print("→ 준비 끝! 문서를 만들 수 있어요.")
        return 0
    if options.check:
        print("→ 문서 도구가 필요해요. 설치에 동의한 뒤 이 스크립트를 --check 없이 실행해 주세요.")
        return 1

    try:
        if prepared is None:
            result = subprocess.run([sys.executable, "-m", "venv", str(home / "venv")], capture_output=True, text=True)
            if result.returncode:
                if "permission denied" in result.stderr.lower() or "access is denied" in result.stderr.lower():
                    print("→ 폴더를 만들 권한이 없어요. --home 뒤에 다른 폴더를 지정해 다시 실행해 주세요.")
                else:
                    print(f'→ {sys.executable}에서 준비 폴더를 만들지 못했어요. Python을 다시 설치해 주세요. Windows에서는 설치할 때 "Add python.exe to PATH"를 선택해 주세요.')
                return 1
        result = subprocess.run([str(python), "-m", "pip", "install", "--disable-pip-version-check", "lxml>=5", "python-hwpx>=6.6"], capture_output=True, text=True)
        if result.returncode:
            error = (result.stderr + result.stdout).lower()
            if "permission denied" in error or "access is denied" in error:
                print("→ 설치할 권한이 없어요. --home 뒤에 다른 폴더를 지정해 다시 실행해 주세요.")
            elif any(word in error for word in ("connection", "network", "timed out", "name resolution", "unreachable", "temporary failure")):
                print("→ 인터넷에 연결하지 못했어요. 학교 정보 담당자에게 python.org와 pypi.org 접속을 허용해 달라고 요청해 주세요.")
            else:
                print("→ 문서 도구를 설치하지 못했어요. Python과 인터넷 연결을 확인하고 다시 실행해 주세요.")
            return 1
        verified = venv_packages(python)
        if verified is not None and all(verified):
            print("→ 준비 끝! 문서를 만들 수 있어요.")
            return 0
        print("→ 설치한 문서 도구를 확인하지 못했어요. Python을 확인하고 다시 실행해 주세요.")
        return 1
    except PermissionError:
        print("→ 폴더를 사용하거나 설치할 권한이 없어요. --home 뒤에 다른 폴더를 지정해 다시 실행해 주세요.")
        return 1
    except OSError:
        print(f'→ {sys.executable}에서 준비 폴더나 설치 도구를 실행하지 못했어요. Python을 다시 설치해 주세요. Windows에서는 "Add python.exe to PATH"를 선택해 주세요.')
        return 1


def main():
    try:
        return run()
    except Exception:
        print("→ 확인 중 문제가 생겼어요. Python을 확인한 뒤 다시 실행해 주세요.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
