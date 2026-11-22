"""Generate 300 original frames with a seven-segment counter. Run from any directory."""
from pathlib import Path
import av
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "demo" / "replay.mp4"
DIGITS = ("abcdef", "bc", "abdeg", "abcdg", "bcfg", "acdfg", "acdefg", "abc", "abcdefg", "abcdfg")
BARS = [(8, 0, 68, 8), (68, 8, 76, 65), (68, 76, 76, 133), (8, 133, 68, 141),
        (0, 76, 8, 133), (0, 8, 8, 65), (8, 66, 68, 74)]


def generate():
    with av.open(str(OUT), "w") as container:
        stream = container.add_stream("libx264", rate=10)
        stream.width, stream.height, stream.pix_fmt = 640, 360, "yuv420p"
        for frame_no in range(300):
            second = frame_no // 10
            image = Image.new("RGB", (640, 360), "#101f31")
            draw = ImageDraw.Draw(image)
            draw.text((34, 26), "STREAM REPLAY    /    RECORDING CLOCK", fill="#a4b9cd", font_size=18)
            for pos, digit in enumerate(f"{second:02}"):
                x = 218 + pos * 98
                for name, (a, b, c, d) in zip("abcdefg", BARS):
                    draw.rectangle((x+a, 87+b, x+c, 87+d), fill="#65edcd" if name in DIGITS[int(digit)] else "#1d3448")
            draw.text((231, 249), "ELAPSED SECONDS", fill="#bdcbda", font_size=22)
            draw.rectangle((34, 307, 606, 314), fill="#284054")
            draw.rectangle((34, 307, 34 + round(572 * frame_no / 299), 314), fill="#65edcd")
            for packet in stream.encode(av.VideoFrame.from_image(image)):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)


if __name__ == "__main__":
    generate()

