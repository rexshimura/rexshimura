"""Generate an animated SMIL SVG of Langton's Ant on a 53x7 contribution-style grid."""

from pathlib import Path

COLS = 50
ROWS = 50
CELL = 4
GAP = 1
PITCH = CELL + GAP
PAD_X = 12
PAD_TOP = 24
PAD_BOT = 12

STEPS = 300
DURATION_SEC = 30.0  # 0.1s per step

OFF_COLOR = "#1C1C21"
ON_COLOR = "#E4E4E7"
ANT_COLOR = "#FF6B35"
BG_COLOR = "#141414"
BORDER_COLOR = "#27272A"


def simulate_langtons_ant(cols: int, rows: int, steps: int):
    """Run Langton's Ant on a toroidal grid and record cell flips + ant positions."""
    grid = [[0] * cols for _ in range(rows)]
    x, y = cols // 2, rows // 2
    # 0=up, 1=right, 2=down, 3=left
    direction = 0
    dirs = [(0, -1), (1, 0), (0, 1), (-1, 0)]

    ant_positions = [(x, y)]
    cell_events = {(cx, cy): [(0.0, OFF_COLOR)] for cy in range(rows) for cx in range(cols)}

    for step in range(1, steps + 1):
        t = step / steps
        if grid[y][x] == 0:
            direction = (direction + 1) % 4
            grid[y][x] = 1
            cell_events[(x, y)].append((t, ON_COLOR))
        else:
            direction = (direction - 1) % 4
            grid[y][x] = 0
            cell_events[(x, y)].append((t, OFF_COLOR))

        dx, dy = dirs[direction]
        x = (x + dx) % cols
        y = (y + dy) % rows
        ant_positions.append((x, y))

    return ant_positions, cell_events


def build_svg() -> str:
    ant_positions, cell_events = simulate_langtons_ant(COLS, ROWS, STEPS)

    width = PAD_X * 2 + COLS * PITCH - GAP
    height = PAD_TOP + ROWS * PITCH - GAP + PAD_BOT

    lines = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg">',
        f'  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="8" fill="{BG_COLOR}" stroke="{BORDER_COLOR}" />',
        f'  <text x="{PAD_X}" y="16" fill="#71717A" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="9.5" font-weight="600" letter-spacing="0.8">LANGTON\'S ANT</text>',
    ]

    for cy in range(ROWS):
        for cx in range(COLS):
            px = PAD_X + cx * PITCH
            py = PAD_TOP + cy * PITCH
            events = cell_events[(cx, cy)]
            if len(events) == 1:
                lines.append(
                    f'  <rect x="{px}" y="{py}" width="{CELL}" height="{CELL}" rx="1" fill="{OFF_COLOR}" />'
                )
            else:
                values = ";".join(color for _, color in events)
                key_times = ";".join(f"{t:.4f}" for t, _ in events)
                lines.append(
                    f'  <rect x="{px}" y="{py}" width="{CELL}" height="{CELL}" rx="1" fill="{OFF_COLOR}">'
                    f'<animate attributeName="fill" values="{values}" keyTimes="{key_times}" calcMode="discrete" dur="{DURATION_SEC}s" repeatCount="indefinite" />'
                    f"</rect>"
                )

    ant_xs = ";".join(str(PAD_X + ax * PITCH) for ax, _ in ant_positions[:-1])
    ant_ys = ";".join(str(PAD_TOP + ay * PITCH) for _, ay in ant_positions[:-1])
    ant_kt = ";".join(f"{i / STEPS:.4f}" for i in range(STEPS))
    init_ax = PAD_X + ant_positions[0][0] * PITCH
    init_ay = PAD_TOP + ant_positions[0][1] * PITCH

    lines.append(
        f'  <rect x="{init_ax}" y="{init_ay}" width="{CELL}" height="{CELL}" rx="1" fill="{ANT_COLOR}">'
        f'<animate attributeName="x" values="{ant_xs}" keyTimes="{ant_kt}" calcMode="discrete" dur="{DURATION_SEC}s" repeatCount="indefinite" />'
        f'<animate attributeName="y" values="{ant_ys}" keyTimes="{ant_kt}" calcMode="discrete" dur="{DURATION_SEC}s" repeatCount="indefinite" />'
        f"</rect>"
    )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    out_path = Path(__file__).resolve().parent.parent / "output" / "langtons-ant.svg"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_svg(), encoding="utf-8")
    print(f"Generated {out_path}")
