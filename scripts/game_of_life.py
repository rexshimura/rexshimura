"""Generate an animated SMIL SVG of Conway's Game of Life (Gosper Glider Gun) on a 50x50 grid."""

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
DURATION_SEC = 30.0  # 0.1s per generation

OFF_COLOR = "#1C1C21"
ON_COLOR = "#E4E4E7"
BG_COLOR = "#141414"
BORDER_COLOR = "#27272A"

# Classic Gosper Glider Gun (36x9) on 50x50 grid
SEED_CELLS = [
    (24, 0),
    (22, 1), (24, 1),
    (12, 2), (13, 2), (20, 2), (21, 2), (34, 2), (35, 2),
    (11, 3), (15, 3), (20, 3), (21, 3), (34, 3), (35, 3),
    (0, 4), (1, 4), (10, 4), (16, 4), (20, 4), (21, 4),
    (0, 5), (1, 5), (10, 5), (14, 5), (16, 5), (17, 5), (22, 5), (24, 5),
    (10, 6), (16, 6), (24, 6),
    (11, 7), (15, 7),
    (12, 8), (13, 8),
]


def simulate_life(cols: int, rows: int, steps: int):
    """Run Conway's Game of Life (B3/S23) with open boundaries and record cell transitions."""
    grid = [[0] * cols for _ in range(rows)]
    for gx, gy in SEED_CELLS:
        x, y = gx + 3, gy + 4
        if 0 <= x < cols and 0 <= y < rows:
            grid[y][x] = 1

    cell_events = {
        (cx, cy): [(0.0, ON_COLOR if grid[cy][cx] else OFF_COLOR)]
        for cy in range(rows)
        for cx in range(cols)
    }

    for step in range(1, steps + 1):
        t = step / steps
        next_grid = [[0] * cols for _ in range(rows)]
        for y in range(rows):
            for x in range(cols):
                neighbors = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < cols and 0 <= ny < rows:
                            neighbors += grid[ny][nx]
                alive = grid[y][x]
                nxt = 1 if (alive and neighbors in (2, 3)) or (not alive and neighbors == 3) else 0
                next_grid[y][x] = nxt
                if nxt != alive:
                    cell_events[(x, y)].append((t, ON_COLOR if nxt else OFF_COLOR))
        grid = next_grid

    return cell_events


def build_svg() -> str:
    cell_events = simulate_life(COLS, ROWS, STEPS)

    width = PAD_X * 2 + COLS * PITCH - GAP
    height = PAD_TOP + ROWS * PITCH - GAP + PAD_BOT

    lines = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg">',
        f'  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="8" fill="{BG_COLOR}" stroke="{BORDER_COLOR}" />',
        f'  <text x="{PAD_X}" y="16" fill="#71717A" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="9.5" font-weight="600" letter-spacing="0.8">GAME OF LIFE</text>',
    ]

    for cy in range(ROWS):
        for cx in range(COLS):
            px = PAD_X + cx * PITCH
            py = PAD_TOP + cy * PITCH
            events = cell_events[(cx, cy)]
            init_color = events[0][1]
            if len(events) == 1:
                lines.append(
                    f'  <rect x="{px}" y="{py}" width="{CELL}" height="{CELL}" rx="1" fill="{init_color}" />'
                )
            else:
                values = ";".join(color for _, color in events)
                key_times = ";".join(f"{t:.4f}" for t, _ in events)
                lines.append(
                    f'  <rect x="{px}" y="{py}" width="{CELL}" height="{CELL}" rx="1" fill="{init_color}">'
                    f'<animate attributeName="fill" values="{values}" keyTimes="{key_times}" calcMode="discrete" dur="{DURATION_SEC}s" repeatCount="indefinite" />'
                    f"</rect>"
                )

    lines.append("</svg>")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    out_path = Path(__file__).resolve().parent.parent / "output" / "game-of-life.svg"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_svg(), encoding="utf-8")
    print(f"Generated {out_path}")
