import copy,json,re,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
import build_gongmun as g
EXAMPLE=json.loads((R/'examples/sample_science_club.json').read_text())
def by_id(results):return {r['id']:r for r in results}
class GongmunTests(unittest.TestCase):
 def setUp(self):self.data=copy.deepcopy(EXAMPLE)
 def item(self,*path):
  node={'children':self.data['items']}
  for i in path:node=node['children'][i]
  return node
 def test_sample_passes_with_known_warnings(self):
  r=by_id(g.check(self.data))
  self.assertEqual(g.overall(g.check(self.data)),'warn')
  for k in ('V1','C1','C2','C3','C4','V3-1'):self.assertEqual(r[k]['status'],'ok',k)
  for k in ('V2-1','V2-5','C5'):self.assertEqual(r[k]['status'],'warn',k)
 def test_numbering_and_end_mark(self):
  body=g.lines(self.data)
  self.assertEqual(body[0],(0,'1. 관련'))
  self.assertEqual(body[1][1],'가. 한빛초등학교-1234(2026. 3. 2., "2026. 과학 탐구 동아리 운영 계획")')
  self.assertTrue(body[3][1].startswith('2. 2026. 과학'))
  self.assertIn((2,'1) 실험 재료비: 156,000원'),body);self.assertIn((3,'가) 리트머스 종이: 3,000원*12모둠=36,000원'),body)
  self.assertEqual(body[-2][1],'붙임  1. 견적서 1부.');self.assertEqual(body[-1][1],'      2. 지출(지급)품의서 1부.  끝.')
 def test_single_related_and_no_attachment(self):
  self.data['related']=self.data['related'][:1];self.data['attachments']=[]
  body=g.lines(self.data)
  self.assertTrue(body[0][1].startswith('1. 관련: 한빛초등학교-1234('))
  self.assertTrue(body[-1][1].endswith('교육운영비  끝.'))
 def test_copy_text_keeps_number_and_text_on_one_line(self):
  text=g.plain_body(g.lines(self.data))
  self.assertIn('\n  가. 용도: 과학',text);self.assertIn('\n      가) 리트머스',text);self.assertIn('\n\n붙임  1. 견적서',text)
 def test_wrong_multiplication(self):
  self.item(4,0,0)['text']='리트머스 종이: 3,000원*12모둠=35,000원'
  self.assertEqual(by_id(g.check(self.data))['C1']['status'],'fail')
 def test_wrong_subtotal(self):
  self.item(4,0)['text']='실험 재료비: 150,000원'
  self.assertEqual(by_id(g.check(self.data))['C2']['status'],'fail')
 def test_total_must_match_breakdown(self):
  self.item(3)['text']='소요예산: 금250,000원(금이십오만원)'
  self.assertEqual(by_id(g.check(self.data))['C2']['status'],'fail')
 def test_korean_amount(self):
  self.assertEqual(g.korean_amount(368000),'삼십육만팔천');self.assertEqual(g.korean_amount(1150000),'백십오만')
  self.assertEqual(g.normalize_korean('일백십오만'),g.normalize_korean('백십오만'))
  self.item(3)['text']='소요예산: 금246,000원(금이십사만오천원)'
  self.assertEqual(by_id(g.check(self.data))['C3']['status'],'fail')
  self.item(3)['text']='소요예산: 금246,000원'
  self.assertEqual(by_id(g.check(self.data))['C3']['status'],'fail')
 def test_weekday_including_short_date_after_full_date(self):
  self.assertEqual(g.weekday_errors('2026. 11. 2.(월)~11. 5.(목)'),[])
  self.assertEqual(len(g.weekday_errors('2026. 11. 2.(월)~11. 5.(금)')),1)
  self.item(1)['text']='운영 기간: 2026. 11. 16.(화) ~ 11. 27.(금)'
  self.assertEqual(by_id(g.check(self.data))['C4']['status'],'fail')
 def test_ledger_over_allocation(self):
  self.data['ledger'][1]['allocated']=80000
  self.assertEqual(by_id(g.check(self.data))['V3-1']['status'],'fail')
 def test_related_needs_source_and_shape(self):
  self.data['related']=[dict(self.data['related'][0],source=None)]
  self.assertEqual(by_id(g.check(self.data))['V2-1']['status'],'warn')
  self.data['related'][0]['doc_no']='1234'
  self.assertEqual(by_id(g.check(self.data))['V2-1']['status'],'fail')
 def test_already_numbered_item_rejected(self):
  self.item(0)['text']='가. 용도: 재료 구입'
  self.assertEqual(by_id(g.check(self.data))['V1']['status'],'fail')
 def test_page_has_data_and_no_placeholder(self):
  page=g.render(self.data,g.check(self.data))
  self.assertNotIn('__DRAFT_DATA__',page);self.assertNotIn('__PAGE_TITLE__',page)
  self.assertIn('<title>과학 동아리 재료비 품의</title>',page)
  data=json.loads(re.search(r'const D = (\{.*?\});\n',page,re.S).group(1))
  self.assertEqual(data['status'],'warn');self.assertEqual(data['lines'][-1]['depth'],-1)
 def test_example_has_no_real_people(self):
  text=json.dumps(EXAMPLE,ensure_ascii=False)
  for a in EXAMPLE['approval']+EXAMPLE['cooperation']:self.assertNotIn('name',a)
  self.assertIsNone(re.search(r'\d{2,3}-\d{3,4}-\d{4}',text))
if __name__=='__main__':unittest.main()
