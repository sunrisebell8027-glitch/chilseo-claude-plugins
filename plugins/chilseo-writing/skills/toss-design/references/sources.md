# 근거 자료

이 스킬은 토스가 공개한 자료를 참고해 만든 **비공식** 가이드다. 토스(비바리퍼블리카)와 관계없다. 토스의 원칙만 빌리고, 시각 자산은 쓰지 않는다.

## 공식 자료 (2026-10-07 확인)

- **앱인토스 UI/UX 가이드**: 그래픽 사용 원칙 7가지, 직접 그래픽을 만들 때 유의사항, 다크패턴 방지 정책
  https://developers-apps-in-toss.toss.im/design/consumer-ux-guide
  (마크다운 원문: 주소 끝에 `.md`를 붙인다)
- **피그마/TDS Mobile UI Kit 라이선스**: 앱인토스용 앱 밖에서 UI Kit와 그 구성요소(컴포넌트, 스타일)를 사용·복사·수정·재배포하는 것을 금지한다. 이 스킬이 토스 모양을 따라 하지 않는 이유다.
  https://developers-apps-in-toss.toss.im/design/prepare/figma-ui-license
- 문서 목록(주소가 바뀌었을 때): https://developers-apps-in-toss.toss.im/llms.txt

## 토스 기술 블로그 (toss.tech) 디자인 글

흐름 설계(A)의 원칙은 아래 글들에서 반복되는 생각을 정리한 것이다.

- 업무 효율화, 작은 단계부터 다시 보기: 행동 단위로 쪼개고 이유를 묻기
- Value first, Cost later / Easy to answer / 추천은 제일 좋은 것 하나: 덜 고민하게 만들기
- 디자이너가 시안 대신 앱을 만든 이유 (https://toss.tech/article/deadend): 경험이 끝난 뒤를 설계하기
- 시각장애인에게 읽는 순서가 왜 중요할까 / 시각 정보를 소리로 번역하는 법: 접근성은 실제로 혼자 끝낼 수 있는지의 문제
- 토스에서 가장 안 좋은 경험 만들기 (https://toss.tech/article/42221): 예상하지 못한 방해 줄이기

## 참고한 커뮤니티 스킬

- Ilbie/Toss-Design-Skill (MIT): toss.tech 디자인 글 129개 요약. 행동 단위 분해, 유지·삭제·자동화·보조 분류 아이디어를 참고했다. 내용을 그대로 복사하지 않고 교실 앱에 맞게 새로 썼다.
  https://github.com/Ilbie/Toss-Design-Skill
- elayadesign/ai-design-skills의 `landing-page-design` (MIT, © 2026 Elaya): 모서리 안의 모서리 공식, 줄바꿈(`text-wrap`), `transform`·`opacity`만 움직이기, 누르는 것의 상태, 회색 뼈대 로딩, 막힌 링크·본문 건너뛰기 링크를 참고했다(2026-10-30). 글꼴·아이콘·움직임 길이·홍보 문구·검색 노출 규칙은 교실 앱과 맞지 않아 뺐고, 우리말로 새로 썼다.
  https://github.com/elayadesign/ai-design-skills
