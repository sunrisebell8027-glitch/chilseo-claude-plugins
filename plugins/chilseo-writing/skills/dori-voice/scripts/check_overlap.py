#!/usr/bin/env python3
"""공백과 문장부호를 제외한 연속 구간을 비교한다."""
import argparse
import sys
import unicodedata
from pathlib import Path
from file_read import read_text


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, '사용법: check_overlap.py 검사할 파일 --against 원고 파일이나 폴더 [--min 글자수]\n입력을 확인하세요.\n')


def normalize(text):
    chars, positions = [], []
    line = col = 1
    for char in text:
        if not char.isspace() and not unicodedata.category(char).startswith('P'):
            chars.append(char)
            positions.append((line, col))
        if char == '\n':
            line, col = line + 1, 1
        else:
            col += 1
    return ''.join(chars), positions


def overlaps(left, right, minimum):
    # 같은 창의 첫 위치를 사용하고, 이어지는 창을 한 구간으로 합친다.
    windows = {}
    for j in range(len(right) - minimum + 1):
        windows.setdefault(right[j:j + minimum], j)
    start = match = end = None
    for i in range(len(left) - minimum + 1):
        if start is not None and i + minimum - 1 == end and match + end - start < len(right) and left[end] == right[match + end - start]:
            end += 1
            continue
        if start is not None:
            yield start, match, left[start:end]
            start = match = end = None
        j = windows.get(left[i:i + minimum])
        if j is not None:
            start, match, end = i, j, i + minimum
    if start is not None:
        yield start, match, left[start:end]


def main():
    parser = Parser(description='원고와 겹치는 연속 구간을 검사합니다.')
    parser.add_argument('file')
    parser.add_argument('--against', nargs='+', required=True)
    parser.add_argument('--min', type=int, default=14)
    args = parser.parse_args()
    if args.min < 1:
        print('최소 글자 수는 1 이상으로 입력하세요.', file=sys.stderr)
        return 2
    try:
        target = Path(args.file)
        left, left_pos = normalize(read_text(target))
        paths = []
        for name in args.against:
            path = Path(name)
            if path.is_dir():
                paths.extend(p for p in sorted(path.rglob('*')) if p.is_file() and p.suffix.lower() in ('.md', '.txt'))
            elif path.is_file():
                paths.append(path)
            else:
                raise ValueError('찾을 수 없는 경로: ' + name)
        if not paths:
            raise ValueError('비교할 파일이 없습니다.')
        found = False
        timed_out = False
        for path in dict.fromkeys(paths):
            try:
                right, right_pos = normalize(read_text(path))
            except TimeoutError:
                print('파일을 여는 데 30초가 넘었어요. 확인하세요: ' + str(path), file=sys.stderr)
                timed_out = True
                continue
            for i, j, value in overlaps(left, right, args.min):
                found = True
                print('{}:{}:{} ↔ {}:{}:{} — {}'.format(target, *left_pos[i], path, *right_pos[j], value))
        if not found:
            print('겹치는 구간 없음')
        return 2 if timed_out else int(found)
    except TimeoutError:
        print('파일을 여는 데 30초가 넘었어요. 확인하세요: ' + str(target), file=sys.stderr)
        return 2
    except (OSError, UnicodeError, ValueError) as exc:
        print('파일을 확인하세요: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
