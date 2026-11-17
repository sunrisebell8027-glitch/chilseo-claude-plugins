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


TASK = json.loads((SKILL / 'examples' / 'sample_video_shoot_board.json').read_text(encoding='utf-8'))

# 보드 화면의 스크립트를 node로 끝까지 돌려 보는 가짜 문서. 글자와 숨김, 칸 배치 값을 남겨 둔다
HARNESS = r'''
class Element {
  constructor() { this.childNodes = []; this.children = this.childNodes; this.dataset = {}; this.hidden = false; this.cls = new Set();
    this.style = { props: {}, setProperty(k, v) { this.props[k] = v; } };
    const self = this; this.classList = { add(c) { self.cls.add(c); }, remove(c) { self.cls.delete(c); }, toggle(c, on) { (on ?? !self.cls.has(c)) ? self.cls.add(c) : self.cls.delete(c); return self.cls.has(c); } }; }
  get firstChild() { return this.childNodes[0]; }
  set textContent(value) { this.childNodes = []; this._text = value; }
  get textContent() { return this._text || ''; }
  set className(v) { this.cls = new Set(String(v).split(' ').filter(Boolean)); }
  get className() { return [...this.cls].join(' '); }
  appendChild(node) { this.childNodes.push(node); return node; }
  append(...nodes) { nodes.forEach(node => this.appendChild(node)); }
  setAttribute() {} addEventListener() {} remove() {} after() {} focus() {} scrollIntoView() {} select() {}
  querySelector() { return new Element(); }
}
const elements = new Map();
const __el = id => { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); };
global.document = {
  getElementById: __el,
  querySelector(sel) { return __el('query:' + sel); }, querySelectorAll() { return []; },
  createElement() { return new Element(); }, createTextNode(text) { const e = new Element(); e.textContent = text; return e; },
  documentElement: new Element(), execCommand() { return false; }
};
global.localStorage = { getItem() { throw Error('localStorage disabled'); }, setItem() { throw Error('localStorage disabled'); }, removeItem() { throw Error('localStorage disabled'); } };
global.matchMedia = () => ({ matches: false, addEventListener() {} });
global.IntersectionObserver = class { observe() {} disconnect() {} };
global.requestAnimationFrame = fn => fn();
global.navigator = { clipboard: { writeText() { return Promise.resolve(); } } };
'''
REPORT = r'''
const text = e => (e._text || '') + e.childNodes.map(text).join('');
const ids = ['guide', 'decide', 'docs', 'money', 'budget', 'schedule', 'checks', 'log'];
console.log(JSON.stringify({
  heads: Object.fromEntries(['eyebrow', 'decideHead', 'docsHead', 'windowTitle', 'checkHead', 'flow', 'decideList', 'moneyHead', 'budgetHead'].map(k => [k, text(__el(k))])),
  paper: text(paper),
  hidden: Object.fromEntries(ids.map(k => [k, __el(k).hidden])),
  areas: __el('query:.bento').style.props,
}));
'''


def render_page(data):
    """보드를 만들어 화면 스크립트를 node로 돌리고, 보이는 글과 숨긴 칸, 칸 배치를 돌려준다."""
    data = copy.deepcopy(data)
    html = bb.render(data, bb.check(data))
    script = html.split('<script>', 1)[1].split('</script>', 1)[0]
    run = subprocess.run(['node', '-e', HARNESS + '\n' + script + '\n' + REPORT], capture_output=True, text=True)
    if run.returncode: raise AssertionError(run.stderr)
    return json.loads(run.stdout)


def status(results, id_):
    return next(r['status'] for r in results if r['id'] == id_)


class BoardTest(unittest.TestCase):
    def test_ledger_without_purchase_amount_fails(self):
        data = {'school': '한빛초등학교', 'project': '사업', 'updated': '2026-03-02',
                'docs': [{'id': 'buy', 'kind': '품의', 'title': '재료', 'status': 'todo', 'need': 'buy'}],
                'ledger': [{'name': '재료', 'allocated': 100, 'spend': [{'doc': 'buy', 'name': '재료', 'amount': 50}]}]}
        row = next(r for r in bb.check(data) if r['id'] == '합계')
        self.assertEqual(row['status'], 'fail')
        self.assertIn('amounts', row['detail'])

    def test_dates_require_documented_format(self):
        data = {'school': '한빛초등학교', 'project': '사업', 'updated': '20260302'}
        with self.assertRaisesRegex(ValueError, 'YYYY-MM-DD'): bb.check(data)
        data['updated'] = '2026-03-02'
        data['schedule'] = [{'date': '20260303', 'title': '준비'}]
        with self.assertRaisesRegex(ValueError, 'YYYY-MM-DD'): bb.check(data)

    def test_title_escapes_html(self):
        data = {'school': '한빛초등학교', 'project': '<b>사업 & 준비</b>', 'updated': '2026-03-02'}
        html = bb.render(data, bb.check(data))
        self.assertIn('<title>&lt;b&gt;사업 &amp; 준비&lt;/b&gt; 보드</title>', html)

    def test_weekday_uses_explicit_year_for_following_dates(self):
        data = {'school': '한빛초등학교', 'project': '2025. 3. 2.(일) ~ 3. 3.(월)', 'updated': '2026-03-02'}
        self.assertEqual(bb.weekday_errors(data), [])
        data['project'] = '2025. 3. 2.(일) ~ 3. 3.(화)'
        self.assertIn('3. 3.(화) → (월)', bb.weekday_errors(data))

    def test_ledger_rejects_numbers_that_javascript_cannot_represent(self):
        data = {'school': '한빛초등학교', 'project': '사업', 'updated': '2026-03-02',
                'ledger': [{'name': '예산', 'allocated': 2**53}]}
        with self.assertRaisesRegex(ValueError, 'allocated'): bb.check(data)
        data['ledger'] = [{'name': '첫째', 'allocated': 2**53 - 1}, {'name': '둘째', 'allocated': 1}]
        with self.assertRaisesRegex(ValueError, '합계'): bb.check(data)

    def test_invalid_draft_items_identify_field(self):
        data = copy.deepcopy(SAMPLE)
        next(d for d in data['docs'] if d['id'] == 'buy2')['draft']['items'] = [{}]
        with self.assertRaisesRegex(ValueError, 'items.*text'): bb.check(data)

    def test_cli_rejects_invalid_unicode_without_traceback(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / '입력.json'
            path.write_text('{"school":"학교", "project":"\\ud800", "updated":"2026-03-02"}', encoding='utf-8')
            run = subprocess.run([sys.executable, str(SKILL / 'scripts' / 'build_board.py'), str(path), '-o', str(Path(tmp) / '보드.html')], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertIn('유니코드', run.stderr)
        self.assertNotIn('Traceback', run.stderr)

    def test_cli_reports_unwritable_output_without_traceback(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'board.json'
            path.write_text(json.dumps({'school': '한빛초등학교', 'project': '사업', 'updated': '2026-03-02'}), encoding='utf-8')
            run = subprocess.run([sys.executable, str(SKILL / 'scripts' / 'build_board.py'), str(path), '-o', tmp], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertIn('저장 경로', run.stderr)
        self.assertNotIn('Traceback', run.stderr)

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
        self.assertIn('남은 질문', bb.say_steps(UNANSWERED)[1])

    def test_board_without_guide_says_now_and_next_from_its_own_items(self):
        data = {'school': '한빛초등학교', 'project': '2026. 시작 보드', 'updated': '2026-03-02'}
        self.assertFalse([r for r in bb.check(data) if r['status'] == 'fail'])
        self.assertEqual(bb.say_steps(data), ['지금 할 일: 아직 할 일이 없어요. docs에 할 일을 넣으면 알려 드려요.', '다음 할 일: 없어요.'])
        self.assertEqual(bb.page_data(data, bb.check(data))['docs'], [])
        no_guide = copy.deepcopy(SAMPLE); no_guide.pop('guide')
        self.assertEqual(bb.say_steps(no_guide)[0], '지금 할 일: 2026. 과학 탐구 동아리 실험 재료 구입 및 간식비 지출 건의 (작성 중)')
        self.assertTrue(bb.say_steps(no_guide)[1].startswith('다음 할 일: 2026. 과학 탐구 동아리 운영 결과 보고'))

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
        # 예산 자료가 하나도 없으면 예산 검사를 하지 않는다(기본은 빼기). 예산과목만 있어도 켠다
        no_guide = {'school': '한빛초등학교', 'project': '시작', 'updated': '2026-03-02'}
        self.assertNotIn('편성액', [r['id'] for r in bb.check(no_guide)])
        no_guide['budget_code'] = '교육운영비'
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
        harness = HARNESS
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

    def test_decide_links_and_images_have_korean_errors(self):
        base = {'school': '한빛초등학교', 'project': '사업', 'updated': '2026-03-02'}
        for bad in ([{'label': '공문', 'url': 'http://example.com'}], [{'label': '', 'url': 'https://example.com'}], ['주소']):
            with self.assertRaisesRegex(ValueError, 'links.*https'):
                bb.check({**base, 'decide': [{'text': '정해 주세요', 'links': bad}]})
        for bad in ([{'src': '캡처.gif', 'alt': '공문'}], [{'src': '캡처.png'}], ['캡처.png']):
            with self.assertRaisesRegex(ValueError, 'images.*png'):
                bb.check({**base, 'decide': [{'text': '정해 주세요', 'images': bad}]})
        ok = {**base, 'decide': [{'text': '정해 주세요', 'links': [{'label': '공문', 'url': 'https://example.com/a'}],
                                  'images': [{'src': '캡처/공문.PNG', 'alt': '공문 2쪽'}]}]}
        bb.check(ok)

    def test_decide_capture_is_embedded_from_the_json_folder(self):
        import base64, tempfile
        png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=')
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp); (tmp / '캡처').mkdir(); (tmp / '캡처' / '공문.png').write_bytes(png)
            data = {'school': '한빛초등학교', 'project': '사업', 'updated': '2026-03-02',
                    'decide': [{'text': '정해 주세요', 'images': [{'src': '캡처/공문.png', 'alt': '공문 2쪽'}]}]}
            (tmp / '보드.json').write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            out = tmp / '보드.html'
            r = subprocess.run([sys.executable, str(SKILL / 'scripts' / 'build_board.py'), str(tmp / '보드.json'), '-o', str(out)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            html = out.read_text(encoding='utf-8')
            self.assertIn('data:image/png;base64,iVBORw0KGgo', html)
            self.assertNotIn('캡처/공문.png', html)  # 파일 경로는 보드에 남기지 않는다
            data['decide'][0]['images'][0]['src'] = '캡처/없음.png'
            (tmp / '보드.json').write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            r = subprocess.run([sys.executable, str(SKILL / 'scripts' / 'build_board.py'), str(tmp / '보드.json'), '-o', str(out)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
            self.assertIn('캡처 파일을 찾지 못했어요', r.stderr)
            self.assertNotIn('Traceback', r.stderr)

    def test_capture_over_the_size_limit_is_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp); (tmp / '큰.png').write_bytes(b'0' * (bb.IMAGE_LIMIT + 1))
            data = {'decide': [{'text': '정해 주세요', 'images': [{'src': '큰.png', 'alt': '공문'}]}]}
            with self.assertRaisesRegex(ValueError, '1.5MB'): bb.embed_images(data, tmp)

    def test_board_without_budget_drops_money_tiles_and_checks(self):
        data = {'school': '한빛초등학교', 'project': '설문', 'updated': '2026-03-02', 'guide': {'budget': 'no'}}
        checks = bb.check(data)
        self.assertFalse({'합계', '편성액'} & {r['id'] for r in checks})
        self.assertEqual(bb.page_data(data, checks)['features'], {'approval': True, 'budget': False})
        self.assertEqual(bb.page_data(copy.deepcopy(SAMPLE), bb.check(copy.deepcopy(SAMPLE)))['features'], {'approval': True, 'budget': True})
        page = render_page(data)
        self.assertTrue(page['hidden']['money'] and page['hidden']['budget'])
        self.assertNotIn('money', page['areas']['--a3'])

    def test_sample_decide_link_reaches_the_page_data(self):
        data = copy.deepcopy(SAMPLE)
        page = bb.page_data(data, bb.check(data))
        links = [l for d in page['decide'] for l in d.get('links', [])]
        self.assertEqual(links[0]['url'], 'https://example.com/notice')
        self.assertTrue(all(d['images'] == [] for d in page['decide']))

    # ---- 범용 보드: 결재·예산·학교 없이도 정할 것 · 할 일 흐름 · 일정 · 작업 기록만으로 읽힌다 ----

    def test_task_board_turns_off_approval_and_budget_by_default(self):
        data = copy.deepcopy(TASK)
        self.assertEqual(bb.features(data), {'approval': False, 'budget': False})
        results = bb.check(data)
        self.assertFalse([r for r in results if r['status'] == 'fail'])
        self.assertEqual([r['id'] for r in results], ['요일', '기한', '빈칸'])
        self.assertIn('할 일이 없어요', next(r for r in results if r['id'] == '기한')['detail'])
        page = bb.page_data(data, results)
        self.assertEqual(page['ledger'], [])
        self.assertEqual(page['school'], '')
        self.assertEqual({d['status_label'] for d in page['docs']}, {'마침', '확인 중', '하는 중', '아직'})

    def test_task_board_says_doing_first_then_todo_and_waits_for_review(self):
        self.assertEqual(bb.say_steps(copy.deepcopy(TASK)), [
            '지금 할 일: ② 독서 기록 대시보드 만들기 (1분 30초) (하는 중)',
            '다음 할 일: ③ 상담 기록 표 만들기 (2분) (아직)'])
        page = bb.page_data(copy.deepcopy(TASK), bb.check(copy.deepcopy(TASK)))
        self.assertEqual((page['now'], page['next']), ('v2', 'v3'))
        docs = [{'id': i, 'title': i, 'status': s} for i, s in [('a', 'review'), ('b', 'todo'), ('c', 'todo'), ('d', 'done')]]
        now, nxt = bb.now_next(docs)
        self.assertEqual((now['id'], nxt['id']), ('b', 'c'))
        self.assertEqual(bb.now_next([{'id': 'a', 'title': 'a', 'status': 'review'}])[0]['id'], 'a')
        done = copy.deepcopy(TASK)
        for d in done['docs']: d['status'] = 'done'
        self.assertEqual(bb.say_steps(done), ['지금 할 일: 할 일을 모두 마쳤어요.', '다음 할 일: 없어요.'])

    def test_task_items_carry_links_note_checklist_and_ask(self):
        page = bb.page_data(copy.deepcopy(TASK), bb.check(copy.deepcopy(TASK)))
        v1, v2, v3 = (next(d for d in page['docs'] if d['id'] == k) for k in ('v1', 'v2', 'v3'))
        self.assertEqual(v1['links'][0]['type'], 'video')
        self.assertEqual([c['done'] for c in v1['checklist']], [True, True, False])
        self.assertEqual(v2['checklist'][0], {'text': '알림 끄기', 'done': False})
        self.assertTrue(v2['note'])
        self.assertEqual((v3['links'], v3['note'], v3['checklist'], v3['images']), ([], '', [], []))
        self.assertIn('‘③ 상담 기록 표 만들기 (2분)’', v3['ask'])
        self.assertIn(TASK['project'], v3['ask'])
        self.assertEqual([d['group'] for d in page['docs']], ['준비', '촬영', '촬영', '촬영', '촬영', '마무리'])

    def test_phase_without_group_uses_plain_step_names(self):
        data = {'project': '영상', 'updated': '2026-11-16', 'docs': [
            {'id': 'send', 'title': '보내기', 'status': 'todo', 'phase': 'close'},
            {'id': 'v1', 'title': '찍기', 'status': 'doing', 'phase': 'run'}]}
        page = bb.page_data(data, bb.check(data))
        self.assertEqual([(d['id'], d['group']) for d in page['docs']], [('v1', '진행'), ('send', '마무리')])
        self.assertEqual(page['docs'][0]['status'], 'draft')
        self.assertEqual(page['docs'][0]['status_label'], '하는 중')

    @unittest.skipUnless(shutil.which('node'), 'node가 없어요')
    def test_task_page_shows_no_office_words_or_empty_tiles(self):
        page = render_page(TASK)
        heads = page['heads']
        self.assertEqual(heads['eyebrow'], '프로젝트 보드')
        self.assertTrue(heads['docsHead'].startswith('할 일 흐름.'))
        self.assertEqual(heads['windowTitle'], '할 일')
        self.assertIn('지금 할 일', heads['flow'])
        self.assertIn('다음', heads['flow'])
        self.assertIn('관련 할 일 보기', heads['decideList'])
        shown = ' '.join(v for k, v in heads.items() if not page['hidden'].get({'moneyHead': 'money', 'budgetHead': 'budget', 'checkHead': 'checks'}.get(k, ''), False))
        for word in ('결재', '기안문', '편성액', '품의', '길잡이', '선생님'):
            self.assertNotIn(word, shown + page['paper'])
        self.assertEqual(page['hidden'], {'guide': True, 'decide': False, 'docs': False, 'money': True, 'budget': True,
                                          'schedule': False, 'checks': True, 'log': False})
        self.assertEqual(page['areas'], {'--a1': '"decide" "docs" "schedule" "log"',
                                         '--a2': '"decide decide" "docs docs" "schedule log"',
                                         '--a3': '"decide decide decide" "docs docs docs" "schedule log log"'})
        # 넓은 화면에서는 지금 할 일(②)을 펼쳐 두고, 붙인 자료를 보여 준다
        self.assertIn('② 독서 기록 대시보드 만들기', page['paper'])
        self.assertIn('자료 열기', page['paper'])
        self.assertIn('할 것 3개 가운데 0개를 마쳤어요', page['paper'])

    @unittest.skipUnless(shutil.which('node'), 'node가 없어요')
    def test_task_item_without_materials_offers_a_request(self):
        data = copy.deepcopy(TASK)
        for d in data['docs']:
            if d['id'] in ('v1', 'v2'): d['status'] = 'done'
        page = render_page(data)  # 지금 할 일은 ③(아직 시작하지 않은 첫 할 일), 붙인 자료가 없다
        self.assertIn('③ 상담 기록 표 만들기', page['paper'])
        self.assertIn('자료를 붙이면 여기에서 바로 열 수 있어요.', page['paper'])
        self.assertIn('부탁 문구 복사하기', page['paper'])
        self.assertNotIn('기안문', page['paper'])

    @unittest.skipUnless(shutil.which('node'), 'node가 없어요')
    def test_task_page_shows_checks_only_when_something_needs_a_look(self):
        data = copy.deepcopy(TASK)
        data['docs'][1]['due'] = '2026-11-10'  # 지난 기한
        page = render_page(data)
        self.assertFalse(page['hidden']['checks'])
        self.assertIn('확인할 것 1개', page['heads']['checkHead'])
        self.assertEqual(page['areas']['--a3'], '"decide decide decide" "docs docs docs" "schedule schedule checks" "log log log"')

    @unittest.skipUnless(shutil.which('node'), 'node가 없어요')
    def test_office_board_keeps_its_tiles_and_words(self):
        page = render_page(SAMPLE)
        self.assertEqual(page['heads']['eyebrow'], '프로젝트 보드 · 한빛초등학교')
        self.assertTrue(page['heads']['docsHead'].startswith('문서 흐름. 결재 문서'))
        self.assertEqual(page['heads']['windowTitle'], '결재 문서')
        self.assertIn('선생님이 직접 해 주세요.', page['heads']['decideHead'])
        self.assertIn('편성액', page['heads']['moneyHead'])
        self.assertFalse(any(page['hidden'][k] for k in ('guide', 'money', 'budget', 'checks')))
        self.assertEqual(page['areas']['--a3'], '"guide guide guide" "decide decide money" "docs docs docs" "budget schedule checks" "log log log"')
        self.assertEqual(page['areas']['--a2'], '"guide guide" "decide decide" "money money" "docs docs" "budget schedule" "checks log"')

    @unittest.skipUnless(shutil.which('node'), 'node가 없어요')
    def test_task_board_with_a_budget_speaks_plainly(self):
        data = copy.deepcopy(TASK)
        data['ledger'] = [{'name': '간식', 'allocated': 50000, 'spend': [{'doc': 'send', 'name': '간식', 'amount': 20000}]}]
        self.assertEqual(bb.features(data), {'approval': False, 'budget': True})
        results = bb.check(data)
        self.assertEqual(status(results, '합계'), 'ok')
        self.assertNotIn('문서번호', [r['id'] for r in results])
        page = render_page(data)
        self.assertIn('예산 50,000원 가운데', page['heads']['moneyHead'])
        self.assertIn('1줄 모두 예산 안이에요.', page['heads']['budgetHead'])
        data['ledger'][0]['spend'][0]['doc'] = 'nope'
        self.assertEqual(status(bb.check(data), '합계'), 'fail')

    def test_board_without_school_builds_but_a_draft_needs_one(self):
        data = {'project': '행사 준비', 'updated': '2026-05-01',
                'docs': [{'id': 'a', 'title': '장소 정하기', 'status': 'todo'}]}
        self.assertFalse([r for r in bb.check(data) if r['status'] == 'fail'])
        self.assertEqual(bb.page_data(data, bb.check(data))['school'], '')
        with self.assertRaisesRegex(ValueError, 'school'):
            bb.check({**data, 'school': 3})
        data = copy.deepcopy(SAMPLE); data.pop('school')
        with self.assertRaisesRegex(ValueError, 'school에 학교 이름'):
            bb.check(data)

    def test_explicit_switches_win_but_cannot_hide_existing_data(self):
        data = {'project': '사업', 'updated': '2026-03-02', 'approval': True, 'budget': True}
        self.assertEqual(bb.features(data), {'approval': True, 'budget': True})
        self.assertIn('편성액', [r['id'] for r in bb.check(data)])
        self.assertIn('문서번호', [r['id'] for r in bb.check(data)])
        with self.assertRaisesRegex(ValueError, 'budget을 false'):
            bb.check({**copy.deepcopy(SAMPLE), 'budget': False})
        with self.assertRaisesRegex(ValueError, 'approval을 false'):
            bb.check({**copy.deepcopy(SAMPLE), 'approval': False})
        with self.assertRaisesRegex(ValueError, 'approval'):
            bb.check({**data, 'approval': 'yes'})

    def test_task_item_fields_have_korean_errors(self):
        base = {'project': '사업', 'updated': '2026-03-02'}
        for item, phrase in [
            ({'links': [{'label': '대본', 'url': 'http://example.com'}]}, 'links.*https'),
            ({'links': [{'label': '대본', 'url': 'https://example.com', 'type': 'audio'}]}, 'type'),
            ({'links': '주소'}, 'links'),
            ({'images': [{'src': '시안.gif', 'alt': '시안'}]}, 'images.*png'),
            ({'checklist': ['']}, 'checklist'),
            ({'checklist': [{'text': '찍기', 'done': 'yes'}]}, 'checklist'),
            ({'note': ['메모']}, 'note'),
            ({'status': 'finished'}, 'status'),
        ]:
            doc = {'id': 'a', 'title': '찍기', 'status': 'todo', **item}
            with self.subTest(phrase=phrase), self.assertRaisesRegex(ValueError, phrase):
                bb.check({**base, 'docs': [doc]})

    def test_task_item_preview_image_is_embedded(self):
        import base64, tempfile
        png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=')
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp); (tmp / '시안').mkdir(); (tmp / '시안' / '첫 장면.png').write_bytes(png)
            data = {'project': '영상', 'updated': '2026-03-02',
                    'docs': [{'id': 'v1', 'title': '찍기', 'status': 'todo', 'images': [{'src': '시안/첫 장면.png', 'alt': '첫 장면 시안'}]}]}
            (tmp / '보드.json').write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            r = subprocess.run([sys.executable, str(SKILL / 'scripts' / 'build_board.py'), str(tmp / '보드.json'), '-o', str(tmp / '보드.html')],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            html = (tmp / '보드.html').read_text(encoding='utf-8')
            self.assertIn('data:image/png;base64,iVBORw0KGgo', html)
            self.assertNotIn('시안/첫 장면.png', html)
            data['docs'][0]['images'][0]['src'] = '시안/없음.png'
            (tmp / '보드.json').write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            r = subprocess.run([sys.executable, str(SKILL / 'scripts' / 'build_board.py'), str(tmp / '보드.json'), '-o', str(tmp / '보드.html')],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
            self.assertIn('docs의 v1', r.stderr)
            self.assertNotIn('Traceback', r.stderr)

    def test_guide_rejects_unknown_answer(self):
        data = copy.deepcopy(SAMPLE)
        data['guide']['outside'] = 'maybe'
        with self.assertRaises(ValueError): bb.check(data)


if __name__ == '__main__': unittest.main()
