# chilseo-docs: 학교 문서 만들기

계획서·기안문·가정통신문을 학교 양식에 맞게 만들고, 사업 하나의 문서와 할 일 순서를 보드로 정리하는 스킬 네 가지에, 처음 쓸 때 길을 잡아 주는 시작하기 스킬을 더한 묶음입니다.
만든 뒤에는 숫자와 날짜를 스스로 검사하고, 틀린 곳이 있으면 무엇이 틀렸는지 알려 드립니다.

| 스킬 | 만드는 것 | 검사하는 것 |
|---|---|---|
| `school-start` | 처음 쓸 때: 준비물 확인·설치, 학교 설정(`학교설정.json`) 저장, 할 수 있는 일 안내 | Python, 패키지(lxml·python-hwpx), Node.js가 있는지 |
| `school-plan-hwpx` | 계획서 원고 → 학교 내부결재 양식의 한글(HWPX) 파일 | 예산 산출식·합계, 요일, 시간표 학급 중복, 빈자리, 근거·목적·예산 절 |
| `school-gongmun-draft` | 기안문 → 종이 모양 화면(제목·본문 복사 버튼, 예산 장부, 검사 결과) | 본문 체계, 관련 문서번호, 곱셈 검산, 합계, 금액 한글 표기, 요일, 편성액, 붙임 |
| `school-newsletter` | 가정통신문 → 학교 양식의 한글 파일 + 보호자용 미리보기 화면 | 요일, 회신 기한, 빈자리, 개인정보 수집 문구를 넣을지 |
| `school-project-board` | 사업 하나 → 한 장의 보드(필요한 문서, 지금 할 일과 다음 할 일, 부탁 문구, 예산 장부, 일정) | 품의 금액과 장부 합계, 편성액, 요일, 결재를 마친 문서의 문서번호, 지난 기한, 필요한 문서가 빠졌는지 |

## 들어 있는 것

| 이름 | 내용 |
|---|---|
| 스킬 5개 | 위 표와 같습니다. |
| 칠서초 계획서·가정통신문 양식 | 학교 표어·제목 상자·교표만 남긴 빈 양식입니다. 예전 문서 내용은 모두 지웠습니다. |
| 기안문·미리보기 화면 틀 | 어느 선생님이 만들어도 같은 모양이 나오게 하는 HTML 틀입니다. |
| kordoc 연결 | Claude Code에서는 한글 파일 미리 보기·고치기 도구(kordoc)를 함께 켭니다. Node.js가 있어야 합니다. 없어도 문서 만들기는 됩니다. |

## 설치

**Claude Code**

1. `/plugin marketplace add sunrisebell8027-glitch/chilseo-claude-plugins`
2. `/plugin install chilseo-docs@chilseo-plugins`
3. Claude Code를 다시 시작합니다.
4. "처음이에요. 시작하기 도와주세요."라고 말합니다. Claude가 Python과 패키지를 확인해 없는 것을 선생님 홈 폴더(`~/.chilseo`)에 설치하고, 학교 이름과 결재선을 한 번 묻고, 첫 부탁 예시를 보여 줍니다.

**Claude 앱(채팅 화면)**

1. 저장소 [Releases](https://github.com/sunrisebell8027-glitch/chilseo-claude-plugins/releases)에서 zip을 받습니다(압축을 풀지 않습니다): `school-plan-hwpx.zip`, `school-gongmun-draft.zip`, `school-newsletter.zip`, `school-project-board.zip`
2. 설정 → 기능(Capabilities)에서 **코드 실행 및 파일 만들기**를 켜고, **스킬(Skills)** → **스킬 업로드**로 zip을 하나씩 올립니다.
3. 노션 원고를 쓰신다면 설정 → 커넥터에서 **Notion**을 연결합니다. 원고를 대화에 붙여 넣어도 됩니다.

`school-start`는 Claude Code 전용이라 zip이 없습니다. Claude 앱에서는 각 스킬이 처음 쓸 때 필요한 것을 직접 묻습니다.

## 첫 부탁 예시

**처음 쓸 때**

> 처음이에요. 시작하기 도와주세요.

**계획서**

> 노션에 쓴 이 계획서를 학교 내부결재 양식 한글 파일로 만들어 주세요: (노션 페이지 주소)

> 아래 원고로 운영 계획(안) 한글 파일을 만들어 주세요. 모르는 값은 채우지 말고 먼저 물어봐 주세요.
> (원고 붙여 넣기)

**기안문**

> 아래 내용으로 지출 품의 기안문 화면을 만들어 주세요. 산출식과 합계, 금액 한글 표기도 검산해 주세요.
> 제목: 2026. 과학 탐구 동아리 실험 재료 구입비 지출 건의 / 관련: (결재한 계획서 문서번호와 날짜) / 산출: 비커 세트 10,000원 12모둠

> 운영 결과 보고 공문 본문을 써 주세요. 관련 문서번호를 모르면 지어내지 말고 [확인 필요]로 남겨 주세요.

**가정통신문**

> 3학년 박물관 체험학습 가정통신문을 만들어 주세요. 2026. 12. 9.(수) 9시부터 3시까지, 준비물은 도시락·물·편한 신발이고, 참가 동의서는 12. 2.(수)까지 받아요.

> 학예회 안내 가정통신문을 만들어 주세요. 회신서는 필요 없어요. 보호자가 휴대폰으로 볼 미리보기도 보여 주세요.

**사업 보드**

> 과학 탐구 동아리 사업 보드를 만들어 주세요. 무엇부터 해야 할지 알려 주세요.

Claude가 작년 계획서, 예산, 목적사업비, 학교 밖 활동, 보호자 회신, 외부 강사, 결과 보고를 하나씩 묻고, 필요한 문서를 순서대로 놓은 보드를 만들어 줍니다. 결재를 마치면 "결재 끝났어요, 문서번호는 ○○예요"라고 알려 주세요. 보드를 고치고 다음 할 일을 알려 드립니다.

## 학교 설정은 한 번만

학교 이름, 양식, 기안문 결재선, 학교 대표 전화는 `학교설정.json` 한 파일에 모읍니다. 시작하기가 만들고, 네 스킬이 같은 파일을 읽습니다. 작업 폴더에 두거나, 여러 폴더에서 쓰려면 `~/.chilseo/학교설정.json`에 둡니다.
이름·전화번호는 이 파일에만 있고, 스킬 폴더나 이 저장소에는 넣지 않습니다.

## 다른 학교에서 쓰려면

- **계획서**: 예전에 결재한 계획서 한글 파일(HWPX) 하나를 Claude에게 주고 "이 파일로 우리 학교 빈 양식을 만들어 주세요"라고 부탁합니다.
- **가정통신문**: 예전에 보낸 가정통신문 한글 파일을 주면 Claude가 kordoc으로 그 파일의 서식을 살려 내용만 바꿉니다.
- **기안문**: 학교 이름과 결재선만 알려 주시면 됩니다.

칠서초 양식 말고는 아직 시험 단계입니다. 처음 몇 번은 결과를 한글에서 꼭 열어 보세요.

## 꼭 알아 두세요

- **결과는 초안입니다.** 예산은 예상액이고, 결재·발송·정산은 선생님이 직접 하십니다.
- **지어낸 값은 넣지 않습니다.** 원고에 없는 문서번호·날짜·장소는 `[확인 필요]`로 남깁니다. 화면에서 노란색으로 표시되니 상정·발송 전에 채워 주세요.
- **한글에서 꼭 열어 보세요.** 쪽 나눔·줄 바꿈은 한글에서 마지막으로 확인해 주세요. PDF도 한글에서 저장합니다.
- **학생 개인정보는 넣지 않습니다.** 원고에 학생 이름이나 연락처가 있으면 Claude가 빼고 만든 뒤 알려 드립니다.
- **동의서가 붙은 가정통신문은** 보호자 이름과 서명을 받습니다. 개인정보 수집·이용 안내를 넣을지 Claude가 여쭙니다. 학교 개인정보 담당자와 정해 주세요.
- **기안문 검사 번호(V1, V2-1 등)는** 예전에 쓰던 검사 화면에서 거꾸로 정리한 것입니다. 원본 규칙을 찾으면 맞춰 고칠 예정입니다.
- 학운위 심의용·교육청 제출용 양식, 표가 많은 통신문(식단표 등)은 아직 지원하지 않습니다.

## 직접 실행하기 (선택)

계획서·가정통신문 스크립트는 `lxml`과 `python-hwpx`가 필요합니다. 시작하기 스킬이 만든 `~/.chilseo/venv`가 있으면 스크립트가 알아서 씁니다. 없으면 먼저 설치합니다. `pip install`이 막히면(`externally-managed-environment`) 가상환경을 만들고 그 안의 python으로 실행합니다.

```bash
python3 -m pip install -r skills/school-plan-hwpx/requirements.txt
python3 skills/school-plan-hwpx/scripts/build.py skills/school-plan-hwpx/examples/sample_reading_week.json -o 결과/계획서.hwpx
python3 skills/school-gongmun-draft/scripts/build_gongmun.py skills/school-gongmun-draft/examples/sample_science_club.json -o 결과/기안문.html
python3 skills/school-newsletter/scripts/build_newsletter.py skills/school-newsletter/examples/sample_museum_trip.json -o 결과/가정통신문.hwpx --preview 결과/미리보기.html
python3 skills/school-project-board/scripts/build_board.py skills/school-project-board/examples/sample_science_club_board.json -o 결과/보드.html
for s in skills/*/; do python3 -m unittest discover -s "$s/tests"; done
```

입력 형식은 각 스킬의 `references/input-format.md`를 봅니다.
