# 칠서초 Claude 플러그인 묶음

칠서초등학교 선생님들이 Claude에서 바로 가져다 쓸 수 있게 묶은 도구입니다.
생성형 AI를 처음 쓰시는 분도 아래 순서대로 따라 하시면 됩니다.

| 이름 | 하는 일 | 이럴 때 씁니다 |
|---|---|---|
| [chilseo-writing](plugins/chilseo-writing/README.md) | 웹 앱·수업 도구의 화면 디자인과 문구를 다듬습니다. | 수업용 웹 앱, 가정통신문 신청 화면, 학급 도구를 만들 때 |
| [chilseo-docs](plugins/chilseo-docs/README.md) | 계획서·가정통신문을 학교 양식의 한글(HWPX) 파일로 만들고, 기안문을 에듀파인에 붙여 넣기 좋은 화면으로 보여 줍니다. 예산·요일을 검사합니다. | 운영 계획(안), 지출 품의·결과 보고 기안문, 가정통신문을 만들 때 |
| kordoc (다른 분이 만든 도구) | 한글 파일을 읽고, 빈칸을 채우고, 고치고, 미리 보여 줍니다. | chilseo-docs와 함께 쓰면 좋습니다 |

## 어디서 쓰시나요?

Claude는 두 가지 방법으로 씁니다. 쓰시는 쪽의 설치 방법을 고르세요.

- **Claude 앱(웹·데스크톱의 채팅 화면)**: 대부분의 선생님이 쓰시는 화면입니다. 스킬 파일(zip)을 올려서 씁니다.
- **Claude Code(데스크톱 앱의 Code 탭이나 터미널)**: 플러그인으로 한 번에 설치합니다.

### Claude 앱에서 쓰기 (스킬 zip 올리기)

1. **zip 파일을 받습니다.** 연구부에서 나눠 드린 `dist` 폴더(또는 저장소의 Releases)에서 필요한 스킬 zip을 받습니다. 압축은 풀지 않습니다.
   - 계획서 만들기: `school-plan-hwpx.zip`
   - 기안문 만들기: `school-gongmun-draft.zip`
   - 가정통신문 만들기: `school-newsletter.zip`
   - 웹 앱 만들기: `toss-writing.zip`, `toss-design.zip`, `krds-design.zip`, `web-assets.zip`
2. **Claude 설정에서 올립니다.** Claude 왼쪽 아래 이름 → **설정** → **기능(Capabilities)** 으로 갑니다. **코드 실행 및 파일 만들기**를 켠 뒤, **스킬(Skills)** 에서 **스킬 업로드**를 눌러 zip을 하나씩 올립니다.
3. **새 대화에서 부탁합니다.** 아래 "첫 부탁 예시"처럼 말하면 Claude가 알맞은 스킬을 알아서 씁니다.

화면 이름은 Claude 업데이트에 따라 조금 다를 수 있습니다. "스킬"이나 "Skills"를 찾으시면 됩니다.

### Claude Code에서 쓰기 (플러그인 설치)

1. **묶음을 등록합니다.** Claude Code 입력창에 아래를 그대로 입력합니다.
   ```
   /plugin marketplace add sunrisebell8027-glitch/chilseo-claude-plugins
   ```
   받은 폴더가 있으면 주소 대신 폴더 위치를 씁니다. 예: `/plugin marketplace add ~/Downloads/chilseo-claude-plugins`
2. **필요한 플러그인을 설치합니다.**
   ```
   /plugin install chilseo-docs@chilseo-plugins
   /plugin install chilseo-writing@chilseo-plugins
   ```
   한글 파일을 미리 보고 고치는 기능까지 쓰려면 `/plugin install kordoc@chilseo-plugins`도 설치합니다.
3. **Claude Code를 다시 시작합니다.** 다시 열면 스킬이 목록에 나타납니다.

## 첫 부탁 예시

- "노션에 쓴 이 계획서를 학교 내부결재 양식 한글 파일로 만들어 주세요: (노션 페이지 주소)"
- "아래 원고로 2026. 겨울 독서 주간 운영 계획(안) 한글 파일을 만들어 주세요. 예산 합계도 검산해 주세요. (원고 붙여 넣기)"
- "아래 내용으로 지출 품의 기안문을 만들어 주세요. 산출식과 합계도 검산해 주세요. (내용 붙여 넣기)"
- "3학년 박물관 체험학습 가정통신문을 만들어 주세요. 참가 동의서도 붙여 주세요."
- "우리 반 아침 활동 타이머 웹 앱을 만들어 주세요. 버튼 문구는 토스처럼 쉽게 써 주세요."
- "보호자용 체험학습 신청 화면을 KRDS 디자인으로 만들어 주세요."

## 쓰실 때 꼭 지켜 주세요

- **학생 이름·연락처·상담 내용은 Claude에 넣지 않습니다.** 명단이 필요한 표는 빈 칸으로 만들고, 학교에서 직접 채웁니다.
- **공문 원문을 통째로 붙여 넣지 않습니다.** 근거에는 기관·문서번호·날짜·제목만 씁니다.
- **만든 한글 파일은 꼭 한글에서 열어 확인합니다.** 도구가 예산·요일·빈칸을 검사하지만, 쪽 나눔과 내용은 선생님이 마지막으로 봐 주셔야 합니다.
- **AI가 지어낸 값이 없는지 봅니다.** 이 도구는 원고에 없는 값을 채우지 않고 묻도록 만들었습니다. 그래도 낯선 숫자나 날짜가 보이면 원고와 대조해 주세요.

## 함께 설치하면 좋은 것

다른 분이 만든 도구입니다. 이 저장소에는 넣지 않았고, 각 저장소의 안내를 따라 설치합니다.

- [kordoc](https://github.com/chrisryugj/kordoc) (MIT): 한글 문서 읽기·채우기·고치기·렌더. 위 묶음에서 바로 설치할 수 있습니다.
- [humanize-korean (im-not-ai)](https://github.com/epoko77-ai/im-not-ai) (MIT): AI가 쓴 한글 글을 자연스럽게 다듬습니다. Claude Code에서 `/plugin marketplace add epoko77-ai/im-not-ai`로 등록합니다.
- [superpowers](https://github.com/obra/superpowers-marketplace) (MIT): Claude Code에서 계획·검증 습관을 도와줍니다. `/plugin marketplace add obra/superpowers-marketplace`로 등록합니다.

## 저장소 구성

```
.claude-plugin/marketplace.json   플러그인 목록
plugins/chilseo-writing/          디자인·문구 스킬 4종
plugins/chilseo-docs/             학교 계획서·기안문·가정통신문 스킬
tools/make_skill_zips.py          Claude 앱용 스킬 zip 만들기
dist/                             만든 zip (저장소에는 올리지 않음)
```

Claude 앱용 zip을 다시 만들려면 `python3 tools/make_skill_zips.py`를 실행합니다.

## 라이선스

선생님들이 만든 스킬·코드·문서는 [MIT](LICENSE)입니다. 학교 양식 파일(머리말·교표)은 MIT에 포함되지 않습니다. 자세한 내용은 [NOTICE.md](NOTICE.md)를 봅니다.
