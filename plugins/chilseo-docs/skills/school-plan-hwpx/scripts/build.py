#!/usr/bin/env python3
"""Build an internal approval HWPX from a school template and reviewed JSON.

The template must be shaped by clean_template.py: masthead (children 0..2),
a sample paragraph (child 3) and a sample table (child 4) in section0.
"""
from __future__ import annotations
import argparse, copy, datetime, hashlib, json, math, re, subprocess, sys, zipfile
from pathlib import Path
from lxml import etree as E
SCRIPTS = Path(__file__).resolve().parent
SKILL = SCRIPTS.parent
DEFAULT_TEMPLATE = SKILL/'templates'/'chilseo_plan_template.hwpx'
NS = {k: f'http://www.hancom.co.kr/hwpml/2011/{v}' for k,v in [('hp','paragraph'),('hh','head'),('hc','core')]}
NS['opf']='http://www.idpf.org/2007/opf/'
def q(k):
    a,b=k.split(':'); return '{'+NS[a]+'}'+b

def resolve_template(name=None, base=None):
    """A template name is looked up next to the input JSON, then in templates/."""
    if not name:return DEFAULT_TEMPLATE
    p=Path(name).expanduser()
    for c in ([p] if p.is_absolute() else [Path(base or '.')/p, SKILL/'templates'/p]):
        if c.exists():return c
    raise FileNotFoundError(f'Template not found: {name}')

def budget_items(b):
    """Return (items, total). Accepts {items, total} or the older {unit_price, headcount, total}."""
    if 'items' in b:return b['items'],b.get('total')
    return [{'formula':f"{b['unit_price']:,}원 × {b['headcount']}명",'amount':b['total'],
             'factors':[b['unit_price'],b['headcount']]}],b['total']

def formula_product(formula):
    """'5,000원 × 106명 × 2회' -> 1060000; None if a factor has no number."""
    product=1
    for part in re.split(r'[×xX*]',formula):
        m=re.search(r'\d[\d,]*',part)
        if not m:return None
        product*=int(m.group().replace(',',''))
    return product

def validate(data, masthead_text=None):
    for key in ('title','pages'):
        if not data.get(key): raise ValueError(f'Missing required field: {key}')
    if data.get('school') and masthead_text is not None and data['school'] not in masthead_text:
        raise ValueError('School name not found in the template masthead')
    if data.get('event_date'):datetime.date.fromisoformat(data['event_date'])
    if data.get('budget'):
        items,total=budget_items(data['budget'])
        if not items or type(total) is not int or total<=0: raise ValueError('Budget values must be positive integers')
        for item in items:
            if type(item.get('amount')) is not int or item['amount']<=0: raise ValueError('Budget values must be positive integers')
            if item.get('formula') and formula_product(item['formula'])!=item['amount']: raise ValueError('Budget calculation mismatch')
        if sum(i['amount'] for i in items)!=total: raise ValueError('Budget calculation mismatch')
        budget_tables=[block for page in data['pages'] for block in page
                       if block['kind']=='table' and any('금액' in str(c) for c in block['rows'][0])]
        if not budget_tables: raise ValueError('A budget table is required')
        cells=[str(c) for table in budget_tables for row in table['rows'][1:] for c in row]
        for amount in [total]+[i['amount'] for i in items]:
            if not any(f'{amount:,}' in c for c in cells): raise ValueError('Budget metadata and displayed amount differ')
        for item in items:
            if item.get('formula') and not any(item['formula'] in c for c in cells):
                raise ValueError('Budget metadata and displayed formula differ')
    if data.get('slots'):
        classes=[c for slot in data['slots'] for c in slot['classes']]
        if len(set(classes))!=len(classes): raise ValueError('Duplicate class in timetable')
        schedule=[block for page in data['pages'] for block in page
                  if block['kind']=='table' and block['rows'][0][:2]==['시간','학급']]
        expected=[(slot['periods'],c) for slot in data['slots'] for c in slot['classes']]
        if len(schedule)!=1 or [(r[0],r[1]) for r in schedule[0]['rows'][1:]]!=expected:
            raise ValueError('Timetable metadata and rows differ')
    for page in data['pages']:
        for block in page:
            if block['kind']=='table':
                rows=block['rows'];widths=block['widths']
                if not rows or not widths or any(w<=0 for w in widths): raise ValueError('Invalid table geometry')
                if any(len(row)!=len(widths) for row in rows): raise ValueError('Nonrectangular table')
                align=block.get('align')
                if align is not None and (len(align)!=len(widths) or any(a not in ALIGN for a in align)):
                    raise ValueError('Invalid table column alignment')
            elif block['kind'] not in ('heading','subheading','text','note'): raise ValueError('Unknown content block')

# Body-table style from a teacher's own Hangul revision: blue lines,
# tinted header row with a double bottom rule, thicker outer side lines.
TABLE_LINE='#6182D6'; TABLE_HEAD_FILL='#DFE6F7'
ALIGN={'center':'CENTER','justify':'JUSTIFY','left':'LEFT','right':'RIGHT'}
def cell_border(ri,ci,ncols):
    """Return (left, right, top, bottom, fill) for a cell by its position."""
    if ri==0:return (('SOLID','0.15 mm'),('SOLID','0.15 mm'),('SOLID','0.1 mm'),('DOUBLE_SLIM','0.5 mm'),TABLE_HEAD_FILL)
    left=('SOLID','0.15 mm' if ci==0 else '0.12 mm');right=('SOLID','0.15 mm' if ci==ncols-1 else '0.12 mm')
    top=('DOUBLE_SLIM','0.5 mm') if ri==1 else ('SOLID','0.12 mm')
    return (left,right,top,('SOLID','0.12 mm'),None)

def load_template(template):
    with zipfile.ZipFile(template) as z: parts={i.filename:z.read(i.filename) for i in z.infolist()}
    sec=E.fromstring(parts['Contents/section0.xml'])
    t=sec[4].find('.//hp:tbl',NS) if len(sec)>=5 else None
    if t is None or len(sec[1].findall('.//hp:tr',NS))<2 or len(t.findall('hp:tr',NS))<2 or int(t.get('colCnt'))<2:
        raise ValueError('Template is not prepared; run clean_template.py on the school plan first')
    masthead=''.join(''.join(c.itertext()) for c in list(sec)[:3])
    return parts,sec,masthead

def build(data, target, base=None):
    template=resolve_template(data.get('template'),base)
    parts,sec,masthead=load_template(template)
    validate(data,masthead)
    head=E.fromstring(parts['Contents/header.xml'])
    para_template=copy.deepcopy(sec[3]);table_template=copy.deepcopy(sec[4])
    run0=para_template.find('.//hp:run',NS);base_char=run0.get('charPrIDRef') if run0 is not None else '0'
    styles=head.find('.//hh:charProperties',NS);paras=head.find('.//hh:paraProperties',NS)
    def char(size,bold=False):
        el=copy.deepcopy(styles.find(f"hh:charPr[@id='{base_char}']",NS));i=str(max(int(x.get('id')) for x in styles)+1)
        el.set('id',i);el.set('height',str(int(size*100)))
        for c in el.findall('hh:bold',NS):el.remove(c)
        if bold:E.SubElement(el,q('hh:bold'))
        styles.append(el);styles.set('itemCnt',str(len(styles)));return i
    chars={k:char(s,b) for k,s,b in [('heading',14,True),('subheading',12,False),('text',11,False),('note',10,False),('cell',10,False),('cellhead',10,True),('title',16,True)]}
    def para_style(base='0',center=False,heading=False):
        el=copy.deepcopy(paras.find(f"hh:paraPr[@id='{base}']",NS));i=str(max(int(x.get('id')) for x in paras)+1);el.set('id',i)
        el.find('hh:align',NS).set('horizontal','CENTER' if center else 'JUSTIFY')
        for line in el.findall('.//hh:lineSpacing',NS):line.set('value','150' if not center else '130')
        for margin in el.findall('.//hh:margin',NS):
            for child in margin:
                local=E.QName(child).localname
                child.set('value','500' if local=='prev' and heading else '0')
        br=el.find('hh:breakSetting',NS)
        if br is not None:br.set('keepWithNext','1' if heading else '0');br.set('keepLines','0')
        paras.append(el);paras.set('itemCnt',str(len(paras)));return i
    pst={k:para_style(center=(k=='cell'),heading=(k=='heading')) for k in ['heading','text','cell']}
    # Table cells: line spacing 130% with a per-column horizontal alignment.
    cellpst={'CENTER':pst['cell']}
    for a in ('JUSTIFY','LEFT','RIGHT'):
        i=para_style(center=True);el=paras.find(f"hh:paraPr[@id='{i}']",NS);el.find('hh:align',NS).set('horizontal',a);cellpst[a]=i
    fills=head.find('.//hh:borderFills',NS);borders={}
    def border_fill(spec):
        if spec in borders:return borders[spec]
        left,right,top,bottom,fill=spec;i=str(max(int(x.get('id')) for x in fills)+1)
        el=E.SubElement(fills,q('hh:borderFill'),id=i,threeD='0',shadow='0',centerLine='NONE',breakCellSeparateLine='0')
        for tag in ('slash','backSlash'):E.SubElement(el,q('hh:'+tag),type='NONE',Crooked='0',isCounter='0')
        for tag,(kind,width) in zip(('leftBorder','rightBorder','topBorder','bottomBorder'),(left,right,top,bottom)):
            E.SubElement(el,q('hh:'+tag),type=kind,width=width,color=TABLE_LINE)
        E.SubElement(el,q('hh:diagonal'),type='SOLID',width='0.12 mm',color='#000000')
        if fill:
            brush=E.SubElement(el,q('hc:fillBrush'));E.SubElement(brush,q('hc:winBrush'),faceColor=fill,hatchColor='#000000',alpha='0')
        fills.set('itemCnt',str(len(fills)));borders[spec]=i;return i
    counter=100000
    def pid():
        nonlocal counter
        counter+=1;return str(counter)
    def ptext(text,kind='text',pagebreak=False,cell=False,align='CENTER'):
        p=copy.deepcopy(para_template)
        p.set('id',pid());p.set('pageBreak','1' if pagebreak else '0');p.set('paraPrIDRef',cellpst[align] if cell else pst['heading' if kind=='heading' else 'text'])
        for child in list(p):p.remove(child)
        run=E.SubElement(p,q('hp:run'),charPrIDRef=chars[kind])
        E.SubElement(run,q('hp:t')).text=text
        return p
    # Preserve school masthead, decorative title table and emblem; discard the samples.
    for child in list(sec)[3:]:sec.remove(child)
    titlep=sec[1].findall('.//hp:tr',NS)[1].find('hp:tc/hp:subList/hp:p',NS)
    for child in list(titlep):titlep.remove(child)
    r=E.SubElement(titlep,q('hp:run'),charPrIDRef=chars['title']);tt=E.SubElement(r,q('hp:t'))
    # A newline in the title becomes a Hangul line break.
    first,*rest=data['title'].split('\n');tt.text=first
    for line in rest:E.SubElement(tt,q('hp:lineBreak')).tail=line
    # The template has a reusable table shell; reproduce its borders/margins.
    def table(block):
        p=copy.deepcopy(table_template);p.set('id',pid());p.set('paraPrIDRef',pst['text'])
        t=p.find('.//hp:tbl',NS);t.set('id',pid());t.set('rowCnt',str(len(block['rows'])));t.set('colCnt',str(len(block['widths'])));t.set('pageBreak','CELL')
        samples=t.findall('hp:tr',NS);headercell=copy.deepcopy(samples[0][1]);bodycell=copy.deepcopy(samples[1][1])
        for row in t.findall('hp:tr',NS):t.remove(row)
        fullwidth=47622;weights=block['widths'];widths=[round(fullwidth*w/sum(weights)) for w in weights];widths[-1]=fullwidth-sum(widths[:-1])
        totalheight=0;align=[ALIGN[a] for a in block.get('align',['center']*len(widths))]
        for ri,values in enumerate(block['rows']):
            row=E.SubElement(t,q('hp:tr'))
            # Conservative heights; Hangul reflows long cell text automatically.
            height=max(2000,max(math.ceil(max(1,len(str(v)))/(max(1,w/1000)))*1400+500 for v,w in zip(values,widths)))
            totalheight+=height
            for ci,(value,width) in enumerate(zip(values,widths)):
                cell=copy.deepcopy(headercell if ri==0 else bodycell);cell.set('header','1' if ri==0 else '0')
                cell.set('borderFillIDRef',border_fill(cell_border(ri,ci,len(widths))))
                sub=cell.find('hp:subList',NS);sub.set('vertAlign','CENTER')
                for child in list(sub):sub.remove(child)
                for line in str(value).split('\n'):sub.append(ptext(line,'cellhead' if ri==0 else 'cell',cell=True,align='CENTER' if ri==0 else align[ci]))
                cell.find('hp:cellMargin',NS).attrib.update({k:'141' for k in ('left','right','top','bottom')})
                cell.find('hp:cellAddr',NS).attrib.update({'colAddr':str(ci),'rowAddr':str(ri)})
                cell.find('hp:cellSpan',NS).attrib.update({'colSpan':'1','rowSpan':'1'})
                cell.find('hp:cellSz',NS).attrib.update({'width':str(width),'height':str(height)})
                row.append(cell)
        t.find('hp:sz',NS).attrib.update({'width':str(fullwidth),'height':str(totalheight)})
        return p
    for pi,page in enumerate(data['pages']):
        for bi,block in enumerate(page):
            if block['kind']=='table':sec.append(table(block))
            else:sec.append(ptext(block['text'],block['kind'],pagebreak=pi>0 and bi==0))
    # Remove stale line-layout caches and any extra section, including manifest entries.
    for el in sec.findall('.//hp:linesegarray',NS):el.getparent().remove(el)
    for i,el in enumerate(sec.findall('.//hp:p',NS)):el.set('id',str(200000+i))
    head.set('secCnt','1')
    manifest=E.fromstring(parts['Contents/content.hpf'])
    for el in manifest.xpath('//*[starts-with(@id,"section") and @id!="section0"] | //*[starts-with(@idref,"section") and @idref!="section0"]'):el.getparent().remove(el)
    manifest.find('.//opf:title',NS).text=data['title'].replace('\n',' ')
    for el in manifest.findall('.//opf:meta',NS):
        if el.get('name') in ('description','subject'):el.text=data.get('subject') or data['title'].split('\n')[-1]
        if el.get('name') in ('date','ModifiedDate'):el.text=data.get('doc_date') or datetime.date.today().isoformat()
    for name,root in [('Contents/header.xml',head),('Contents/section0.xml',sec),('Contents/content.hpf',manifest)]:parts[name]=E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
    for name in [n for n in parts if re.fullmatch(r'Contents/section[1-9]\d*\.xml',n)]:parts.pop(name)
    parts.pop('Preview/PrvImage.png',None)
    texts=[(x.text or '')+''.join('\n'+(b.tail or '') for b in x.findall('hp:lineBreak',NS)) for x in sec.findall('.//hp:t',NS)]
    parts['Preview/PrvText.txt']='\n'.join(texts).encode('utf-8')
    # Standard namespace prefixes are preserved by lxml. Run mandatory namespace fixer too.
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype',parts.pop('mimetype'),compress_type=zipfile.ZIP_STORED)
        for name,value in parts.items():z.writestr(name,value)
    subprocess.run([sys.executable,str(SCRIPTS/'fix_namespaces.py'),str(target)],check=True,stdout=subprocess.DEVNULL)
    sys.path.insert(0,str(SCRIPTS))
    import gate
    required=data.get('required_sections') or ['근거','목적']+(['예산'] if data.get('budget') else [])
    fs,blocked=gate.run(target,required=required)
    report={'file':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'template':template.name,'template_sha256':hashlib.sha256(template.read_bytes()).hexdigest(),'checks':[f.__dict__ for f in fs],'blocked':bool(blocked),'visual_review':'pending','source_urls':data.get('source_urls',[])}
    target.with_suffix('.validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    target.with_suffix('.txt').write_text('\n'.join(texts))
    if blocked:raise ValueError('Output validation failed: '+str([f.detail for f in blocked]))
    return report

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('input',type=Path);ap.add_argument('-o','--output',type=Path,required=True);args=ap.parse_args()
    try:
        report=build(json.loads(args.input.read_text()),args.output,base=args.input.parent)
        print(json.dumps({'file':report['file'],'package_checks':'passed','visual_review':'pending'},ensure_ascii=False))
    except (ValueError,KeyError,FileNotFoundError) as e:
        print(f'Build failed: {e}',file=sys.stderr);return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
