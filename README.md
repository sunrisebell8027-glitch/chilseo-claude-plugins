# 칠서초 Claude 플러그인 묶음

칠서초등학교 선생님들이 Claude로 계획서·기안문·가정통신문·사업 보드·수업용 웹 앱을 만들 수 있게 묶은 도구입니다.
생성형 AI를 처음 쓰시는 분도 아래 순서대로 따라 하시면 됩니다. 이 저장소 주소 하나면 됩니다.

## 5분 만에 시작하기 (Claude Code)

Claude Code는 Claude 데스크톱 앱의 **Code 탭**이나 터미널에서 씁니다.

1. **Claude Code를 준비합니다.** [Claude 데스크톱 앱](https://claude.ai/download)을 설치하고 Code 탭을 엽니다. 터미널로 쓰려면 [설치 안내](https://code.claude.com/docs/en/install)를 따릅니다. Windows에서는 [Git for Windows](https://git-scm.com/download/win)도 설치합니다. 플러그인을 받아 오는 데 필요합니다.
2. **입력창에 두 줄을 차례로 넣습니다.**
   ```
   /plugin marketplace add sunrisebell8027-glitch/chilseo-claude-plugins
   /plugin install chilseo-docs@chilseo-plugins
   ```
   수업용 웹 앱도 만들 거면 `/plugin install chilseo-writing@chilseo-plugins`를 더 넣습니다.
   한글 파일 미리보기 도구(kordoc)를 켤지 물으면 허용해도 됩니다. Node.js가 있어야 움직이고, 없어도 문서 만들기는 됩니다.
3. **Claude Code를 다시 시작합니다.**
4. **"처음이에요. 시작하기 도와주세요."라고 말합니다.** Claude가 준비물(Python 등)을 확인해 없는 것을 설치하고, 학교 이름과 결재선을 한 번 묻고, 무엇을 부탁할 수 있는지 보여 줍니다. 이름·전화번호는 선생님 컴퓨터의 `학교설정.json`에만 저장하고 어디에도 올리지 않습니다.
5. **첫 부탁을 합니다.** 예: "3학년 박물관 체험학습 가정통신문을 만들어 주세요. 참가 동의서도 붙여 주세요."

터미널에서 바로 하려면 아래 두 줄을 차례로 실행합니다.

```bash
claude plugin marketplace add sunrisebell8027-glitch/chilseo-claude-plugins
```

```bash
claude plugin install chilseo-docs@chilseo-plugins
```

## 무엇을 할 수 있나요?

| 이렇게 말하면 | 만들어 드리는 것 | 플러그인 |
|---|---|---|
| "○○ 운영 계획서를 학교 양식 한글 파일로 만들어 주세요" | 내부결재용 계획서(HWPX), 예산·요일 검산 | [chilseo-docs](plugins/chilseo-docs/README.md) |
| "○○ 지출 품의 기안문을 만들어 주세요" | 에듀파인에 붙여 넣을 제목·본문, 예산 장부, 검산 결과 | chilseo-docs |
| "○학년 ○○ 체험학습 가정통신문을 만들어 주세요" | 학교 양식 가정통신문(HWPX)과 보호자용 미리보기 | chilseo-docs |
| "○○ 사업 보드를 만들어 주세요. 무엇부터 해야 해요?" | 필요한 문서와 지금 할 일·다음 할 일이 담긴 보드 | chilseo-docs |
| "처음이에요. 시작하기 도와주세요." | 준비물 확인·설치, 학교 설정 저장, 할 수 있는 일 안내 | chilseo-docs |
| "우리 반 ○○ 웹 앱을 만들어 주세요" | 보기 좋고 문구가 쉬운 수업용 웹 앱(토스·KRDS 공개 원칙 참고) | [chilseo-writing](plugins/chilseo-writing/README.md) |
| "이 한글 파일을 읽고 고쳐 주세요" | HWP·HWPX 읽기·채우기·고치기·미리보기 | kordoc (다른 분이 만든 도구) |

## 첫 부탁 예시

- "노션에 쓴 이 계획서를 학교 내부결재 양식 한글 파일로 만들어 주세요: (노션 페이지 주소)"
- "아래 원고로 2026. 겨울 독서 주간 운영 계획(안) 한글 파일을 만들어 주세요. 예산 합계도 검산해 주세요. (원고 붙여 넣기)"
- "아래 내용으로 지출 품의 기안문을 만들어 주세요. 산출식과 합계도 검산해 주세요. (내용 붙여 넣기)"
- "3학년 박물관 체험학습 가정통신문을 만들어 주세요. 참가 동의서도 붙여 주세요."
- "과학 탐구 동아리 사업 보드를 만들어 주세요. 무엇부터 해야 할지 알려 주세요."
- "우리 반 아침 활동 타이머 웹 앱을 만들어 주세요. 버튼 문구는 토스처럼 쉽게 써 주세요."
- "보호자용 체험학습 신청 화면을 KRDS 디자인으로 만들어 주세요."

## 쓰실 때 꼭 지켜 주세요

- **학생 이름·연락처·상담 내용은 Claude에 넣지 않습니다.** 명단이 필요한 표는 빈 칸으로 만들고, 학교에서 직접 채웁니다.
- **공문 원문을 통째로 붙여 넣지 않습니다.** 근거에는 기관·문서번호·날짜·제목만 씁니다.
- **만든 한글 파일은 꼭 한글에서 열어 확인합니다.** 도구가 예산·요일·빈칸을 검사하지만, 쪽 나눔과 내용은 선생님이 마지막으로 봐 주셔야 합니다.
- **AI가 지어낸 값이 없는지 봅니다.** 이 도구는 원고에 없는 값을 채우지 않고 묻도록 만들었습니다. 그래도 낯선 숫자나 날짜가 보이면 원고와 대조해 주세요.

## 막혔을 때

| 이런 일이 생기면 | 이렇게 합니다 |
|---|---|
| `/plugin` 명령을 모른다고 나옵니다 | Claude Code를 최신으로 올립니다. 터미널에서 `claude update`를 실행합니다. |
| 설치했는데 스킬이 반응하지 않습니다 | Claude Code를 다시 시작합니다. `/plugin list`에 `chilseo-docs`가 보이는지 확인하고, 부탁에 "가정통신문", "계획서"처럼 문서 이름을 넣습니다. |
| Python이 없다고 합니다 | "시작하기 도와주세요"라고 말하면 Claude가 설치 방법을 안내합니다. Windows는 설치 첫 화면에서 **Add python.exe to PATH**를 켭니다. |
| `externally-managed-environment` 오류가 납니다 | 정상입니다. 시작하기가 선생님 홈 폴더(`~/.chilseo`)에 따로 설치합니다. |
| 한글 미리보기(kordoc)가 보이지 않습니다 | [Node.js LTS](https://nodejs.org)를 설치하고 Claude Code를 다시 시작합니다. 없어도 문서 만들기는 됩니다. |
| 만든 한글 파일이 열리지 않습니다 | HWPX 형식을 여는 한글이 필요합니다. 오래된 한글은 열지 못할 수 있습니다. 그래도 안 되면 파일과 함께 알려 주세요. |

## Claude 앱(채팅 화면)에서 쓰기

Claude Code 대신 Claude 앱(웹·데스크톱의 채팅 화면)을 쓰신다면 스킬 파일(zip)을 올려서 씁니다.

1. **zip 파일을 받습니다.** 저장소의 [Releases](https://github.com/sunrisebell8027-glitch/chilseo-claude-plugins/releases)에서 필요한 스킬 zip을 받습니다. 압축은 풀지 않습니다.
   - 계획서 만들기: `school-plan-hwpx.zip`
   - 기안문 만들기: `school-gongmun-draft.zip`
   - 가정통신문 만들기: `school-newsletter.zip`
   - 사업 보드(필요한 문서와 할 일 순서): `school-project-board.zip`
   - 웹 앱 만들기: `toss-writing.zip`, `toss-design.zip`, `krds-design.zip`, `web-assets.zip`
   - 시작하기(`school-start`)는 Claude Code 전용이라 zip이 없습니다.
2. **Claude 설정에서 올립니다.** Claude 왼쪽 아래 이름 → **설정** → **기능(Capabilities)** 으로 갑니다. **코드 실행 및 파일 만들기**를 켠 뒤, **스킬(Skills)** 에서 **스킬 업로드**를 눌러 zip을 하나씩 올립니다.
3. **새 대화에서 부탁합니다.** 위 "첫 부탁 예시"처럼 말하면 Claude가 알맞은 스킬을 알아서 씁니다.

화면 이름은 Claude 업데이트에 따라 조금 다를 수 있습니다. "스킬"이나 "Skills"를 찾으시면 됩니다.

## 함께 설치하면 좋은 것

다른 분이 만든 도구입니다. 이 저장소에는 넣지 않았고, 각 저장소의 안내를 따라 설치합니다.

- [kordoc](https://github.com/chrisryugj/kordoc) (MIT): 한글 문서 읽기·채우기·고치기·렌더. 위 묶음에서 바로 설치할 수 있습니다.
- [humanize-korean (im-not-ai)](https://github.com/epoko77-ai/im-not-ai) (MIT): AI가 쓴 한글 글을 자연스럽게 다듬습니다. Claude Code에서 `/plugin marketplace add epoko77-ai/im-not-ai`로 등록합니다.
- [superpowers](https://github.com/obra/superpowers-marketplace) (MIT): Claude Code에서 계획·검증 습관을 도와줍니다. `/plugin marketplace add obra/superpowers-marketplace`로 등록합니다.

## 저장소 구성

```
.claude-plugin/marketplace.json   플러그인 목록
plugins/chilseo-docs/             시작하기, 학교 계획서·기안문·가정통신문·사업 보드 스킬
plugins/chilseo-writing/          디자인·문구 스킬 4종
tools/make_skill_zips.py          Claude 앱용 스킬 zip 만들기
.github/workflows/ci.yml          밀어 넣을 때마다 시험, v* 태그에 zip을 Releases에 올림
dist/                             만든 zip (저장소에는 올리지 않음)
```

Claude 앱용 zip을 직접 만들려면 `python3 tools/make_skill_zips.py`를 실행합니다.

## 라이선스

선생님들이 만든 스킬·코드·문서는 [MIT](LICENSE)입니다. 학교 양식 파일(머리말·교표)은 MIT에 포함되지 않습니다. 자세한 내용은 [NOTICE.md](NOTICE.md)를 봅니다.
