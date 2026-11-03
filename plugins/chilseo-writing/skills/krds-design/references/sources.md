# 근거 자료 (2026-10-07 확인)

## 공식 자료

- KRDS 누리집: https://www.krds.go.kr
  - 디자인 원칙, 디자인 스타일(색상·타이포그래피·형태·레이아웃·아이콘·엘리베이션·선명한 화면 모드·디자인 토큰), 컴포넌트, 기본 패턴, 서비스 패턴, 디지털 포용
  - 누리집 본문은 자바스크립트로 그려져서 `curl`로는 내용이 안 보인다. 브라우저로 연다.
- KRDS 저작권 정책: https://www.krds.go.kr/html/site/utility/utility_06.html
  - 저작권법 제24조의2(공공저작물의 자유이용)에 따라, KRDS가 지식재산권 전부를 가진 자료(디자인, 코드, 문서 등)는 **출처를 표기하면 별도 허락 없이 이용**할 수 있다.
- KRDS HTML 컴포넌트 키트: https://github.com/KRDS-uiux/krds-uiux (npm 패키지 `krds-uiux`, 2026-10 기준 1.1.0)
  - `resources/cdn/krds.min.css`, `krds.min.js`: 전체 묶음
  - `resources/css/token/krds_tokens.css`, `tokens/*.json`: 디자인 토큰
  - `resources/img/component/icon/`: 아이콘
  - `html/code/`: 컴포넌트 예제 (`components.md` 참고)
  - 저장소에 별도 라이선스 파일은 없고, README에 "KRDS 이용약관을 따름"이라고 적혀 있다.
- Pretendard GOV 글꼴: https://github.com/orioncactus/pretendard (SIL OFL 1.1)

## 2026-10-07에 직접 확인한 구현 사실

- `krds.min.css`가 아이콘 350곳을 `https://www.krds.go.kr/resources/img/component/icon/...` 절대 주소로 불러온다(서로 다른 아이콘 76개). 인터넷이 없으면 아이콘이 보이지 않는다. web-assets 스크립트가 로컬 경로로 바꾼다.
- `krds.min.css`는 `html { font-size: 62.5% }`를 쓴다(1rem = 10px).
- `krds.min.css` 안에 Pretendard GOV의 `@font-face` 선언이 없다. 글꼴 파일과 선언을 따로 넣어야 한다. web-assets 스크립트가 `pretendard-gov/font.css`를 만든다.

## 해설 자료

- 디자인 나침반, "KRDS: 대한민국 정부 디자인 시스템": https://designcompass.org/2024/04/17/krds/
- 디자인 나침반, "대한민국 정부 UI/UX 디자인 시스템 개시": https://designcompass.org/2025/01/22/krds-start/
