#!/usr/bin/env python3
"""Check a 기안문 draft JSON and render it into the shared artifact page.

    python3 build_gongmun.py draft.json -o 기안문.html     # check, then write the page
    python3 build_gongmun.py draft.json --check            # check only

The JSON is the single source: numbering (1. 가. 1) 가)), the 붙임 line and
"끝." are generated here, so the page and the copy buttons always agree.
"""
from __future__ import annotations
import argparse, datetime, html, json, re, sys
from pathlib import Path
from urllib.parse import urlsplit

SKILL = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL/'assets'/'gongmun.html'
DOW = '월화수목금토일'
HANGUL_SEQ = '가나다라마바사아자차카타파하'
CONFIRM = '[확인 필요]'

# ---------- numbering ----------

def marker(depth, i):
    """depth 1: 가.  2: 1)  3: 가)  4: (1)"""
    if depth == 1: return HANGUL_SEQ[i] + '.'
    if depth == 2: return f'{i+1})'
    if depth == 3: return HANGUL_SEQ[i] + ')'
    return f'({i+1})'

LEADING_NUMBER = re.compile(r'^\s*(\d{1,2}\.(?!\s*\d{1,2}\.)|[가-하]\.|\d{1,2}\)|[가-하]\)|\(\d{1,2}\))\s')

def fmt_date(iso):
    d = datetime.date.fromisoformat(iso)
    return f'{d.year}. {d.month}. {d.day}.'

def related_text(r):
    no = r.get('doc_no') or CONFIRM
    date = fmt_date(r['date']) if r.get('date') and r['date'] != CONFIRM else CONFIRM
    return f'{no}({date}, "{r.get("title") or CONFIRM}")'

def attachment_text(a):
    return f'{a["name"]} {a.get("count", 1)}부.'

def lines(data):
    """Return [(depth, text)] for the body, from 1. 관련 to 끝."""
    out = []
    n = 1
    related = data.get('related') or []
    if len(related) == 1:
        out.append((0, f'{n}. 관련: {related_text(related[0])}')); n += 1
    elif related:
        out.append((0, f'{n}. 관련'))
        out += [(1, f'{marker(1, i)} {related_text(r)}') for i, r in enumerate(related)]
        n += 1
    out.append((0, f'{n}. {data["lead"]}'))
    def walk(items, depth):
        for i, item in enumerate(items):
            out.append((depth, f'{marker(depth, i)} {item["text"]}'))
            walk(item.get('children') or [], depth + 1)
    walk(data.get('items') or [], 1)
    atts = data.get('attachments') or []
    if not atts:
        d, t = out[-1]; out[-1] = (d, t + '  끝.')
    elif len(atts) == 1:
        out.append((-1, f'붙임  {attachment_text(atts[0])}  끝.'))
    else:
        for i, a in enumerate(atts):
            prefix = '붙임  ' if i == 0 else '      '
            end = '  끝.' if i == len(atts) - 1 else ''
            out.append((-1, f'{prefix}{i+1}. {attachment_text(a)}{end}'))
    return out

def plain_body(body):
    return '\n'.join(('' if d <= 0 else '  ' * d) + t for d, t in body).replace('\n붙임', '\n\n붙임', 1)

# ---------- money ----------

def won(s):
    if not re.fullmatch(r'(?:\d+|\d{1,3}(?:,\d{3})+)', s):
        raise ValueError('금액과 수량의 숫자 또는 쉼표 위치를 확인해 주세요')
    return int(s.replace(',', ''))

def korean_amount(n):
    """368000 -> 삼십육만팔천 (leading 일 before 십·백·천·만 left out)."""
    if n == 0: return '영'
    if n < 0 or n >= 10**16: raise ValueError('금액은 0원 이상 1경 원 미만으로 적어 주세요')
    digits = '영일이삼사오육칠팔구'
    out = ''
    for unit, group in zip(['조', '억', '만', ''], [n // 10**12 % 10**4, n // 10**8 % 10**4, n // 10**4 % 10**4, n % 10**4]):
        if not group: continue
        g = ''
        for place, p in zip(['천', '백', '십', ''], [group // 1000, group // 100 % 10, group // 10 % 10, group % 10]):
            if p: g += ('' if p == 1 and place else digits[p]) + place
        out += g + unit
    return out

def normalize_korean(s):
    return re.sub(r'일(?=[십백천])|(?<![가-힣])일(?=[만억조])', '', s)

FORMULA = re.compile(r'([\d,]+)원((?:\s*[*×xX]\s*[\d,]+[가-힣]*)+)\s*=\s*([\d,]+)원')
OWN_AMOUNT = re.compile(r'^[^:：]{1,40}[:：]\s*금?([\d,]+)원')
KOREAN_AMOUNT = re.compile(r'금\s*([\d,]+)원\s*\(\s*금\s*([가-힣]+)\s*원\s*\)')

def node_amount(item):
    """An item's own amount: '=N원' result, else 'label: N원'; None when absent."""
    m = FORMULA.search(item['text'])
    if m: return won(m.group(3))
    m = OWN_AMOUNT.search(item['text'])
    return won(m.group(1)) if m else None

def tree_amount(item):
    own = node_amount(item)
    if own is not None: return own
    kids = [tree_amount(c) for c in item.get('children') or []]
    return sum(kids) if kids and None not in kids else None

# ---------- dates ----------

DATE = re.compile(r'(?<!\d)(?:(\d{4})\.\s*)?(\d{1,2})\.\s*(\d{1,2})\.\s*\(([월화수목금토일])\)')

def weekday_errors(text, year_hint=None):
    errs = []; year = year_hint
    for m in DATE.finditer(text):
        y = int(m.group(1)) if m.group(1) else year
        if m.group(1): year = y
        if y is None: continue
        try:
            d = datetime.date(y, int(m.group(2)), int(m.group(3)))
        except ValueError:
            errs.append(f'{m.group(0)}: 없는 날짜예요'); continue
        if DOW[d.weekday()] != m.group(4):
            errs.append(f'{m.group(0)} → {DOW[d.weekday()]}요일이에요')
    return errs

# ---------- checks ----------

def validate(data):
    def obj(value, path):
        if not isinstance(value, dict): raise ValueError(f'{path}을 객체로 적어 주세요')
    def string(value, path, required=False):
        if not isinstance(value, str) or (required and not value.strip()):
            raise ValueError(f'{path}에 글자를 적어 주세요')
    def fields(value, path, required=(), optional=()):
        obj(value, path)
        for key in required: string(value.get(key), f'{path}.{key}', True)
        for key in optional:
            if key in value and value[key] is not None: string(value[key], f'{path}.{key}')
    def seq(value, path):
        if not isinstance(value, list): raise ValueError(f'{path}을 목록으로 적어 주세요')
    def date(value, path):
        if value and value != CONFIRM:
            try:
                if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value): raise ValueError()
                datetime.date.fromisoformat(value)
            except ValueError: raise ValueError(f'{path}을 연도-월-일 형식으로 적어 주세요')
    fields(data, '입력', ('school', 'title', 'lead'), ('receiver', 'via', 'slogan', 'kind', 'written', 'page_title'))
    date(data.get('written'), 'written')
    if data.get('written') == CONFIRM: raise ValueError('written에 연도-월-일을 적거나 칸을 지워 주세요')
    if 'example' in data and not isinstance(data['example'], bool): raise ValueError('example을 true 또는 false로 적어 주세요')
    def items(rows, depth):
        seq(rows, 'items.children' if depth > 1 else 'items')
        if depth > 4 and rows: raise ValueError('items는 네 단계까지만 적어 주세요')
        if depth in (1, 3) and len(rows) > len(HANGUL_SEQ): raise ValueError('같은 단계의 항목은 14개까지만 적어 주세요')
        for row in rows:
            fields(row, 'items 항목', ('text',))
            items(row.get('children') or [], depth + 1)
            if 'children' in row and row['children'] is not None: seq(row['children'], 'items.children')
    for key in ('related', 'items', 'attachments', 'approval', 'cooperation', 'ledger', 'todo', 'links'):
        if key in data and data[key] is not None: seq(data[key], key)
    items(data.get('items') or [], 1)
    related = data.get('related') or []
    if len(related) > len(HANGUL_SEQ): raise ValueError('관련 문서는 14개까지만 적어 주세요')
    for row in related:
        fields(row, 'related 항목', optional=('doc_no', 'date', 'title', 'source'))
        date(row.get('date'), 'related.date')
    for row in data.get('attachments') or []:
        fields(row, 'attachments 항목', ('name',))
        if 'count' in row and (type(row['count']) is not int or row['count'] < 1): raise ValueError('attachments.count에 1 이상의 정수를 적어 주세요')
        if 'ready' in row and not isinstance(row['ready'], bool): raise ValueError('attachments.ready를 true 또는 false로 적어 주세요')
    for key in ('approval', 'cooperation'):
        for row in data.get(key) or []: fields(row, key + ' 항목', ('role',), ('name',))
    if data.get('footer') is not None: fields(data['footer'], 'footer', optional=('doc_no', 'address', 'phone', 'fax', 'disclosure'))
    for row in data.get('ledger') or []:
        fields(row, 'ledger 항목', ('name',), ('basis', 'basis_doc'))
        if type(row.get('allocated')) is not int or not 0 <= row['allocated'] <= 2**53-1: raise ValueError('ledger.allocated에 0 이상 9,007,199,254,740,991 이하의 정수 금액을 적어 주세요')
        seq(row.get('spend'), 'ledger.spend')
        for spend in row['spend']:
            fields(spend, 'spend 항목', ('name',))
            if type(spend.get('amount')) is not int or not 0 <= spend['amount'] <= 2**53-1: raise ValueError('spend.amount에 0 이상 9,007,199,254,740,991 이하의 정수 금액을 적어 주세요')
    if sum(s['amount'] for row in data.get('ledger') or [] for s in row['spend']) > 2**53-1:
        raise ValueError('장부의 전체 집행 합계를 9,007,199,254,740,991원 이하로 적어 주세요')
    for value in data.get('todo') or []: string(value, 'todo 항목', True)
    for row in data.get('links') or []:
        fields(row, 'links 항목', ('label', 'url'))
        try:
            url = urlsplit(row['url'])
            host, port = url.hostname, url.port
        except ValueError: raise ValueError('links.url에 올바른 웹 주소를 적어 주세요')
        if url.scheme not in ('http', 'https') or not host or '\\' in url.netloc or any(c.isspace() or ord(c) < 32 for c in row['url']):
            raise ValueError('links.url에 http 또는 https로 시작하는 웹 주소를 적어 주세요')


def check(data):
    """Return a list of {id, label, status, detail}. status: ok | warn | fail."""
    res = []
    def add(id, label, status, detail): res.append({'id': id, 'label': label, 'status': status, 'detail': detail})
    validate(data)
    body = lines(data)
    texts = [t for _, t in body] + [data['title']]

    # V1 형식
    problems = []
    if not data.get('receiver'): problems.append('수신이 비어 있어요')
    if data['title'].rstrip().endswith('.'): problems.append('제목 끝에 마침표가 있어요')
    def all_items(items):
        for it in items:
            yield it; yield from all_items(it.get('children') or [])
    doubled = [it['text'] for it in all_items(data.get('items') or []) if LEADING_NUMBER.match(it['text'])]
    if doubled: problems.append(f'항목 글에 번호가 이미 있어요: {doubled[0][:20]}')
    if LEADING_NUMBER.match(data['lead']): problems.append('본문 첫 문장에 번호가 이미 있어요')
    if sum(t.count('끝.') for t in texts) != 1: problems.append('"끝."이 한 번만 있어야 해요')
    add('V1', '형식', 'fail' if problems else 'ok',
        '; '.join(problems) or '수신·제목·관련·본문·붙임 "끝." 체계를 갖췄어요')

    # V2-1 관련 문서
    related = data.get('related') or []
    if related:
        bad = [r for r in related if r.get('doc_no') and r['doc_no'] != CONFIRM and not re.fullmatch(r'\S+-\d+', r['doc_no'])]
        unknown = [r for r in related if not r.get('doc_no') or r['doc_no'] == CONFIRM or not r.get('date') or r.get('date') == CONFIRM or not r.get('title') or r.get('title') == CONFIRM]
        unsourced = [r for r in related if r not in unknown and not r.get('source')]
        if bad: add('V2-1', '관련 문서', 'fail', f'문서번호 모양이 달라요: {bad[0]["doc_no"]} (기관명-번호)')
        elif unknown or unsourced:
            add('V2-1', '관련 문서', 'warn', f'{len(unknown)}건은 문서번호·날짜·제목을 아직 몰라요' if unknown
                else f'{len(unsourced)}건은 어디서 확인했는지 적혀 있지 않아요. 결재 문서와 맞춰 주세요')
        else:
            add('V2-1', '관련 문서', 'ok', f'{len(related)}건의 문서번호·날짜를 ' + ', '.join(sorted({r["source"] for r in related})) + '에서 확인했어요')

    # C1 곱셈, C2 합계, C3 한글 금액
    calc_err, n_formula = [], 0
    for t in texts:
        for m in FORMULA.finditer(t):
            n_formula += 1
            product = won(m.group(1))
            for f in re.findall(r'[\d,]+', m.group(2)): product *= won(f)
            if product != won(m.group(3)): calc_err.append(f'{m.group(0)} → {product:,}원')
    if n_formula:
        add('C1', '곱셈 검산', 'fail' if calc_err else 'ok', calc_err[0] if calc_err else f'산출식 {n_formula}개가 모두 맞아요')
    sum_err, n_sum = [], 0
    def sums(items):
        nonlocal n_sum
        for it in items:
            kids = it.get('children') or []
            own = node_amount(it)
            if kids and own is not None and not FORMULA.search(it['text']):
                kid_sum = [tree_amount(k) for k in kids]
                n_sum += 1
                if None in kid_sum: sum_err.append(f'{it["text"][:24]}… 아래 빠진 금액을 적어 주세요')
                elif sum(kid_sum) != own: sum_err.append(f'{it["text"][:24]}… 아래 합은 {sum(kid_sum):,}원이에요')
            sums(kids)
    items = data.get('items') or []
    sums(items)
    total_item = next((it for it in all_items(items) if '소요예산' in it['text']), None)
    breakdown = next((it for it in all_items(items) if it['text'].strip().startswith('산출내역')), None)
    if total_item and breakdown:
        n_sum += 1
        t_amount, b_amount = node_amount(total_item), tree_amount(breakdown)
        if t_amount is None: sum_err.append('소요예산에 금액이 없어요')
        elif b_amount is None: sum_err.append('산출내역에 빠진 금액을 적어 주세요')
        elif b_amount != t_amount: sum_err.append(f'소요예산 {t_amount:,}원과 산출내역 합 {b_amount:,}원이 달라요')
    if n_sum:
        add('C2', '합계', 'fail' if sum_err else 'ok', sum_err[0] if sum_err else f'소계·총액 {n_sum}곳이 모두 맞아요')
    kor_err, n_kor = [], 0
    for t in texts:
        for m in KOREAN_AMOUNT.finditer(t):
            n_kor += 1
            want = korean_amount(won(m.group(1)))
            if normalize_korean(m.group(2)) != normalize_korean(want): kor_err.append(f'{m.group(0)} → 금{want}원')
    if total_item and not KOREAN_AMOUNT.search(total_item['text']):
        kor_err.append('소요예산을 "금368,000원(금삼십육만팔천원)"처럼 한글로도 적어 주세요')
    if n_kor or total_item:
        add('C3', '금액 한글 표기', 'fail' if kor_err else 'ok', kor_err[0] if kor_err else '숫자와 한글 금액이 같아요')

    # C4 요일
    year = None
    if data.get('written'): year = datetime.date.fromisoformat(data['written']).year
    day_err, n_day, missing_year = [], 0, False
    for t in texts:
        matches = list(DATE.finditer(t))
        n_day += len(matches); day_err += weekday_errors(t, year)
        current_year = year
        for m in matches:
            if m.group(1): current_year = int(m.group(1))
            if current_year is None: missing_year = True
    if n_day:
        add('C4', '요일', 'fail' if day_err else 'warn' if missing_year else 'ok', day_err[0] if day_err else '연도가 없는 날짜는 written에 작성 연도를 적어 확인해 주세요' if missing_year else f'날짜 {n_day}개의 요일이 달력과 같아요')

    # V3-1 편성액 안에서 집행
    ledger = data.get('ledger') or []
    if ledger:
        over, mism = [], []
        for g in ledger:
            spent = sum(s['amount'] for s in g['spend'])
            if spent > g['allocated']: over.append(f'{g["name"]} {spent - g["allocated"]:,}원 넘어요')
            match = next((it for it in all_items(items) if it['text'].split(':')[0].strip() == g['name']), None)
            if match and node_amount(match) is None: mism.append(f'{g["name"]} 본문에 금액을 적어 주세요')
            elif match and node_amount(match) != spent: mism.append(f'{g["name"]} 장부 {spent:,}원, 본문 {node_amount(match):,}원')
        if over or mism: add('V3-1', '편성액 안 집행', 'fail', (over + mism)[0])
        else: add('V3-1', '편성액 안 집행', 'ok', f'{len(ledger)}개 항목 모두 편성액 안이에요')

    # V2-5 붙임
    atts = data.get('attachments') or []
    if atts:
        missing = [a['name'] for a in atts if not a.get('ready')]
        add('V2-5', '붙임', 'warn' if missing else 'ok',
            f'아직 없는 붙임: {", ".join(missing)}' if missing else f'붙임 {len(atts)}건이 준비됐어요')

    # 남은 [확인 필요]
    page_text = json.dumps(data, ensure_ascii=False)
    n_confirm = page_text.count(CONFIRM)
    if n_confirm: add('C5', '빈칸', 'warn', f'{CONFIRM} {n_confirm}곳을 채운 뒤 상정해요')
    return res

def overall(results):
    if any(r['status'] == 'fail' for r in results): return 'fail'
    if any(r['status'] == 'warn' for r in results): return 'warn'
    return 'ok'

# ---------- page ----------

def render(data, results):
    body = lines(data)
    page = {
        'school': data['school'], 'slogan': data.get('slogan', ''), 'receiver': data.get('receiver', ''),
        'via': data.get('via', ''), 'title': data['title'], 'kind': data.get('kind', '기안문'),
        'written': data.get('written'), 'example': bool(data.get('example')),
        'lines': [{'depth': d, 'text': t} for d, t in body], 'copy_body': plain_body(body),
        'approval': data.get('approval') or [], 'cooperation': data.get('cooperation') or [],
        'footer': data.get('footer') or {}, 'ledger': data.get('ledger') or [], 'todo': data.get('todo') or [],
        'links': data.get('links') or [], 'checks': results, 'status': overall(results),
    }
    payload = json.dumps(page, ensure_ascii=False).replace('</', '<\\/')
    out = TEMPLATE.read_text()
    out = out.replace('__PAGE_TITLE__', html.escape(data.get('page_title') or data['title'][:30]))
    return out.replace('"__DRAFT_DATA__"', payload)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('input', type=Path); ap.add_argument('-o', '--output', type=Path)
    ap.add_argument('--check', action='store_true', help='check only, write nothing')
    a = ap.parse_args()
    try:
        data = json.loads(a.input.read_text())
        results = check(data)
    except json.JSONDecodeError:
        print('JSON 형식을 확인해 주세요.', file=sys.stderr); return 2
    except (OSError, UnicodeError):
        print('입력 파일 경로와 글자 인코딩을 확인해 주세요.', file=sys.stderr); return 2
    except (ValueError, KeyError) as e:
        print(f'검사하지 못했어요: {e}', file=sys.stderr); return 2
    for r in results:
        print(f'[{ {"ok": "통과", "warn": "확인", "fail": "고침"}[r["status"]] }] {r["id"]} {r["label"]}: {r["detail"]}')
    status = overall(results)
    if a.check or not a.output: return 1 if status == 'fail' else 0
    if status == 'fail':
        print('고칠 곳이 있어 화면을 만들지 않았어요.', file=sys.stderr); return 1
    try:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(render(data, results))
    except (OSError, ValueError) as e:
        print(f'화면을 만들지 못했어요: {e}', file=sys.stderr); return 2
    print(f'화면을 만들었어요: {a.output}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
