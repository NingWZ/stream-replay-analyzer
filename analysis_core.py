"""Chat timestamps are integer seconds from the beginning of the recording."""
import csv
import io
from dataclasses import dataclass
from itertools import groupby

WINDOW = 5
THRESHOLD = 3


@dataclass(frozen=True)
class Comment:
    second: int
    message: str


@dataclass(frozen=True)
class Segment:
    start: int
    end: float
    count: int
    windows: int
    representative: Comment


def playback_start(second: int) -> int:
    return max(0, second - 5)


def parse_chat(data: bytes, duration: float) -> list[Comment]:
    try:
        source = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV を UTF-8 または UTF-8 BOM 付きで保存してください。") from exc
    reader = csv.reader(io.StringIO(source, newline=""), strict=True)
    comments = []
    try:
        if next(reader, None) != ["seconds", "message"]:
            raise ValueError("1 行目の列名は seconds,message にしてください。")
        for row in reader:
            if not row:
                continue
            where = f"{reader.line_num} 行目"
            if len(row) != 2:
                raise ValueError(f"{where}：2 列必要です。本文にカンマを含む場合は二重引用符で囲んでください。")
            value, message = (field.strip() for field in row)
            if not value.isascii() or not value.isdecimal() or len(value) > 10:
                raise ValueError(f"{where}：seconds には 0 以上の整数秒を入力してください。")
            second = int(value)
            if second >= duration:
                raise ValueError(f"{where}：{second} 秒は動画の範囲外です（長さ {duration:g} 秒）。")
            if not message:
                raise ValueError(f"{where}：message が空です。")
            comments.append(Comment(second, message))
    except csv.Error as exc:
        raise ValueError(f"{reader.line_num} 行目：CSV の引用符と区切りを確認してください。") from exc
    return sorted(comments, key=lambda item: item.second)


def candidates(comments: list[Comment], duration: float) -> list[Segment]:
    ordered = sorted(comments, key=lambda item: item.second)
    peaks = []
    for index, items in groupby(ordered, key=lambda item: item.second // WINDOW):
        rows = list(items)
        if len(rows) >= THRESHOLD:
            peaks.append((index, rows))
    segments = []
    for _, adjacent in groupby(enumerate(peaks), key=lambda item: item[1][0] - item[0]):
        run = [peak for _, peak in adjacent]
        strongest = max(run, key=lambda peak: len(peak[1]))
        segments.append(Segment(run[0][0] * WINDOW, min(duration, (run[-1][0] + 1) * WINDOW),
                                sum(len(rows) for _, rows in run), len(run), strongest[1][0]))
    return segments

