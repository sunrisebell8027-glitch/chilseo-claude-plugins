#!/usr/bin/env python3
"""Turn one school 가정통신문 HWPX into the empty newsletter template.

Kept: the school masthead (slogan, emblem, school name), the title box, one
sample paragraph of each kind and the reply form. Every text becomes a
{{MARKER}} that build_newsletter.py fills; contact lines, the earlier notice,
unused pictures, the preview image and author metadata are removed.

The source layout is the 칠서초 가정통신문 (paragraph order below). Another
school's file needs its own index map.
"""
import argparse, zipfile
from pathlib import Path
from lxml import etree as E
NS = {'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph', 'opf': 'http://www.idpf.org/2007/opf/'}

def set_marker(p, marker, keep_prefix=True):
    """Put marker in the paragraph's longest text; drop every other non-space text."""
    ts = [t for t in p.iter('{%s}t' % NS['hp'])]
    main = max(ts, key=lambda t: len((t.text or '').strip()))
    lead = (main.text or '')[:len(main.text or '') - len((main.text or '').lstrip())] if keep_prefix else ''
    main.text = lead + marker
    for c in list(main): main.remove(c)
    for t in ts:
        if t is not main and (t.text or '').strip(): t.getparent().remove(t)

def cell(tbl, row, col):
    for tc in tbl.iter('{%s}tc' % NS['hp']):
        a = tc.find('hp:cellAddr', NS)
        if a.get('rowAddr') == str(row) and a.get('colAddr') == str(col): return tc
    raise KeyError((row, col))

def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('source'); ap.add_argument('-o', '--output', required=True)
    a = ap.parse_args()
    with zipfile.ZipFile(a.source) as z: parts = {i.filename: z.read(i.filename) for i in z.infolist()}
    sec = E.fromstring(parts['Contents/section0.xml'])
    p = list(sec)
    set_marker(p[0], '{{LABEL}}')
    contact = cell(p[1].find('.//hp:tbl', NS), 0, 2).find('hp:subList', NS)
    for extra in contact.findall('hp:p', NS)[1:]: contact.remove(extra)
    set_marker(contact.find('hp:p', NS), '{{CONTACT}}')
    set_marker(cell(p[2].find('.//hp:tbl', NS), 1, 0).find('.//hp:p', NS), '{{TITLE}}')
    set_marker(p[3], '{{GREETING}}'); set_marker(p[5], '{{ITEM}}'); set_marker(p[11], '{{NOTE}}')
    set_marker(p[13], '{{DATE}}'); set_marker(p[14], '{{HEAD}}')
    set_marker(p[16].find('.//hp:tc//hp:p', NS), '{{REPLY_TITLE}}')
    form = p[17].find('.//hp:tbl', NS)
    set_marker(cell(form, 0, 1).find('.//hp:p', NS), '{{PROGRAM}}')
    set_marker(cell(form, 3, 0).find('.//hp:p', NS), '{{REPLY_DATE}}')
    set_marker(p[18], '{{PLEDGE}}'); set_marker(p[20], '{{TO}}')
    for extra in p[6:11]: sec.remove(extra)  # one item sample is enough
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
    parts['Preview/PrvText.txt'] = '\n'.join(t.text or '' for t in sec.iter('{%s}t' % NS['hp'])).encode()
    parts['Contents/section0.xml'] = E.tostring(sec, encoding='UTF-8', xml_declaration=True, standalone=True)
    parts['Contents/content.hpf'] = E.tostring(manifest, encoding='UTF-8', xml_declaration=True, standalone=True)
    out = Path(a.output); out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', parts.pop('mimetype'), compress_type=zipfile.ZIP_STORED)
        for name, value in parts.items(): z.writestr(name, value)
    print(out)

if __name__ == '__main__': main()
