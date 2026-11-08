#!/usr/bin/env python3
"""Build a project board page (길잡이 · 문서 흐름 · 기안문 · 예산 장부 · 일정 · 작업 기록) from one JSON file.

Checks run before the page is written: every 품의 amount equals its ledger lines,
no ledger line spends more than its 편성액, weekdays written in text match the
date, finished documents carry a document number, nothing past its due date
is still open, and every 기안문 written into the board passes the 기안문 checks.
The 길잡이 answers say which documents the project needs; a needed document
that is not in the flow yet is a warning. The last lines say what to do now and next. A failed check writes no page.
"""
import argparse, datetime as dt, html as html_lib, json, re, sys
from pathlib import Path

import build_gongmun as gm  # 기안문 스킬의 파일을 그대로 복사해 둔다(같은지 tests에서 본다)
import guide

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / 'assets' / 'board.html'
WEEK = '월화수목금토일'
STATUS = {'done': '결재 완료', 'review': '결재 중', 'draft': '작성 중', 'todo': '아직'}
CONFIRM = '[확인 필요]'
MAX_MONEY = 2**53 - 1
DOC_NO = re.compile(r'^\S+-\d+$')
DATE = re.compile(r'(?<!\d)(?:(\d{4})\.\s*)?(\d{1,2})\.\s*(\d{1,2})\.\s*\(([월화수목금토일])\)')


def day(iso):
    return dt.date.fromisoformat(iso)


def validate_data(data):
    """보드 자료의 모양과 선택값을 확인하고, 생략한 목록은 빈 목록으로 둔다."""
    if not isinstance(data, dict):
        raise ValueError('JSON 맨 위에는 객체를 넣어 주세요.')
    try:
        json.dumps(data, ensure_ascii=False).encode('utf-8')
    except UnicodeEncodeError:
        raise ValueError('입력 글자에 올바르지 않은 유니코드가 있어요. 해당 글자를 다시 입력해 주세요.')

    def need_text(key):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f'{key}에 비어 있지 않은 글자를 넣어 주세요.')

    def need_day(where, value):
        try:
            if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
                raise ValueError
            day(value)
        except (TypeError, ValueError):
            raise ValueError(f'{where} 날짜를 YYYY-MM-DD로 고쳐 주세요.')

    def need_int(where, value):
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= MAX_MONEY:
            raise ValueError(f'{where}에 0 이상 {MAX_MONEY:,} 이하의 정수를 넣어 주세요.')

    for key in ('school', 'project', 'updated'):
        need_text(key)
    need_day('updated', data['updated'])
    if 'period' in data:
        if not isinstance(data['period'], list) or len(data['period']) != 2:
            raise ValueError('period에는 시작일과 끝일을 두 개 넣어 주세요.')
        for value in data['period']:
            need_day('period', value)
    for key in ('docs', 'ledger', 'decide', 'schedule', 'log'):
        if key not in data:
            data[key] = []
        if not isinstance(data[key], list):
            raise ValueError(f'{key}에는 목록을 넣어 주세요.')
    if not isinstance(data.get('amounts', {}), dict):
        raise ValueError('amounts에는 문서 id와 금액을 넣은 객체를 써 주세요.')
    if 'guide' in data and not isinstance(data['guide'], dict):
        raise ValueError('guide에는 질문 id와 답을 넣은 객체를 써 주세요.')
    if 'example' in data and not isinstance(data['example'], bool):
        raise ValueError('example에는 true 또는 false를 넣어 주세요.')
    if data.get('look', '') not in ('', 'blueprint'):
        raise ValueError('look에는 blueprint 또는 빈 값을 넣어 주세요.')
    for optional in ('owner', 'budget_code', 'page_title'):
        if optional in data and not isinstance(data[optional], str):
            raise ValueError(f'{optional}에는 글자를 넣어 주세요.')
    ids = set()
    for i, doc in enumerate(data['docs'], 1):
        if not isinstance(doc, dict):
            raise ValueError(f'docs {i}번째 항목을 객체로 고쳐 주세요.')
        for key in ('id', 'kind', 'title', 'status'):
            if not isinstance(doc.get(key), str) or not doc[key].strip():
                raise ValueError(f'docs {i}번째 항목에 {key}를 넣어 주세요.')
        if doc['id'] in ids:
            raise ValueError(f'문서 id가 겹쳐요: {doc["id"]}')
        ids.add(doc['id'])
        if doc['status'] not in STATUS:
            allowed = ', '.join(STATUS)
            raise ValueError(f'{doc["id"]}의 status는 {allowed} 가운데 하나로 고쳐 주세요.')
        if 'need' in doc and (not isinstance(doc['need'], str) or doc['need'] not in {item['id'] for item in guide.ITEMS}):
            raise ValueError(f'{doc["id"]}의 need에는 길잡이 문서 id를 넣어 주세요.')
        if 'phase' in doc and (not isinstance(doc['phase'], str) or doc['phase'] not in {p['id'] for p in guide.PHASES}):
            raise ValueError(f'{doc["id"]}의 phase에는 prep, notice, run, close 가운데 하나를 넣어 주세요.')
        if doc.get('need') and doc.get('phase'):
            raise ValueError(f'{doc["id"]}에는 need와 phase를 함께 쓰지 말고 하나만 넣어 주세요.')
        if 'doc_no' in doc and not isinstance(doc['doc_no'], str):
            raise ValueError(f'{doc["id"]}의 doc_no에는 문서번호 글자를 넣어 주세요.')
        if 'draft' in doc and not isinstance(doc['draft'], dict):
            raise ValueError(f'{doc["id"]}의 draft에는 기안문 객체를 넣어 주세요.')
        for key in ('date', 'due'):
            if key in doc:
                need_day(f'{doc["id"]}의 {key}', doc[key])
    try:
        guide.validate(data.get('guide', {}), data['docs'])
    except TypeError:
        raise ValueError('guide에는 질문 id와 정해진 답 값을 넣어 주세요.')
    for i, row in enumerate(data['ledger'], 1):
        if not isinstance(row, dict) or not isinstance(row.get('name'), str) or not row['name'].strip():
            raise ValueError(f'ledger {i}번째 항목에 name을 넣어 주세요.')
        need_int(f'{row["name"]}의 allocated', row.get('allocated'))
        row.setdefault('spend', [])
        if not isinstance(row['spend'], list):
            raise ValueError(f'{row["name"]}의 spend에는 목록을 넣어 주세요.')
        for spend in row['spend']:
            if not isinstance(spend, dict) or not all(
                    isinstance(spend.get(k), str) and spend[k] for k in ('doc', 'name')):
                raise ValueError(f'{row["name"]}의 spend에는 doc, name, 0 이상의 amount를 넣어 주세요.')
            need_int(f'{row["name"]}의 spend amount', spend.get('amount'))
    if (sum(row['allocated'] for row in data['ledger']) > MAX_MONEY or
            sum(s['amount'] for row in data['ledger'] for s in row['spend']) > MAX_MONEY):
        raise ValueError(f'장부의 편성액 합계와 집행 합계를 각각 {MAX_MONEY:,}원 이하로 넣어 주세요.')
    for key in ('schedule', 'log'):
        for i, row in enumerate(data[key], 1):
            field = 'title' if key == 'schedule' else 'text'
            if (not isinstance(row, dict) or not isinstance(row.get('date'), str)
                    or not isinstance(row.get(field), str) or not row[field].strip()):
                raise ValueError(f'{key} {i}번째 항목에 date와 {field}를 넣어 주세요.')
            need_day(f'{key} {i}번째 date', row['date'])
    for i, row in enumerate(data['decide'], 1):
        if not isinstance(row, dict) or not isinstance(row.get('text'), str) or not row['text'].strip():
            raise ValueError(f'decide {i}번째 항목에 text를 넣어 주세요.')
    for doc, amount in data.get('amounts', {}).items():
        if not isinstance(doc, str) or not doc:
            raise ValueError('amounts에는 문서 id와 0 이상의 정수 금액을 넣어 주세요.')
        if doc not in ids:
            raise ValueError(f'amounts의 문서 id {doc}가 docs에 없어요.')
        need_int('amounts 금액', amount)


def fmt(iso):
    d = day(iso)
    return f'{d.year}. {d.month}. {d.day}.({WEEK[d.weekday()]})'


def strings(node):
    if isinstance(node, str): yield node
    elif isinstance(node, dict):
        for v in node.values(): yield from strings(v)
    elif isinstance(node, list):
        for v in node: yield from strings(v)


def weekday_errors(data):
    bad = []
    for s in strings(data):
        year = day(data['updated']).year
        for y, m, d, w in DATE.findall(s):
            if y: year = int(y)
            try: real = WEEK[dt.date(int(y or year), int(m), int(d)).weekday()]
            except ValueError: bad.append(f'{m}. {d}. 없는 날짜'); continue
            if real != w: bad.append(f'{m}. {d}.({w}) → ({real})')
    return bad


def ledger(data):
    """Each line: 편성액, 결재 마친 집행, 아직 결재 전인 품의, 남은 돈."""
    status = {d['id']: d['status'] for d in data['docs']}
    rows = []
    for line in data['ledger']:
        done = sum(s['amount'] for s in line['spend'] if status.get(s['doc']) == 'done')
        pending = sum(s['amount'] for s in line['spend'] if status.get(s['doc']) != 'done')
        rows.append({**line, 'done': done, 'pending': pending, 'left': line['allocated'] - done - pending})
    return rows


def items_of(items):
    for it in items:
        yield it; yield from items_of(it.get('children') or [])


def draft_input(data, doc):
    """보드 자료에서 기안문 한 장의 입력을 만든다. 제목·관련 문서·장부는 보드에 한 번만 적는다."""
    by_id = {d['id']: d for d in data['docs']}
    related = []
    for r in doc['draft'].get('related', []):
        if isinstance(r, dict): related.append(r); continue
        if r not in by_id: raise ValueError(f"{doc['id']} 기안문의 관련 문서 {r}가 문서 흐름에 없어요")
        x = by_id[r]
        related.append({'doc_no': x.get('doc_no') or CONFIRM, 'date': x.get('date'), 'title': x['title'], 'source': '문서 흐름'})
    ledger = []
    for line in data['ledger']:
        mine = [s for s in line['spend'] if s['doc'] == doc['id']]
        if not mine: continue
        others = sum(s['amount'] for s in line['spend'] if s['doc'] != doc['id'])
        ledger.append({'name': line['name'], 'allocated': line['allocated'] - others,
                       'spend': [{'name': s['name'], 'amount': s['amount']} for s in mine]})
    return {**doc['draft'], 'school': data['school'], 'title': doc['title'], 'related': related, 'ledger': ledger}


def drafts(data):
    """[(문서, 기안문 입력, 기안문 검사 결과)] — draft가 있는 문서만."""
    out = []
    for doc in data['docs']:
        if not doc.get('draft'): continue
        g = draft_input(data, doc)
        out.append((doc, g, gm.check(g)))
    return out


def amounts(data):
    """품의 금액: 기안문이 있으면 소요예산에서, 없으면 amounts에서. 둘 다 있는데 다르면 conflicts에 적는다."""
    given = data.get('amounts', {})
    out, conflicts = dict(given), []
    for doc in data['docs']:
        if not doc.get('draft'): continue
        total = next((it for it in items_of(doc['draft'].get('items') or []) if '소요예산' in it['text']), None)
        n = gm.node_amount(total) if total else None
        if n is None: continue
        if doc['id'] in given and given[doc['id']] != n:
            conflicts.append(f"{doc['id']}: 기안문 소요예산 {n:,}원 ≠ 적어 둔 금액 {given[doc['id']]:,}원")
        out[doc['id']] = n
    return out, conflicts


def check(data):
    validate_data(data)
    draft_results = drafts(data)
    out = []
    add = lambda id_, label, st, detail: out.append({'id': id_, 'label': label, 'status': st, 'detail': detail})
    ids = {d['id'] for d in data['docs']}
    rows = ledger(data)

    unknown = sorted({s['doc'] for r in data['ledger'] for s in r['spend']} - ids)
    per_doc = {}
    for r in data['ledger']:
        for s in r['spend']: per_doc[s['doc']] = per_doc.get(s['doc'], 0) + s['amount']
    money, conflicts = amounts(data)
    wrong = conflicts + [f'{k}: 품의 {v:,}원 ≠ 장부 {per_doc.get(k, 0):,}원' for k, v in money.items() if per_doc.get(k, 0) != v]
    wrong += [f'{k}: 품의 금액을 draft 또는 amounts에 넣어 주세요' for k in per_doc if k in ids and k not in money]
    if unknown or wrong: add('합계', '품의와 장부', 'fail', '; '.join(wrong + [f'없는 문서: {u}' for u in unknown]))
    else: add('합계', '품의와 장부', 'ok', '품의 금액과 장부 줄이 모두 맞아요.')

    over = [f"{r['name']} {r['done'] + r['pending']:,}원 > {r['allocated']:,}원" for r in rows if r['left'] < 0]
    if over: add('편성액', '편성액 안 집행', 'fail', '; '.join(over))
    elif not data['ledger']:
        if data.get('guide', {}).get('budget') == 'yes':
            add('편성액', '편성액 안 집행', 'warn', '예산 장부가 아직 없어요. 예산과목과 편성액을 넣어 주세요.')
        else:
            add('편성액', '편성액 안 집행', 'warn', '예산 장부가 아직 없어요.')
    else: add('편성액', '편성액 안 집행', 'ok', f"남은 돈 {sum(r['left'] for r in rows):,}원")

    bad = weekday_errors(data)
    add('요일', '요일', 'fail' if bad else 'ok', '; '.join(bad) if bad else '글에 쓴 요일이 모두 맞아요.')

    missing = [d['title'] for d in data['docs'] if d['status'] == 'done' and not DOC_NO.match(d.get('doc_no') or '')]
    add('문서번호', '문서번호', 'warn' if missing else 'ok',
        ('결재를 마쳤는데 번호가 빈 문서: ' + ', '.join(missing)) if missing else '결재 마친 문서에 번호가 모두 있어요.')

    today = day(data['updated'])
    late = [d['title'] for d in data['docs'] if d['status'] != 'done' and d.get('due') and day(d['due']) < today]
    add('기한', '기한', 'warn' if late else 'ok', ('기한이 지난 문서: ' + ', '.join(late)) if late else '기한이 지난 문서가 없어요.')

    n = sum(s.count(CONFIRM) for s in strings(data))
    add('빈칸', '빈칸', 'warn' if n else 'ok', f'{CONFIRM}로 둔 곳이 {n}곳이에요.' if n else '빈칸이 없어요.')

    if 'guide' in data: out.append(guide_check(data))

    for doc, _, res in draft_results:
        left = [r for r in res if r['status'] != 'ok']
        add('기안문', f"{doc['kind']} 기안문", gm.overall(res),
            '; '.join(f"{r['label']}: {r['detail']}" for r in left) if left else f'기안문 검사 {len(res)}개를 모두 통과했어요.')
    return out


def guide_check(data):
    answers = data['guide']
    have = {d.get('need') for d in data['docs']}
    missing, ask, extra = [], [], []
    for item in guide.ITEMS:
        st, _, _ = guide.judge(item, answers)
        if st == 'need' and item['id'] not in have: missing.append(item['name'])
        if st == 'ask': ask.append(item['name'])
        if st == 'skip' and item['id'] in have: extra.append(item['name'])
    unanswered = [q['q'] for q in guide.QUESTIONS if guide.asked(q, answers) and q['id'] not in answers]
    parts = ([f"아직 흐름에 없는 문서: {', '.join(missing)}"] if missing else []) + \
            ([f"물어볼 문서: {', '.join(ask)}"] if ask else []) + \
            ([f"필요 없다고 답했는데 흐름에 있는 문서: {', '.join(extra)}"] if extra else []) + \
            ([f"답하지 않은 질문 {len(unanswered)}개"] if unanswered else [])
    return {'id': '길잡이', 'label': '길잡이', 'status': 'warn' if parts else 'ok',
            'detail': '; '.join(parts) if parts else '필요한 문서가 모두 흐름에 있어요.'}


def guide_data(data):
    if 'guide' not in data: return None
    items = [{**i, 'prompts': [{**p, 'text': p['text'].format(project=data['project'])} for p in i['prompts']]} for i in guide.ITEMS]
    return {'answers': data['guide'], 'questions': guide.QUESTIONS, 'items': items, 'phases': guide.PHASES, 'tips': guide.NOW_TIP}


def say_steps(data):
    """선생님에게 그대로 말해 줄 차례: 지금 할 일과 다음 할 일."""
    if 'guide' not in data:
        return ['차례: 길잡이 답이 없어서 정하지 못했어요. guide에 답을 넣으면 지금 할 일을 알려 드려요.']
    st = guide.steps(data['guide'], data['docs'])
    name = {'now': '지금 할 일', 'next': '다음 할 일'}
    lines = [f"{name[x['state']]}: {x['do']}" + (f" ({x['doc']['title']}, {STATUS[x['doc']['status']]})" if x['doc'] else '') +
             (f" - {x['tip']}" if x['state'] == 'now' else '') for x in st if x['state'] in name]
    if lines:
        if len(lines) == 1:
            unanswered = any(guide.asked(q, data['guide']) and q['id'] not in data['guide'] for q in guide.QUESTIONS)
            lines.append('다음 할 일: ' + ('길잡이의 남은 질문에 답하면 알려 드려요.' if unanswered else '없어요.'))
        return lines
    return ['지금 할 일: 필요한 문서를 모두 마쳤어요.', '다음 할 일: 없어요.']


def paper(g, res):
    body = gm.lines(g)
    return {'receiver': g.get('receiver', ''), 'via': g.get('via', ''), 'title': g['title'],
            'lines': [{'depth': d, 'text': t} for d, t in body], 'copy_body': gm.plain_body(body),
            'checks': res, 'status': gm.overall(res)}


def page_data(data, results):
    today = day(data['updated'])
    money, _ = amounts(data)
    papers = {doc['id']: paper(g, res) for doc, g, res in drafts(data)}
    docs = [{**{k: v for k, v in d.items() if k != 'draft'}, 'status_label': STATUS[d['status']],
             'date_text': fmt(d['date']) if d.get('date') else '', 'due_text': fmt(d['due']) if d.get('due') else '',
             'amount': money.get(d['id']), 'draft': papers.get(d['id'])}
            for d in data['docs']]
    schedule = [{**s, 'date_text': fmt(s['date']), 'days': (day(s['date']) - today).days}
                for s in sorted(data.get('schedule', []), key=lambda s: s['date'])]
    log = [{**l, 'date_text': fmt(l['date'])} for l in sorted(data.get('log', []), key=lambda l: l['date'], reverse=True)]
    return {'example': data.get('example', False), 'look': data.get('look', ''), 'school': data['school'], 'project': data['project'],
            'owner': data.get('owner', ''), 'budget_code': data.get('budget_code', ''),
            'period': ' ~ '.join(fmt(p) for p in data.get('period', [])), 'updated': fmt(data['updated']),
            'decide': data.get('decide', []), 'docs': docs, 'ledger': ledger(data), 'schedule': schedule,
            'log': log, 'checks': results, 'guide': guide_data(data)}


def render(data, results):
    html = TEMPLATE.read_text(encoding='utf-8')
    payload = json.dumps(page_data(data, results), ensure_ascii=False).replace('</', '<\\/')
    title = html_lib.escape(data.get('page_title') or data['project'] + ' 보드')
    return html.replace('__PAGE_TITLE__', title).replace('"__BOARD_DATA__"', payload)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input'); ap.add_argument('-o', '--output')
    ap.add_argument('--check', action='store_true', help='검사만 하고 화면은 만들지 않아요')
    a = ap.parse_args()
    try:
        data = json.loads(Path(a.input).read_text(encoding='utf-8'))
        results = check(data)
    except (OSError, json.JSONDecodeError, ValueError, KeyError) as e:
        print(f'검사하지 못했어요: {e}', file=sys.stderr); sys.exit(2)
    except (TypeError, AttributeError, IndexError):
        print('검사하지 못했어요: 입력 자료의 값이나 구조를 확인해 주세요.', file=sys.stderr); sys.exit(2)
    for r in results: print(f"[{r['status']}] {r['id']} {r['label']}: {r['detail']}")
    for doc, _, res in drafts(data):
        for r in res: print(f"    [{r['status']}] {doc['id']} 기안문 {r['id']} {r['label']}: {r['detail']}")
    if any(r['status'] == 'fail' for r in results):
        print('고칠 곳이 있어서 화면을 만들지 않았어요.', file=sys.stderr); sys.exit(1)
    for line in say_steps(data): print(line)
    if a.check or not a.output: return
    out = Path(a.output)
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(data, results), encoding='utf-8')
    except OSError as e:
        print(f'화면을 저장하지 못했어요: 저장 경로를 확인해 주세요. {e}', file=sys.stderr); sys.exit(2)
    print(out)


if __name__ == '__main__': main()
