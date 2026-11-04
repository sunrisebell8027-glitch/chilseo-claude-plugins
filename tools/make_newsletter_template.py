#!/usr/bin/env python3
"""Turn one approved school 가정통신문 HWPX into the empty newsletter template.

Kept as the school made it: the masthead (slogan, emblem beside the school
name, contact rows), the title box, the 구분/내용 table, the date and 학교장
lines, the cut line and the consent form (학년·반·이름 line, 동의함 table,
signature lines). Every changing text becomes a {{MARKER}} that
build_newsletter.py fills; phone numbers, the website, the earlier notice,
the preview image and author metadata are removed.

The source layout is the 칠서초 현장체험학습 가정통신문 that was approved in
2026 (paragraph order below). Another school's file needs its own index map.
Then every top-level table and the cut line are fitted to the text width.
"""
import argparse, copy, zipfile
from pathlib import Path
from lxml import etree as E
NS = {'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph', 'opf': 'http://www.idpf.org/2007/opf/',
      'hh': 'http://www.hancom.co.kr/hwpml/2011/head', 'hc': 'http://www.hancom.co.kr/hwpml/2011/core'}
HP = '{%s}' % NS['hp']

def set_marker(p, marker, keep_prefix=True):
    """Put marker in the paragraph's longest text; drop every other non-space text."""
    ts = [t for t in p.iter('{%s}t' % NS['hp'])]
    main = max(ts, key=lambda t: len((t.text or '').strip()))
    lead = (main.text or '')[:len(main.text or '') - len((main.text or '').lstrip())] if keep_prefix else ''
    main.text = lead + marker
    for c in list(main): main.remove(c)
    for t in ts:
        if t is not main and (t.text or '').strip(): t.getparent().remove(t)

def set_runs(p, markers):
    """Give each non-space text of the paragraph, in order, its own marker (None keeps the text)."""
    ts = [t for t in p.iter(HP + 't') if (t.text or '').strip()]
    for t, m in zip(ts, markers):
        if m is not None:
            t.text = m
            for c in list(t): t.remove(c)

def cell(tbl, row, col):
    for tc in tbl.iter('{%s}tc' % NS['hp']):
        a = tc.find('hp:cellAddr', NS)
        if a.get('rowAddr') == str(row) and a.get('colAddr') == str(col): return tc
    raise KeyError((row, col))

def fit_table(tbl, width):
    """Resize a table to `width` (outer margins kept) and scale its columns in proportion."""
    cells = [(int(tc.find('hp:cellAddr', NS).get('colAddr')), int(tc.find('hp:cellSpan', NS).get('colSpan')), tc)
             for tc in tbl.findall('hp:tr/hp:tc', NS)]
    cols = {c: int(tc.find('hp:cellSz', NS).get('width')) for c, n, tc in cells if n == 1}
    for _ in range(len(cells)):  # a column with only merged cells takes what its merged cell leaves over
        for c, n, tc in cells:
            missing = [c + i for i in range(n) if c + i not in cols]
            if len(missing) == 1:
                cols[missing[0]] = int(tc.find('hp:cellSz', NS).get('width')) - sum(cols.get(c + i, 0) for i in range(n) if c + i != missing[0])
    out = tbl.find('hp:outMargin', NS)
    target = width - int(out.get('left')) - int(out.get('right'))
    old = sum(cols.values())
    new = {c: round(w * target / old) for c, w in cols.items()}
    new[max(new)] += target - sum(new.values())
    for c, n, tc in cells: tc.find('hp:cellSz', NS).set('width', str(sum(new[c + i] for i in range(n))))
    tbl.find('hp:sz', NS).set('width', str(target))

CUT = ('<hp:run xmlns:hp="%(hp)s" charPrIDRef="%(cp)s"><hp:tbl id="%(id)s" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM"'
       ' textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="0" rowCnt="1" colCnt="1" cellSpacing="0"'
       ' borderFillIDRef="%(tbf)s" noAdjust="0"><hp:sz width="%(w)s" widthRelTo="ABSOLUTE" height="1000" heightRelTo="ABSOLUTE" protect="0"/>'
       '<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="PARA"'
       ' vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/><hp:outMargin left="0" right="0" top="0" bottom="0"/>'
       '<hp:inMargin left="0" right="0" top="0" bottom="0"/><hp:tr><hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0"'
       ' borderFillIDRef="%(bf)s"><hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0"'
       ' linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0"><hp:p id="0" paraPrIDRef="%(pp)s" styleIDRef="%(st)s"'
       ' pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="%(cp)s"><hp:t/></hp:run></hp:p></hp:subList>'
       '<hp:cellAddr colAddr="0" rowAddr="0"/><hp:cellSpan colSpan="1" rowSpan="1"/><hp:cellSz width="%(w)s" height="1000"/>'
       '<hp:cellMargin left="0" right="0" top="0" bottom="0"/></hp:tc></hp:tr></hp:tbl><hp:t/></hp:run>')

def fit_to_page(sec, header, cut_char=None):
    """Make every top-level table and the cut line span the text area.

    A space typed before an inline table pushes it past the right margin, so it
    is dropped. The cut line was a typed row of dashes whose length followed the
    font; it becomes a one-cell table with only a dashed bottom border, set in
    `cut_char` (a small font) so the line is no taller than it needs to be.
    """
    page = sec.find('.//hp:pagePr', NS); m = page.find('hp:margin', NS)
    width = int(page.get('width')) - int(m.get('left')) - int(m.get('right'))
    for p in sec.findall('hp:p', NS):
        tables = p.findall('hp:run/hp:tbl', NS)
        for tbl in tables: fit_table(tbl, width)
        if tables:
            for t in p.findall('hp:run/hp:t', NS):
                if not (t.text or '').strip(): t.text = None
    cut = [p for p in sec.findall('hp:p', NS) if set(''.join(t.text or '' for t in p.iter(HP + 't'))) == {'-'}]
    if not cut: return
    fills = header.find('.//hh:borderFills', NS); paras = header.find('.//hh:paraProperties', NS)
    bf = copy.deepcopy(fills.find("hh:borderFill[@id='2']", NS)); bf_id = str(max(int(b.get('id')) for b in fills) + 1)
    bf.set('id', bf_id)
    for side in ('left', 'right', 'top'): bf.find('hh:%sBorder' % side, NS).set('type', 'NONE')
    bf.find('hh:bottomBorder', NS).attrib.update({'type': 'DASH', 'width': '0.12 mm', 'color': '#000000'})
    fills.append(bf); fills.set('itemCnt', str(len(fills)))
    next_tbl = max(int(t.get('id')) for t in sec.iter(HP + 'tbl')) + 1
    for p in cut:
        pp = copy.deepcopy(paras.find("hh:paraPr[@id='%s']" % p.get('paraPrIDRef'), NS)); pp_id = str(max(int(x.get('id')) for x in paras) + 1)
        pp.set('id', pp_id)
        for intent in pp.iter('{%s}intent' % NS['hc']): intent.set('value', '0')
        paras.append(pp); paras.set('itemCnt', str(len(paras)))
        cp = cut_char or p.find('hp:run', NS).get('charPrIDRef')
        for run in p.findall('hp:run', NS): p.remove(run)
        p.set('paraPrIDRef', pp_id)
        p.append(E.fromstring(CUT % {'hp': NS['hp'], 'cp': cp, 'id': next_tbl, 'tbf': '3', 'w': width, 'bf': bf_id,
                                     'pp': pp_id, 'st': p.get('styleIDRef')}))
        next_tbl += 1

def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('source'); ap.add_argument('-o', '--output', required=True)
    a = ap.parse_args()
    with zipfile.ZipFile(a.source) as z: parts = {i.filename: z.read(i.filename) for i in z.infolist()}
    sec = E.fromstring(parts['Contents/section0.xml'])
    header = E.fromstring(parts['Contents/header.xml'])
    p = list(sec)
    mast = p[0].find('hp:run/hp:tbl', NS)
    info = cell(mast, 0, 2).findall('hp:subList/hp:p', NS)
    set_runs(info[0], ['{{SHORT}}', '{{YEAR}}학년도'])
    set_runs(info[1], [None, '{{TEL1}}']); set_runs(info[2], [None, '{{TEL2}}'])
    set_marker(info[3], '{{HOMEPAGE}}', keep_prefix=False)
    set_marker(cell(p[1].find('hp:run/hp:tbl', NS), 1, 0).find('.//hp:p', NS), '{{TITLE}}', keep_prefix=False)
    set_marker(p[2], '{{GREETING}}'); sec.remove(p[3])
    set_marker(p[5], '{{ITEMS_HEAD}}')
    items = p[6].find('hp:run/hp:tbl', NS)
    rows = items.findall('hp:tr', NS)
    keep = [rows[1], rows[2], rows[-1]]  # first row (double line on top), middle rows, last row (thick bottom)
    for row in keep:
        set_marker(row.findall('hp:tc', NS)[0].find('.//hp:p', NS), '{{ITEM_LABEL}}')
        text_cell = row.findall('hp:tc', NS)[1].find('hp:subList', NS)
        for extra in text_cell.findall('hp:p', NS)[1:]: text_cell.remove(extra)
        set_marker(text_cell.find('hp:p', NS), '{{ITEM_TEXT}}')
    for extra in rows[1:]:
        if extra not in keep: items.remove(extra)
    items.set('rowCnt', '4')
    note = copy.deepcopy(p[16]); set_marker(note, '{{NOTE}}'); p[6].addnext(note)
    set_marker(p[7], '{{DATE}}'); set_marker(p[8], '{{HEAD}}')
    reply_tbl = p[10].find('hp:run/hp:tbl', NS); reply_box = cell(reply_tbl, 0, 0).find('hp:subList', NS)
    for extra in reply_box.findall('hp:p', NS)[1:]: reply_box.remove(extra)
    for sz in (reply_tbl.find('hp:sz', NS), reply_tbl.find('.//hp:cellSz', NS)): sz.set('height', '2600')  # 두 줄 → 한 줄 상자
    set_marker(reply_box.find('hp:p', NS), '{{REPLY_TITLE}}', keep_prefix=False)
    set_marker(p[13], '{{PLEDGE}}'); set_marker(p[16], '{{REPLY_NOTE}}')
    for el in sec.findall('.//hp:linesegarray', NS): el.getparent().remove(el)
    used = {el.get('binaryItemIDRef') for el in sec.iter() if el.get('binaryItemIDRef')}
    manifest = E.fromstring(parts['Contents/content.hpf'])
    for item in manifest.findall('.//opf:item', NS):
        if item.get('href', '').startswith('BinData/') and item.get('id') not in used:
            parts.pop(item.get('href'), None); item.getparent().remove(item)
    for meta in manifest.findall('.//opf:meta', NS):
        if meta.get('name') in ('creator', 'lastsaveby', 'subject', 'description', 'CreatedDate', 'ModifiedDate', 'date', 'keyword'): meta.text = None
    manifest.find('.//opf:title', NS).text = '가정통신문 양식'
    parts.pop('Preview/PrvImage.png', None)
    # 한글 줄 나눔을 어절 단위로: OWPML의 KEEP_WORD는 글자 단위라서(승인본도 '협|조를'처럼 낱말 중간에서
    # 끊긴다) BREAK_WORD로 바꾼다.
    for b in header.iter('{%s}breakSetting' % NS['hh']): b.set('breakNonLatinWord', 'BREAK_WORD')
    fit_to_page(sec, header, cut_char=note.find('hp:run', NS).get('charPrIDRef'))
    write(parts, sec, header, manifest, a.output)

def write(parts, sec, header, manifest, output):
    parts['Preview/PrvText.txt'] = '\n'.join(t.text or '' for t in sec.iter('{%s}t' % NS['hp'])).encode()
    parts['Contents/section0.xml'] = E.tostring(sec, encoding='UTF-8', xml_declaration=True, standalone=True)
    parts['Contents/header.xml'] = E.tostring(header, encoding='UTF-8', xml_declaration=True, standalone=True)
    if manifest is not None: parts['Contents/content.hpf'] = E.tostring(manifest, encoding='UTF-8', xml_declaration=True, standalone=True)
    out = Path(output); out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', parts.pop('mimetype'), compress_type=zipfile.ZIP_STORED)
        for name, value in parts.items(): z.writestr(name, value)
    print(out)

if __name__ == '__main__': main()
