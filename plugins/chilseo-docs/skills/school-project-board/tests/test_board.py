import copy, json, shutil, subprocess, sys, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(SKILL / 'scripts'))
import build_board as bb
import guide

SAMPLE = json.loads((SKILL / 'examples' / 'sample_science_club_board.json').read_text(encoding='utf-8'))
FRESH = json.loads((SKILL / 'examples' / 'sample_first_start_board.json').read_text(encoding='utf-8'))
UNANSWERED = json.loads((SKILL / 'examples' / 'sample_unanswered_start_board.json').read_text(encoding='utf-8'))


def status(results, id_):
    return next(r['status'] for r in results if r['id'] == id_)


class BoardTest(unittest.TestCase):
    def test_gongmun_copy_matches_gongmun_skill(self):
        mine = (SKILL / 'scripts' / 'build_gongmun.py').read_bytes()
        theirs = SKILL.parent / 'school-gongmun-draft' / 'scripts' / 'build_gongmun.py'
        if theirs.exists(): self.assertEqual(mine, theirs.read_bytes())

    def test_sample_builds(self):
        results = bb.check(SAMPLE)
        self.assertFalse([r for r in results if r['status'] == 'fail'])
        page = bb.page_data(SAMPLE, results)
        buy2 = next(d for d in page['docs'] if d['id'] == 'buy2')
        self.assertEqual(buy2['amount'], 246000)
        self.assertTrue(buy2['draft']['copy_body'].startswith('1. 관련'))
        self.assertIn('한빛초등학교-1234', buy2['draft']['copy_body'])

    def test_sample_guide_and_flow_heads_name_different_counts(self):
        html = bb.render(SAMPLE, bb.check(SAMPLE))
        script = html.split('<script>', 1)[1].split('</script>', 1)[0]
        guide_head = "필요한 문서 ${needN}개 가운데"
        flow_head = "결재 문서 ${live.length}개 가운데 ${doneN}개를 마쳤어요."
        self.assertIn(guide_head, script)
        self.assertIn(flow_head, script)
        self.assertNotIn('필요한 문서', flow_head)

    def test_first_start_builds_without_docs_or_ledger(self):
        results = bb.check(FRESH)
        self.assertFalse([r for r in results if r['status'] == 'fail'])
        self.assertEqual(status(results, '길잡이'), 'warn')
        self.assertTrue(bb.say_steps(FRESH)[0].startswith('지금 할 일:'))
        page = bb.page_data(FRESH, results)
        self.assertEqual(page['docs'], [])
        self.assertEqual(page['ledger'], [])
        html = bb.render(FRESH, results)
        self.assertIn('예산 장부를 넣으면 남은 돈을 보여 드려요.', html)
        self.assertIn('예산과목과 편성액을 넣으면 장부를 보여 드려요.', html)
        self.assertIn("$('money').querySelector('.stat').hidden = true", html)
        self.assertIn('[hidden] { display: none !important; }', html)
        self.assertIn("if (!B.ledger.length) {", html)
        self.assertIn("$('budget').querySelector('.panel-head').hidden = !B.budget_code", html)

    def test_unanswered_start_example_builds(self):
        results = bb.check(UNANSWERED)
        self.assertFalse([r for r in results if r['status'] == 'fail'])
        self.assertEqual(status(results, '길잡이'), 'warn')
        self.assertEqual(bb.page_data(UNANSWERED, results)['docs'], [])
        self.assertTrue(bb.say_steps(UNANSWERED)[0].startswith('지금 할 일:'))

    def test_board_without_guide_builds_and_explains_how_to_get_steps(self):
        data = {'school': '한빛초등학교', 'project': '2026. 시작 보드', 'updated': '2026-03-02'}
        self.assertFalse([r for r in bb.check(data) if r['status'] == 'fail'])
        self.assertEqual(bb.say_steps(data), ['차례: 길잡이 답이 없어서 정하지 못했어요. guide에 답을 넣으면 지금 할 일을 알려 드려요.'])
        self.assertEqual(bb.page_data(data, bb.check(data))['docs'], [])

    def test_invalid_status_phase_and_empty_project_have_korean_errors(self):
        for change, phrase in [
            (lambda d: d['docs'][0].update(status='finished'), 'status'),
            (lambda d: d['docs'][0].update(phase='later'), 'phase'),
            (lambda d: d['docs'][0].update(need='plan-ish'), 'need'),
            (lambda d: d['docs'][0].update(need=[]), 'need'),
            (lambda d: d.update(project=' '), 'project'),
        ]:
            data = copy.deepcopy(SAMPLE); change(data)
            with self.subTest(phrase=phrase), self.assertRaisesRegex(ValueError, phrase): bb.check(data)

    def test_cli_reports_bad_json_without_traceback(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.json'; path.write_text('{', encoding='utf-8')
            run = subprocess.run([sys.executable, str(SKILL / 'scripts' / 'build_board.py'), str(path)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertIn('검사하지 못했어요', run.stderr)
        self.assertNotIn('Traceback', run.stderr)

    def test_completed_project_says_there_is_no_next_task(self):
        data = copy.deepcopy(SAMPLE)
        for doc in data['docs']:
            doc['status'] = 'done'
            doc['doc_no'] = doc.get('doc_no') or '한빛초등학교-9999'
        self.assertEqual(bb.say_steps(data), ['지금 할 일: 필요한 문서를 모두 마쳤어요.', '다음 할 일: 없어요.'])
        results = bb.check(data)
        self.assertFalse([r for r in results if r['status'] == 'fail'])

    def test_draft_amount_must_match_ledger(self):
        data = copy.deepcopy(SAMPLE)
        data['ledger'][0]['spend'][0]['amount'] = 150000
        results = bb.check(data)
        self.assertEqual(status(results, '합계'), 'fail')
        self.assertEqual(status(results, '기안문'), 'fail')

    def test_draft_formula_error_fails_board(self):
        data = copy.deepcopy(SAMPLE)
        buy2 = next(d for d in data['docs'] if d['id'] == 'buy2')
        buy2['draft']['items'][4]['children'][0]['children'][1]['text'] = '비커 세트: 10,000원*12모둠=130,000원'
        self.assertEqual(status(bb.check(data), '기안문'), 'fail')

    def test_unknown_related_doc_is_reported(self):
        data = copy.deepcopy(SAMPLE)
        next(d for d in data['docs'] if d['id'] == 'buy2')['draft']['related'] = ['nope']
        with self.assertRaises(ValueError): bb.check(data)

    def test_guide_sample_has_every_needed_doc(self):
        self.assertEqual(status(bb.check(SAMPLE), '길잡이'), 'ok')
        st = {i['id']: guide.judge(i, SAMPLE['guide'])[0] for i in guide.ITEMS}
        self.assertEqual(st['newmoney'], 'skip')
        self.assertEqual(st['safety'], 'need')

    def test_guide_warns_when_needed_doc_is_missing(self):
        data = copy.deepcopy(SAMPLE)
        data['docs'] = [d for d in data['docs'] if d.get('need') != 'safety']
        row = next(r for r in bb.check(data) if r['id'] == '길잡이')
        self.assertEqual(row['status'], 'warn')
        self.assertIn('안전계획', row['detail'])

    def test_empty_ledger_warns_and_does_not_invent_remaining_money(self):
        data = copy.deepcopy(FRESH)
        checks = bb.check(data)
        row = next(r for r in checks if r['id'] == '편성액')
        self.assertEqual(row['status'], 'warn')
        self.assertIn('예산과목과 편성액', row['detail'])
        self.assertNotIn('0원', row['detail'])
        html = (SKILL / 'assets' / 'board.html').read_text(encoding='utf-8')
        self.assertIn('예산 장부를 넣으면 남은 돈을 보여 드려요.', html)
        self.assertIn("$('money').querySelector('.stat').hidden = true", html)
        self.assertIn('예산과목과 편성액을 넣으면 장부를 보여 드려요.', html)
        no_guide = {'school': '한빛초등학교', 'project': '시작', 'updated': '2026-03-02'}
        self.assertIn('장부가 아직 없어요', next(r for r in bb.check(no_guide) if r['id'] == '편성액')['detail'])

    def test_unknown_need_and_bad_nested_fields_are_korean_errors(self):
        data = copy.deepcopy(SAMPLE)
        next(d for d in data['docs'] if d['id'] == 'plan')['need'] = 'unknown'
        with self.assertRaisesRegex(ValueError, 'need'):
            bb.check(data)
        data = copy.deepcopy(SAMPLE)
        data['ledger'][0]['spend'] = [None]
        with self.assertRaisesRegex(ValueError, 'spend'):
            bb.check(data)
        data = copy.deepcopy(SAMPLE)
        data['amounts']['missing'] = 100
        with self.assertRaisesRegex(ValueError, 'docs에 없어요'):
            bb.check(data)

    def test_guide_rules_follow_answers(self):
        a = {'budget': 'yes', 'source': 'unsure', 'outside': 'no', 'consent': 'none', 'report': 'no'}
        st = {i['id']: guide.judge(i, a)[0] for i in guide.ITEMS}
        self.assertEqual(st, {'plan': 'need', 'newmoney': 'ask', 'safety': 'skip', 'letter': 'skip', 'buy': 'need', 'report': 'skip'})
        self.assertEqual(guide.judge(next(i for i in guide.ITEMS if i['id'] == 'letter'), {})[0], 'open')
        self.assertFalse(guide.asked(next(q for q in guide.QUESTIONS if q['id'] == 'source'), {'budget': 'no'}))

    def test_plan_prompt_uses_last_year_plan(self):
        plan = next(i for i in guide.ITEMS if i['id'] == 'plan')
        self.assertIn('작년', guide.prompt(plan, {'lastyear': 'yes'}))
        self.assertNotIn('작년', guide.prompt(plan, {'lastyear': 'no'}))
        page = bb.page_data(SAMPLE, bb.check(SAMPLE))
        text = next(i for i in page['guide']['items'] if i['id'] == 'plan')['prompts'][0]['text']
        self.assertIn(SAMPLE['project'], text)

    def test_steps_say_what_to_do_now_and_next(self):
        st = guide.steps(SAMPLE['guide'], SAMPLE['docs'])
        self.assertEqual([(x['id'], x['state']) for x in st],
                         [('plan', 'done'), ('safety', 'done'), ('letter', 'done'), ('buy', 'now'), ('report', 'next')])
        self.assertEqual(st[3]['doc']['id'], 'buy2')
        fresh = guide.steps({'budget': 'yes', 'source': 'unsure', 'report': 'unsure'}, [])
        self.assertEqual(fresh[0]['state'], 'now')
        self.assertEqual(fresh[1]['do'], '행정실에 성립전 예산 물어보기')
        self.assertTrue(bb.say_steps(SAMPLE)[0].startswith('지금 할 일: 품의 올리기'))

    @unittest.skipUnless(shutil.which('node'), 'node가 없어요')
    def test_rendered_page_javascript_parses(self):
        html = bb.render(FRESH, bb.check(FRESH))
        script = html.split('<script>', 1)[1].split('</script>', 1)[0]
        run = 'new Function(' + json.dumps(script) + ')'
        subprocess.run(['node', '-e', run], capture_output=True, text=True, check=True)

    @unittest.skipUnless(shutil.which('node'), 'node가 없어요')
    def test_example_pages_run_their_full_inline_script(self):
        examples = [json.loads(path.read_text(encoding='utf-8'))
                    for path in sorted((SKILL / 'examples').glob('*.json'))]
        no_guide = copy.deepcopy(SAMPLE)
        no_guide.pop('guide')
        examples.append(no_guide)
        harness = r'''
class Element {
  constructor() { this.childNodes = []; this.children = this.childNodes; this.dataset = {}; this.style = { setProperty() {} }; this.classList = { add() {} }; this.hidden = false; }
  get firstChild() { return this.childNodes[0]; }
  set textContent(value) { this.childNodes = []; this._text = value; }
  get textContent() { return this._text || ''; }
  appendChild(node) { this.childNodes.push(node); return node; }
  append(...nodes) { nodes.forEach(node => this.appendChild(node)); }
  setAttribute() {} addEventListener() {} remove() {} after() {} focus() {} scrollIntoView() {} select() {}
  querySelector() { return new Element(); }
}
const elements = new Map();
global.document = {
  getElementById(id) { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); },
  querySelector() { return new Element(); }, querySelectorAll() { return []; },
  createElement() { return new Element(); }, createTextNode(text) { const e = new Element(); e.textContent = text; return e; },
  documentElement: new Element(), execCommand() { return false; }
};
global.localStorage = { getItem() { throw Error('localStorage disabled'); }, setItem() { throw Error('localStorage disabled'); }, removeItem() { throw Error('localStorage disabled'); } };
global.matchMedia = () => ({ matches: false, addEventListener() {} });
global.IntersectionObserver = class { observe() {} disconnect() {} };
global.requestAnimationFrame = fn => fn();
global.navigator = { clipboard: { writeText() { return Promise.resolve(); } } };
'''
        for index, data in enumerate(examples):
            with self.subTest(example=index):
                results = bb.check(data)
                html = bb.render(data, results)
                script = html.split('<script>', 1)[1].split('</script>', 1)[0]
                run = harness + '\n' + script
                result = subprocess.run(['node', '-e', run], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shutil.which('node'), 'node가 없어요')
    def test_board_page_orders_steps_like_python(self):
        html = (SKILL / 'assets' / 'board.html').read_text(encoding='utf-8')
        js = html[html.index('const matches ='):html.index('const STEP_LABEL')]
        page = bb.page_data(SAMPLE, bb.check(SAMPLE))
        answer_sets = [
            SAMPLE['guide'],
            {'budget': 'yes', 'source': 'unsure', 'outside': 'no', 'report': 'unsure'},
            {},
            {'lastyear': 'no', 'budget': 'no'},
            {'lastyear': 'yes', 'budget': 'yes', 'source': 'unsure'},
            {'budget': 'yes', 'source': 'new', 'report': 'unsure'},
            {'budget': 'no', 'source': 'new', 'outside': 'yes', 'consent': 'notice', 'external': 'yes', 'report': 'no'},
            {'lastyear': 'yes', 'budget': 'yes', 'source': 'new', 'outside': 'yes', 'consent': 'reply', 'external': 'yes', 'report': 'unsure'},
            {'budget': 'yes', 'source': 'school', 'outside': 'no', 'consent': 'none', 'external': 'no', 'report': 'yes'},
        ]
        for answers in answer_sets:
            g = {**page['guide'], 'answers': answers}
            run = f"const B = {json.dumps({'docs': page['docs']}, ensure_ascii=False)}; const G = {json.dumps(g, ensure_ascii=False)};\n{js}\n" \
                  "const o = steps(G.answers); console.log(JSON.stringify({steps:o.map(x => [x.it.id, x.state, x.do, x.tip])," \
            "needed:o.filter(x=>x.j.st==='need').length, ask:o.filter(x=>x.j.st==='ask').length}));"
            out = json.loads(subprocess.run(['node', '-e', run], capture_output=True, text=True, check=True).stdout)
            want = [[x['id'], x['state'], x['do'], x['tip']] for x in guide.steps(answers, SAMPLE['docs'])]
            self.assertEqual(out['steps'], want)
            st = [guide.judge(item, answers)[0] for item in guide.ITEMS]
            self.assertEqual(out['needed'], st.count('need'))
            self.assertEqual(out['ask'], st.count('ask'))

    def test_guide_rejects_unknown_answer(self):
        data = copy.deepcopy(SAMPLE)
        data['guide']['outside'] = 'maybe'
        with self.assertRaises(ValueError): bb.check(data)


if __name__ == '__main__': unittest.main()
