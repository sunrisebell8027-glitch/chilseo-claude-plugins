# 자료 목록: 저작권 걱정 없이 쓸 수 있는 글꼴·아이콘·CSS

2026-10-07에 각 저장소의 라이선스 파일을 직접 확인했다. 쓰기 전에 최신 라이선스를 다시 확인한다.
`fetch_assets.py` 옵션이 있는 자료는 스크립트로 받으면 라이선스 파일과 출처 목록이 자동으로 함께 생긴다.

## 글꼴

| 이름 | 라이선스 | 특징 | 스크립트 옵션 |
|---|---|---|---|
| Pretendard | SIL OFL 1.1 | 화면용 한글 글꼴로 가장 많이 쓰인다. 숫자·영문이 깔끔하다 | `--pretendard` |
| Pretendard GOV | SIL OFL 1.1 | KRDS 기본 글꼴. Pretendard의 공공 서비스용 판 | `--krds`에 포함 |
| SUIT | SIL OFL 1.1 | 조금 더 둥글고 부드럽다. https://github.com/sun-typeface/SUIT | 직접 받기 |
| Noto Sans KR | SIL OFL 1.1 | 구글 글꼴. 파일이 크다 | 직접 받기 |

- SIL OFL은 무료로 쓰고 함께 배포할 수 있다. 글꼴 파일만 따로 파는 것은 안 된다. 라이선스 파일을 함께 넣는다.
- 스크립트는 쓰는 글자만 남긴 subset 파일(굵기별 약 250KB)을 받는다.
- 글꼴 파일을 넣지 않으려면 시스템 글꼴을 쓴다. 인터넷 없이도 동작한다:

```css
font-family: "Pretendard", -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo",
             "Malgun Gothic", "맑은 고딕", "Noto Sans KR", sans-serif;
```

## 아이콘

| 이름 | 라이선스 | 특징 | 스크립트 옵션 |
|---|---|---|---|
| Lucide | ISC | 선 아이콘 1,000개 이상. 깔끔하고 가볍다. 이름은 https://lucide.dev 에서 찾는다 | `--lucide users,shuffle` |
| Tabler Icons | MIT | 선 아이콘 5,000개 이상. 이름은 https://tabler.io/icons | `--tabler users,dice` |
| Phosphor | MIT | 굵기 6가지. https://phosphoricons.com | 직접 받기 |
| KRDS 아이콘 | KRDS 저작권 정책(출처 표시) | 공공 서비스용. KRDS 컴포넌트와 함께 쓴다 | `--krds`에 포함 |

- 한 앱에는 한 세트만 쓴다. 섞으면 선 굵기와 모양이 달라 어수선해 보인다.
- 필요한 아이콘만 SVG로 받아 쓴다. HTML에 직접 붙여 넣으면 `currentColor`로 글자색을 따라가게 할 수 있다.

## 기본 스타일 CSS

| 이름 | 라이선스 | 특징 | 스크립트 옵션 |
|---|---|---|---|
| Pico CSS | MIT | CSS 파일 하나만 연결하면 기본 HTML 태그가 깔끔해진다. 빌드 과정이 없어 `index.html` 하나로 내는 앱에 잘 맞는다 | `--pico` |
| KRDS HTML 컴포넌트 키트 | KRDS 저작권 정책(출처 표시) | 정부 서비스 표준 컴포넌트. 공공·학교 문서형 화면에 맞는다. 사용법은 krds-design 스킬 | `--krds` |

- 두 CSS를 한 앱에 섞지 않는다. KRDS는 `html` 글자 크기를 62.5%(1rem=10px)로 바꿔서 다른 CSS의 크기가 모두 작아진다.
- shadcn/ui, Tailwind CSS(둘 다 MIT)도 많이 쓰지만 빌드 과정이 필요하다. 빌드 결과물을 ZIP에 넣을 수 있을 때만 쓴다.

## 이모지

- 기기에 들어 있는 기본 이모지를 그대로 쓰면 가장 안전하다(기기마다 모양은 다르다).
- 토스페이스는 쓰지 않는다. 자체 라이선스가 있고, 토스 고유의 시각 자산이다.

## 쓰지 않는 것

- 토스 디자인 시스템(TDS) UI Kit·컴포넌트·스타일, 토스 아이콘·이모지·3D 그래픽, Toss Product Sans, 토스 브랜드 색: 앱인토스 밖 사용 금지
- 출처를 모르는 인터넷 이미지, 캐릭터(뽀로로, 포켓몬 등), 연예인 사진
- AI로 만든 이미지는 쓸 수 있지만, 쓴 도구의 이용 약관(상업적 이용, 저작권 귀속)을 확인하고 안내 문서에 "AI로 생성"이라고 밝힌다.
