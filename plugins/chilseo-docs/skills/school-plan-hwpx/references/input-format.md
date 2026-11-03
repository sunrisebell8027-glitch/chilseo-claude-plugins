# 입력 JSON 형식

`scripts/build.py`가 읽는 파일이다. 예시: `examples/sample_reading_week.json`.

## 맨 위 칸

| 칸 | 꼭 | 뜻 |
|---|---|---|
| `title` | ✔ | 제목 상자에 들어갈 제목. `\n`으로 줄을 바꾼다. |
| `pages` | ✔ | 쪽 목록. 각 쪽은 블록 목록이다. 둘째 쪽부터 새 쪽에서 시작한다. |
| `school` | | 학교 이름. 쓰면 양식 머리말의 학교 이름과 같은지 검사한다. |
| `template` | | 양식 파일. 비우면 `templates/chilseo_plan_template.hwpx`. 이름만 쓰면 입력 JSON 옆 → `templates/` 순서로 찾는다. |
| `budget` | | 예산. 쓰면 아래 검사를 하고, 예산 절을 필수로 본다. |
| `slots` | | 교시별 학급. 쓰면 시간표 표와 맞는지 검사한다. |
| `event_date` | | 대표 날짜(`2026-12-08`). 형식만 검사한다. |
| `subject` | | 문서 정보(설명)에 들어갈 한 줄. 비우면 제목 마지막 줄. |
| `doc_date` | | 문서 정보 날짜. 비우면 오늘. |
| `required_sections` | | 꼭 있어야 할 절 이름. 비우면 `근거`, `목적`(+예산이 있으면 `예산`). |
| `source_urls` | | 참고한 원고 주소. 검사 기록(`.validation.json`)에만 남는다. 문서에는 들어가지 않는다. |

## 블록

```json
{"kind": "heading", "text": "1. 근거"}
{"kind": "subheading", "text": "가. 운영 개요"}
{"kind": "text", "text": "가. 운영 기간: 2026. 12. 7.(월) ~ 2026. 12. 11.(금)"}
{"kind": "note", "text": "※ 금액은 예상액이다."}
{"kind": "table", "widths": [3, 5, 3], "align": ["center", "justify", "right"],
 "rows": [["내용", "산출 내역", "금액(원)"], ["…", "…", "…"]]}
```

- 표의 첫 줄은 머리행이다. 모든 줄의 칸 수는 `widths` 길이와 같아야 한다.
- `widths`는 비율이다. 표 전체 너비는 양식 본문 너비로 맞춘다.
- `align`은 열마다 `center`·`justify`·`left`·`right` 가운데 하나. 비우면 모두 가운데. 머리행은 늘 가운데.
- 칸 안 줄 바꿈은 `\n`.

## 예산

```json
"budget": {
  "items": [
    {"name": "작가 초청 강사비", "formula": "300,000원 × 1명 × 1회", "amount": 300000},
    {"name": "독서 활동 재료비", "formula": "2,000원 × 60명", "amount": 120000}
  ],
  "total": 420000
}
```

- `formula`의 숫자를 모두 곱한 값이 `amount`와 같아야 한다. `formula`는 비워도 된다.
- `amount`의 합이 `total`과 같아야 한다.
- 머리행에 `금액`이 들어간 표가 있어야 하고, 그 표에 각 `amount`와 `total`(천 단위 쉼표), 각 `formula`가 그대로 적혀 있어야 한다.
- 예전 형식 `{"unit_price": 5000, "headcount": 106, "total": 530000}`도 받는다(`5,000원 × 106명`으로 본다).

## 시간표

```json
"slots": [
  {"periods": "1·2교시", "classes": ["1-1", "2-1"]},
  {"periods": "3·4교시", "classes": ["4-1"]}
]
```

- 한 학급이 두 번 나오면 막는다.
- 머리행이 `시간`, `학급`으로 시작하는 표가 하나 있어야 하고, 그 표의 앞 두 칸이 `slots` 순서와 같아야 한다.
