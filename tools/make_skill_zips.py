#!/usr/bin/env python3
"""Pack each plugin skill as a Claude app skill zip (one folder with SKILL.md) into dist/."""
import sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {
    '__pycache__', '.venv', 'venv', 'tests', 'evals', 'dist', 'build',
    '.pytest_cache', '.mypy_cache', '.ruff_cache', 'node_modules',
}
SKIP_FILES = {'.DS_Store', '.env', '.env.local', '.env.development', '.env.production'}
PRIVATE_NAMES = {'.npmrc', '.pypirc', 'credentials', 'credentials.json', 'secrets.json'}


def pack(skill, dist):
    target = dist / f'{skill.name}.zip'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in sorted(skill.rglob('*')):
            rel = path.relative_to(skill)
            if (path.is_dir() or path.is_symlink() or path.name in SKIP_FILES
                    or path.name.lower() in PRIVATE_NAMES
                    or path.name.lower().startswith('.env.')
                    or SKIP_DIRS & set(rel.parts) or path.suffix == '.pyc'):
                continue
            z.write(path, Path(skill.name) / rel)
    return target


def main():
    dist = ROOT / 'dist'
    dist.mkdir(exist_ok=True)
    skills = sorted(p.parent for p in ROOT.glob('plugins/*/skills/*/SKILL.md'))
    if not skills:
        print('No skills found', file=sys.stderr)
        return 1
    for skill in skills:
        target = pack(skill, dist)
        print(f'{target.relative_to(ROOT)}  {target.stat().st_size // 1024} KB')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
