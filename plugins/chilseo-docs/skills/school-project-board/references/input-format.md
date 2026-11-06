# 보드 JSON 형식

예시: `examples/sample_science_club_board.json`(모두 지어낸 자료). 날짜는 모두 `YYYY-MM-DD`로 쓴다.

`school`, `project`, `updated`는 꼭 넣는다. `docs`, `ledger`는 생략하면 빈 목록으로 처리한다. `guide`를 생략하면 길잡이 없이 문서 흐름만 만든다. 형식이 틀리거나 허용하지 않는 값을 넣으면 빌더가 고칠 칸을 한국어로 알려 준다.

## 맨 위

| 칸 | 꼭 | 내용 |
|---|---|---|
| `school` | ✔ | 학교 이름 |
| `project` | ✔ | 사업 이름. 부탁 문구의 「」 안에 들어간다 |
| `updated` | ✔ | 마지막으로 고친 날. 지난 기한과 일정의 남은 날을 이 날 기준으로 센다 |
| `period` | | `[시작, 끝]` |
| `owner` | | "담당 교사"처럼 쓴다. 실명은 넣지 않는다 |
| `budget_code` | | 예산과목(에듀파인에서 본 그대로) |
| `example` | | `true`면 "예시 자료" 표시 |
| `look` | | `"blueprint"`면 청사진 모양 |
| `page_title` | | 브라우저 탭 이름. 없으면 "사업 이름 보드" |

`look`은 생략하거나 `blueprint`를 쓴다. `example`은 생략하거나 참·거짓 값으로 쓴다.

## `guide`: 길잡이 답

질문 id를 키로, 고른 답의 값을 적는다. 질문과 답 값은 `scripts/guide.py`의 `QUESTIONS`에 있다.

```json
"guide": {"lastyear": "yes", "budget": "yes", "source": "school", "outside": "yes", "consent": "reply", "external": "no", "report": "no"}
```

답하지 않은 질문은 빼 둔다. 그 질문에 걸린 문서는 "답 기다림"으로 흐리게 보인다.

## `docs`: 문서 흐름

| 칸 | 꼭 | 내용 |
|---|---|---|
| `id` | ✔ | 영문 id |
| `kind` | ✔ | 계획·품의·안내·보고 등 짧은 종류 |
| `title` | ✔ | 문서 제목 |
| `status` | ✔ | `done`(결재 완료) · `review`(결재 중) · `draft`(작성 중) · `todo`(아직) |
| `doc_no` | | 문서번호. `done`이면 있어야 한다(없으면 확인 표시) |
| `date` | | 결재한 날 |
| `due` | | 기한. 지났는데 `done`이 아니면 확인 표시 |
| `need` | | 길잡이 문서 id: `plan` · `newmoney` · `safety` · `letter` · `buy` · `report` |
| `phase` | | `need`가 없는 문서의 단계: `prep` · `notice` · `run` · `close`(없으면 `run`) |
| `draft` | | 기안문. `school-gongmun-draft`의 입력과 같은 형식(`receiver`, `via`, `written`, `related`, `lead`, `items`, `attachments`) |

`status`는 `done`, `review`, `draft`, `todo` 가운데 하나를 쓴다. `need`는 길잡이 문서 id만 쓴다. `phase`는 `need`가 없는 문서에서만 쓰며, `prep`, `notice`, `run`, `close` 가운데 하나를 쓴다. 날짜 칸에는 실제 날짜를 `YYYY-MM-DD`로 쓴다. `id`는 문서마다 달라야 한다.

품의(`buy`)는 돈을 쓸 때마다 한 건씩 넣는다. 모두 `done`이어야 차례에서 마친 것이 된다.

## `ledger`, `amounts`: 예산 장부

```json
"ledger": [{"name": "실험 재료비", "allocated": 200000, "spend": [{"doc": "buy2", "name": "리트머스 종이·비커 세트", "amount": 156000}]}],
"amounts": {"buy1": 180000}
```

- `spend.doc`은 그 돈을 쓰는 품의 문서 id다. 품의가 `done`이면 집행, 아니면 결재 전으로 센다.
- 품의 금액은 기안문의 소요예산에서 읽는다. 기안문이 없는 품의는 `amounts`에 적는다. 품의 금액과 장부 줄의 합이 다르면 화면을 만들지 않는다.
- `allocated`, `spend.amount`, `amounts` 금액은 0 이상의 정수로 쓴다. 장부 줄에서 `spend`를 생략하면 빈 목록으로 처리한다.

## 나머지

- `decide`: 선생님이 정할 것. `[{"text": "…", "doc": "문서 id"}]`(`doc`은 없어도 된다)
- `schedule`: `[{"date": "…", "title": "…"}]`
- `log`: 작업 기록. `[{"date": "…", "text": "…"}]` 최근 4개를 보여 준다
