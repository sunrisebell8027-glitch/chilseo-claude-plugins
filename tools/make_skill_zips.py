#!/usr/bin/env python3
"""Pack each plugin skill as a Claude app skill zip (one folder with SKILL.md) into dist/."""
import sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {'__pycache__', '.venv', 'tests'}
SKIP_FILES = {'.DS_Store'}


def pack(skill, dist):
    target = dist / f'{skill.name}.zip'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in sorted(skill.rglob('*')):
            rel = path.relative_to(skill)
            if path.is_dir() or path.name in SKIP_FILES or SKIP_DIRS & set(rel.parts) or path.suffix == '.pyc':
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
