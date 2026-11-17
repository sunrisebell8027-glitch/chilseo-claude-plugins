import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import signal
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE / 'scripts/check_voice.py'
sys.path.insert(0, str(SCRIPT.parent))
spec = importlib.util.spec_from_file_location('check_voice', SCRIPT)
voice = importlib.util.module_from_spec(spec)
spec.loader.exec_module(voice)


def table_rows():
    text = (BASE / 'references/voice-rules.md').read_text(encoding='utf-8')
    text = text.split('### 3.1 ', 1)[1].split('### 3.7 ', 1)[0]
    for line in text.splitlines():
        if line.startswith('|'):
            cells = line.split('|')
            if len(cells) > 3 and cells[1].strip() not in ('쓰지 않음', '---'):
                yield cells[1].strip(), cells[2].strip()


def run(text, *options):
    with tempfile.TemporaryDirectory(prefix='검사 공간 ') as tmp:
        path = Path(tmp) / '원고 파일.md'
        path.write_text(text, encoding='utf-8')
        return subprocess.run([sys.executable, str(SCRIPT), str(path), *options], text=True, capture_output=True)


class VoiceTests(unittest.TestCase):
    def test_general_sentence_patterns(self):
        examples = {
            '극적 도입': ('숨기고 싶은 숫자가 하나 있다', '솔직하게 말해야 할 사실이 있다',
                      '털어놓자면 이야기 하나 있다', '한 줄을 적었다',
                      '아직 내지 않은 세 명이 누구인지 나는 안다',
                      '아직 답하지 않은 두 명이 누구인지 나는 안다', '무엇인지 나는 안다'),
            '격언형 맺음': ('기록은 아이를 재려고 남기는 것이 아니라 알려고 남기는 것이다',
                       '점수는 줄을 세우려고 내는 것이 아니라 도우려고 내는 것이다',
                       '가장 중요한 것은 대화이다', '이 순간이 바로 변화의 시작이다',
                       '함께했다, 그것이 노력의 증거다', '~이 나는 가장 기뻤다'),
            '구호형 목표': ('배움이 교실 밖으로 이어지는 학교', '질문이 다음 수업으로 이어지는 교실',
                       '생각이 함께 자라는 교실', '질문이 피어나는 학급', '대화가 살아 있는 수업'),
        }
        for kind, phrases in examples.items():
            for phrase in phrases:
                with self.subTest(kind=kind, phrase=phrase):
                    text = '"' + phrase + '"' if kind == '구호형 목표' else phrase
                    self.assertIn(kind, [item['kind'] for item in voice.check_text(text)])
        self.assertTrue(next(item for item in voice.check_text('"배움이 교실 밖으로 이어지는 학교"')
                             if item['kind'] == '구호형 목표')['quoted'])

    def test_general_hints_and_conjugated_stems(self):
        cases = [
            ('솔직하게 말해야 할 사실이 있다', '극적 도입', '사실을 바로 쓴다'),
            ('가장 중요한 것은 대화이다', '격언형 맺음', "'나는 ~라고 생각한다'로 바꾼다"),
            ('질문이 다음 수업으로 이어지는 교실', '구호형 목표', '무엇을 어떻게 하는 학교인지 사실로 쓴다'),
            ('# 봄을 지나 만난 수업', '제목', '사실형 명사구로'),
            ('기록이 방학에도 이어졌다', '사물 비유', '쓰다, 적용하다, 계속하다'),
            ('마음이 흔들렸다', '몸·움직임', '집중하지 못하다, 불안하다'),
        ]
        for text, kind, hint in cases:
            with self.subTest(text=text):
                self.assertEqual(hint, next(x['hint'] for x in voice.check_text(text) if x['kind'] == kind))

    def test_original_sentences_are_absent(self):
        fragments = (
            ('솔직하게',
             '숫자',
             '있다'),
            ('판정하려고',
             '이해하려고'),
            ('기록이', '수업',
             '이어지는', '학교'),
            ('다섯', '누구',
             '안다'),
        )
        for folder in (BASE / 'scripts', BASE / 'tests'):
            for path in folder.rglob('*'):
                if path.is_file() and path.suffix in ('.py', '.txt', '.json', '.md'):
                    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
                        for part in re.split(r'''['"]''', line):
                            for words in fragments:
                                with self.subTest(path=path, line=number, words=words):
                                    found = all(word in part for word in words)
                                    if words is fragments[0]:
                                        found = found and part.rstrip(' .,!?').endswith(words[-1])
                                    self.assertFalse(found)

    def test_descriptive_titles(self):
        for title in ('멈췄던 기록이 다시 흐르기까지, 교사들이 움직였다', '봄을 지나 만난 수업',
                      '어제를 지나, 오늘의 교실'):
            with self.subTest(title=title):
                self.assertIn('제목', [item['kind'] for item in voice.check_text('# ' + title)])

    def test_document_table(self):
        for bad, _ in table_rows():
            bad = re.sub(r'\([^)]*\)', '', bad)
            for phrase in re.split(r', (?=(?:[^"]*"[^"]*")*[^"]*$)', bad):
                phrase = phrase.strip('"')
                with self.subTest(phrase=phrase):
                    self.assertTrue(voice.check_text(phrase + '.'), phrase)

    def test_each_table_row_hint(self):
        for bad, good in table_rows():
            bad = re.sub(r'\([^)]*\)', '', bad)
            for phrase in re.split(r', (?=(?:[^"]*"[^"]*")*[^"]*$)', bad):
                phrase = phrase.strip('"')
                with self.subTest(phrase=phrase):
                    findings = voice.check_text(phrase + '.')
                    self.assertIn(good, [item['hint'] for item in findings])


    def test_script_dialogue_quotes_and_multiline(self):
        text = "화자: \"잣대를 확인합니다.\n'힘을 쏟다'라고 말했다.\n잣대를 살폈다.\""
        findings = voice.check_text(text, '대본')
        self.assertEqual([x['quoted'] for x in findings if x['kind'] == '꾸민 말'], [False, False])
        self.assertTrue(next(x for x in findings if x['kind'] == '몸·움직임')['quoted'])
        self.assertEqual(run(text, '--kind', '대본').returncode, 1)
        self.assertTrue(voice.check_text('"잣대"', '원고')[0]['quoted'])

    def test_context_exceptions(self):
        for text in ('시트에 기록이 쌓인다.', 'DB에 기록이 쌓였다.', '기록의 힘', '데이터의 힘',
                     '순간을 살폈다.', '화면이 흐려졌다.', '옷 한 벌', '자료 3벌',
                     '기록됐다.', '제출됐다.', '등록됐다.'):
            with self.subTest(text=text):
                self.assertEqual([], voice.check_text(text))
        for text in ('기록이 쌓였다.', '읽고 쓰는 힘', '생각하는 힘', '흐려졌을 순간', '흐려졌을 순간들',
                     '매뉴얼 한 벌', '안내서 한 벌', '자료 한 벌', '양식 한 벌'):
            with self.subTest(text=text):
                self.assertTrue(voice.check_text(text))
        self.assertTrue(voice.check_text('오래가지 못하다', '원고'))
        self.assertEqual([], voice.check_text('오래가지 못하다', '대본'))

    def test_script_form_lines(self):
        for prefix in ('학습 목표', '학습 내용', '학습 정리', '평가', '자막', '내레이션', '[화면]', '|'):
            text = prefix + ' 확인했다. 도구가 아니라 기준이다. ' * 3
            with self.subTest(prefix=prefix):
                self.assertFalse(any(x['kind'] in ('종결어미', '대조 반복') for x in voice.check_text(text, '대본')))
        self.assertTrue(voice.check_text('자막: 잣대를 보았다.', '대본'))

    def test_contrast_sections_and_wording(self):
        line = '도구가 아니라 충분히 자세한 설명을 먼저 확인한다.\n'
        self.assertEqual([], voice.check_text('도구는 아니고 설명이다.\n' * 3))
        self.assertFalse(any(x['kind'] == '대조 반복' for x in voice.check_text('## 첫째\n' + line * 2 + '### 둘째\n' + line * 2, '대본')))
        findings = voice.check_text('## 첫째\n' + line * 3, '대본')
        self.assertIn('소제목의 대조를 회수하는 문장과 대구는 빼고 세세요', next(x['hint'] for x in findings if x['kind'] == '대조 반복'))

    def test_inanimate_subjects(self):
        for text in ('기록이 줄었다.', '데이터가 늘었다.', '수업이 바뀌었다.', '시간이 달라졌다.',
                     '기록이 남았다.', '자료가 모였다.', 'AI가 제안한다.', '수식이 계산한다.', '표가 보여 준다.'):
            self.assertFalse(any(x['kind'] == '사물 주어' for x in voice.check_text(text)), text)
        self.assertEqual(next(x['confidence'] for x in voice.check_text('지침이 품질을 높였다.') if x['kind'] == '사물 주어'), '낮음')

    def test_read_timeout_and_cleanup(self):
        import file_read
        if not hasattr(signal, 'SIGALRM'):
            self.skipTest('POSIX signal 없음')
        path = mock.Mock()
        def interrupted(**kwargs):
            signal.raise_signal(signal.SIGALRM)
        path.read_text.side_effect = interrupted
        previous = signal.getsignal(signal.SIGALRM)
        with self.assertRaises(TimeoutError):
            file_read.read_text(path)
        self.assertEqual(signal.getsignal(signal.SIGALRM), previous)
        self.assertEqual(signal.alarm(0), 0)

    def test_timeout_skips_file_and_returns_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / '느린 파일.txt'
            second = Path(tmp) / '다음 파일.txt'
            first.touch()
            second.touch()
            def read(path):
                if path == first:
                    raise TimeoutError()
                return '잣대'
            with mock.patch.object(voice, 'read_text', side_effect=read), mock.patch.object(sys, 'argv', ['check_voice.py', str(first), str(second)]), mock.patch('sys.stderr', new_callable=__import__('io').StringIO) as err, mock.patch('sys.stdout', new_callable=__import__('io').StringIO) as out:
                self.assertEqual(voice.main(), 2)
                self.assertIn('느린 파일.txt', err.getvalue())
                self.assertIn('잣대', out.getvalue())

    def test_repeated_expression_on_same_line(self):
        result = run('잣대와 잣대를 살폈다.')
        self.assertEqual(result.stdout.count('— 잣대'), 1)
        self.assertIn('잣대 (2회) → 대신: 평가 기준', result.stdout)
        findings = json.loads(run('"잣대"와 잣대', '--json').stdout)
        self.assertEqual(findings[0]['count'], 2)
        self.assertFalse(findings[0]['quoted'])

    def test_replacements_are_clean(self):
        for _, good in table_rows():
            with self.subTest(good=good):
                self.assertEqual([], voice.check_text(good))

    def test_contrast_threshold(self):
        sentence = '도구가 아니라 질문이 먼저다.\n'
        self.assertEqual(run(sentence * 2).returncode, 0)
        self.assertIn('대조 반복', run(sentence * 3).stdout)

    def test_quote_and_skipped_regions(self):
        result = run('"힘을 쏟았다."\n<!-- 잣대 -->\n```\n찬찬히\n```\n')
        self.assertEqual(result.returncode, 0)
        self.assertIn('(인용)', result.stdout)
        self.assertNotIn('잣대', result.stdout)
        self.assertNotIn('찬찬히', result.stdout)
        self.assertEqual(run('---\n제목: 잣대\n---\n내용이다.').returncode, 0)

    def test_endings(self):
        self.assertEqual(run('확인했습니다.', '--kind', '원고').returncode, 1)
        self.assertEqual(run('확인했다.', '--kind', '대본').returncode, 1)
        self.assertIn('섞임', run('확인했다.\n' * 9 + '확인했습니다.').stdout)
        self.assertEqual(run('"확인했습니다."\n확인했다.', '--kind', '원고').returncode, 0)

    def test_heading_spacing_json(self):
        result = run('# 함께한 여정\n학생이 확인해주었다.', '--json')
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertEqual(set(data[0]), {'file', 'line', 'kind', 'text', 'hint', 'confidence', 'quoted'})
        self.assertEqual({x['kind'] for x in data}, {'제목', '띄어쓰기'})

    def test_missing(self):
        result = subprocess.run([sys.executable, str(SCRIPT), '/tmp/없는-검사-파일.md'], text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stderr)
        self.assertIn('확인', result.stderr)

    def test_conjugations(self):
        for text in ('힘을 쏟았다', '힘을 쏟아', '짚게 했다', '기록이 쌓였다', '기록이 쌓인', '기록이 쌓여', '수업이 돌아갔다'):
            with self.subTest(text=text):
                self.assertTrue(voice.check_text(text))

    def test_conjugated_row_hints(self):
        for phrase, hint in [
            ('힘을 썼다', '집중하다, 시간을 들이다'),
            ('AI를 불렀다', ''),
            ('마음이 흔들렸다', '집중하지 못하다, 불안하다'),
            ('수업이 돌아갔다', '진행하다, 운영에 문제가 없다'),
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(hint, [item['hint'] for item in voice.check_text(phrase)])

    def test_common_verbs_need_context(self):
        for text in ('책을 읽었다.', '길을 통했다.', '학생이 사례를 들었다.'):
            with self.subTest(text=text):
                self.assertEqual([], voice.check_text(text))
        self.assertIn('알려 주다, 제안하다', [x['hint'] for x in voice.check_text('교사가 고칠 곳을 짚어 주었다.')])
        self.assertEqual('낮음', voice.check_text('기차가 터널을 벗어났다.')[0]['confidence'])
        self.assertTrue(voice.check_text('일이 터졌다.'))
        self.assertTrue(voice.check_text('글이 올라왔다.'))

    def test_regular_conjugation_forms(self):
        forms = (
            ('감당하다', '감당했다', '감당하는', '감당할'),
            ('주춤하다', '주춤했다', '주춤하는', '주춤할'),
            ('모여들다', '모여들었다', '모여드는', '모여들'),
            ('요소를 붙이다', '요소를 붙였다', '요소를 붙이는', '요소를 붙일'),
            ('기록이 쌓이다', '기록이 쌓였다', '기록이 쌓이는', '기록이 쌓일'),
        )
        for group in forms:
            for phrase in group:
                with self.subTest(phrase=phrase):
                    self.assertTrue(voice.check_text(phrase))

    def test_author_decisions(self):
        for form in ('짚어 주다', '짚어 줬다', '짚어 준', '짚도록', '짚기', '짚는', '짚었다'):
            with self.subTest(form=form):
                self.assertIn('알려 주다, 제안하다', [x['hint'] for x in voice.check_text(form)])
        for form in ('짚게 하다', '짚게 했다'):
            with self.subTest(form=form):
                self.assertEqual(['고르게 하다'], [x['hint'] for x in voice.check_text(form)])
        for form in ('건네다', '건넨', '건넸다', '건네준'):
            for context in ('피드백', '결과', '의견', '카드', '안내'):
                with self.subTest(form=form, context=context):
                    finding = next(x for x in voice.check_text(context + '을 ' + form) if x['kind'] == '몸·움직임')
                    self.assertEqual(('보내다, 주다', '높음'), (finding['hint'], finding['confidence']))
            finding = next(x for x in voice.check_text('자료를 ' + form) if x['kind'] == '몸·움직임')
            self.assertEqual('낮음', finding['confidence'])
        self.assertEqual('낮음', voice.check_text('결과를 확인했다. 자료를 건넸다.')[0]['confidence'])
        for kind in ('원고', '대본'):
            for adjective in ('신기한', '놀라운', '재미있는', '흥미로운', '이상한'):
                for noun, particle, verb in (('일', '이', '일어나'), ('변화', '가', '생기'), ('일', '', '벌어지')):
                    with self.subTest(kind=kind, adjective=adjective, noun=noun, verb=verb):
                        findings = voice.check_text(f'{adjective} {noun}{particle} {verb}', kind)
                        self.assertIn(('극적 도입', '무슨 일이 있었는지 바로 말한다'),
                                      [(x['kind'], x['hint']) for x in findings])
            for phrase in ('세 갈래', '목표를 잡았다', '자신의 손으로', '추이를 읽었다', '흐름을 읽었다'):
                with self.subTest(kind=kind, phrase=phrase):
                    self.assertTrue(voice.check_text(phrase, kind))
        self.assertTrue(voice.check_text('오래가지 못합니다', '원고'))
        self.assertFalse(voice.check_text('오래가지 못합니다', '대본'))

    def test_goal_with_intervening_words(self):
        for kind in ('원고', '대본'):
            for gap in ('', ' 세', ' 세 가지로', ' 우리 반의 목표로'):
                for ending in ('다', '았다', '은', '고'):
                    text = '목표를' + gap + ' 잡' + ending
                    with self.subTest(kind=kind, text=text):
                        self.assertIn('목표를 정하다', [x['hint'] for x in voice.check_text(text, kind)])
            for text in ('목표를 우리 반의 세 가지로 잡았다', '목표를 정했다. 방향을 잡았다', '목표를 정했다! 잡았다', '목표를 정했다? 잡았다'):
                with self.subTest(kind=kind, text=text):
                    self.assertFalse(any(x['text'].startswith('목표를') for x in voice.check_text(text, kind)))

    def test_combined_syllable_verb_forms(self):
        for kind in ('원고', '대본'):
            for phrase in ('신기한 일이 일어났다', '놀라운 변화가 생겼다',
                           '재미있는 일이 벌어졌습니다', '신기한 일이 일어납니다',
                           '신기한 일이 일어난다', '신기한 일이 일어날',
                           '놀라운 변화가 생깁니다', '놀라운 변화가 생긴', '놀라운 변화가 생길',
                           '재미있는 일이 벌어집니다', '재미있는 일이 벌어진', '재미있는 일이 벌어질'):
                with self.subTest(kind=kind, phrase=phrase):
                    self.assertTrue(any(x['kind'] == '극적 도입' for x in voice.check_text(phrase, kind)))
        for phrase, category in (('힘을 씁니다', '몸·움직임'), ('눈여겨 봅니다', '몸·움직임'),
                                 ('짚어 줍니다', '몸·움직임'), ('수업이 돌아갑니다', '사물 비유'),
                                 ('과제가 밀립니다', '사물 비유'), ('기록이 이어집니다', '사물 비유'),
                                 ('주춤합니다', '사물 비유')):
            with self.subTest(phrase=phrase):
                self.assertTrue(any(x['kind'] == category for x in voice.check_text(phrase)))
        self.assertFalse(voice.check_text('길을 통합니다.'))
        self.assertFalse(voice.check_text('자료가 이어집니다.'))

    def test_sentence_context_and_boundaries(self):
        gap = '아주 자세한 설명을 여러 번 다시 살펴본 다음에 '
        for text in ('방법은 ' + gap + '통했다.', '통했다 ' + gap + '방법이.',
                     '과제는 ' + gap + '밀렸다.', '도구를 ' + gap + '벗어날',
                     '사례에 ' + gap + '머무는', '과제는 ' + gap + '밀릴'):
            with self.subTest(text=text):
                self.assertTrue(any(x['confidence'] == '높음' for x in voice.check_text(text)))
        self.assertFalse(voice.check_text('방법을 확인했다. 길을 통했다.'))
        self.assertEqual('낮음', next(x['confidence'] for x in voice.check_text('과제를 확인했다! 계획이 밀렸다') if x['kind'] == '사물 비유'))

    def test_hints_do_not_match_similar_prefixes(self):
        self.assertEqual('', voice.row_hint('사물 비유', '쌓인 다른 말', ''))
        self.assertEqual('', voice.row_hint('꾸민 말', '읽는 힘', ''))
        self.assertEqual('~의 기록, 기록되다', voice.row_hint('사물 비유', '쌓인 기록', ''))
        self.assertEqual('읽고 쓰는 능력', voice.row_hint('꾸민 말', '쓰는 힘', ''))

    def test_all_regular_table_verbs(self):
        # 르 불규칙과 ㅡ 탈락, 형용사 '멀다', 이미 활용된 문장은 제외한다.
        exceptions = {'힘을 쓰다', '멀다', '가르다', 'AI를 부르다', '옮겨 쓰다',
                      '~뜻으로 읽었다', '세 번 쟀다', '제자리였다', '걱정부터 적었다',
                      '프로젝트를 실시하였다', '중점을 두었다', '학습자 주도적 퇴고 활동을 전개하였다',
                      '역량을 함양하였다'}
        def forms(phrase):
            stem = phrase[:-1]
            last = ord(stem[-1]) - 0xAC00
            vowel, final = (last % 588) // 28, last % 28
            past = stem + ('았다' if vowel in (0, 8) else '었다')
            if not final and vowel in (0, 4):
                past = stem[:-1] + chr(ord(stem[-1]) + 20) + '다'
            elif not final and vowel == 20:
                past = stem[:-1] + chr(ord(stem[-1]) - 20 * 28 + 6 * 28 + 20) + '다'
            elif not final and vowel == 8:
                past = stem[:-1] + chr(ord(stem[-1]) + 1 * 28 + 20) + '다'
            elif not final and vowel == 13:
                past = stem[:-1] + chr(ord(stem[-1]) + 1 * 28 + 20) + '다'
            if stem.endswith('하'):
                past = stem[:-1] + '했다'
            present = (stem[:-1] + chr(ord(stem[-1]) - 8) if final == 8 else stem) + '는'
            future = stem[:-1] + chr(ord(stem[-1]) + 8) if not final else (stem if final == 8 else stem + '을')
            return phrase, past, present, future
        for bad, _ in table_rows():
            bad = re.sub(r'\([^)]*\)', '', bad)
            for phrase in re.split(r', (?=(?:[^"]*"[^"]*")*[^"]*$)', bad):
                if not phrase.endswith('다') or phrase in exceptions or phrase.startswith('"'):
                    continue
                for form in forms(phrase):
                    with self.subTest(phrase=phrase, form=form):
                        context = {'흔들리다': '마음이 ', '통하다': '방법이 ', '이어지다': '기록이 '}.get(phrase, '')
                        self.assertTrue(voice.check_text(context + form), form)

    def test_new_variants_and_context(self):
        examples = ('감당할', '감당하기', '평균을 흔든다', '평균을 흔들어', '꾸려', '꾸린',
                    '세 번 재어', '세 번 쟀던', '세 번 재서', '받쳤다', '받친',
                    '과제가 밀릴', '과제가 밀려', '요소를 붙여', '요소를 붙인',
                    '첫 단계에서 다음 단계로 넘어갔다', '첫 단계에서 다음 단계로 넘어가는',
                    '도구로 수업 활동을 꾸미는', '도구로 수업 활동을 꾸며',
                    '요소를 독서 기록장에 붙였다', 'AI는 필요할 때만 불렀다',
                    '기록이 방학에도 이어졌다', '솔직하게 말해야 할 사실도 있다',
                    '점수는 줄을 세우려고 내는 것이 아니라 도우려고 내는 것이다',
                    '기록을 남기지 않은 사람이 누구인지 나는 안다')
        for text in examples:
            with self.subTest(text=text):
                self.assertTrue(voice.check_text(text))
        self.assertFalse(voice.check_text('요소를 보았다. 기록장에 붙였다.'))
        self.assertEqual('', next(x['hint'] for x in voice.check_text('읽는 힘') if x['kind'] == '꾸민 말'))
        self.assertEqual('낮음', next(x['confidence'] for x in voice.check_text('계획이 밀렸다') if x['kind'] == '사물 비유'))
        self.assertEqual('높음', next(x['confidence'] for x in voice.check_text('과제가 밀렸다') if x['kind'] == '사물 비유'))
        self.assertFalse(voice.check_text('길이 멀다.'))
        self.assertFalse(voice.check_text('자료가 흩어졌다.'))

    def test_fixture_recall_and_false_positives(self):
        folder = BASE / 'tests/fixtures'
        manifest = json.loads((folder / 'expected.json').read_text(encoding='utf-8'))
        for name, expected in manifest.items():
            text = (folder / name).read_text(encoding='utf-8')
            findings = voice.check_text(text)
            lines = {item['line'] for item in findings}
            targets = {item['line'] for item in expected}
            hits = sum(any(item['line'] == x['line'] and item['kind'] == x['kind'] for x in findings) for item in expected)
            false_positives = len(lines - targets)
            with self.subTest(name=name):
                self.assertGreaterEqual(hits / len(expected), 0.9)
                self.assertLessEqual(false_positives, 3)

    def test_quoted_heading(self):
        self.assertEqual(run('# \"힘을 쏟았다\"').returncode, 0)

    def test_table_and_inline_comments(self):
        self.assertEqual(run('| 잣대 | 항목 |').returncode, 1)
        self.assertEqual(run('내용 <!-- 잣대 --> 확인').returncode, 0)


if __name__ == '__main__':
    unittest.main()
