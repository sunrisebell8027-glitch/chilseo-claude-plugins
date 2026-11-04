#!/usr/bin/env python3
"""Build a 가정통신문 HWPX (and a guardian preview page) from reviewed JSON.

    python3 build_newsletter.py 통신문.json -o 결과/가정통신문.hwpx --preview 결과/미리보기.html

The template is the school's approved 가정통신문 with {{MARKER}} texts: the
greeting and note paragraphs are copied once per entry and the 구분/내용 table
gets one row per item. The consent form is kept only when the JSON has `reply`.
"""
from __future__ import annotations
import argparse, copy, datetime, hashlib, html, json, re, subprocess, sys, zipfile
from pathlib import Path
from lxml import etree as E
SCRIPTS = Path(__file__).resolve().parent
SKILL = SCRIPTS.parent
DEFAULT_TEMPLATE = SKILL/'templates'/'chilseo_newsletter_template.hwpx'
PREVIEW = SKILL/'assets'/'preview.html'
NS = {'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph', 'opf': 'http://www.idpf.org/2007/opf/'}
T = '{%s}t' % NS['hp']
DOW = '월화수목금토일'
CONFIRM = '[확인 필요]'
LINE_EXTRA = 1883  # 한 줄 더 쓸 때 늘어나는 칸 높이: 승인된 양식의 두 줄 칸(4448) - 한 줄 칸(2565)
DATE = re.compile(r'(?<!\d)(?:(\d{4})\.\s*)?(\d{1,2})\.\s*(\d{1,2})\.\s*\(([월화수목금토일])\)')

def resolve_template(name=None, base=None):
    if not name: return DEFAULT_TEMPLATE
    p = Path(name).expanduser()
    for c in ([p] if p.is_absolute() else [Path(base or '.')/p, SKILL/'templates'/p]):
        if c.exists(): return c
    raise FileNotFoundError(f'Template not found: {name}')

def dates_in(text, year=None):
    """Yield (date, weekday-as-written, raw) for each dated mention; a short date takes the last full date's year."""
    for m in DATE.finditer(text):
        if m.group(1): year = int(m.group(1))
        if not year: continue
        try: d = datetime.date(year, int(m.group(2)), int(m.group(3)))
        except ValueError: d = None
        yield d, m.group(4), m.group(0)

def strings(data):
    """Every text the notice shows, in reading order."""
    out = [data['title'], *data.get('greeting', [])]
    out += [f'{i.get("label", "")} {i["text"]}' for i in data.get('items', [])] + data.get('notes', [])
    s = data.get('summary') or {}
    out += [s.get('when', ''), s.get('reply_by', ''), *s.get('bring', [])]
    r = data.get('reply') or {}
    out += [r.get('title', ''), r.get('pledge', ''), r.get('note', '')]
    return [x for x in out if x]

def privacy_lines(reply):
    p = reply.get('privacy') or {}
    if p.get('include') is not True: return []
    v = lambda k: p.get(k) or CONFIRM
    return [f'※ 개인정보 수집·이용 안내: 수집 항목({v("items")}), 이용 목적({v("purpose")}), 보유 기간({v("retention")})',
            f'   동의하지 않을 수 있으며, 동의하지 않으면 {v("refusal")}.',
            '   개인정보 수집·이용에 동의합니까?   □ 동의함   □ 동의하지 않음']

def validate(data, masthead=None):
    """Raise ValueError on what must be fixed; return the list of things to confirm."""
    for key in ('title', 'school', 'items', 'summary'):
        if not data.get(key): raise ValueError(f'Missing required field: {key}')
    if masthead is not None and data['school'] not in masthead:
        raise ValueError('School name not found in the template masthead')
    if not data['summary'].get('when'): raise ValueError('summary.when is required (보호자가 맨 위에서 볼 날짜)')
    year = None
    if data.get('doc_date'): year = datetime.date.fromisoformat(data['doc_date']).year
    for text in strings(data):
        for d, dow, raw in dates_in(text, year):
            if d is None: raise ValueError(f'Invalid date: {raw}')
            if DOW[d.weekday()] != dow: raise ValueError(f'Weekday mismatch: {raw} is {DOW[d.weekday()]}')
    confirm = []
    reply = data.get('reply')
    if reply:
        due = data['summary'].get('reply_by')
        if not due: raise ValueError('summary.reply_by is required when there is a reply form')
        first_event = next((d for d, _, _ in dates_in(data['summary']['when'], year) if d), None)
        due_date = next((d for d, _, _ in dates_in(due, first_event.year if first_event else year) if d), None)
        if first_event and due_date and due_date >= first_event:
            raise ValueError('Reply deadline must come before the event')
        include = (reply.get('privacy') or {}).get('include')
        if include is None:
            confirm.append('동의서에 학생·보호자 이름과 서명을 받아요. 개인정보 수집·이용 동의 문구를 넣을지 정해 주세요.')
        elif include is True:
            confirm += [f'개인정보 안내의 {k} 칸' for k in ('items', 'purpose', 'retention', 'refusal')
                        if not (reply['privacy'].get(k))]
    m = data.get('masthead') or {}
    if len(m.get('phones') or []) < 2 or not m.get('homepage'):
        confirm.append('머리말의 교무실·행정실 전화번호와 누리집 주소를 학교설정에서 채워 주세요.')
    n = json.dumps(data, ensure_ascii=False).count(CONFIRM)
    if n: confirm.append(f'{CONFIRM}로 둔 {n}곳을 채워 주세요.')
    return confirm

def build(data, target, base=None):
    template = resolve_template(data.get('template'), base)
    with zipfile.ZipFile(template) as z: parts = {i.filename: z.read(i.filename) for i in z.infolist()}
    sec = E.fromstring(parts['Contents/section0.xml'])
    masthead = ''.join(list(sec)[0].itertext())
    confirm = validate(data, masthead)
    today = datetime.date.fromisoformat(data['doc_date']) if data.get('doc_date') else datetime.date.today()
    school = data['school']

    def holder(marker):
        for t in sec.iter(T):
            if t.text and marker in t.text: return t
        raise ValueError(f'Template is missing {marker}')
    def para_of(t):
        p = t.getparent()
        while E.QName(p).localname != 'p': p = p.getparent()
        return p
    def fill(marker, value):
        t = holder(marker); t.text = t.text.replace(marker, value)
    def repeat(marker, values):
        """Copy the marker's paragraph once per value, in order; drop it when there are none."""
        t = holder(marker); p = para_of(t); parent = p.getparent(); at = parent.index(p)
        for i, v in enumerate(values):
            q = copy.deepcopy(p)
            for tt in q.iter(T):
                if tt.text and marker in tt.text: tt.text = tt.text.replace(marker, v)
            parent.insert(at + 1 + i, q)
        parent.remove(p)

    def item_rows(items):
        """One 구분/내용 row per item, in the template's first/middle/last row styles.

        A text with line breaks becomes one paragraph per line and the row grows
        by LINE_EXTRA per extra line (the approved form's two-line row).
        """
        styles = []
        for t in sec.iter(T):
            if t.text and '{{ITEM_LABEL}}' in t.text:
                row = t.getparent()
                while E.QName(row).localname != 'tr': row = row.getparent()
                styles.append(row)
        tbl = styles[0].getparent(); at = tbl.index(styles[0]); first = tbl.findall('hp:tr', NS).index(styles[0])
        last = len(items) - 1
        for n, item in enumerate(items):
            r = copy.deepcopy(styles[0] if n == 0 else styles[-1] if n == last else styles[1])
            for a in r.iter('{%s}cellAddr' % NS['hp']): a.set('rowAddr', str(first + n))
            for t in r.iter(T):
                if t.text and '{{ITEM_LABEL}}' in t.text: t.text = t.text.replace('{{ITEM_LABEL}}', item.get('label', ''))
            t = next(t for t in r.iter(T) if t.text and '{{ITEM_TEXT}}' in t.text); p = para_of(t)
            lines = item['text'].split('\n')
            for line in lines:
                q = copy.deepcopy(p)
                for tt in q.iter(T):
                    if tt.text and '{{ITEM_TEXT}}' in tt.text: tt.text = tt.text.replace('{{ITEM_TEXT}}', line)
                p.addprevious(q)
            p.getparent().remove(p)
            for sz in r.iter('{%s}cellSz' % NS['hp']): sz.set('height', str(int(sz.get('height')) + LINE_EXTRA * (len(lines) - 1)))
            tbl.insert(at + n, r)
        for row in styles: tbl.remove(row)
        tbl.set('rowCnt', str(first + len(items)))
        heights = [int(tr.find('hp:tc/hp:cellSz', NS).get('height')) for tr in tbl.findall('hp:tr', NS)]
        tbl.find('hp:sz', NS).set('height', str(sum(heights)))

    m = data.get('masthead') or {}
    phones = (m.get('phones') or []) + [CONFIRM, CONFIRM]
    school_year = today.year if today.month >= 3 else today.year - 1
    fill('{{SHORT}}', re.sub(r'(초|중|고)(등)?학교$', r'\1', school))  # 칠서초등학교 -> 칠서초, to fit the narrow cell
    fill('{{YEAR}}', str(school_year))
    fill('{{TEL1}}', phones[0]); fill('{{TEL2}}', phones[1]); fill('{{HOMEPAGE}}', m.get('homepage') or CONFIRM)
    fill('{{TITLE}}', data['title'])
    repeat('{{GREETING}}', data.get('greeting') or [])
    fill('{{ITEMS_HEAD}}', data.get('items_title') or '< 안내 내용 >')
    item_rows(data['items'])
    repeat('{{NOTE}}', [x if x.lstrip().startswith('※') else '※ ' + x for x in data.get('notes') or []])
    fill('{{DATE}}', data.get('issue_date') or f'{today.year}년 {today.month}월    일')
    head_p = para_of(holder('{{HEAD}}'))
    fill('{{HEAD}}', ' '.join(school + '장'))
    reply = data.get('reply')
    if reply:
        fill('{{REPLY_TITLE}}', reply.get('title') or f'『{data["title"]}』 참가 동의서')
        repeat('{{PLEDGE}}', [reply.get('pledge') or '상기 내용을 확인하고 동의서를 제출합니다.'] + privacy_lines(reply))
        note = reply.get('note')
        repeat('{{REPLY_NOTE}}', [note if note.lstrip().startswith('※') else '※' + note] if note else [])
    else:
        body = list(sec)
        for p in body[body.index(head_p) + 1:]: sec.remove(p)

    for i, p in enumerate(sec.iter('{%s}p' % NS['hp'])): p.set('id', str(300000 + i))
    for el in sec.findall('.//hp:linesegarray', NS): el.getparent().remove(el)
    manifest = E.fromstring(parts['Contents/content.hpf'])
    manifest.find('.//opf:title', NS).text = data['title']
    for el in manifest.findall('.//opf:meta', NS):
        if el.get('name') in ('date', 'ModifiedDate'): el.text = today.isoformat()
        if el.get('name') == 'subject': el.text = '가정통신문'
    texts = [t.text or '' for t in sec.iter(T)]
    parts['Preview/PrvText.txt'] = '\n'.join(texts).encode('utf-8')
    for name, root in [('Contents/section0.xml', sec), ('Contents/content.hpf', manifest)]:
        parts[name] = E.tostring(root, encoding='UTF-8', xml_declaration=True, standalone=True)
    target = Path(target); target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', parts.pop('mimetype'), compress_type=zipfile.ZIP_STORED)
        for name, value in parts.items(): z.writestr(name, value)
    subprocess.run([sys.executable, str(SCRIPTS/'fix_namespaces.py'), str(target)], check=True, stdout=subprocess.DEVNULL)
    sys.path.insert(0, str(SCRIPTS))
    import gate
    fs, blocked = gate.run(target)
    report = {'file': str(target), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'template': template.name,
              'checks': [f.__dict__ for f in fs], 'blocked': bool(blocked), 'needs_confirmation': confirm, 'visual_review': 'pending'}
    target.with_suffix('.validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    target.with_suffix('.txt').write_text('\n'.join(texts))
    if blocked: raise ValueError('Output validation failed: ' + str([f.detail for f in blocked]))
    return report

def preview(data, confirm, target):
    page = {k: data.get(k) for k in ('school', 'title', 'greeting', 'items', 'notes', 'summary', 'issue_date', 'example')}
    reply = data.get('reply')
    page['reply'] = reply and {'title': reply.get('title') or f'『{data["title"]}』 참가 동의서', 'pledge': reply.get('pledge'), 'note': reply.get('note'),
                               'privacy': privacy_lines(reply), 'privacy_include': (reply.get('privacy') or {}).get('include')}
    page['confirm'] = confirm
    payload = json.dumps(page, ensure_ascii=False).replace('</', '<\\/')
    out = PREVIEW.read_text().replace('__PAGE_TITLE__', html.escape(data.get('page_title') or data['title'][:30]))
    target = Path(target); target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(out.replace('"__NOTICE_DATA__"', payload))

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('input', type=Path); ap.add_argument('-o', '--output', type=Path, required=True)
    ap.add_argument('--preview', type=Path, help='보호자용 미리보기 HTML도 만든다')
    a = ap.parse_args()
    try:
        data = json.loads(a.input.read_text())
        report = build(data, a.output, base=a.input.parent)
        if a.preview: preview(data, report['needs_confirmation'], a.preview)
    except (ValueError, KeyError, FileNotFoundError) as e:
        print(f'만들지 못했어요: {e}', file=sys.stderr); return 1
    print(json.dumps({'file': report['file'], 'package_checks': 'passed', 'needs_confirmation': report['needs_confirmation'],
                      'preview': str(a.preview) if a.preview else None, 'visual_review': 'pending'}, ensure_ascii=False, indent=1))
    return 0

if __name__ == '__main__': raise SystemExit(main())
