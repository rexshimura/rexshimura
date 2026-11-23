"""Format animated GIFs into widescreen rounded banners matching GitHub Dark (#0d1117)."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageSequence

RADIUS = 8
BG_COLOR = (13, 17, 23)  # GitHub dark (#0d1117)


def build_rounded_mask(w: int, h: int, radius: int) -> Image.Image:
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    return mask


def build_vertical_fade(
    w: int,
    h: int,
    *,
    top_end: float = 0.0,
    bottom_start: float = 0.20,
    bottom_end: float = 0.90,
    power: float = 0.9,
) -> Image.Image:
    """Create an RGBA overlay that fades top and/or bottom edges into BG_COLOR."""
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    top_px = int(h * top_end)
    bot_start_px = int(h * bottom_start)
    bot_end_px = int(h * bottom_end)

    for y in range(h):
        alpha = 0
        if top_px > 0 and y < top_px:
            t = 1.0 - (y / top_px)
            alpha = max(alpha, int(255 * (t ** power)))
        if y >= bot_start_px:
            if y >= bot_end_px:
                alpha = 255
            else:
                t = (y - bot_start_px) / max(1, bot_end_px - bot_start_px)
                alpha = max(alpha, int(255 * (t ** power)))
        if alpha > 0:
            draw.line([(0, y), (w, y)], fill=(BG_COLOR[0], BG_COLOR[1], BG_COLOR[2], alpha))

    return overlay


def load_clip_frames(
    src: Path,
    *,
    target_w: int,
    target_h: int,
    crop_ref_h: int,
    trim_start: int,
    frame_step: int,
    mask: Image.Image,
    fade: Image.Image,
) -> tuple[list[Image.Image], list[int]]:
    """Load, resize, crop, and apply rounded corners + fade to all frames of a GIF."""
    im = Image.open(src)
    rgb_frames: list[Image.Image] = []
    durations: list[int] = []

    for idx, frame in enumerate(ImageSequence.Iterator(im)):
        if idx < trim_start or (idx - trim_start) % frame_step != 0:
            continue
        rgba = frame.convert("RGBA")
        scale_h = round(rgba.height * (target_w / rgba.width))
        resized = rgba.resize((target_w, scale_h), Image.Resampling.LANCZOS)
        top = max(0, (scale_h - crop_ref_h) // 2)
        cropped = resized.crop((0, top, target_w, top + target_h))

        composited = Image.alpha_composite(cropped, fade)
        canvas = Image.new("RGBA", (target_w, target_h), (*BG_COLOR, 255))
        canvas.paste(composited, (0, 0), mask)

        rgb_frames.append(canvas.convert("RGB"))
        durations.append(frame.info.get("duration", 100) * frame_step)

    return rgb_frames, durations


def crossfade_loop(
    clips: list[tuple[list[Image.Image], list[int]]],
    overlap: int,
) -> tuple[list[Image.Image], list[int]]:
    """Concatenate clips with smooth crossfades between each clip and back to the first."""
    if overlap <= 0:
        all_frames: list[Image.Image] = []
        all_durations: list[int] = []
        for frames, durations in clips:
            all_frames.extend(frames)
            all_durations.extend(durations)
        return all_frames, all_durations

    out_frames: list[Image.Image] = []
    out_durations: list[int] = []
    count = len(clips)

    for idx, (frames, durations) in enumerate(clips):
        next_frames, _ = clips[(idx + 1) % count]
        body = frames[overlap:]
        body_dur = durations[overlap:]
        n = len(body)
        for i, frame in enumerate(body):
            if i >= n - overlap:
                j = i - (n - overlap)
                alpha = (j + 1) / (overlap + 1)
                out_frames.append(Image.blend(frame, next_frames[j], alpha))
            else:
                out_frames.append(frame)
            out_durations.append(body_dur[i])

    return out_frames, out_durations


def save_gif(rgb_frames: list[Image.Image], durations: list[int], dst: Path) -> None:
    global_palette = rgb_frames[0].quantize(colors=64, method=Image.Quantize.MEDIANCUT)
    frames = [
        f.quantize(palette=global_palette, dither=Image.Dither.NONE)
        for f in rgb_frames
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
    print(f"Generated {dst} ({frames[0].size[0]}x{frames[0].size[1]}, {len(frames)} frames)")


def build_top_sequence(root: Path) -> None:
    w, h = 840, 175
    mask = build_rounded_mask(w, h, RADIUS)
    fade = build_vertical_fade(w, h, top_end=0.0, bottom_start=0.20, bottom_end=0.90, power=0.9)

    sources = [
        (root / "public" / "banner_loop.gif", 220, 10),
        (root / "public" / "eye_loop.gif", 175, 0),
        (root / "public" / "angel_loop.gif", 175, 0),
    ]
    clips = [
        load_clip_frames(
            src,
            target_w=w,
            target_h=h,
            crop_ref_h=ref_h,
            trim_start=trim,
            frame_step=1,
            mask=mask,
            fade=fade,
        )
        for src, ref_h, trim in sources
    ]
    loop_frames, loop_durations = crossfade_loop(clips, overlap=8)
    save_gif(loop_frames, loop_durations, root / "output" / "banner.gif")


def build_bottom_banner(root: Path) -> None:
    w, h = 840, 210
    mask = build_rounded_mask(w, h, RADIUS)
    fade = build_vertical_fade(w, h, top_end=0.28, bottom_start=0.72, bottom_end=0.96, power=1.0)
    frames, durations = load_clip_frames(
        root / "public" / "self_blaming_self.gif",
        target_w=w,
        target_h=h,
        crop_ref_h=h,
        trim_start=10,
        frame_step=2,
        mask=mask,
        fade=fade,
    )
    save_gif(frames, durations, root / "output" / "banner-bottom.gif")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    build_top_sequence(project_root)
    build_bottom_banner(project_root)
