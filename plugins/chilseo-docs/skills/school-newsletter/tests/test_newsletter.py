import copy,datetime,json,re,shutil,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from lxml import etree as E
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
import build_newsletter as b
EXAMPLE=json.loads((R/'examples/sample_museum_trip.json').read_text())
def body(path):
 with zipfile.ZipFile(path) as z:return z.read('Preview/PrvText.txt').decode()
class NewsletterTests(unittest.TestCase):
 def setUp(self):self.data=copy.deepcopy(EXAMPLE);self.tmp=tempfile.TemporaryDirectory();self.out=Path(self.tmp.name)/'통신문.hwpx'
 def tearDown(self):self.tmp.cleanup()
 def test_template_has_markers_only(self):
  with zipfile.ZipFile(b.DEFAULT_TEMPLATE) as z:
   names=z.namelist();sec=z.read('Contents/section0.xml').decode();meta=z.read('Contents/content.hpf').decode()
  text=''.join(E.fromstring(sec.encode()).itertext())
  for word in ('2026','055','미술관','이건희','5학년','gne.go.kr'):self.assertNotIn(word,text)
  for m in ('{{TITLE}}','{{GREETING}}','{{ITEM_LABEL}}','{{ITEM_TEXT}}','{{NOTE}}','{{PLEDGE}}','{{TEL1}}','{{HOMEPAGE}}'):self.assertIn(m,text)
  self.assertEqual([n for n in names if n.startswith('BinData/')],['BinData/image1.png'])
  self.assertNotIn('Preview/PrvImage.png',names);self.assertNotIn('USER',meta)
 def test_build_fills_every_marker(self):
  report=b.build(self.data,self.out)
  text=body(self.out)
  self.assertFalse(report['blocked']);self.assertNotIn('{{',text)
  self.assertIn('2026. 12. 9.(수) 09:00~15:00',text);self.assertIn('오후: 점심 식사, 전통 놀이 체험',text)
  self.assertIn('참가 동의서를 2026. 12. 2.(수)까지',text);self.assertIn('칠 서 초 등 학 교 장',text)
  self.assertIn('2026학년도',text);self.assertIn('참가 동의함',text);self.assertIn('※참가에 동의하지 않는 학생은',text)
 def test_one_row_per_item_and_full_width_tables(self):
  b.build(self.data,self.out)
  with zipfile.ZipFile(self.out) as z:sec=E.fromstring(z.read('Contents/section0.xml'))
  ns={'hp':'http://www.hancom.co.kr/hwpml/2011/paragraph'}
  pg=sec.find('.//hp:pagePr',ns);m=pg.find('hp:margin',ns);width=int(pg.get('width'))-int(m.get('left'))-int(m.get('right'))
  tables=[t for p in sec.findall('hp:p',ns) for t in p.findall('hp:run/hp:tbl',ns)]
  for t in tables:
   o=t.find('hp:outMargin',ns);self.assertEqual(int(t.find('hp:sz',ns).get('width'))+int(o.get('left'))+int(o.get('right')),width)
  items=next(t for t in tables if '구분' in ''.join(t.itertext()))
  self.assertEqual(int(items.get('rowCnt')),1+len(self.data['items']))
  self.assertEqual([tr.find('hp:tc/hp:cellAddr',ns).get('rowAddr') for tr in items.findall('hp:tr',ns)],[str(i) for i in range(1+len(self.data['items']))])
 def test_single_item_keeps_bottom_border(self):
  self.data['items']=self.data['items'][:1];b.build(self.data,self.out)
  with zipfile.ZipFile(self.out) as z:sec=E.fromstring(z.read('Contents/section0.xml'));head=E.fromstring(z.read('Contents/header.xml'))
  ns={**b.NS,'hh':'http://www.hancom.co.kr/hwpml/2011/head'}
  table=next(t for t in sec.iter('{%s}tbl'%ns['hp']) if '구분' in ''.join(t.itertext()))
  for cell in table.findall('hp:tr',ns)[-1].findall('hp:tc',ns):
   border=head.find(".//hh:borderFill[@id='%s']/hh:bottomBorder"%cell.get('borderFillIDRef'),ns)
   self.assertEqual(border.get('width'),'0.4 mm')
 def test_invalid_utf8_has_korean_help(self):
  source=Path(self.tmp.name)/'입력.json';source.write_bytes(b'\xff')
  result=subprocess.run([sys.executable,str(R/'scripts/build_newsletter.py'),str(source),'-o',str(self.out)],capture_output=True,text=True)
  self.assertNotEqual(result.returncode,0);self.assertIn('UTF-8 형식으로 저장해 주세요',result.stderr);self.assertNotIn('Traceback',result.stderr)
 def test_body_spacing_and_margin_below_table(self):
  b.build(self.data,self.out)
  with zipfile.ZipFile(self.out) as z:sec=E.fromstring(z.read('Contents/section0.xml'));head=E.fromstring(z.read('Contents/header.xml'))
  ns={'hp':'http://www.hancom.co.kr/hwpml/2011/paragraph','hh':'http://www.hancom.co.kr/hwpml/2011/head','hc':'http://www.hancom.co.kr/hwpml/2011/core'}
  top=list(sec);text=lambda p:''.join(p.itertext())
  greet=next(p for p in top if text(p).startswith('3학년'));note=next(p for p in top if text(p).strip().startswith('※ 멀미'))
  for p in (greet,note):
   pr=head.find(f".//hh:paraPr[@id='{p.get('paraPrIDRef')}']",ns)
   self.assertEqual({e.get('value') for e in pr.iter('{%s}lineSpacing'%ns['hh'])},{'160'})
  pr=head.find(f".//hh:paraPr[@id='{greet.get('paraPrIDRef')}']",ns)
  self.assertGreater(int(pr.find('.//hc:intent',ns).get('value')),0)
  i=top.index(note);self.assertIn('구분',text(top[i-1]))
  items=next(t for t in sec.iter('{%s}tbl'%ns['hp']) if '구분' in text(t))
  self.assertEqual(items.find('hp:outMargin',ns).get('bottom'),str(b.TABLE_GAP))
  del self.data['notes'];b.build(self.data,self.out)
  with zipfile.ZipFile(self.out) as z:top=list(E.fromstring(z.read('Contents/section0.xml')))
  i=next(n for n,p in enumerate(top) if '구분' in text(p));self.assertTrue(text(top[i+1]).startswith('20'))
 def test_privacy_question_is_raised(self):
  self.data['reply']['privacy']={'include':None}
  confirm=b.build(self.data,self.out)['needs_confirmation']
  self.assertTrue(any('개인정보' in c for c in confirm))
 def test_privacy_lines_when_included(self):
  self.data['reply']['privacy']={'include':True,'items':'학생 학반·이름, 보호자 이름·연락처','purpose':'체험학습 참가 확인과 비상 연락','retention':'체험학습 종료 후 즉시 파기','refusal':'체험학습에 참가하기 어려울 수 있습니다'}
  report=b.build(self.data,self.out);text=body(self.out)
  self.assertIn('수집 항목(학생 학반·이름, 보호자 이름·연락처)',text);self.assertIn('□ 동의함',text)
  self.assertFalse(any('개인정보' in c for c in report['needs_confirmation']))
  self.data['reply']['privacy']={'include':True}
  self.assertTrue(any('retention' in c for c in b.build(self.data,self.out)['needs_confirmation']))
 def test_whitespace_privacy_fields_need_confirmation(self):
  self.data['reply']['privacy']={'include':True,'items':' ','purpose':'\t','retention':'','refusal':'  '}
  report=b.build(self.data,self.out);text=body(self.out)
  for key in ('items','purpose','retention','refusal'):
   self.assertTrue(any(key in c for c in report['needs_confirmation']))
  self.assertIn('수집 항목([확인 필요])',text)
  self.assertIn('동의하지 않으면 [확인 필요]',text)
  page=Path(self.tmp.name)/'미리보기.html';b.preview(self.data,report['needs_confirmation'],page)
  self.assertIn('수집 항목([확인 필요])',page.read_text())
 def test_sections_sit_between_notes_and_date(self):
  self.data['sections']=[{'title':'< 가정에서 챙겨 주세요 >','lines':['1. 멀미약은 가정에서 먹여 보내 주십시오.']}]
  b.build(self.data,self.out);text=body(self.out)
  self.assertLess(text.index('※ 멀미를'),text.index('< 가정에서 챙겨 주세요 >'))
  self.assertLess(text.index('1. 멀미약은'),text.index('칠 서 초 등 학 교 장'))
 def test_extra_consents_and_fields_on_the_form(self):
  self.data['reply'].update(consents=['활동 사진을 학교 누리집에 싣는 것'],fields=['건강 특이 사항'])
  b.build(self.data,self.out);form=body(self.out).split('참가 동의서')[-1]
  self.assertIn('누리집에 싣는 것에 동의합니까?   □ 동의함   □ 동의하지 않음',form)
  self.assertIn('○ 건강 특이 사항: ___',form)
  self.assertLess(form.index('상기 내용을 확인하고'),form.index('○ 활동 사진'))
 def test_examples_fit_one_page_and_long_notice_warns(self):
  for name in ('sample_museum_trip','sample_arts_festival','sample_camp'):
   data=json.loads((R/f'examples/{name}.json').read_text())
   self.assertLess(b.page_height(data),b.PAGE_BODY,name)
   self.assertFalse(any('한 쪽' in c for c in b.validate(data)),name)
  self.data['items']+=[{'label':f'일정 {i}','text':'09:00 출발\n10:00 도착\n12:00 점심'} for i in range(6)]
  self.assertTrue(any('한 쪽을 넘을 것 같아요' in c for c in b.validate(self.data)))
 def test_simple_examples_ask_one_action(self):
  for name in ('sample_museum_trip','sample_camp'):
   reply=json.loads((R/f'examples/{name}.json').read_text())['reply']
   self.assertFalse(reply.get('consents') or reply.get('fields'),name)
 def test_no_reply_drops_form(self):
  del self.data['reply'];self.data['summary'].pop('reply_by')
  b.build(self.data,self.out);text=body(self.out)
  self.assertNotIn('동의',text.split('칠 서 초 등 학 교 장')[1]);self.assertNotIn('서명',text)
 def test_weekday_mismatch_rejected(self):
  self.data['items'][0]['text']='2026. 12. 9.(목) 09:00~15:00'
  with self.assertRaisesRegex(ValueError,'Weekday'):b.validate(self.data)
 def test_weekday_in_issue_date_rejected(self):
  self.data['issue_date']='2026. 12. 9.(목)'
  with self.assertRaisesRegex(ValueError,'Weekday'):b.validate(self.data)
 def test_reply_deadline_before_event(self):
  self.data['summary']['reply_by']='2026. 12. 10.(목)'
  with self.assertRaisesRegex(ValueError,'deadline'):b.validate(self.data)
 def test_iso_deadline_is_compared_and_unknown_dates_are_flagged(self):
  self.data['summary']['reply_by']='2026-12-10'
  with self.assertRaisesRegex(ValueError,'deadline'):b.validate(self.data)
  self.data['summary']['reply_by']='추후 안내'
  self.assertTrue(any('비교할 수 없어요' in c for c in b.validate(self.data)))
  self.data['summary']['reply_by']='2026-02-30'
  with self.assertRaisesRegex(ValueError,'실제 날짜'):b.validate(self.data)
 def test_greeting_equal_to_table_heading(self):
  self.data['greeting']=['구분']
  b.build(self.data,self.out)
  self.assertIn('구분',body(self.out))
 def test_reply_needs_deadline(self):
  self.data['summary'].pop('reply_by')
  with self.assertRaisesRegex(ValueError,'reply_by'):b.validate(self.data)
 def test_school_must_match_masthead(self):
  with self.assertRaisesRegex(ValueError,'School'):b.build(dict(self.data,school='다른초등학교'),self.out)
  with self.assertRaisesRegex(ValueError,'School'):b.build(dict(self.data,school='칠서초'),self.out)
 def test_preview_page(self):
  report=b.build(self.data,self.out);page=Path(self.tmp.name)/'p.html'
  b.preview(self.data,report['needs_confirmation'],page);html=page.read_text()
  self.assertIn('<title>박물관 체험학습 안내</title>',html);self.assertNotIn('__NOTICE_DATA__',html)
  data=json.loads(re.search(r'const N = (\{.*?\});\n',html,re.S).group(1))
  self.assertEqual(data['summary']['reply_by'],'2026. 12. 2.(수)');self.assertEqual(len(data['confirm']),2)
  self.assertEqual(data['reply']['privacy'],[])
  self.assertIn('white-space: pre-line',html)
 def test_invalid_inputs_report_korean_without_traceback(self):
  cases=[{'summary':'날짜'}, {'items':[{'label':'일시'}]}, {'sections':'잘못된 값'}, {'title':'안내\x01문'}, {'reply':{'privacy':{'include':'true'}}}]
  for change in cases:
   data=dict(self.data,**change); path=Path(self.tmp.name)/'입력 파일.json';path.write_text(json.dumps(data,ensure_ascii=False))
   result=subprocess.run([sys.executable,str(R/'scripts/build_newsletter.py'),str(path),'-o',str(self.out)],capture_output=True,text=True)
   self.assertNotEqual(result.returncode,0);self.assertIn('주세요',result.stderr);self.assertNotIn('Traceback',result.stderr)
 def test_short_dates_use_current_year_without_doc_date(self):
  self.data.pop('doc_date',None);today=datetime.date.today();date=datetime.date(today.year,12,9)
  wrong=b.DOW[(date.weekday()+1)%7];self.data['summary']['when']=f'12. 9.({wrong})'
  with self.assertRaisesRegex(ValueError,'Weekday'):b.validate(self.data)
 def test_preview_uses_document_date(self):
  self.data['doc_date']='2025-04-01';self.data['summary']['when']='[확인 필요]';self.data.pop('reply')
  page=Path(self.tmp.name)/'미리보기.html';b.preview(self.data,[],page)
  data=json.loads(re.search(r'const N = (\{.*?\});\n',page.read_text(),re.S).group(1))
  self.assertEqual(data['issue_date'],'2025년 4월    일')
 def test_example_has_no_personal_data(self):
  text=json.dumps(EXAMPLE,ensure_ascii=False)
  self.assertIsNone(re.search(r'\d{2,3}-\d{3,4}-\d{4}',text));self.assertNotRegex(text,r'\d+명')
 def test_blank_masthead_values_need_confirmation(self):
  self.data['masthead']={'phones':['', '  '], 'homepage':'  '}
  report=b.build(self.data,self.out)
  self.assertTrue(any('머리말' in c for c in report['needs_confirmation']))
  self.assertGreaterEqual(body(self.out).count('[확인 필요]'),3)
 def test_empty_reply_is_a_reply(self):
  self.data['reply']={}
  report=b.build(self.data,self.out)
  self.assertIn('참가 동의함',body(self.out))
  self.assertTrue(any('개인정보' in c for c in report['needs_confirmation']))
  page=Path(self.tmp.name)/'preview.html';b.preview(self.data,report['needs_confirmation'],page)
  data=json.loads(re.search(r'const N = (\{.*?\});\n',page.read_text(),re.S).group(1))
  self.assertIsInstance(data['reply'],dict)
  self.data['summary'].pop('reply_by')
  with self.assertRaisesRegex(ValueError,'reply_by'):b.validate(self.data)
 def test_colliding_paths_are_rejected_before_writing(self):
  source=Path(self.tmp.name)/'입력.json';source.write_text(json.dumps(self.data,ensure_ascii=False))
  for args in ([str(source),'-o',str(source)], [str(source),'-o',str(self.out),'--preview',str(self.out)],
               [str(source),'-o',str(self.out),'--preview',str(self.out.with_suffix('.txt'))]):
   before=source.read_bytes()
   result=subprocess.run([sys.executable,str(R/'scripts/build_newsletter.py'),*args],capture_output=True,text=True)
   self.assertNotEqual(result.returncode,0);self.assertIn('서로 다른 경로',result.stderr)
   self.assertNotIn('Traceback',result.stderr);self.assertEqual(source.read_bytes(),before)
   self.assertFalse(self.out.exists())
 def test_template_cannot_be_overwritten_by_output(self):
  template=Path(self.tmp.name)/'양식.hwpx';shutil.copy(b.DEFAULT_TEMPLATE,template)
  self.data['template']=str(template)
  source=Path(self.tmp.name)/'입력.json';source.write_text(json.dumps(self.data,ensure_ascii=False))
  before=template.read_bytes()
  for args in (['-o',str(template)], ['-o',str(self.out),'--preview',str(template)]):
   result=subprocess.run([sys.executable,str(R/'scripts/build_newsletter.py'),str(source),*args],capture_output=True,text=True)
   self.assertNotEqual(result.returncode,0);self.assertIn('서로 다른 경로',result.stderr)
   self.assertEqual(template.read_bytes(),before);self.assertFalse(self.out.exists())
 def test_blank_reply_deadline_is_rejected(self):
  self.data['summary']['reply_by']='  '
  with self.assertRaisesRegex(ValueError,'reply_by'):b.validate(self.data)
 def test_long_item_grows_and_long_titles_are_rejected(self):
  self.data['items'][0]['text']='가'*150
  b.build(self.data,self.out)
  with zipfile.ZipFile(self.out) as z:sec=E.fromstring(z.read('Contents/section0.xml'))
  table=next(t for t in sec.iter('{%s}tbl'%b.NS['hp']) if '구분' in ''.join(t.itertext()))
  row=table.findall('hp:tr',b.NS)[1]
  self.assertEqual(int(row.find('hp:tc/hp:cellSz',b.NS).get('height')),2565+3*b.LINE_EXTRA)
  for change in ({'title':'가'*61}, {'items':[{'label':'가'*21,'text':'내용'}]}, {'reply':{'title':'가'*61}}):
   with self.assertRaisesRegex(ValueError,'줄여 주세요'):b.validate(dict(self.data,**change))
 def test_long_pledge_counts_toward_page_warning(self):
  before=b.page_height(self.data);self.data['reply']['pledge']='가'*1000
  self.assertGreater(b.page_height(self.data),before)
  self.assertTrue(any('한 쪽을 넘을 것 같아요' in c for c in b.validate(self.data)))
if __name__=='__main__':unittest.main()
