#!/usr/bin/env python3
"""원고의 말투를 확인할 후보를 찾는다."""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from file_read import read_text

# 이름, 표현, 대신 쓸 말, 신뢰도
RULES = [
    ('몸·움직임', r'힘을\s*(?:쏟|쏟았|쓰|썼)|손이\s*가지\s*않|짚게\s*(?:하|했|해|할)|눈여겨\s*(?:보|봤|볼)|들여다\s*(?:보|봤|볼)|(?<!뒷)받(?:치|쳐|쳤|친|칠)|떠받(?:치|쳐|쳤|친|칠)|감당(?:하|해|했|할)|눈에\s*띄는\s*아이|겹쳐\s*(?:보|봤|볼)|가르|갈랐|목표를\s*(?:잡|잡았)|자신의\s*손으로|오래가지\s*(?:못하|못했|못할)|찬찬히', '집중하다, 알려 주다, 살펴보다', '높음'),
    ('몸·움직임', r'흔들리|흔들렸|흔들릴|통하|통했|통할|멀다|멀었|멀어', '불안하다, 효과가 있다, 관련이 적다', '낮음'),
    ('사물 비유', r'기록이[^.!?\n]{0,20}?쌓(?:이|였|인|여|일)|(?:요소|기능)[을를][^.!?\n]{0,20}?붙(?:이|였|인|여|일)|AI[를는가][^.!?\n]{0,20}?(?:부르|불렀|불러|부를)|수업이\s*돌아(?:가|갔|간|갈)|잘\s*돌아(?:가|갔|간|갈)|평균을\s*(?:흔들|흔든|흔드)|모여들|모여든|모여드|꾸리|꾸렸|꾸린|꾸려|꾸릴', '기록되다, 넣다, 쓰다, 진행하다, 모이다', '높음'),
    ('사물 비유', r'벗어나|벗어났|벗어날|이어지|이어졌|이어진|이어져|이어질|밀리|밀렸|밀린|밀릴|밀려|터지|터졌|터진|터질|머물|머무|이어\s*가|이어\s*갔|이어\s*갈|올라오|올라왔|올라온|올라올', '쓰다, 적용하다, 생기다, 제출되다', '낮음'),
    ('사물 비유', r'쌓인\s*기록|(?:건수|쪽수)(?:·쪽수)?[가이][^.!?\n]{0,20}?쌓(?:이|였|여|인|일)|도구로[^.!?\n]{0,20}?꾸(?:미|며|몄|밀)|(?:~|[가-힣]*)단계에서[^.!?\n]{0,20}?단계로\s*넘어(?:가|갔|간|갈)|틀을\s*만들면[^.!?\n]{0,20}?채(?:우|웠|울)|옮겨\s*(?:쓰|써|썼|갈|가|갔|간)|몰리|몰렸|몰려|몰릴|자라|자랐|자란|자랄|주춤하|주춤했|주춤해|주춤할', '', '높음'),
    ('읽기·평가', r'(?:변화|흐름|추이)[을를][^.!?\n]{0,20}?읽|뜻으로\s*읽|조심스럽게\s*읽어야\s*할\s*점|세\s*번\s*(?:쟀|재|잰)|재어|재서|잰\s*수치', '확인하다, 해석하다, 평가하다', '높음'),
    ('꾸민 말', r'흐려졌을\s*순간들?|(?:[가-힣]+(?:는|은)\s+힘)|세\s*갈래|출발선|한\s*걸음씩|여름의\s*공백|기록이\s*쓰이는\s*자리|잣대|제자리였|(?:매뉴얼|안내서|자료|양식)\s+한\s*벌|첫머리', '내용, 능력, 방법, 날짜와 사실, 평가 기준', '높음'),
    ('꾸민 말', r'흐름', '추이', '낮음'),
    ('꾸민 말', r'순환|내려간\s*선|올라간\s*선|그\s*자체로\s*일이\s*(?:되|될)|걱정부터\s*적|(?:~|[가-힣]+)로\s*(?:들리|들렸|들릴)|(?:~|[가-힣]+)고\s*(?:느끼|느꼈|느낄)', '', '높음'),
    ('극적 도입', r'(?:솔직하게|숨기고\s*싶은|털어놓자면)\s*(?:\S{1,8}\s*){0,3}(?:숫자|사실|기록|이야기)\S{0,3}\s*(?:하나\s*)?있다|한\s*줄을\s*적었다|(?:누구인지|무엇인지)\s*나는\s*안다', '사실을 바로 쓰기', '높음'),
    ('격언형 맺음', r'[가-힣]+[은는]\s+[^.!?\n]{0,20}(?:려고|기\s*위해)\s*[^.!?\n]{0,10}(?:것이|게)\s*아니라\s*[^.!?\n]{0,20}(?:려고|기\s*위해)\s*[^.!?\n]{0,10}것이다|(?:~|[가-힣]+)이\s*나는\s*가장\s*(?:반가웠|기뻤)|가장\s*중요한\s*것은[^.!?\n]*이다|이\s*순간이\s*(?:곧|바로)[^.!?\n]*이다|그것이\s*[^.!?\n]*증거다', '자신의 판단으로 쓰기', '높음'),
    ('구호형 목표', r'[가-힣]+[이가]\s+[^\"“”「」\n]{0,15}(?:이어지는|자라는|피어나는|살아\s*있는)\s*(?:학교|교실|학급|수업)', '활용 내용을 구체적으로 쓰기', '높음'),
    ('계획서 말투', r'프로젝트를\s*실시하(?:였|였던|다)|중점을\s*두(?:었|었|다)|할\s*수\s*있도록\s*하였|학습자\s*주도적(?:으로(?:\s*퇴고\s*과정을\s*거쳤다)?|\s*퇴고\s*활동을\s*전개하(?:였|도록))|역량을\s*함양하(?:였|다)', '무엇을 했는지 장면으로 쓰기', '높음'),
    ('사물 주어', r'(?:기록이|데이터가|도구가|시간이|수업이|지침이|기능이|폼이|플랫폼이|순간이)[^.!?\n]*(?:만들|바꾸|바꿔|높이|높였|높여|키우|흔들|가르|이끌|열어|가져)', '사람이 한 일로 쓰기', '낮음'),
    ('띄어쓰기', r'(?<=[가-힣])(?:해주|해보|적어달라|읽어보|써보|만들어보|해줬|해줄)', '띄어 쓰기: 해 주다, 해 보다', '높음'),
    ('띄어쓰기', r'할\s+지\b|두번째|세번째|향상\s+시키|매\s+시간\s+마다|줄서서', '할지, 두 번째, 향상시키다, 매 시간마다, 줄 서서', '높음'),
]
RULES = [(name, re.compile(p), hint, confidence) for name, p, hint, confidence in RULES]
# 규칙표의 각 행과 검사 패턴을 연결해 원문의 대체 표현을 그대로 쓴다.
def table_hints():
    text = (Path(__file__).resolve().parents[1] / 'references/voice-rules.md').read_text(encoding='utf-8')
    text = text.split('### 3.1 ', 1)[1].split('### 3.7 ', 1)[0]
    hints = []
    for line in text.splitlines():
        cells = line.split('|')
        if len(cells) < 4 or cells[1].strip() in ('쓰지 않음', '---'):
            continue
        bad, hint = re.sub(r'\([^)]*\)', '', cells[1]).strip(), cells[2].strip()
        for name, pattern, _, _ in RULES:
            for match in pattern.finditer(bad):
                hints.append((name, re.sub(r'\s+', '', match.group()), hint))
    return hints


TABLE_HINTS = table_hints()


def row_hint(name, value, default):
    value = re.sub(r'\s+', '', value)
    if name == '꾸민 말' and value == '흐름':
        return '추이'
    candidates = [(len(key), hint) for kind, key, hint in TABLE_HINTS
                  if kind == name and (value in key or key in value)]
    if not candidates and name in ('몸·움직임', '사물 비유'):
        for kind, key, hint in TABLE_HINTS:
            if kind != name:
                continue
            common = 0
            for a, b in zip(key, value):
                if a != b:
                    break
                common += 1
            if (common >= 2 and len(key) - common == 1 and len(value) - common == 1
                    and '가' <= key[-1] <= '힣' and '가' <= value[-1] <= '힣'
                    and (ord(key[-1]) - ord('가')) // 588 == (ord(value[-1]) - ord('가')) // 588):
                candidates.append((common, hint))
    if candidates:
        return max(candidates, key=lambda item: item[0])[1]
    return {
        '극적 도입': '사실을 바로 쓴다',
        '격언형 맺음': "'나는 ~라고 생각한다'로 바꾼다",
        '구호형 목표': '무엇을 어떻게 하는 학교인지 사실로 쓴다',
        '제목': '사실형 명사구로',
    }.get(name, '')


QUOTE = re.compile(r'"[^"\n]*"|\'[^\'\n]*\'|「[^」\n]*」|“[^”\n]*”')
ENDING = re.compile(r'(?:습니다|지요|했다|이다|였다|한다)\.')


def visible(text):
    text = re.sub(r'<!--.*?(?:-->|\Z)', lambda m: re.sub(r'[^\n]', ' ', m.group()), text, flags=re.S)
    lines = text.splitlines()
    fence = False
    yaml = bool(lines and lines[0].strip() == '---')
    for index, line in enumerate(lines):
        stripped = line.strip()
        if yaml:
            if index and stripped in ('---', '...'):
                yaml = False
            continue
        if stripped.startswith('```'):
            fence = not fence
            continue
        if not fence:
            yield index + 1, line


def check_text(text, kind=None, filename=''):
    findings, endings, contrasts = [], [], {}
    section = 0
    dialogue = False
    def add(line, name, value, hint, confidence, quoted):
        findings.append(dict(file=str(filename), line=line, kind=name, text=value,
                             hint=hint, confidence=confidence, quoted=quoted))
    for line_no, line in visible(text):
        if kind == '대본' and re.match(r'^\s*#{2,3}\s', line):
            section += 1
        dialogue_start = re.match(r'^\s*[가-힣]{1,6}:\s+"', line) if kind == '대본' and not dialogue else None
        start = dialogue_start.end() - 1 if dialogue_start else (0 if dialogue else None)
        end = line.find('"', start + 1 if dialogue_start else start) if start is not None else -1
        dialogue_end = end if end >= 0 else len(line)
        if start is not None:
            dialogue = end < 0
        quote_line = line
        if start is not None:
            quote_line = line[:start] + line[start:dialogue_end + (end >= 0)].replace('"', ' ') + line[dialogue_end + (end >= 0):]
        quotes = [(m.start(), m.end()) for m in QUOTE.finditer(quote_line)]
        def is_quoted(pos):
            return any(start <= pos < end for start, end in quotes)
        heading = bool(re.match(r'^\s*#{1,6}\s', line) or re.match(r'^\s*\*\*.+?\*\*\s*$', line))
        title_hit = None
        for name, pattern, hint, base_confidence in RULES:
            for match in pattern.finditer(line):
                confidence = base_confidence
                sentence_before = re.split(r'[.!?]', line[:match.start()])[-1]
                if match.group().startswith('기록이') and re.search(r'데이터베이스|시트|DB|노션|폼에', sentence_before):
                    continue
                if match.group().startswith('오래가지') and kind == '대본':
                    continue
                if confidence == '낮음' and name in ('사물 비유', '몸·움직임', '꾸민 말'):
                    contexts = {'벗어나': '도구', '벗어났': '도구', '벗어날': '도구', '이어지': '기록|순환', '이어져': '기록|순환', '이어졌': '기록|순환', '이어진': '순환', '이어질': '기록|순환', '밀리': '과제', '밀렸': '과제', '밀린': '과제', '밀릴': '과제', '밀려': '과제', '터지': '일이', '터졌': '일이', '터진': '일이', '터질': '일이', '머물': '사례에', '머무': '사례에', '올라오': '글이', '올라왔': '글이', '올라온': '글이', '올라올': '글이', '통하': '방법', '통했': '방법', '통할': '방법', '멀다': '수업', '멀었': '수업', '멀어': '수업', '흔들리': '마음', '흔들렸': '마음', '흔들릴': '마음', '흐름': '점수'}
                    required = contexts.get(match.group())
                    sentence = re.split(r'[.!?]', line[:match.start()])[-1] + re.split(r'[.!?]', line[match.end():])[0]
                    if required and not re.search(required, sentence) and line.strip().rstrip('.!?') not in (match.group(), match.group() + '다'):
                        if match.group().startswith(('통하', '통했', '통할', '멀', '흔들리', '흔들렸', '흔들릴', '이어')):
                            continue
                    elif required:
                        confidence = '높음'
                if name == '몸·움직임' and match.group() in ('가르', '갈랐') and len(line.strip().rstrip('.!?')) > len(match.group()) + 1 and not re.search('받아들|거절|나누', line):
                    continue
                if name == '사물 비유' and match.group().startswith(('몰리', '몰렸', '몰려', '몰릴', '자라', '자랐', '자란', '자랄')) and len(line.strip().rstrip('.!?')) > len(match.group()) + 1 and not re.search('응답|분포|능력|실력|문해력', line):
                    continue
                add(line_no, name, match.group(), row_hint(name, match.group(), hint), confidence, is_quoted(match.start()))
                if heading and name in ('몸·움직임', '사물 비유', '읽기·평가', '꾸민 말', '극적 도입', '격언형 맺음', '구호형 목표', '계획서 말투'):
                    title_hit = match
        if heading:
            title = re.search(r'을\s*지나|를\s*지나|지나,|흐르기까지|움직였다|시작했다|자라는|피어나|여정|이야기(?=\s*(?:\*\*)?\s*$)', line)
            if title or title_hit:
                m = title or title_hit
                add(line_no, '제목', m.group(), '사실형 명사구로', '높음', is_quoted(m.start()))
        if kind == '대본' and re.match(r'^\s*(?:학습\s*(?:목표|내용|정리)|평가|자막|내레이션|\[화면\]|\|)', line):
            continue
        for match in ENDING.finditer(line):
            if not is_quoted(match.start()):
                endings.append((line_no, match.group(), match.group() in ('습니다.', '지요.')))
        for match in re.finditer(r'(?:가 아니라|이 아니라)', line):
            if not is_quoted(match.start()):
                contrasts.setdefault(section, []).append((line_no, match.group()))
    for group in contrasts.values():
        if len(group) >= 3:
            for line_no, value in group:
                add(line_no, '대조 반복', value, '둘로 끊거나 결론만 쓰기. 소제목의 대조를 회수하는 문장과 대구는 빼고 세세요', '높음', False)
    if kind:
        for line_no, value, spoken in endings:
            if spoken == (kind == '원고'):
                add(line_no, '종결어미', value, '원고는 서술체, 대본은 강의체로 통일', '높음', False)
    elif endings:
        counts = Counter(spoken for _, _, spoken in endings)
        if min(counts[True], counts[False]) and min(counts[True], counts[False]) / len(endings) >= 0.1:
            minority = counts[True] <= counts[False]
            for line_no, value, spoken in endings:
                if spoken == minority:
                    add(line_no, '종결어미 섞임', value, '한 가지 종결어미로 통일', '높음', False)
    combined = {}
    for item in findings:
        key = (item['file'], item['line'], item['kind'], item['text'])
        if key in combined:
            combined[key]['count'] = combined[key].get('count', 1) + 1
            combined[key]['quoted'] = combined[key]['quoted'] and item['quoted']
        else:
            combined[key] = item
    return sorted(combined.values(), key=lambda item: item['line'])


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, '사용법: check_voice.py 파일이나 폴더 [--kind 원고|대본] [--json]\n입력을 확인하세요.\n')


def main():
    parser = Parser(description='원고의 말투를 검사합니다.')
    parser.add_argument('targets', nargs='+')
    parser.add_argument('--kind', choices=['원고', '대본'])
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    paths = []
    try:
        for target in args.targets:
            path = Path(target)
            if not path.exists():
                raise ValueError('찾을 수 없는 경로: ' + target)
            if path.is_dir():
                paths.extend(p for p in sorted(path.rglob('*')) if p.is_file() and p.suffix.lower() in ('.md', '.txt'))
            elif path.is_file() and path.suffix.lower() in ('.md', '.txt'):
                paths.append(path)
            else:
                raise ValueError('md 또는 txt 파일을 지정하세요: ' + target)
        if not paths:
            raise ValueError('검사할 md 또는 txt 파일이 없습니다.')
        results = []
        timed_out = False
        for path in dict.fromkeys(paths):
            try:
                results.extend(check_text(read_text(path), args.kind, path))
            except TimeoutError:
                print('파일을 여는 데 30초가 넘었어요. 확인하세요: ' + str(path), file=sys.stderr)
                timed_out = True
    except (OSError, UnicodeError, ValueError) as exc:
        print('파일을 확인하세요: ' + str(exc), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(results, ensure_ascii=False))
    else:
        previous = None
        for item in results:
            if item['file'] != previous:
                print('\n■ ' + item['file'])
                previous = item['file']
            count = ' ({}회)'.format(item['count']) if item.get('count', 1) > 1 else ''
            quote = ' (인용)' if item['quoted'] else ''
            confidence = ' (신뢰도 낮음)' if item['confidence'] == '낮음' else ''
            print("  {}: {}{}{} — {} → 대신: {}".format(item['line'], item['kind'], quote, confidence, item['text'] + count, item['hint']))
        counts = Counter(item['kind'] for item in results)
        print('\n유형별 개수: ' + (', '.join('{} {}개'.format(k, v) for k, v in sorted(counts.items())) or '없음'))
    return 2 if timed_out else int(any(not item['quoted'] for item in results))


if __name__ == '__main__':
    sys.exit(main())
