# chilseo-docs: 학교 계획서 한글(HWPX) 만들기

노션이나 대화에 쓴 계획서 원고를 **학교 공용 내부결재 양식의 한글 파일**로 만들어 줍니다.
한컴오피스가 없어도 파일을 만들 수 있고, 만든 뒤에 아래를 스스로 검사합니다.

- 예산 산출식(곱셈)과 합계가 맞는지
- `2026. 12. 8.(화)`처럼 적은 날짜의 요일이 달력과 맞는지
- 시간표에 같은 학급이 두 번 들어가지 않았는지
- `○○○`, `TODO` 같은 빈자리가 남지 않았는지
- 근거·목적·예산 절이 빠지지 않았는지

검사에 하나라도 걸리면 파일을 넘기지 않고 무엇이 틀렸는지 알려 드립니다.

## 들어 있는 것

| 이름 | 내용 |
|---|---|
| `school-plan-hwpx` 스킬 | 원고 읽기 → 모자란 값 한 번에 묻기 → 한글 파일 만들기 → 검사 → 미리 보기 |
| 칠서초 계획서 양식 | 학교 표어·제목 상자·교표만 남긴 빈 양식입니다. 예전 계획서 내용은 모두 지웠습니다. |
| kordoc 연결 | Claude Code에서는 한글 파일 미리 보기·고치기 도구(kordoc)를 함께 켭니다. Node.js가 있어야 합니다. |

## 설치 3단계

**Claude 앱(채팅 화면)**

1. `school-plan-hwpx.zip`을 받습니다(압축을 풀지 않습니다).
2. 설정 → 기능(Capabilities)에서 **코드 실행 및 파일 만들기**를 켜고, **스킬(Skills)** → **스킬 업로드**로 zip을 올립니다.
3. 노션 원고를 쓰신다면 설정 → 커넥터에서 **Notion**을 연결합니다. 원고를 대화에 붙여 넣어도 됩니다.

**Claude Code**

1. `/plugin marketplace add sunrisebell8027-glitch/chilseo-claude-plugins`
2. `/plugin install chilseo-docs@chilseo-plugins`
3. Claude Code를 다시 시작합니다.

## 첫 부탁 예시

> 노션에 쓴 이 계획서를 학교 내부결재 양식 한글 파일로 만들어 주세요: (노션 페이지 주소)

> 아래 원고로 운영 계획(안) 한글 파일을 만들어 주세요. 모르는 값은 채우지 말고 먼저 물어봐 주세요.
> (원고 붙여 넣기)

처음 쓰실 때 Claude가 학교 이름과 양식을 한 번 묻습니다. 칠서초등학교라고 답하시면 들어 있는 양식을 씁니다.

## 다른 학교에서 쓰려면

예전에 결재한 계획서 한글 파일(HWPX) 하나를 Claude에게 주고 "이 파일로 우리 학교 빈 양식을 만들어 주세요"라고 부탁합니다.
Claude가 머리말·교표만 남기고 나머지 내용을 지운 양식을 만들어 보여 드립니다. 예전 내용이 남지 않았는지 함께 확인해 주세요.
칠서초 양식 말고는 아직 시험 단계입니다. 처음 몇 번은 결과를 한글에서 꼭 열어 보세요.

## 꼭 알아 두세요

- **결과는 계획안입니다.** 예산은 예상액이고, 결재·발송·정산은 선생님이 직접 하십니다.
- **한글에서 꼭 열어 보세요.** 도구의 검사는 파일 구조와 숫자를 봅니다. 쪽 나눔·줄 바꿈은 한글에서 마지막으로 확인해 주세요. PDF도 한글에서 저장합니다.
- **학생 개인정보는 넣지 않습니다.** 원고에 학생 이름이나 연락처가 있으면 Claude가 빼고 만든 뒤 알려 드립니다. 명단 표는 빈 칸으로 만듭니다.
- **한글에서 고친 파일이 있으면 그 파일을 주세요.** Claude가 처음부터 다시 만들지 않고, 고치신 파일에 필요한 곳만 손봅니다(kordoc 필요).
- 학운위 심의용·교육청 제출용 양식은 아직 지원하지 않습니다.

## 직접 실행하기 (선택)

```bash
python3 -m pip install -r skills/school-plan-hwpx/requirements.txt
python3 skills/school-plan-hwpx/scripts/build.py skills/school-plan-hwpx/examples/sample_reading_week.json -o 결과/예시.hwpx
python3 -m unittest discover -s skills/school-plan-hwpx/tests
```

입력 형식은 [references/input-format.md](skills/school-plan-hwpx/references/input-format.md)를 봅니다.
