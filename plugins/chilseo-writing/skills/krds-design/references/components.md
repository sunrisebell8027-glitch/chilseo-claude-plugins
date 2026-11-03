# KRDS 컴포넌트 예제 목록

공식 저장소(https://github.com/KRDS-uiux/krds-uiux, `main` 브랜치)의 `html/code/` 폴더에 있는 예제 HTML이다. 2026-10-07 기준.

예제 받는 주소:
```
https://raw.githubusercontent.com/KRDS-uiux/krds-uiux/main/html/code/<이름>.html
```
예: `curl -sL https://raw.githubusercontent.com/KRDS-uiux/krds-uiux/main/html/code/step_indicator.html`

각 컴포넌트를 언제 어떻게 써야 하는지(사용 규칙)는 KRDS 누리집 "컴포넌트" 메뉴에 있다: https://www.krds.go.kr/html/site/component/component_summary.html

## 학교 화면에서 자주 쓸 것

| 하고 싶은 일 | 예제 이름 |
|---|---|
| 버튼 (주·보조·약한 버튼) | `button`, `button_hierarchy`, `button_size`, `button_with_icon`, `button_icon`, `button_text` |
| 글자 입력 | `text_input`, `text_input_state`(오류 표시), `text_input_size`, `text_input_icon`, `textarea` |
| 날짜 입력 | `date_input`, `calendar`, `calendar_range` |
| 고르기 | `radio_button`, `radio_chip`, `checkbox`, `checkbox_chip`, `select`, `toggle_switch` |
| 파일 첨부 | `file_upload` |
| 단계 표시 (신청서) | `step_indicator` |
| 확인·안내 창 | `modal`, `modal_sample` |
| 중요한 알림 | `critical_alerts` |
| 도움말 | `contextual_help`, `help_panel`, `tooltip`, `tooltip_box`, `tutorial_panel`, `coach_mark` |
| 목록·표 | `structured_list`, `structured_list_table`, `table`, `text_list`, `text_list_ordered` |
| 접기·펼치기 | `accordion`, `accordion_line`, `disclosure` |
| 탭, 페이지 넘기기 | `tab`, `pagination` |
| 상태 표시 | `badge`, `badge_number`, `tag`, `spinner` |
| 읽어 주기 (TTS) | `tts`, `tts_icon`, `tts_size` |
| 글자 크기 조절 | `resize` |
| 본문 바로가기 (접근성) | `skip_link` |
| 페이지 안 이동 | `in_page_navigation`, `side_navigation`, `breadcrumb` |
| 머리글·바닥글·메뉴 | `header`, `footer`, `main_menu_pc`, `main_menu_mobile` (정부 로고·문구는 학교 정보로 바꾼다) |
| 언어 바꾸기 (다문화 가정) | `language_switcher`, `language_switcher_page` |

## 학교 앱에서 쓰지 않을 것

| 예제 이름 | 이유 |
|---|---|
| `masthead` | "대한민국 공식 전자정부 누리집" 배너. 정부 서비스로 오인된다 |
| `identifier` | 정부 운영기관 식별자 |
| `favicon` | 정부 파비콘 |

## 예제를 쓸 때

- 예제의 자리표시 글자("버튼 : primary", "단계 레이블", "모달 제목", 반복된 설명 문장)를 실제 문구로 바꾼다. 문구는 toss-writing 기준으로 쓴다.
- `aria-*`, `role`, `sr-only`(화면 읽기 프로그램용 숨김 글자) 같은 접근성 속성은 지우지 않는다.
- 모달·탭·아코디언 같은 움직이는 컴포넌트는 `krds.min.js`가 있어야 동작한다.
