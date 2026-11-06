"""길잡이: 사업을 시작할 때 묻는 질문과, 답에 따라 필요한 문서를 고르는 규칙.

규칙은 자료로만 적는다. 보드 화면(JS)도 같은 자료를 받아 같은 방법으로 판단하므로,
여기만 고치면 검사와 화면이 함께 바뀐다.

문서 하나의 상태는 rules를 위에서부터 보고 처음 맞는 줄로 정한다.
  need = 필요해요, ask = 담당 부서에 물어봐야 해요, skip = 필요 없어요, open = 아직 답을 고르지 않았어요
"""

PHASES = [
    {'id': 'prep', 'name': '준비', 'when': '사업을 시작하기 전'},
    {'id': 'notice', 'name': '안내', 'when': '활동 전, 보호자가 답할 시간을 두고'},
    {'id': 'run', 'name': '운영', 'when': '돈을 쓰기 전마다'},
    {'id': 'close', 'name': '마무리', 'when': '활동이 끝난 뒤'},
]

QUESTIONS = [
    {'id': 'lastyear', 'short': '작년 계획서', 'q': '작년에 쓴 계획서가 있나요?', 'help': '있으면 작년 계획서의 짜임을 그대로 두고 올해 날짜·대상·예산만 새로 써요.',
     'choices': [['yes', '네, 있어요'], ['no', '올해 처음 해요']]},
    {'id': 'budget', 'short': '예산', 'q': '예산을 쓰나요?', 'help': '물건을 사거나 강사비·차비를 내면 예산을 써요.',
     'choices': [['yes', '네, 써요'], ['no', '아니요']]},
    {'id': 'source', 'short': '목적사업비', 'q': '이 사업에 쓸 목적사업비를 새로 받았나요?', 'help': '목적사업비는 교육청이나 다른 기관이 이 사업에만 쓰라고 따로 보내 주는 돈이에요. 학교 예산을 짠 뒤에 받았다면, 쓰기 전에 학교 예산에 먼저 넣어야 해요.',
     'ask_if': {'budget': ['yes']},
     'choices': [['new', '네, 새로 받았어요'], ['school', '아니요, 학교 예산에 이미 있어요'], ['unsure', '잘 모르겠어요']]},
    {'id': 'outside', 'short': '학교 밖', 'q': '학생이 학교 밖으로 나가나요?', 'help': '체험학습, 견학, 대회 참가처럼 교문 밖으로 가는 활동이요.',
     'choices': [['yes', '네, 나가요'], ['no', '학교 안에서만 해요']]},
    {'id': 'consent', 'short': '보호자', 'q': '보호자에게 받을 것이 있나요?', 'help': '참가 동의나 신청을 받으려면 회신서가 붙은 가정통신문을 보내요.',
     'choices': [['reply', '동의·회신을 받아요'], ['notice', '알리기만 해요'], ['none', '따로 없어요']]},
    {'id': 'external', 'short': '외부 강사·기관', 'q': '외부 강사나 기관과 함께하나요?', 'help': '',
     'choices': [['yes', '네, 함께해요'], ['no', '아니요']]},
    {'id': 'report', 'short': '결과 보고', 'q': '끝나고 결과 보고를 올려야 하나요?', 'help': '지원 사업이거나 학교 계획에 결과 보고가 적혀 있으면 올려요.',
     'choices': [['yes', '네, 올려요'], ['no', '아니요'], ['unsure', '잘 모르겠어요']]},
]

# do: 차례에 보여 줄 할 일(ask_do: 물어볼 문서일 때). skill: 이 문서를 만드는 칠서 스킬. prompts는 위에서부터 처음 맞는 문구를 쓰고, {project}는 사업 이름으로 바뀐다
ITEMS = [
    {'id': 'plan', 'name': '계획서(내부결재)', 'do': '계획서 결재 받기', 'phase': 'prep', 'skill': 'school-plan-hwpx',
     'rules': [{'if': {'lastyear': ['yes']}, 'then': 'need', 'why': '작년 계획서를 바탕으로 올해 날짜·대상·예산을 새로 써서 결재를 받아요. 다른 문서는 모두 이 계획을 근거로 써요.'},
               {'if': {}, 'then': 'need', 'why': '무엇을 왜 하고, 돈을 얼마 쓰는지 먼저 결재를 받아요. 다른 문서는 모두 이 계획을 근거로 써요.'}],
     'notes': [{'if': {'lastyear': ['yes']}, 'text': '부탁할 때 작년 계획서 파일(한글이나 PDF)을 함께 올려 주세요.'},
               {'if': {'external': ['yes']}, 'text': '함께하는 외부 강사·기관과 맡는 일을 계획서에 적어 두세요.'}],
     'prompts': [{'if': {'lastyear': ['yes']}, 'text': '작년 「{project}」 계획서를 올릴게요. 짜임과 문장은 살리고, 올해 계획서를 학교 내부결재 양식 한글 파일로 만들어 주세요. 날짜·대상·인원·예산·근거 공문은 작년 값을 옮기지 말고 한 번에 모아 물어봐 주세요.'},
                 {'if': {}, 'text': '「{project}」 계획서를 학교 내부결재 양식 한글 파일로 만들어 주세요. 모르는 값은 지어내지 말고 먼저 물어봐 주세요.'}]},
    {'id': 'newmoney', 'name': '성립전 예산', 'do': '성립전 예산 올리기', 'ask_do': '행정실에 성립전 예산 물어보기', 'phase': 'prep', 'skill': 'school-gongmun-draft',
     'rules': [{'if': {'budget': ['no']}, 'then': 'skip', 'why': '예산을 쓰지 않으면 올리지 않아도 돼요.'},
               {'if': {'source': ['school']}, 'then': 'skip', 'why': '학교 예산에 이미 있는 돈이면 올리지 않아도 돼요.'},
               {'if': {'source': ['new']}, 'then': 'need', 'why': '새로 받은 목적사업비는 쓰기 전에 학교 예산에 먼저 넣어야 해요. 이걸 성립전 예산이라고 해요. 누가 어떤 문서를 올리는지는 행정실에 물어봐 주세요.'},
               {'if': {'source': ['unsure']}, 'then': 'ask', 'why': '이 돈이 새로 받은 목적사업비인지 행정실에 먼저 물어봐 주세요. 새로 받았다면 성립전 예산이 필요해요.'}],
     'notes': [],
     'prompts': [{'if': {}, 'text': '「{project}」에 새로 받은 목적사업비를 성립전 예산으로 올리는 기안문을 써 주세요. 관련 공문 번호를 모르면 지어내지 말고 물어봐 주세요.'}]},
    {'id': 'safety', 'name': '안전계획', 'do': '안전계획 결재 받기', 'phase': 'prep', 'skill': 'school-plan-hwpx',
     'rules': [{'if': {'outside': ['yes']}, 'then': 'need', 'why': '학생이 학교 밖으로 나가면 이동 방법, 인솔, 비상 연락을 미리 정해 결재를 받아요.'},
               {'if': {'outside': ['no']}, 'then': 'skip', 'why': '학교 안에서만 하면 따로 쓰지 않아도 돼요.'}],
     'notes': [{'if': {'lastyear': ['yes']}, 'text': '작년 안전계획이 있으면 함께 올려 주세요. 그 짜임대로 올해 내용을 써요.'}],
     'prompts': [{'if': {}, 'text': '「{project}」 학교 밖 활동 안전계획을 한글 파일로 만들어 주세요. 이동 수단, 인솔 교사 수, 비상 연락 방법을 하나씩 물어봐 주세요.'}]},
    {'id': 'letter', 'name': '가정통신문', 'do': '가정통신문 보내기', 'phase': 'notice', 'skill': 'school-newsletter',
     'rules': [{'if': {'consent': ['reply']}, 'then': 'need', 'why': '동의나 회신을 받아야 하니 회신서가 붙은 가정통신문을 보내요.'},
               {'if': {'consent': ['notice']}, 'then': 'need', 'why': '보호자가 미리 알 수 있게 안내 가정통신문을 보내요.'},
               {'if': {'outside': ['yes']}, 'then': 'need', 'why': '학생이 학교 밖으로 나가면 보호자에게 미리 알려요.'},
               {'if': {'consent': ['none'], 'outside': ['no']}, 'then': 'skip', 'why': '보호자에게 알리거나 받을 것이 없으면 보내지 않아도 돼요.'}],
     'notes': [{'if': {'lastyear': ['yes']}, 'text': '작년에 보낸 가정통신문이 있으면 함께 올려 주세요. 그 짜임대로 올해 내용을 써요.'}],
     'prompts': [{'if': {}, 'text': '「{project}」 가정통신문을 만들어 주세요. 날짜·장소·준비물을 하나씩 물어봐 주시고, 보호자가 휴대폰으로 볼 미리보기도 보여 주세요.'}]},
    {'id': 'buy', 'name': '품의', 'do': '품의 올리기', 'phase': 'run', 'skill': 'school-gongmun-draft',
     'rules': [{'if': {'budget': ['yes']}, 'then': 'need', 'why': '돈을 쓰기 전에 품의로 먼저 결재를 받아요. 쓸 때마다 한 건씩 올려요.'},
               {'if': {'budget': ['no']}, 'then': 'skip', 'why': '예산을 쓰지 않으면 올리지 않아도 돼요.'}],
     'notes': [{'if': {'external': ['yes'], 'budget': ['yes']}, 'text': '외부 강사 수당도 품의로 올려요.'}],
     'prompts': [{'if': {}, 'text': '「{project}」 지출 품의 기안문을 만들어 주세요. 산출식과 합계, 금액 한글 표기도 검산해 주세요.'}]},
    {'id': 'report', 'name': '결과 보고', 'do': '결과 보고 올리기', 'ask_do': '담당 부서에 결과 보고 물어보기', 'phase': 'close', 'skill': 'school-gongmun-draft',
     'rules': [{'if': {'report': ['yes']}, 'then': 'need', 'why': '운영한 내용과 쓴 돈을 정리해 보고해요.'},
               {'if': {'report': ['unsure']}, 'then': 'ask', 'why': '결과 보고가 필요한지 담당 부서에 물어봐 주세요. 지원 사업이면 대개 올려요.'},
               {'if': {'report': ['no']}, 'then': 'skip', 'why': '결과 보고가 없는 사업이면 건너뛰어도 돼요.'}],
     'notes': [{'if': {'lastyear': ['yes']}, 'text': '작년 결과 보고가 있으면 함께 올려 주세요. 같은 형식으로 이어 써요.'}],
     'prompts': [{'if': {}, 'text': '「{project}」 운영 결과 보고 기안문을 써 주세요. 관련 계획 문서번호와 쓴 돈은 보드에서 가져와 주세요.'}]},
]

OPEN_WHY = '길잡이 질문에 답하면 필요한지 알려 드려요.'

# 차례에서 지금 할 일 아래에 붙이는 한 줄. 문서가 없으면 none, 있으면 그 문서의 결재 상태로 고른다
NOW_TIP = {
    'none': '부탁 문구를 복사해 Claude에게 보내면 만들어 드려요.',
    'todo': 'Claude에게 이 문서를 만들어 달라고 해 주세요.',
    'draft': '마무리해서 결재에 올려 주세요.',
    'review': '결재가 끝나면 문서번호를 보드에 알려 주세요.',
}


def match(cond, answers):
    return all(answers.get(k) in v for k, v in cond.items())


def asked(q, answers):
    return match(q.get('ask_if', {}), answers)


def judge(item, answers):
    """(상태, 까닭, 덧붙일 말들)"""
    rule = next((r for r in item['rules'] if match(r['if'], answers)), None)
    notes = [n['text'] for n in item['notes'] if match(n['if'], answers)]
    return (rule['then'], rule['why'], notes) if rule else ('open', OPEN_WHY, notes)


def prompt(item, answers):
    return next(p['text'] for p in item['prompts'] if match(p['if'], answers))


def validate(answers, docs):
    qs = {q['id']: {c[0] for c in q['choices']} for q in QUESTIONS}
    for k, v in answers.items():
        if k not in qs: raise ValueError(f'길잡이에 없는 질문이에요: {k}')
        if v not in qs[k]: raise ValueError(f'길잡이 {k}의 답은 {", ".join(sorted(qs[k]))} 가운데 하나예요: {v}')
    items, phases = {i['id'] for i in ITEMS}, {p['id'] for p in PHASES}
    for d in docs:
        if d.get('need') and d['need'] not in items: raise ValueError(f"{d['id']}의 need {d['need']}는 길잡이 문서에 없어요")
        if d.get('phase') and d['phase'] not in phases: raise ValueError(f"{d['id']}의 phase {d['phase']}는 {', '.join(sorted(phases))} 가운데 하나예요")


def steps(answers, docs):
    """필요한 문서를 단계 순서대로 늘어놓고 마친 것(done), 지금 할 일(now), 다음(next), 그 뒤(later)를 붙인다.
    문서가 있고 모두 결재를 마쳤으면 마친 것이다. 물어볼 문서(ask)는 답을 알기 전까지 마치지 않은 것으로 본다."""
    out = []
    for item in ITEMS:
        st, why, _ = judge(item, answers)
        if st not in ('need', 'ask'): continue
        mine = [d for d in docs if d.get('need') == item['id']]
        done = st == 'need' and bool(mine) and all(d['status'] == 'done' for d in mine)
        doc = next((d for d in mine if d['status'] != 'done'), None)
        out.append({'id': item['id'], 'do': item['ask_do'] if st == 'ask' else item['do'], 'st': st, 'why': why, 'done': done, 'doc': doc})
    left = [x for x in out if not x['done']]
    for x in out:
        x['state'] = 'done' if x['done'] else ('now', 'next')[left.index(x)] if left.index(x) < 2 else 'later'
        x['tip'] = x['why'] if x['st'] == 'ask' else NOW_TIP[x['doc']['status'] if x['doc'] else 'none']
    return out
