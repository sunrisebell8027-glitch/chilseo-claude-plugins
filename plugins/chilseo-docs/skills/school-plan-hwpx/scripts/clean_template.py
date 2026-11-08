#!/usr/bin/env python3
"""Turn a real school plan HWPX into an empty template for build.py.

Keeps the school masthead (slogan, title box, emblem) and one sample body
paragraph and one sample table for their styles. Every other paragraph, the
second section, the preview image and unused pictures are removed, and all
remaining text is cleared, so no earlier plan content leaves the school.

The output always has this shape, which build.py relies on:
  section0 children 0..2  masthead (title box is child 1, row 2)
  section0 child 3        sample paragraph (text cleared)
  section0 child 4        sample table (text cleared, >= 2 rows and 2 columns)

Usage:
  python3 clean_template.py 원본계획서.hwpx -o 학교_계획서_양식.hwpx [--para N] [--table N]
"""
from __future__ import annotations
import argparse, os, re, shutil, subprocess, sys, zipfile
from pathlib import Path


def _venv_python(folder):
    return folder / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def _python_candidates():
    configured = os.environ.get('CHILSEO_PYTHON')
    home = Path(os.environ.get('CHILSEO_HOME') or Path.home() / '.chilseo').expanduser()
    return ([configured] if configured else []) + [
        _venv_python(home / 'venv'), _venv_python(Path(__file__).resolve().parent.parent / '.venv'),
        _venv_python(Path.cwd() / '.venv')]


def _bootstrap():
    if 'CHILSEO_BOOTSTRAPPED' not in os.environ:
        for candidate in _python_candidates():
            executable = shutil.which(str(candidate))
            if not executable or os.path.normcase(os.path.abspath(executable)) == os.path.normcase(os.path.abspath(sys.executable)):
                continue
            try:
                check = subprocess.run([executable, '-c', 'import lxml'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if check.returncode == 0:
                    env = os.environ.copy()
                    env['CHILSEO_BOOTSTRAPPED'] = '1'
                    sys.exit(subprocess.run([executable, *sys.argv], env=env).returncode)
            except OSError:
                continue
    requirements = Path(__file__).resolve().parent.parent / 'requirements.txt'
    requirements_arg = f'"{requirements}"' if ' ' in str(requirements) else str(requirements)
    print('문서를 만들려면 lxml과 python-hwpx가 필요해요.\n'
          "Claude Code에서 먼저 '시작하기'(school-start)를 실행해 주세요.\n"
          f'직접 설치하려면 다음 명령을 실행해 주세요: python3 -m pip install -r {requirements_arg}\n'
          'externally-managed-environment(시스템 설치 제한) 오류가 나면 '
          "'시작하기'로 별도 설치 폴더를 만들어 주세요.", file=sys.stderr)
    sys.exit(2)


try:
    from lxml import etree as E
except ImportError:
    _bootstrap()

NS = {'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
      'opf': 'http://www.idpf.org/2007/opf/'}
MASTHEAD = 3
TITLE_PLACEHOLDER = '제목'


def has_table(p):
    return p.find('.//hp:tbl', NS) is not None


def pick_para(sec):
    for i, p in enumerate(sec):
        if i >= MASTHEAD and not has_table(p) and p.find('.//hp:pic', NS) is None \
                and ''.join(p.itertext()).strip():
            return i
    raise ValueError('No plain body paragraph found; pass --para')


def pick_table(sec):
    for i, p in enumerate(sec):
        t = p.find('.//hp:tbl', NS)
        if i >= MASTHEAD and t is not None and int(t.get('rowCnt')) >= 2 and int(t.get('colCnt')) >= 2:
            return i
    raise ValueError('No table with 2+ rows and columns found; pass --table')


def clear_text(el):
    for t in el.iter('{%s}t' % NS['hp']):
        for child in list(t):
            t.remove(child)
        t.text = ''


def clean(src, target, para=None, table=None):
    with zipfile.ZipFile(src) as z:
        parts = {i.filename: z.read(i.filename) for i in z.infolist()}
    sec = E.fromstring(parts['Contents/section0.xml'])
    title = sec[1].findall('.//hp:tr', NS)
    if len(sec) <= MASTHEAD or len(title) < 2:
        raise ValueError('First three paragraphs must be the masthead with a title box')
    para = pick_para(sec) if para is None else para
    table = pick_table(sec) if table is None else table
    keep = list(sec)[:MASTHEAD] + [sec[para], sec[table]]
    for child in list(sec):
        if all(child is not k for k in keep):
            sec.remove(child)
    # Sample table: header row and one body row are enough for build.py.
    tbl = sec[MASTHEAD + 1].find('.//hp:tbl', NS)
    for tr in tbl.findall('hp:tr', NS)[2:]:
        tbl.remove(tr)
    tbl.set('rowCnt', '2')
    for span in tbl.iter('{%s}cellSpan' % NS['hp']):
        span.set('rowSpan', '1')
    for child in keep[MASTHEAD:]:
        # Fields (formulas, hyperlinks) keep earlier values in their parameters.
        for ctrl in child.findall('.//hp:ctrl', NS):
            ctrl.getparent().remove(ctrl)
        clear_text(child)
    # Title box: one placeholder line, earlier plan name removed.
    tp = sec[1].findall('.//hp:tr', NS)[1].find('.//hp:subList/hp:p', NS)
    ts = tp.findall('.//hp:t', NS)
    clear_text(tp)
    if ts:
        ts[0].text = TITLE_PLACEHOLDER
    for el in sec.findall('.//hp:linesegarray', NS):
        el.getparent().remove(el)
    parts['Contents/section0.xml'] = E.tostring(sec, encoding='UTF-8', xml_declaration=True, standalone=True)

    head = E.fromstring(parts['Contents/header.xml'])
    head.set('secCnt', '1')
    parts['Contents/header.xml'] = E.tostring(head, encoding='UTF-8', xml_declaration=True, standalone=True)
    for name in [n for n in parts if re.fullmatch(r'Contents/section[1-9]\d*\.xml', n)]:
        parts.pop(name)
    parts.pop('Preview/PrvImage.png', None)

    # Drop pictures no remaining part refers to, and personal document metadata.
    used = set(re.findall(rb'binaryItemIDRef="([^"]+)"', parts['Contents/section0.xml'] + parts['Contents/header.xml']))
    manifest = E.fromstring(parts['Contents/content.hpf'])
    for item in manifest.xpath('//opf:item', namespaces=NS):
        href = item.get('href') or ''
        gone = href not in parts
        if href.startswith('BinData/') and item.get('id').encode() not in used:
            parts.pop(href, None)
            gone = True
        if gone:
            for ref in manifest.xpath(f'//opf:itemref[@idref="{item.get("id")}"]', namespaces=NS):
                ref.getparent().remove(ref)
            item.getparent().remove(item)
    title_el = manifest.find('.//opf:title', NS)
    if title_el is not None:
        title_el.text = None
    for meta in manifest.findall('.//opf:meta', NS):
        if meta.get('name') in ('creator', 'lastsaveby', 'subject', 'description', 'keyword', 'date', 'CreatedDate', 'ModifiedDate'):
            meta.text = None
    parts['Contents/content.hpf'] = E.tostring(manifest, encoding='UTF-8', xml_declaration=True, standalone=True)
    texts = [x.text or '' for x in sec.findall('.//hp:t', NS)]
    parts['Preview/PrvText.txt'] = '\n'.join(t for t in texts if t).encode('utf-8')

    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', parts.pop('mimetype'), compress_type=zipfile.ZIP_STORED)
        for name, value in parts.items():
            z.writestr(name, value)
    return target


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('input', type=Path)
    ap.add_argument('-o', '--output', type=Path, required=True)
    ap.add_argument('--para', type=int, help='index of the sample body paragraph in section0')
    ap.add_argument('--table', type=int, help='index of the sample table paragraph in section0')
    args = ap.parse_args()
    try:
        print(clean(args.input, args.output, args.para, args.table))
    except (ValueError, KeyError, IndexError, AttributeError, OSError, zipfile.BadZipFile, E.XMLSyntaxError) as e:
        print(f'양식을 만들지 못했어요. 입력 파일과 문단·표 번호를 확인해 주세요: {e}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
