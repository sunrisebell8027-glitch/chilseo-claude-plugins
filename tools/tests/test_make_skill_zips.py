import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import make_skill_zips


class PackTests(unittest.TestCase):
    def test_keeps_skill_root_and_excludes_junk_private_files_and_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / 'sample'
            (skill / 'scripts').mkdir(parents=True)
            (skill / 'tests').mkdir()
            (skill / 'dist').mkdir()
            (skill / '.pytest_cache').mkdir()
            (skill / 'SKILL.md').write_text('skill', encoding='utf-8')
            (skill / 'scripts' / 'run.py').write_text('print(1)', encoding='utf-8')
            for name, parent in [('.env', skill), ('token.txt', skill / 'tests'), ('bundle.js', skill / 'dist'), ('state', skill / '.pytest_cache')]:
                (parent / name).write_text('private or junk', encoding='utf-8')
            secret = root / 'outside.txt'
            secret.write_text('outside secret', encoding='utf-8')
            (skill / 'leak.txt').symlink_to(secret)
            out = root / 'out'
            out.mkdir()
            archive = make_skill_zips.pack(skill, out)
            with zipfile.ZipFile(archive) as z:
                names = z.namelist()
                self.assertIn('sample/SKILL.md', names)
                self.assertIn('sample/scripts/run.py', names)
                self.assertEqual(len(names), 2)

    def test_main_skips_code_only_skill_and_packs_other_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('school-start', 'sample'):
                skill = root / 'plugins' / 'example' / 'skills' / name
                skill.mkdir(parents=True)
                (skill / 'SKILL.md').write_text('skill', encoding='utf-8')

            output = StringIO()
            (root / 'dist').mkdir()
            (root / 'dist' / 'school-start.zip').write_bytes(b'old package')
            with patch.object(make_skill_zips, 'ROOT', root), redirect_stdout(output):
                self.assertEqual(make_skill_zips.main(), 0)

            self.assertFalse((root / 'dist' / 'school-start.zip').exists())
            self.assertTrue((root / 'dist' / 'sample.zip').exists())
            self.assertIn('school-start', output.getvalue())
            self.assertIn('제외해요', output.getvalue())


if __name__ == '__main__':
    unittest.main()
