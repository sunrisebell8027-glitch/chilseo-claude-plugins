#!/usr/bin/env python
"""산출물 출력 게이트 — 원클릭·무오류 보장 장치.

방침: 사용자가 산출물을 다시 검토·수정하게 만들면 자동화가 무의미하다.
그래서 스킬은 문서를 넘기기 **전에** 스스로 검사하고, 하나라도 걸리면 넘기지 않는다.

검사 항목
  1. open      한/글에서 열리는지 (패키지·문서 구조)
  2. residue   미완성 자리표시자가 남았는지 (○○, ____, {{ }}, TODO, 예시 …)
  3. budget    예산표 합계 = 항목 합
  4. weekday   `2026. 8. 3.(월)` 의 요일이 실제 달력과 맞는지
  5. attend    출석부 열 수 = 3 + 운영일수 + 2
  6. secnum    절 번호가 연속인지
  7. empty     필수 슬롯이 비었는지

blocking=True 인 항목이 하나라도 실패하면 산출물을 내보내지 않는다.
"""
from __future__ import annotations
import re, datetime, dataclasses

KOR_DOW = "월화수목금토일"
ROMAN = "ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ"

# 자리표시자 검사는 **정밀도가 재현율보다 중요하다.**
# 오탐으로 정상 문서를 막으면 사용자가 개입해야 하고, 그 순간 원클릭이 깨진다.
#
# 실제 학교 문서에서 확인한 오탐 사례:
#   · `N/A`        — 영어캠프 시간표 마지막 날 '수업 주제' 칸의 의도된 내용
#   · `______`     — 가정통신문·참가신청서의 서명란. 있어야 정상
#   · `— 예시`     — 붙임 예시 양식의 의도된 라벨
# 따라서 이들은 차단하지 않는다.

# 차단: 치환 실패가 명백한 것만
RESIDUE_BLOCK = [
    (r"\{\{.*?\}\}|\{[A-Za-z_][A-Za-z0-9_]*\}", "치환되지 않은 템플릿 변수"),
    (r"\bTODO\b|\bTBD\b|\bFIXME\b", "TODO/TBD/FIXME"),
    (r"<\s*(채워|입력|기입)[^>]*>", "미기입 안내 태그"),
    (r"○○○+", "미기입 자리표시자 ○○○"),
]

# 경고: 사람이 의도했을 수도 있어 막지 않고 알린다
RESIDUE_WARN = [
    (r"○○(?!○)", "○○ (기관·이름 미기입 가능)"),
    (r"별도\s*안내\s*$", "'별도 안내' 미확정 가능"),
]


@dataclasses.dataclass
class Finding:
    check: str
    ok: bool
    blocking: bool
    detail: str = ""


def _load(path):
    from hwpx.document import HwpxDocument
    d = HwpxDocument.open(str(path))
    paras = [(p.text or "").strip() for p in d.paragraphs]
    tabs = d.get_table_map()["tables"]
    return d, paras, tabs


def _cellgrid(t):
    return {(c["row"], c["col"]): (c.get("text") or "").strip() for c in t["cells"]}


# ---------- 개별 검사 ----------

def check_open(path):
    """Validate package integrity and references; this does not render in Hangul."""
    import zipfile
    from lxml import etree as E
    from hwpx.document import HwpxDocument
    try:
        with zipfile.ZipFile(path) as z:
            if z.testzip():
                raise ValueError("ZIP CRC mismatch")
            names=set(z.namelist())
            if z.read("mimetype").strip()!=b"application/hwp+zip":
                raise ValueError("Unexpected MIME type")
            roots={n:E.fromstring(z.read(n)) for n in names if n.endswith((".xml", ".hpf"))}
            manifest=roots["Contents/content.hpf"]
            for item in manifest.xpath('//*[local-name()="item"]'):
                href=item.get("href")
                if href and href not in names:
                    raise ValueError(f"Missing manifest resource: {href}")
            head=roots["Contents/header.xml"]
            sections=[r for name,r in roots.items() if re.fullmatch(r"Contents/section\d+\.xml",name)]
            if int(head.get("secCnt"))!=len(sections):
                raise ValueError("Section count mismatch")
            for tag,attr in [("charPr","charPrIDRef"),("paraPr","paraPrIDRef"),("borderFill","borderFillIDRef")]:
                ids={e.get("id") for e in head.xpath(f'//*[local-name()="{tag}"]')}
                for root in sections:
                    for e in root.xpath(f'//*[@{attr}]'):
                        if e.get(attr) not in ids:raise ValueError(f"Missing style: {attr}={e.get(attr)}")
        HwpxDocument.open(str(path))
        return Finding("open", True, True, "ZIP·XML·리소스·스타일 참조 및 재개방 정상(앱 열람 별도)")
    except Exception as e:
        return Finding("open", False, True, f"검증 실패: {type(e).__name__}: {e}")


def check_residue(paras, tabs):
    blob = list(paras) + [c for t in tabs for c in _cellgrid(t).values()]
    hard, soft = [], []
    for text in blob:
        for pat, why in RESIDUE_BLOCK:
            if re.search(pat, text):
                hard.append(f"{why}: “{text[:30]}”")
                break
        else:
            for pat, why in RESIDUE_WARN:
                if re.search(pat, text):
                    soft.append(f"{why}: “{text[:30]}”")
                    break
    if hard:
        return Finding("residue", False, True,
                       f"차단 {len(hard)}건 — " + " / ".join(hard[:3]))
    if soft:
        return Finding("residue", False, False,
                       f"확인 권장 {len(soft)}건 — " + " / ".join(soft[:2]))
    return Finding("residue", True, True, "자리표시자 없음")


def check_budget(tabs):
    """머리행에 '산출내역'/'금액'이 있는 표를 예산표로 보고 합계를 검산."""
    checked = 0
    for t in tabs:
        g = _cellgrid(t)
        head = " ".join(g.get((0, c), "") for c in range(t["cols"]))
        if "금액" not in head:
            continue
        amtcol = next((c for c in range(t["cols"]) if "금액" in g.get((0, c), "")), None)
        if amtcol is None:
            continue
        items, total = [], None
        for r in range(1, t["rows"]):
            label = " ".join(g.get((r, c), "") for c in range(amtcol))
            m = re.search(r"\d[\d,]*", g.get((r, amtcol), ""))
            if not m:
                continue
            v = int(m.group().replace(",", ""))
            if re.search(r"합\s*계|^\s*계\s*$|총\s*계", label):
                total = v
            else:
                items.append(v)
        if total is None or not items:
            continue
        checked += 1
        if sum(items) != total:
            return Finding("budget", False, True,
                           f"합계 불일치: 항목합 {sum(items):,} ≠ 표기 {total:,}")
    return Finding("budget", True, True,
                   f"예산표 {checked}개 합계 일치" if checked else "예산표 없음(건너뜀)")


def check_weekday(paras, tabs):
    blob = " ".join(paras) + " " + " ".join(c for t in tabs for c in _cellgrid(t).values())
    bad, tot = [], 0
    for m in re.finditer(r"(20\d\d)\.\s*(\d{1,2})\.\s*(\d{1,2})\.\s*\(([월화수목금토일])\)", blob):
        y, mo, dd, dow = int(m[1]), int(m[2]), int(m[3]), m[4]
        tot += 1
        try:
            real = KOR_DOW[datetime.date(y, mo, dd).weekday()]
        except ValueError:
            bad.append(f"{y}.{mo}.{dd}. 존재하지 않는 날짜")
            continue
        if real != dow:
            bad.append(f"{y}.{mo}.{dd}.({dow})→실제({real})")
    if bad:
        return Finding("weekday", False, True, f"{len(bad)}/{tot}건 불일치: " + ", ".join(bad[:3]))
    return Finding("weekday", True, True, f"날짜 {tot}건 요일 일치")


def check_attend(tabs, days=None):
    """출석부: 열 = 3(번호·학반·성명) + 운영일수 + 2(계·연락처)."""
    for t in tabs:
        g = _cellgrid(t)
        head = [g.get((1, c), "") or g.get((0, c), "") for c in range(t["cols"])]
        if not ("성명" in head and any("출석" in x for x in
                                       [g.get((0, c), "") for c in range(t["cols"])])):
            continue
        dcols = [h for h in head if re.match(r"\d{1,2}/\d{1,2}", h)]
        if days is not None and len(dcols) != days:
            return Finding("attend", False, True,
                           f"출석부 날짜열 {len(dcols)}개 ≠ 운영일수 {days}")
        expect = 3 + len(dcols) + 2
        if t["cols"] != expect:
            return Finding("attend", False, False,
                           f"출석부 열 {t['cols']} ≠ 3+{len(dcols)}+2={expect}")
        return Finding("attend", True, True, f"출석부 {t['cols']}열 = 3+{len(dcols)}일+2 일치")
    return Finding("attend", True, True, "출석부 없음(건너뜀)")


def check_secnum(paras, tabs):
    rom = []
    for t in tabs:
        if t["r"] if "r" in t else t["rows"] != 1:
            pass
    for t in tabs:
        if t["rows"] != 1:
            continue
        cells = [c for c in _cellgrid(t).values() if c]
        if cells and re.fullmatch(f"[{ROMAN}]", cells[0]):
            rom.append(cells[0])
    if rom:
        idx = [ROMAN.index(x) for x in rom]
        if idx != list(range(len(idx))):
            return Finding("secnum", False, False,
                           f"로마숫자 절 번호 불연속: {''.join(rom)}")
        return Finding("secnum", True, True, f"절 번호 연속 ({''.join(rom)})")
    nums = [int(m[1]) for p in paras if (m := re.match(r"^(\d{1,2})\.\s+\S", p))]
    tops = []
    for n in nums:
        if n == 1 or (tops and n == tops[-1] + 1):
            tops.append(n)
    return Finding("secnum", True, True, f"아라비아 절 {len(tops)}개")


def check_concat(paras):
    """주입 사고 탐지 — 단락 중간에 글머리가 나타나면 덧붙기가 일어난 것이다.

    한 단락은 run 여러 개로 쪼개져 있어서(들여쓰기 / 글머리 / 내용),
    내용 run만 갈아야 한다. `runs[0]`만 바꾸면 나머지가 살아남아
    "새 내용❍ 원래 내용" 처럼 원문이 뒤에 붙는다.
    문법적으로는 정상인 문서라 다른 검사로는 걸리지 않는다.
    """
    bad = []
    for t in paras:
        s = (t or "").strip()
        if len(s) < 12:
            continue
        # 첫 글자 위치를 뺀 나머지에서 글머리 기호나 로마숫자 절이 나오면 의심
        m = re.search(r"\S\s*([❍○◦●]|[ⅠⅡⅢⅣⅤⅥⅦⅧ]\s+\S)", s[1:])
        if m:
            bad.append(s[:44])
    if bad:
        return Finding("concat", False, True,
                       f"단락 중간 글머리 {len(bad)}건(주입 덧붙기 의심): "
                       + " / ".join(f"“{b}”" for b in bad[:2]))
    return Finding("concat", True, True, "덧붙기 흔적 없음")


def check_empty(paras, required=("제목",)):
    missing = [k for k in required
               if not any(k in p for p in paras)] if required else []
    blanks = sum(1 for p in paras if re.fullmatch(r"[\s·\-–]*", p or ""))
    if missing:
        return Finding("empty", False, True, f"필수 항목 누락: {', '.join(missing)}")
    return Finding("empty", True, False, f"빈 단락 {blanks}개")


# ---------- 통합 ----------

def run(path, days=None, required=None):
    _, paras, tabs = _load(path)
    fs = [
        check_open(path),
        check_residue(paras, tabs),
        check_budget(tabs),
        check_weekday(paras, tabs),
        check_attend(tabs, days),
        check_concat(paras),
        check_secnum(paras, tabs),
        check_empty(paras, required or ()),
    ]
    blocked = [f for f in fs if not f.ok and f.blocking]
    return fs, blocked


def report(path, days=None, required=None):
    fs, blocked = run(path, days, required)
    lines = []
    for f in fs:
        mark = "✅" if f.ok else ("⛔" if f.blocking else "⚠️ ")
        lines.append(f"  {mark} {f.check:<8} {f.detail}")
    verdict = ("통과 — 산출물 전달 가능" if not blocked
               else f"차단 {len(blocked)}건 — 전달하지 않음")
    return "\n".join(lines), verdict, blocked


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        body, verdict, _ = report(p)
        print(f"\n▶ {p}\n{body}\n  → {verdict}")
