import copy,json,re,sys,unittest,subprocess,tempfile
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
 def test_unknown_related_date_is_rendered_and_warned(self):
  self.data['related'][0]['date']='[확인 필요]'
  self.assertIn('[확인 필요]',g.lines(self.data)[1][1])
  self.assertEqual(by_id(g.check(self.data))['V2-1']['status'],'warn')
 def test_short_date_without_year_warns(self):
  self.data.pop('written');self.data['items']=[{'text':'일시: 11. 5.(금)'}]
  self.assertEqual(by_id(g.check(self.data))['C4']['status'],'warn')
 def test_korean_amount_keeps_one_before_large_units(self):
  self.data['items']=[{'text':'소요예산: 금1,100,000,000원(금십억원)'}]
  self.assertEqual(by_id(g.check(self.data))['C3']['status'],'fail')
  self.assertEqual(g.korean_amount(0),'영')
  self.assertNotEqual(g.normalize_korean('십일억'),g.normalize_korean('십억'))
 def test_ledger_matched_item_without_amount(self):
  self.data['items']=[{'text':'실험 재료비: 확인 필요'}]
  self.assertEqual(by_id(g.check(self.data))['V3-1']['status'],'fail')
 def test_bad_inputs_report_korean_without_traceback(self):
  cases=[{'items':[{}]}, {'items':'잘못된 항목'}, {'ledger':[{'name':'항목','allocated':5}]}, {'related':[{'date':'2026-99-99'}]}, {'items':[{'text':'항목'}]*15}, {'school':[]}, {'todo':[1]}]
  with tempfile.TemporaryDirectory(prefix='기안 문서 ') as temp:
   path=Path(temp)/'입력 파일.json'
   for case in cases:
    data=copy.deepcopy(EXAMPLE);data.update(case);path.write_text(json.dumps(data,ensure_ascii=False))
    run=subprocess.run([sys.executable,str(R/'scripts/build_gongmun.py'),str(path),'--check'],capture_output=True,text=True)
    self.assertEqual(run.returncode,2,case);self.assertIn('주세요',run.stderr,case);self.assertNotIn('Traceback',run.stderr)
 def test_missing_breakdown_amount_is_not_reported_as_zero(self):
  self.data['items']=[{'text':'소요예산: 금100원(금백원)'},{'text':'산출내역','children':[{'text':'재료비: 확인 필요'}]}]
  result=by_id(g.check(self.data))['C2']
  self.assertEqual(result['status'],'fail');self.assertIn('빠진 금액',result['detail'])
 def test_missing_file_has_no_traceback(self):
  run=subprocess.run([sys.executable,str(R/'scripts/build_gongmun.py'),'/tmp/없는-기안.json'],capture_output=True,text=True)
  self.assertEqual(run.returncode,2);self.assertNotIn('Traceback',run.stderr)
 def test_subtotal_with_missing_child_amount_fails(self):
  self.data['items']=[{'text':'재료비: 100원','children':[{'text':'재료: 100원'},{'text':'추가: 확인 필요'}]}]
  result=by_id(g.check(self.data))['C2']
  self.assertEqual(result['status'],'fail');self.assertIn('빠진 금액',result['detail'])
 def test_ledger_amounts_stay_exact_in_browser(self):
  self.data['ledger']=[{'name':'예산','allocated':2**53,'spend':[]}]
  with self.assertRaisesRegex(ValueError,'ledger.allocated'):g.check(self.data)
  self.data['ledger']=[{'name':'예산','allocated':2**53-1,'spend':[{'name':'첫째','amount':2**53-1},{'name':'둘째','amount':1}]}]
  with self.assertRaisesRegex(ValueError,'전체 집행 합계'):g.check(self.data)
 def test_malformed_amount_reports_what_to_fix(self):
  self.data['items']=[{'text':'재료: ,,원*2개=2원'}]
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'입력.json';path.write_text(json.dumps(self.data,ensure_ascii=False))
   run=subprocess.run([sys.executable,str(R/'scripts/build_gongmun.py'),str(path),'--check'],capture_output=True,text=True)
   self.assertEqual(run.returncode,2);self.assertIn('숫자 또는 쉼표',run.stderr);self.assertNotIn('Traceback',run.stderr)
 def test_dates_require_documented_format(self):
  for key in ('written','related'):
   data=copy.deepcopy(EXAMPLE)
   if key=='written':data[key]='20261104'
   else:data[key][0]['date']='20260302'
   with self.assertRaisesRegex(ValueError,'연도-월-일'):g.check(data)
 def test_year_zero_is_an_invalid_date(self):
  self.data['lead']='일시: 0000. 11. 5.(목)'
  result=by_id(g.check(self.data))['C4']
  self.assertEqual(result['status'],'fail');self.assertIn('없는 날짜',result['detail'])
 def test_links_require_web_addresses(self):
  for url in ('javascript:alert(1)','https://','https://:80','https://example.invalid:99999','https://example.invalid/공백 주소'):
   self.data['links']=[{'label':'자료','url':url}]
   with self.assertRaisesRegex(ValueError,'links.url'):g.check(self.data)
  self.data['links']=[{'label':'자료','url':'https://example.invalid/자료'}]
  g.check(self.data)
 def test_short_date_at_start_is_not_a_duplicate_number(self):
  self.data['items']=[{'text':'11. 27.(금) 행사'}]
  self.assertEqual(by_id(g.check(self.data))['V1']['status'],'ok')
  self.data['items']=[{'text':'11. 행사'}]
  self.assertEqual(by_id(g.check(self.data))['V1']['status'],'fail')
 def test_decimal_formula_does_not_pass_as_integer_formula(self):
  for text in ('재료: 1.5원*2개=10원', '재료: 5원*1.5개=25원', '재료: 5원*2개=10.0원'):
   self.data['items']=[{'text':text}]
   with self.subTest(text=text), self.assertRaisesRegex(ValueError,'산출식'):
    g.check(self.data)
 def test_whitespace_receiver_is_missing(self):
  self.data['receiver']='   '
  self.assertEqual(by_id(g.check(self.data))['V1']['status'],'fail')
 def test_unknown_related_source_is_not_confirmed(self):
  self.data['related']=[dict(self.data['related'][0],source='[확인 필요]')]
  self.assertEqual(by_id(g.check(self.data))['V2-1']['status'],'warn')
 def test_extremely_long_amount_has_korean_error(self):
  self.data['items']=[{'text':'재료: '+ '9'*5000 +'원*2개=2원'}]
  with self.assertRaisesRegex(ValueError,'금액'):
   g.check(self.data)
if __name__=='__main__':unittest.main()
