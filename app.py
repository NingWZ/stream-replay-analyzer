import base64
import io
from html import escape
from pathlib import Path
from string import Template

import av
import streamlit as st
import streamlit.components.v1 as components

from analysis_core import THRESHOLD, WINDOW, candidates, parse_chat, playback_start

ROOT = Path(__file__).resolve().parent


def clock(second):
    minutes, seconds = divmod(int(second), 60)
    fraction = f"{second % 1:.3f}"[1:].rstrip("0").rstrip(".")
    return f"{minutes:02}:{seconds:02}{fraction}"


def video_duration(data):
    with av.open(io.BytesIO(data)) as container:
        if "mp4" not in container.format.name.split(",") or not container.streams.video:
            raise ValueError("映像トラックを含む MP4 を選択してください。")
        if not container.duration or container.duration <= 0:
            raise ValueError("録画時間を取得できません。MP4 を再書き出ししてください。")
        return container.duration / av.time_base


st.set_page_config(page_title="Stream Replay Analyzer", page_icon="▶", layout="wide")
st.title("Stream Replay Analyzer")
st.write("コメントから配信の見どころを探し、その場面を録画で確認できます。")
mode = st.radio("録画ソース", ["デモ録画", "ファイルを読み込む"], horizontal=True, label_visibility="collapsed")
if mode == "デモ録画":
    video = (ROOT / "demo/replay.mp4").read_bytes()
    chat = (ROOT / "demo/chat.csv").read_bytes()
else:
    left, right = st.columns(2)
    recording = left.file_uploader("録画 MP4（40 MiB 以下）", type=["mp4"])
    log = right.file_uploader("コメント CSV（UTF-8、1 MiB 以下）", type=["csv"])
    if recording is None or log is None:
        st.info("録画とコメント CSV をそれぞれ選択してください。")
        st.stop()
    if recording.size > 40 * 1024**2 or log.size > 1024**2:
        st.error("ファイルサイズを確認してください。MP4 は 40 MiB、CSV は 1 MiB が上限です。")
        st.stop()
    video, chat = recording.getvalue(), log.getvalue()

try:
    duration = video_duration(video)
except (av.FFmpegError, ValueError, OSError):
    st.error("動画の長さを読み取れません。映像トラックがある正常な MP4 を選択してください。")
    st.stop()
try:
    comments = parse_chat(chat, duration)
except ValueError as error:
    st.error(str(error))
    st.stop()

segments = candidates(comments, duration)
st.subheader("録画とコメント")
st.caption(f"録画 {clock(duration)}　 ·　 コメント {len(comments)} 件　 ·　 クリックで投稿の 5 秒前から再生")
buttons = "".join(
    f'<button data-start="{playback_start(c.second)}"><time>{clock(c.second)}</time>'
    f'<span>{escape(c.message)}</span></button>' for c in comments
)
template = Template((ROOT / "player.html").read_text(encoding="utf-8"))
components.html(template.substitute(
    video=base64.b64encode(video).decode("ascii"),
    comments=buttons or "<p>コメントはありません。</p>",
), height=380, scrolling=True)

st.subheader(f"見どころ候補 · {len(segments)} 件")
if not segments:
    st.info("基準を満たす区間はありません。")
for segment in segments:
    with st.container(border=True):
        st.markdown(f"**{clock(segment.start)} – {clock(segment.end)}**")
        st.write(f"{WINDOW} 秒あたり {THRESHOLD} 件以上の区間が {segment.windows} 枠、計 {segment.count} 件。")
        st.text(f"代表コメント　{clock(segment.representative.second)}　{segment.representative.message}")

