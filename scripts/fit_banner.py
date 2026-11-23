"""Format public/banner_loop.gif into a widescreen 840x220 rounded banner matching the README theme."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageSequence

TARGET_W = 840
TARGET_H = 175
RADIUS = 8
BG_COLOR = (13, 17, 23)       # GitHub dark (#0d1117)
BORDER_COLOR = (39, 39, 42)   # #27272A (matches marquee & simulator cards)


def build_rounded_mask(w: int, h: int, radius: int) -> Image.Image:
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    return mask


def build_bottom_fade(w: int, h: int) -> Image.Image:
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    fade_start = int(h * 0.35)
    fade_end = int(h * 0.96)
    for y in range(fade_start, h):
        if y >= fade_end:
            alpha = 255
        else:
            t = (y - fade_start) / (fade_end - fade_start)
            alpha = int(255 * (t ** 1.4))
        draw.line([(0, y), (w, y)], fill=(BG_COLOR[0], BG_COLOR[1], BG_COLOR[2], alpha))
    return overlay


def process_banner(src: Path, dst: Path) -> None:
    im = Image.open(src)
    mask = build_rounded_mask(TARGET_W, TARGET_H, RADIUS)
    fade = build_bottom_fade(TARGET_W, TARGET_H)

    OVERLAP = 10  # Crossfade 10 frames (1.0s) for a seamless forward loop
    rgb_frames = []
    durations = []

    for idx, frame in enumerate(ImageSequence.Iterator(im)):
        if idx < 10:  # Trim first 1s (10 frames at 100ms)
            continue
        rgba = frame.convert("RGBA")
        # Scale width to TARGET_W while keeping aspect ratio, then trim extra off the bottom
        scale_h = round(rgba.height * (TARGET_W / rgba.width))
        resized = rgba.resize((TARGET_W, scale_h), Image.Resampling.LANCZOS)
        top = max(0, (scale_h - 220) // 2)
        cropped = resized.crop((0, top, TARGET_W, top + TARGET_H))

        # Apply full bottom fade + rounded corners over dark background (no hard bottom border)
        composited = Image.alpha_composite(cropped, fade)
        canvas = Image.new("RGBA", (TARGET_W, TARGET_H), (*BG_COLOR, 255))
        canvas.paste(composited, (0, 0), mask)

        rgb_frames.append(canvas.convert("RGB"))
        durations.append(frame.info.get("duration", 100))

    # Crossfade the tail into the head so the last frame flows seamlessly into frame 0
    head = rgb_frames[:OVERLAP]
    body = rgb_frames[OVERLAP:]
    n = len(body)
    loop_frames = []
    for i, frame in enumerate(body):
        if i >= n - OVERLAP:
            j = i - (n - OVERLAP)
            alpha = (j + 1) / (OVERLAP + 1)
            loop_frames.append(Image.blend(frame, head[j], alpha))
        else:
            loop_frames.append(frame)
    durations = durations[OVERLAP:]

    # Build one shared global palette from the first frame so delta frames never scramble colors
    global_palette = loop_frames[0].quantize(colors=64, method=Image.Quantize.MEDIANCUT)
    frames = [
        f.quantize(palette=global_palette, dither=Image.Dither.NONE)
        for f in loop_frames
    ]

    dst.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        dst,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        disposal=2,
        optimize=False,
    )
    print(f"Generated {dst} ({TARGET_W}x{TARGET_H}, {len(frames)} frames)")


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    process_banner(root / "public" / "banner_loop.gif", root / "output" / "banner.gif")
