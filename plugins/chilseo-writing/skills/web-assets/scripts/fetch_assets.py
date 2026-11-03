#!/usr/bin/env python3
"""웹 앱에 필요한 글꼴·아이콘·CSS를 프로젝트 안으로 내려받는 스크립트.

인터넷 없이 index.html만 열어도 동작하도록 파일을 모두 프로젝트에 넣고,
라이선스 파일과 출처 목록(THIRD_PARTY_NOTICES.md)을 함께 만든다.

사용법 (프로젝트 폴더 기준):
    python3 fetch_assets.py ./my-app --pretendard
    python3 fetch_assets.py ./my-app --pico
    python3 fetch_assets.py ./my-app --lucide users,shuffle,timer
    python3 fetch_assets.py ./my-app --tabler users,dice
    python3 fetch_assets.py ./my-app --krds            # KRDS 컴포넌트 키트 + Pretendard GOV
    python3 fetch_assets.py ./my-app --list            # 이미 받은 자료 보기

받은 파일은 <프로젝트>/assets/vendor/ 아래에 들어간다.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

RAW = "https://raw.githubusercontent.com/{repo}/{branch}/{path}"
TODAY = dt.date.today().isoformat()


def raw(repo: str, path: str, branch: str = "main") -> str:
    return RAW.format(repo=repo, branch=branch, path=path)


def download(url: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "fetch-assets/1.0"})
        with urllib.request.urlopen(req, timeout=60) as res:
            dest.write_bytes(res.read())
        return True
    except (urllib.error.URLError, TimeoutError) as err:
        print(f"  ✗ 받지 못했어요: {url} ({err})", file=sys.stderr)
        return False


class Notices:
    """THIRD_PARTY_NOTICES.md에 자료별 출처·라이선스를 한 번씩만 적는다."""

    def __init__(self, project: Path):
        self.path = project / "THIRD_PARTY_NOTICES.md"
        self.text = self.path.read_text(encoding="utf-8") if self.path.exists() else (
            "# 함께 넣은 자료와 라이선스\n\n"
            "이 앱에 포함된 외부 자료의 출처와 라이선스예요. "
            "각 라이선스 원문은 `assets/vendor/<자료>/` 폴더에 있어요.\n"
        )

    def add(self, key: str, body: str):
        marker = f"<!-- {key} -->"
        if marker in self.text:
            return
        self.text += f"\n{marker}\n{body.strip()}\n"

    def save(self):
        self.path.write_text(self.text, encoding="utf-8")
        print(f"  ✓ 출처 목록: {self.path}")


def fetch_pretendard(vendor: Path, notices: Notices, gov: bool = False):
    name = "PretendardGOV" if gov else "Pretendard"
    pkg = "pretendard-gov" if gov else "pretendard"
    folder = vendor / ("pretendard-gov" if gov else "pretendard")
    print(f"▶ {name} 글꼴")
    faces = []
    for weight, label in ((400, "Regular"), (500, "Medium"), (700, "Bold")):
        file = f"{name}-{label}.subset.woff2"
        url = raw("orioncactus/pretendard",
                  f"packages/{pkg}/dist/web/static/woff2-subset/{file}")
        if download(url, folder / file):
            faces.append(
                f'@font-face {{\n  font-family: "{"Pretendard GOV" if gov else "Pretendard"}";\n'
                f'  font-weight: {weight};\n  font-style: normal;\n  font-display: swap;\n'
                f'  src: url("./{file}") format("woff2");\n}}\n')
    (folder / "font.css").write_text("\n".join(faces), encoding="utf-8")
    download(raw("orioncactus/pretendard", "LICENSE"), folder / "LICENSE.txt")
    print(f"  ✓ {folder}/font.css 를 <link>로 연결하세요")
    notices.add(name, f"""
## {"Pretendard GOV" if gov else "Pretendard"} (글꼴)
- 출처: https://github.com/orioncactus/pretendard
- 라이선스: SIL Open Font License 1.1 (`assets/vendor/{folder.name}/LICENSE.txt`)
- 받은 날: {TODAY}
""")


def fetch_pico(vendor: Path, notices: Notices):
    print("▶ Pico CSS")
    folder = vendor / "pico"
    download(raw("picocss/pico", "css/pico.min.css"), folder / "pico.min.css")
    download(raw("picocss/pico", "css/pico.classless.min.css"), folder / "pico.classless.min.css")
    download(raw("picocss/pico", "LICENSE.md"), folder / "LICENSE.md")
    print(f"  ✓ {folder}/pico.min.css (클래스 없이 쓰려면 pico.classless.min.css)")
    notices.add("pico", f"""
## Pico CSS (기본 스타일)
- 출처: https://github.com/picocss/pico
- 라이선스: MIT (`assets/vendor/pico/LICENSE.md`)
- 받은 날: {TODAY}
""")


def fetch_icons(vendor: Path, notices: Notices, kind: str, names: list[str]):
    if kind == "lucide":
        repo, path_fmt, lic, lic_name, home = (
            "lucide-icons/lucide", "icons/{n}.svg", "LICENSE", "ISC", "https://lucide.dev")
    else:
        repo, path_fmt, lic, lic_name, home = (
            "tabler/tabler-icons", "icons/outline/{n}.svg", "LICENSE", "MIT", "https://tabler.io/icons")
    print(f"▶ {kind} 아이콘 {len(names)}개")
    folder = vendor / kind
    ok = [n for n in names if download(raw(repo, path_fmt.format(n=n)), folder / f"{n}.svg")]
    download(raw(repo, lic), folder / "LICENSE.txt")
    if ok:
        print(f"  ✓ {folder}/ 에 {', '.join(ok)}")
    if len(ok) < len(names):
        print(f"  ! 이름을 확인하세요: {home} 에서 검색할 수 있어요")
    notices.add(kind, f"""
## {"Lucide" if kind == "lucide" else "Tabler Icons"} (아이콘)
- 출처: {home}
- 라이선스: {lic_name} (`assets/vendor/{kind}/LICENSE.txt`)
- 받은 날: {TODAY}
""")


def fetch_krds(vendor: Path, notices: Notices):
    """KRDS 컴포넌트 키트를 받고, krds.go.kr를 가리키는 아이콘 주소를 로컬 경로로 바꾼다."""
    print("▶ KRDS 컴포넌트 키트")
    repo = "KRDS-uiux/krds-uiux"
    folder = vendor / "krds"
    css_path, js_path = folder / "krds.min.css", folder / "krds.min.js"
    if not download(raw(repo, "resources/cdn/krds.min.css"), css_path):
        return
    download(raw(repo, "resources/cdn/krds.min.js"), js_path)

    css = css_path.read_text(encoding="utf-8")
    remote = re.compile(r"https?://www\.krds\.go\.kr/resources/img/component/icon/([\w.-]+\.svg)")
    icons = sorted(set(remote.findall(css)))
    print(f"  아이콘 {len(icons)}개를 받아 경로를 바꿔요")
    missing = []
    for name in icons:
        if not download(raw(repo, f"resources/img/component/icon/{name}"), folder / "icon" / name):
            missing.append(name)
    css = remote.sub(lambda m: f"./icon/{m.group(1)}", css)
    css_path.write_text(css, encoding="utf-8")
    if missing:
        print(f"  ! 받지 못한 아이콘 {len(missing)}개: {', '.join(missing[:5])}...")

    left = re.findall(r"https?://[^\s\"')]+", css)
    if left:
        print(f"  ! CSS에 아직 외부 주소가 {len(left)}개 남아 있어요: {left[0]}")

    fetch_pretendard(vendor, notices, gov=True)
    print(f"  ✓ <link> 순서: pretendard-gov/font.css → krds/krds.min.css, 그리고 </body> 앞에 krds/krds.min.js")
    print("  ! KRDS CSS는 html 글자 크기를 62.5%(1rem=10px)로 바꿔요. 다른 CSS와 섞을 때 rem 크기가 달라져요")
    notices.add("krds", f"""
## KRDS 대한민국 정부 디자인 시스템 (HTML 컴포넌트 키트, 아이콘)
- 출처: 행정안전부, KRDS - Korea Design System, https://www.krds.go.kr
- 코드: https://github.com/KRDS-uiux/krds-uiux
- 이용 조건: KRDS 저작권 정책(https://www.krds.go.kr/html/site/utility/utility_06.html)에 따라 출처를 표시하고 이용
- 받은 날: {TODAY}
""")


def list_assets(project: Path):
    vendor = project / "assets" / "vendor"
    if not vendor.exists():
        print("아직 받은 자료가 없어요.")
        return
    for folder in sorted(p for p in vendor.iterdir() if p.is_dir()):
        files = [f for f in folder.rglob("*") if f.is_file()]
        size = sum(f.stat().st_size for f in files) / 1024
        print(f"  {folder.name:16} 파일 {len(files):3}개 · {size:,.0f}KB")


def main() -> int:
    parser = argparse.ArgumentParser(description="글꼴·아이콘·CSS를 프로젝트 안으로 내려받아요.")
    parser.add_argument("project", help="웹 앱 프로젝트 폴더 (index.html이 있는 곳)")
    parser.add_argument("--pretendard", action="store_true", help="Pretendard 글꼴")
    parser.add_argument("--pico", action="store_true", help="Pico CSS")
    parser.add_argument("--lucide", help="Lucide 아이콘 이름들 (쉼표로 구분)")
    parser.add_argument("--tabler", help="Tabler 아이콘 이름들 (쉼표로 구분)")
    parser.add_argument("--krds", action="store_true", help="KRDS 컴포넌트 키트 + Pretendard GOV")
    parser.add_argument("--list", action="store_true", help="받은 자료 보기")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"프로젝트 폴더가 없어요: {project}", file=sys.stderr)
        return 1
    if args.list:
        list_assets(project)
        return 0
    if not any([args.pretendard, args.pico, args.lucide, args.tabler, args.krds]):
        parser.print_help()
        return 1

    vendor = project / "assets" / "vendor"
    notices = Notices(project)
    if args.krds:
        fetch_krds(vendor, notices)
    if args.pretendard:
        fetch_pretendard(vendor, notices)
    if args.pico:
        fetch_pico(vendor, notices)
    if args.lucide:
        fetch_icons(vendor, notices, "lucide", [n.strip() for n in args.lucide.split(",") if n.strip()])
    if args.tabler:
        fetch_icons(vendor, notices, "tabler", [n.strip() for n in args.tabler.split(",") if n.strip()])
    notices.save()
    print("\n다음 단계: 인터넷을 끄고 index.html을 열어 글꼴·아이콘이 보이는지 확인하세요.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
