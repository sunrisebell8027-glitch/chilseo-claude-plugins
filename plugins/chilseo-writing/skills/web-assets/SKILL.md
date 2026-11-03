---
name: web-assets
description: 웹 앱에 글꼴·아이콘·CSS·디자인 시스템 파일을 넣을 때 저작권이 확실한 무료 자료를 고르고, 인터넷 없이도 동작하도록 프로젝트 안에 내려받고, 라이선스 파일과 출처 목록(THIRD_PARTY_NOTICES.md)을 함께 만드는 스킬. 사용자가 글꼴, 폰트, 아이콘, 이모지, 이미지, CSS 프레임워크, Pico, Pretendard, Lucide, KRDS 파일, 디자인 에셋, 라이선스, 저작권, 출처 표시, 오프라인 실행, ZIP 제출, CDN을 언급하거나, 웹 앱에 외부 글꼴·아이콘·라이브러리를 넣으려 할 때 따로 요청하지 않아도 반드시 이 스킬을 사용한다. toss-design, krds-design 스킬이 자료가 필요할 때 이 스킬을 쓴다.
---

# 웹 앱 자료(글꼴·아이콘·CSS) 넣기

디자인 스킬(toss-design, krds-design)이 "무엇을 어떻게 디자인할지"를 정한다면, 이 스킬은 "그 디자인에 쓸 파일을 어디서 받아 어떻게 넣을지"를 맡는다. 자료 다루는 방법을 한곳에 모아 두면 디자인 스킬이 바뀌어도 저작권 기준과 받는 방법이 흔들리지 않는다.

이 스킬이 지키는 세 가지:

1. **저작권이 확실한 자료만 쓴다.** 공모전 출품작은 제3자 저작물을 침해하면 안 된다.
2. **인터넷 없이 동작하게 한다.** 심사위원은 ZIP 파일만 받아 `index.html`을 연다. 외부 CDN이나 다른 서버의 파일에 기대면 화면이 깨질 수 있다.
3. **출처를 남긴다.** 무엇을 어디서 받았고 라이선스가 무엇인지 앱 안에 적어 둔다.

## 1. 자료 고르기

`references/catalog.md`에서 고른다. 라이선스를 확인한 글꼴, 아이콘, 기본 스타일 CSS 목록과 쓰지 않을 자료 목록이 있다.

고르는 기준:
- 글꼴은 하나. 특별한 이유가 없으면 Pretendard(공공 화면이면 Pretendard GOV).
- 아이콘은 한 세트. 가볍게 쓰려면 Lucide.
- 기본 스타일은 하나만: 일반 앱은 직접 쓴 CSS 또는 Pico CSS, 공공·학교 문서형 화면은 KRDS. 섞지 않는다.

목록에 없는 자료를 쓰려면 먼저 라이선스 파일을 직접 읽고, 상업적 이용·수정·재배포가 허용되는지 확인한 뒤 사용자에게 알린다.

## 2. 프로젝트 안으로 받기

```bash
S="${CLAUDE_SKILL_DIR}/scripts/fetch_assets.py"   # 값이 비면 이 스킬 폴더의 scripts/fetch_assets.py
python3 "$S" <프로젝트 폴더> --pretendard                 # 글꼴
python3 "$S" <프로젝트 폴더> --lucide users,shuffle,timer # 아이콘 (이름은 lucide.dev에서)
python3 "$S" <프로젝트 폴더> --pico                       # 기본 스타일
python3 "$S" <프로젝트 폴더> --krds                       # KRDS 키트 + Pretendard GOV
python3 "$S" <프로젝트 폴더> --list                       # 받은 자료와 크기 보기
```

- 파일은 `<프로젝트>/assets/vendor/<자료>/`에 들어가고, 라이선스 원문도 같은 폴더에 들어간다.
- 프로젝트 맨 위에 `THIRD_PARTY_NOTICES.md`(출처 목록)가 생기거나 내용이 더해진다.
- `--krds`는 KRDS CSS 안의 아이콘 주소(원래 krds.go.kr 서버를 가리킴)를 받은 파일 경로로 바꾼다. 그대로 쓰면 인터넷이 없을 때 아이콘이 모두 사라진다.

## 3. HTML에 연결하기

상대 경로로 연결한다. `/assets/...`처럼 `/`로 시작하면 `file://`로 열 때 깨진다.

```html
<link rel="stylesheet" href="assets/vendor/pretendard/font.css">
<link rel="stylesheet" href="assets/vendor/pico/pico.min.css">
<link rel="stylesheet" href="style.css">
```

아이콘은 SVG 파일 내용을 HTML에 붙여 넣는 방법을 우선한다. 색을 CSS로 바꿀 수 있고 파일을 따로 불러오지 않아도 된다. 아이콘만 있는 버튼에는 `aria-label`을 붙인다.

```html
<button type="button" aria-label="다시 섞기"><svg ...>...</svg></button>
```

## 4. 마무리 점검

- [ ] HTML·CSS·JS에 `http://`, `https://`, `//cdn`으로 시작하는 외부 주소가 남아 있지 않은가? (`grep -rnE "https?://|//cdn" --include=*.html --include=*.css --include=*.js .`로 확인. 링크로 보여 주는 주소는 괜찮다)
- [ ] 인터넷을 끄고 `index.html`을 더블클릭해 열었을 때 글꼴·아이콘이 제대로 보이는가?
- [ ] `THIRD_PARTY_NOTICES.md`에 쓴 자료가 모두 있는가? 쓰지 않게 된 자료는 파일과 목록에서 함께 지웠는가?
- [ ] 공모전 "사용 방법 안내 PDF"나 README에 출처 목록을 옮겨 적었는가? KRDS를 썼다면 출처(행정안전부, KRDS, https://www.krds.go.kr)를 꼭 적는다.
- [ ] ZIP 용량이 지나치게 크지 않은가? 쓰지 않는 굵기의 글꼴, 쓰지 않는 CSS 파일(예: Pico를 클래스 없이 쓰면 `pico.min.css`는 지워도 된다)을 정리한다.
