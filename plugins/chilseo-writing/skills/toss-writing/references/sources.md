# 근거 자료

이 스킬은 토스가 공개한 자료를 참고해 만든 **비공식** 가이드다. 토스(비바리퍼블리카)와 관계없다.

## 공식 자료

- **앱인토스 개발자센터 > 디자인 > UI/UX 가이드**
  https://developers-apps-in-toss.toss.im/design/consumer-ux-guide
  - 마크다운 원문: https://developers-apps-in-toss.toss.im/design/consumer-ux-guide.md
  - 담긴 내용: 미니앱 브랜딩, **다크패턴 방지 정책**(5가지), **UX 라이팅**(해요체·능동적 말하기·긍정적 말하기·캐주얼한 경어·명사+명사 쓰지 않기, 예외 규칙), 그래픽, 해상도
  - 예전 주소 `.../design/ux-writing.html`은 2026-10 현재 없는 페이지로 나온다. UX 라이팅 내용이 이 페이지로 합쳐졌다.
  - 확인한 날: 2026-10-07
  - 최신 내용을 확인하려면: `curl -sL https://developers-apps-in-toss.toss.im/design/consumer-ux-guide.md | sed -n '/^### 다크패턴/,/^### 그래픽/p'`
  - 주소가 또 바뀌면 문서 목록 `https://developers-apps-in-toss.toss.im/llms.txt`에서 "UI/UX 가이드"를 찾는다.
- **토스 기술 블로그(toss.tech)의 라이팅 원칙 글**: 말투 5가지(Clear, Concise, Casual, Respect, Emotional)와 8가지 라이팅 원칙의 출처.
- **토스피드, "토스가 금융을 더 쉽게 만드는 또 하나의 방법, UX Writing"**
  https://toss.im/tossfeed/article/uxwriter-interview

## 참고한 커뮤니티 스킬 (모두 MIT 라이선스)

아래 저장소의 구성과 아이디어를 참고했다. 코드와 문서를 그대로 복사하지 않고 이 스킬에 맞게 새로 썼다.

- NariP/toss-ux-writing-skills: 5가지 규칙과 예외를 표로 정리한 방식
  https://github.com/NariP/toss-ux-writing-skills
- Ksanbal/toss-ux-writing-skill: 라이팅과 다크패턴 방지를 함께 다루는 구성
  https://github.com/Ksanbal/toss-ux-writing-skill
- claudianus/toss-ux-writing-skill: 예외 판단 순서, 문구 자동 검사 스크립트 아이디어
  https://github.com/claudianus/toss-ux-writing-skill

## 주의

- 토스의 그래픽, 아이콘, 이모지, 3D 이미지, 글꼴은 비바리퍼블리카의 지식재산이다. 앱인토스 밖에서는 쓸 수 없다. 이 스킬은 **원칙만** 빌려 쓰고, 토스의 그래픽 자산은 앱에 넣지 않는다.
