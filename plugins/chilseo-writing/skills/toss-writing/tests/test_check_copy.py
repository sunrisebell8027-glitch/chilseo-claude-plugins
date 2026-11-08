import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'check_copy.py'
spec = importlib.util.spec_from_file_location('check_copy', SCRIPT)
check_copy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_copy)


class CheckCopyTests(unittest.TestCase):
    def test_finds_visible_problematic_copy_but_skips_comment_and_style(self):
        html = '''<button>취소</button><!-- 제출합니다 -->
<style>.message { content: "Error:"; }</style>
<p>저장되었습니다.</p>'''
        findings = check_copy.check_text(html, strict=False)
        hits = [(item[3], item[5]) for item in findings]
        self.assertIn(('취소 버튼', '취소'), hits)
        self.assertIn(('수동형', '저장되었습니다'), hits)
        self.assertNotIn(('해요체', '제출합니다'), hits)
        self.assertNotIn(('기술 메시지 노출', 'Error:'), hits)

    def test_missing_target_returns_korean_error_and_failure_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = str(Path(tmp) / '없는 파일.html')
            from unittest.mock import patch
            import contextlib
            import io
            stdout, stderr = io.StringIO(), io.StringIO()
            with patch('sys.argv', ['check_copy.py', missing]), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = check_copy.main()
            self.assertEqual(result, 1)
            self.assertIn('찾을 수 없어요', stderr.getvalue())

    def test_skips_korean_css_content_even_when_style_is_inline(self):
        html = '<style>.notice::after { content: "저장되었습니다"; }</style><p>저장되었습니다.</p>'
        findings = check_copy.check_text(html, strict=False)
        self.assertTrue(findings)
        self.assertTrue(all(item[1] > html.index('</style>') + len('</style>')
                            for item in findings))


if __name__ == '__main__':
    unittest.main()
