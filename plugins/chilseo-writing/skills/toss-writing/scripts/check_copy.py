#!/usr/bin/env python3
"""웹 앱 화면 문구를 토스라이팅 기준으로 훑어보는 검사 스크립트.

HTML/JS/JSX/TS/TSX/Vue/Svelte 파일에서 한글이 들어간 문구만 골라
고칠 만한 표현을 찾아 준다. 결과는 '확인할 후보'일 뿐이다.
SKILL.md의 예외 규칙에 해당하면 그대로 둔다.

사용법:
    python3 check_copy.py index.html
    python3 check_copy.py src/            # 폴더 안 파일을 모두 검사
    python3 check_copy.py --strict app/   # 참고(info) 항목까지 보기
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EXTENSIONS = {".html", ".htm", ".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".mjs"}
SKIP_DIRS = {"node_modules", "dist", "build", ".git", ".next", ".svelte-kit", "coverage", "vendor"}

# 따옴표·태그·중괄호 사이에서 한글이 들어간 덩어리만 문구로 본다.
SEGMENT = re.compile(r"[^<>\"'`{}]*[가-힣][^<>\"'`{}]*")

# (규칙 이름, 등급, 정규식, 고치는 방법)
RULES = [
    ("해요체", "고칠 것",
     r"(합니다|습니다|십시오|바랍니다|됩니다|입니다)",
     "해요체로 바꿔요: 해요 / 했어요 / 할 수 있어요 / ~해 주세요"),
    ("되어요", "고칠 것",
     r"되어요",
     "'돼요'로 써요"),
    ("과한 경어", "고칠 것",
     r"(시겠어요|시겠습니까|하시겠|하신|주시기|주십시오|계시|계세요|계신|여쭤|여쭙|님께|께서|(?<!함)께(?=\s|$|[.,!?]))",
     "'~할까요?', '있나요?', '확인할게요', '~에게'처럼 써요"),
    ("취소 버튼", "고칠 것",
     r"취소",
     "대화창을 닫는 버튼이면 '닫기'로 써요. 진행 중인 작업을 정말 취소할 때만 '취소'를 써요"),
    ("기술 메시지 노출", "고칠 것",
     r"(Error:|undefined|NaN|\bnull\b|Exception)",
     "무엇이 일어났고 어떻게 하면 되는지 쉬운 말로 알려 줘요"),
    ("수동형", "확인",
     r"([가-힣]+(됐어요|되었어요)|(선택|등록|저장|입력|설정|배정|삭제|변경|추가|완료)된(?=\s))",
     "능동형으로: '설정했어요', '선택한 학생'. 안심·결과 안내·만료라면 그대로 둬요"),
    ("부정형", "확인",
     r"(수 없어요|없어요|안 ?돼요|불가)",
     "'~하면 ~할 수 있어요'로 다음 행동을 알려 줘요. 정책상 금지나 안심 문구라면 그대로 둬요"),
    ("명사 나열", "확인",
     r"[가-힣]{2,} ?(완료|실패|불가|필요|오류|성공|처리|진행 ?중)(?=$|[\s.!,)])",
     "동사로 풀어요: '명단을 등록했어요', '용량이 꽉 차서 저장하지 못했어요'"),
    ("사용자 탓", "확인",
     r"(잘못된|잘못 입력|올바르지 않|유효하지 않)",
     "무엇을 어떻게 넣으면 되는지 알려 줘요: '이름을 한 줄에 한 명씩 넣어 주세요'"),
    ("전문 용어", "확인",
     r"(로컬 ?스토리지|캐시|세션|쿠키|파싱|데이터베이스|서버 오류)",
     "말하듯 쉽게: '이 기기에 저장돼요', '잠시 후 다시 해 주세요'"),
    ("경어 확인", "참고",
     r"(시나요|셨나요)",
     "사용자 맥락을 짚는 질문·상황 추정·설문이 아니면 '~나요?'로 써요"),
]
COMPILED = [(name, level, re.compile(pattern), fix) for name, level, pattern, fix in RULES]

# 버튼 이름으로 자주 쓰이는 뭉뚱그린 말 (문구 전체가 이 낱말 하나일 때만)
GENERIC_CTA = re.compile(r"^(확인|제출|진행|예|아니오|아니요|완료|전송|다음|OK)$")


def iter_files(targets: list[str]):
    for target in targets:
        path = Path(target)
        if path.is_file():
            yield path
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and child.suffix.lower() in EXTENSIONS \
                        and not any(part in SKIP_DIRS for part in child.parts):
                    yield child
        else:
            print(f"찾을 수 없어요: {target}", file=sys.stderr)


def iter_copy(text: str):
    """(줄 번호, 열 번호, 문구)를 돌려준다. 주석과 <style> 안은 건너뛴다."""
    in_block_comment = False
    in_html_comment = False
    in_style = False
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        lower = stripped.lower()

        if in_style:
            if "</style" in lower:
                in_style = False
            continue
        if "<style" in lower and "</style" not in lower:
            in_style = True
            continue
        if in_html_comment:
            if "-->" in line:
                in_html_comment = False
            continue
        if in_block_comment:
            if "*/" in line:
                in_block_comment = False
            continue
        if stripped.startswith("<!--"):
            in_html_comment = "-->" not in stripped
            continue
        if stripped.startswith("/*"):
            in_block_comment = "*/" not in stripped
            continue
        if stripped.startswith(("//", "*", "#")):
            continue

        # 줄 끝의 // 주석 떼기 (URL의 :// 은 남긴다)
        code = re.sub(r"(?<![:\"'])//.*$", "", line)
        for match in SEGMENT.finditer(code):
            segment = match.group(0).strip()
            if segment:
                yield line_no, match.start() + 1, segment


def check_text(text: str, strict: bool):
    findings = []
    for line_no, col, segment in iter_copy(text):
        for name, level, pattern, fix in COMPILED:
            if level == "참고" and not strict:
                continue
            for hit in pattern.finditer(segment):
                findings.append((line_no, col, level, name, segment, hit.group(0), fix))
        if GENERIC_CTA.match(segment):
            findings.append((line_no, col, "확인", "뭉뚱그린 버튼", segment, segment,
                             "버튼이면 누르면 일어날 일을 써요: '모둠 배정하기', '답 보내기'"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="화면 문구를 토스라이팅 기준으로 검사해요.")
    parser.add_argument("targets", nargs="+", help="검사할 파일이나 폴더")
    parser.add_argument("--strict", action="store_true", help="참고 항목까지 보여 줘요")
    args = parser.parse_args()

    total = {"고칠 것": 0, "확인": 0, "참고": 0}
    checked = 0
    for path in iter_files(args.targets):
        checked += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        findings = check_text(text, args.strict)
        if not findings:
            continue
        print(f"\n■ {path}")
        for line_no, col, level, name, segment, hit, fix in findings:
            total[level] += 1
            shown = segment if len(segment) <= 60 else segment[:57] + "..."
            print(f"  {line_no}:{col} [{level}] {name} · '{hit}'")
            print(f"      문구: {shown}")
            print(f"      → {fix}")

    if checked == 0:
        print("검사할 파일이 없어요.")
        return 1
    print(f"\n파일 {checked}개 검사 · 고칠 것 {total['고칠 것']}개 · 확인 {total['확인']}개"
          + (f" · 참고 {total['참고']}개" if args.strict else ""))
    print("확인 항목은 SKILL.md의 예외 규칙(안심·결과 안내·정책상 금지 등)에 해당하면 그대로 둬도 돼요.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
