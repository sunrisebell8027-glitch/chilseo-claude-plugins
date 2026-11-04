import copy,json,re,sys,tempfile,unittest,zipfile
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
  for word in ('2026','055','협력','창원','5학년','gne.go.kr'):self.assertNotIn(word,text)
  for m in ('{{TITLE}}','{{GREETING}}','{{ITEM}}','{{NOTE}}','{{PLEDGE}}','{{CONTACT}}'):self.assertIn(m,text)
  self.assertEqual([n for n in names if n.startswith('BinData/')],['BinData/image2.png'])
  self.assertNotIn('Preview/PrvImage.png',names);self.assertNotIn('USER',meta)
 def test_build_fills_every_marker(self):
  report=b.build(self.data,self.out)
  text=body(self.out)
  self.assertFalse(report['blocked']);self.assertNotIn('{{',text)
  self.assertIn('1. 일시 : 2026. 12. 9.(수) 09:00~15:00',text);self.assertIn('6. 비용 : 없음',text)
  self.assertIn('※ 참가 동의서는 2026. 12. 2.(수)',text);self.assertIn('칠 서 초 등 학 교 장',text)
  self.assertIn('칠서초 2026학년도',text);self.assertIn('칠서초등학교장 귀하',text)
 def test_privacy_question_is_raised(self):
  confirm=b.build(self.data,self.out)['needs_confirmation']
  self.assertTrue(any('개인정보' in c for c in confirm))
 def test_privacy_lines_when_included(self):
  self.data['reply']['privacy']={'include':True,'items':'학생 학반·이름, 보호자 이름·연락처','purpose':'체험학습 참가 확인과 비상 연락','retention':'체험학습 종료 후 즉시 파기','refusal':'체험학습에 참가하기 어려울 수 있습니다'}
  report=b.build(self.data,self.out);text=body(self.out)
  self.assertIn('수집 항목(학생 학반·이름, 보호자 이름·연락처)',text);self.assertIn('□ 동의함',text)
  self.assertFalse(any('개인정보' in c for c in report['needs_confirmation']))
  self.data['reply']['privacy']={'include':True}
  self.assertTrue(any('retention' in c for c in b.build(self.data,self.out)['needs_confirmation']))
 def test_no_reply_drops_form(self):
  del self.data['reply'];self.data['summary'].pop('reply_by')
  b.build(self.data,self.out);text=body(self.out)
  self.assertNotIn('동의서',text.split('칠 서 초 등 학 교 장')[1]);self.assertNotIn('보호자 성명',text)
 def test_weekday_mismatch_rejected(self):
  self.data['items'][0]['text']='2026. 12. 9.(목) 09:00~15:00'
  with self.assertRaisesRegex(ValueError,'Weekday'):b.validate(self.data)
 def test_reply_deadline_before_event(self):
  self.data['summary']['reply_by']='2026. 12. 10.(목)'
  with self.assertRaisesRegex(ValueError,'deadline'):b.validate(self.data)
 def test_reply_needs_deadline(self):
  self.data['summary'].pop('reply_by')
  with self.assertRaisesRegex(ValueError,'reply_by'):b.validate(self.data)
 def test_school_must_match_masthead(self):
  with self.assertRaisesRegex(ValueError,'School'):b.build(dict(self.data,school='다른초등학교'),self.out)
 def test_preview_page(self):
  report=b.build(self.data,self.out);page=Path(self.tmp.name)/'p.html'
  b.preview(self.data,report['needs_confirmation'],page);html=page.read_text()
  self.assertIn('<title>박물관 체험학습 안내</title>',html);self.assertNotIn('__NOTICE_DATA__',html)
  data=json.loads(re.search(r'const N = (\{.*?\});\n',html,re.S).group(1))
  self.assertEqual(data['summary']['reply_by'],'2026. 12. 2.(수)');self.assertEqual(len(data['confirm']),2)
 def test_example_has_no_personal_data(self):
  text=json.dumps(EXAMPLE,ensure_ascii=False)
  self.assertIsNone(re.search(r'\d{2,3}-\d{3,4}-\d{4}',text));self.assertNotRegex(text,r'\d+명')
if __name__=='__main__':unittest.main()
