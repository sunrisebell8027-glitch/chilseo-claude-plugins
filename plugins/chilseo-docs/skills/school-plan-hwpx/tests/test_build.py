import copy,json,sys,tempfile,unittest,zipfile
from pathlib import Path
from lxml import etree as E
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
import build,gate
EXAMPLE=R/'examples/sample_reading_week.json'
class BuildTests(unittest.TestCase):
 def setUp(self):self.data=json.loads(EXAMPLE.read_text())
 def test_budget_bad_math_rejected(self):
  self.data['budget']['total']=400000
  with self.assertRaisesRegex(ValueError,'calculation'):build.validate(self.data)
 def test_budget_bad_formula_rejected(self):
  self.data['budget']['items'][1]['formula']='2,000원 × 61명'
  with self.assertRaisesRegex(ValueError,'calculation'):build.validate(self.data)
 def test_budget_stale_display_rejected(self):
  self.data['pages'][1][1]['rows'][2][2]='100,000'
  with self.assertRaisesRegex(ValueError,'displayed'):build.validate(self.data)
 def test_older_budget_form_accepted(self):
  self.data['budget']={'unit_price':2000,'headcount':60,'total':120000}
  self.data['pages'][1][1]['rows'][3][2]='120,000'
  build.validate(self.data)
 def test_budget_and_slots_are_optional(self):
  for key in ('budget','slots','event_date','school','source_urls'):self.data.pop(key)
  build.validate(self.data)
 def test_school_must_match_template(self):
  with self.assertRaisesRegex(ValueError,'School'):build.validate(dict(self.data,school='다른초등학교'),'칠서초등학교')
 def test_duplicate_class_rejected(self):
  self.data['slots'][1]['classes'].append('1-1')
  with self.assertRaisesRegex(ValueError,'Duplicate'):build.validate(self.data)
 def test_timetable_stale_display_rejected(self):
  self.data['slots'][0]['classes'][0]='1-2'
  with self.assertRaisesRegex(ValueError,'Timetable'):build.validate(self.data)
 def test_table_shape_rejected(self):
  self.data['pages'][0][11]['rows'][1].pop()
  with self.assertRaisesRegex(ValueError,'Nonrectangular'):build.validate(self.data)
 def test_invalid_column_alignment_rejected(self):
  self.data['pages'][0][11]['align']=['center','middle','justify','justify']
  with self.assertRaisesRegex(ValueError,'alignment'):build.validate(self.data)
  self.data['pages'][0][11]['align']=['center','center']
  with self.assertRaisesRegex(ValueError,'alignment'):build.validate(self.data)
 def test_missing_template_reported(self):
  with self.assertRaises(FileNotFoundError):build.resolve_template('없는양식.hwpx',R)
 def test_template_has_no_earlier_plan(self):
  with zipfile.ZipFile(build.DEFAULT_TEMPLATE) as z:
   names=z.namelist();text=z.read('Preview/PrvText.txt').decode();sec=z.read('Contents/section0.xml').decode()
   meta=z.read('Contents/content.hpf').decode()
  body=''.join(E.fromstring(sec.encode()).itertext())
  self.assertEqual([n for n in names if n.startswith('Contents/section')],['Contents/section0.xml'])
  self.assertNotIn('Preview/PrvImage.png',names)
  self.assertIn('칠서초등학교',text)
  for word in ('두드림','google','http','000','학생','강사'):self.assertNotIn(word,body)
  self.assertNotIn('fieldBegin',sec)  # formula fields keep earlier values
  self.assertEqual(body.count('칠서초등학교'),2)  # masthead school name and emblem caption
  self.assertNotIn('lastsaveby" content="text">',meta)
 def test_build_preserves_school_and_writes_content(self):
  self.data['pages'][-1].append({'kind':'note','text':'검사: A & B < C'})
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'검증.hwpx';result=build.build(self.data,out)
   self.assertFalse(result['blocked'])
   self.assertTrue(out.with_suffix('.validation.json').exists())
   with zipfile.ZipFile(out) as z:
    text=z.read('Preview/PrvText.txt').decode();root=E.fromstring(z.read('Contents/section0.xml'))
    self.assertIn('칠서초등학교',text);self.assertIn('420,000',text);self.assertIn('검사: A & B < C',text)
    self.assertNotIn('제목',text.split('\n')[:20])
    self.assertEqual(len(root.findall('.//hp:pic',build.NS)),1)
    for t in root.findall('.//hp:tbl',build.NS):
     self.assertEqual(len(t.findall('hp:tr',build.NS)),int(t.get('rowCnt')))
 def test_cell_border_by_position(self):
  head=build.cell_border(0,1,4);first=build.cell_border(1,0,4);mid=build.cell_border(2,1,4);last=build.cell_border(3,3,4)
  self.assertEqual(head,(('SOLID','0.15 mm'),('SOLID','0.15 mm'),('SOLID','0.1 mm'),('DOUBLE_SLIM','0.5 mm'),'#DFE6F7'))
  self.assertEqual(first[:4],(('SOLID','0.15 mm'),('SOLID','0.12 mm'),('DOUBLE_SLIM','0.5 mm'),('SOLID','0.12 mm')))
  self.assertEqual(mid[:4],(('SOLID','0.12 mm'),)*4);self.assertIsNone(mid[4])
  self.assertEqual(last[:3],(('SOLID','0.12 mm'),('SOLID','0.15 mm'),('SOLID','0.12 mm')))
 def test_table_style_in_output(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'표양식.hwpx';self.assertFalse(build.build(self.data,out)['blocked'])
   with zipfile.ZipFile(out) as z:head=E.fromstring(z.read('Contents/header.xml'));root=E.fromstring(z.read('Contents/section0.xml'))
  ns=dict(build.NS,hc='http://www.hancom.co.kr/hwpml/2011/core')
  fills={b.get('id'):b for b in head.find('.//hh:borderFills',ns)}
  self.assertEqual(int(head.find('.//hh:borderFills',ns).get('itemCnt')),len(fills))
  aligns={p.get('id'):p.find('hh:align',ns).get('horizontal') for p in head.find('.//hh:paraProperties',ns)}
  side=lambda tc,k:(lambda b:(b.get('type'),b.get('width'),b.get('color')))(fills[tc.get('borderFillIDRef')].find('hh:'+k,ns))
  tables=root.findall('.//hp:tbl',ns)[1:]
  self.assertEqual(len(tables),2)
  for t in tables:
   rows=[r.findall('hp:tc',ns) for r in t.findall('hp:tr',ns)];n=len(rows[0])
   for tc in rows[0]:
    self.assertEqual(fills[tc.get('borderFillIDRef')].find('.//hc:winBrush',ns).get('faceColor'),'#DFE6F7')
    self.assertEqual(side(tc,'bottomBorder'),('DOUBLE_SLIM','0.5 mm','#6182D6'))
   for ri,row in enumerate(rows[1:],1):
    for ci,tc in enumerate(row):
     self.assertEqual(side(tc,'topBorder')[:2],('DOUBLE_SLIM','0.5 mm') if ri==1 else ('SOLID','0.12 mm'))
     self.assertEqual(side(tc,'leftBorder')[1],'0.15 mm' if ci==0 else '0.12 mm')
     self.assertEqual(side(tc,'rightBorder')[1],'0.15 mm' if ci==n-1 else '0.12 mm')
     self.assertIsNone(fills[tc.get('borderFillIDRef')].find('.//hc:winBrush',ns))
  schedule=next(t for t in tables if t.find('.//hp:t',ns).text=='시간')
  body=schedule.findall('hp:tr',ns)[1].findall('hp:tc',ns)
  self.assertEqual([aligns[tc.find('.//hp:p',ns).get('paraPrIDRef')] for tc in body],['CENTER','CENTER','JUSTIFY','JUSTIFY'])
 def test_bad_weekday_blocked(self):
  result=gate.check_weekday(['2026. 12. 15.(월)'],[])
  self.assertFalse(result.ok);self.assertTrue(result.blocking)
 def test_output_budget_mismatch_blocked(self):
  tab={'rows':3,'cols':2,'cells':[{'row':0,'col':0,'text':'내용'},{'row':0,'col':1,'text':'금액'}, {'row':1,'col':0,'text':'체험비'},{'row':1,'col':1,'text':'530,000'}, {'row':2,'col':0,'text':'합계'},{'row':2,'col':1,'text':'500,000'}]}
  self.assertFalse(gate.check_budget([tab]).ok)
if __name__=='__main__':unittest.main()
