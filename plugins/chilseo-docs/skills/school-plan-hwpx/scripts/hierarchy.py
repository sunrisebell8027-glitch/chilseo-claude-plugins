#!/usr/bin/env python
"""노션 계획서 → 학교 4단 위계 정규화.

노션은 글머리를 제멋대로 쓴다(❍ ○ - • 가. 1) Ⅰ ###). 그래서 **글머리 모양만으로
레벨을 정하면 안 된다.** 들여쓰기 깊이와 등장 순서를 함께 본다.

정규화 결과는 항상 학교 표준 4단으로 떨어진다:

    1단  1.    14pt  굵게      ← 절 제목
    2단  가.   12pt
    3단  1)    11pt
    4단  -     10pt

크기는 SCALE에서 한 곳으로 바꿀 수 있다.
"""
from __future__ import annotations
import re

# 학교 표준 4단 (글머리, 크기pt, 굵게)
SCALE = {
    1: ("{n}.", 14, True),
    2: ("{k}.", 12, False),
    3: ("{n})", 11, False),
    4: ("-",    10, False),
}
KOR = "가나다라마바사아자차카타파하"

# 노션에서 관측되는 글머리 → 기본 레벨 힌트
GLYPH_HINT = {
    "Ⅰ": 1, "Ⅱ": 1, "Ⅲ": 1, "Ⅳ": 1, "Ⅴ": 1, "Ⅵ": 1, "Ⅶ": 1, "Ⅷ": 1,
    "❍": 2, "○": 2, "◦": 2, "●": 2,
    "•": 4, "-": 4, "–": 4, "*": 4, "·": 4, "▪": 4,
}


def _strip_marker(t: str, hints: dict):
    """맨 앞 글머리 **하나**를 떼어내고 (글머리종류, 남은본문)을 준다.

    연도(`2026.`)를 글머리로 오인하지 않도록 숫자 글머리는 3자리 이하로 제한한다.
    학교 문서는 `1.`~`99.`를 넘기지 않는다.
    """
    m = re.match(r"^([ⅠⅡⅢⅣⅤⅥⅦⅧ])\s*[.)]?\s+(.*)$", t)
    if m:
        return "roman", m.group(2).strip()
    m = re.match(r"^(\d{1,2})\s*\.\s+(.*)$", t)
    if m:
        return "num.", m.group(2).strip()
    m = re.match(r"^(\d{1,2})\s*\)\s*(.*)$", t)
    if m:
        return "num)", m.group(2).strip()
    m = re.match(rf"^[{KOR}]\s*[.)]\s+(.*)$", t)
    if m:
        return "kor.", m.group(1).strip()
    if t and t[0] in hints:
        return t[0], t[1:].strip()
    return None, t


# 글머리 종류 → 기본 레벨
KIND_LEVEL = {"roman": 1, "num.": 1, "kor.": 2, "num)": 3}


def parse_line(raw: str, hints: dict | None = None):
    """한 줄 → (들여쓰기, 글머리종류, 본문). 글머리는 **반복해서** 벗겨낸다.

    노션은 `### 가. 운영 기간`처럼 heading과 글머리를 겹쳐 쓴다. 한 번만 벗기면
    `가. 가. 운영 기간`이 된다.
    """
    hints = hints or GLYPH_HINT
    indent = len(raw) - len(raw.lstrip(" \t"))
    t = raw.strip()
    if not t:
        return None

    kind = None
    m = re.match(r"^(#{1,6})\s*(.*)$", t)
    if m:                                   # heading 깊이를 들여쓰기로 환산
        indent -= (7 - len(m.group(1)))
        t = m.group(2).strip()
        kind = f"h{len(m.group(1))}"

    # 글머리는 **최대 하나만** 벗긴다. 여러 번 벗기면 본문 첫머리(`2026. 4. ~`)를
    # 글머리로 잘못 먹는다. heading 뒤에 글머리가 겹친 경우에만 한 번 더 허용.
    k, rest = _strip_marker(t, hints)
    if k is not None:
        kind, t = k, rest
    return indent, kind, t


def normalize(lines, glyph_map: dict | None = None):
    """노션 본문 줄들 → [(레벨, 본문)].

    레벨은 (들여쓰기, 글머리종류) **조합마다 하나로 고정**한다. 같은 형제끼리
    레벨이 갈리지 않게 하기 위함이다. glyph_map으로 기관별 관례를 덮어쓸 수 있다.
    """
    hints = dict(GLYPH_HINT)
    if glyph_map:
        hints.update(glyph_map)

    parsed = [p for p in (parse_line(l, hints) for l in lines) if p]
    if not parsed:
        return []

    def structured(kind):
        """번호 글머리(Ⅰ 1. 가. 1))만 고유 레벨을 갖는다. 기호는 전부 동급."""
        return KIND_LEVEL.get(kind) if kind in KIND_LEVEL else None

    # 바깥 절을 기준으로 한 **상대 깊이**로 레벨을 정한다.
    #
    # 노션 내보내기는 글머리 앞 들여쓰기를 거의 주지 않아서, 들여쓰기만 보면
    # `❍`(절 바로 아래)와 `1)`(가. 아래)이 똑같이 0으로 보인다. 그래서
    # "지금 어느 절 안인가"를 문맥으로 들고 다니며 기호 글머리는 그 아래로 건다.
    out = []
    context = 0            # 직전 번호 글머리의 레벨
    sym_indents = []       # 현재 문맥 안에서 만난 기호 글머리의 들여쓰기 스택

    for indent, kind, text in parsed:
        lvl = structured(kind)
        if lvl is not None:
            context, sym_indents = lvl, []
        else:
            # 기호(또는 글머리 없음) → 문맥 아래로. 들여쓰기가 깊어지면 한 단 더.
            while sym_indents and indent < sym_indents[-1]:
                sym_indents.pop()
            if not sym_indents or indent > sym_indents[-1]:
                sym_indents.append(indent)
            lvl = context + len(sym_indents)
        out.append((max(1, min(4, lvl)), text))

    return out


def render(items):
    """정규화 결과 → (글머리 붙은 텍스트, 크기pt, 굵게) 목록."""
    counters = {1: 0, 2: 0, 3: 0}
    res = []
    for lvl, text in items:
        fmt, pt, bold = SCALE[lvl]
        if lvl in counters:
            counters[lvl] += 1
            for deeper in range(lvl + 1, 4):
                counters[deeper] = 0
        n = counters.get(lvl, 0)
        mark = fmt.format(n=n, k=KOR[(n - 1) % len(KOR)] if n else "가")
        res.append((f"{mark} {text}", pt, bold))
    return res
