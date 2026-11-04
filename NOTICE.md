# 출처와 사용 범위

## 학교 양식 (MIT에 포함되지 않음)

- 파일: `plugins/chilseo-docs/skills/school-plan-hwpx/templates/chilseo_plan_template.hwpx`
- 내용: 칠서초등학교 내부결재용 계획서의 머리말(학교 표어), 제목 상자, 교표 그림, 표 서식 견본.
- 만든 방법: 학교에서 결재한 계획서 한 건을 `scripts/clean_template.py`로 정리했습니다. 예전 계획서 본문·표 내용·수식 값·외부 링크·작성자 정보·미리보기 그림은 모두 지웠습니다.
- 사용 범위: 칠서초등학교 업무용입니다. 다른 학교는 이 파일 대신 자기 학교 양식으로 빈 양식을 만들어 씁니다. 교표와 학교 표어의 권리는 학교에 있습니다.

## 가정통신문 양식 (MIT에 포함되지 않음)

- 파일: `plugins/chilseo-docs/skills/school-newsletter/templates/chilseo_newsletter_template.hwpx`
- 내용: 칠서초등학교 가정통신문의 머리말(학교 표어·교표·학교 이름), 제목 상자, 구분/내용 표, 참가 동의서(학년·반·이름 줄, 동의함 표, 서명 줄).
- 만든 방법: 2026년에 결재를 받아 보낸 칠서초 현장체험학습 가정통신문 한 건을 `tools/make_newsletter_template.py`로 정리했습니다. 예전 안내 본문·날짜·학교 전화번호·누리집 주소·작성자 정보·미리보기 그림은 지웠고, 남은 글자 자리는 `{{TITLE}}` 같은 표시로 바꿨습니다. 표와 자르는 선은 쪽 너비에 맞췄습니다.
- 사용 범위: 위 학교 양식과 같습니다.

## 참고한 공개 자료

스킬 내용은 아래 자료의 원칙을 참고해 새로 썼습니다. 원문을 복사하지 않았습니다. 자세한 주소와 확인한 날짜는 각 스킬의 `references/sources.md`에 있습니다.

- 토스 앱인토스 UI/UX 가이드, 토스 기술 블로그(toss.tech): 원칙만 참고. 토스의 글꼴·아이콘·그래픽·TDS 키트는 넣지 않았습니다.
- KRDS(대한민국 정부 디자인 시스템): 공공저작물, 출처 표기 후 이용.
- 커뮤니티 스킬(모두 MIT): NariP/toss-ux-writing-skills, Ksanbal/toss-ux-writing-skill, claudianus/toss-ux-writing-skill, Ilbie/Toss-Design-Skill, elayadesign/ai-design-skills.

## 함께 쓰는 다른 도구 (이 저장소에 복사하지 않음)

- kordoc (MIT, chrisryugj): 마켓플레이스 목록에서 원저장소를 가리킵니다. `chilseo-docs`의 `.mcp.json`은 npm 패키지 `kordoc`을 실행합니다.
- python-hwpx, lxml: 실행할 때 설치하는 Python 패키지입니다.
