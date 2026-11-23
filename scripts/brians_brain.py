"""Generate an animated SMIL SVG of Brian's Brain (3-state cellular automaton) on a 40x40 grid."""

import random
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

# States: 0 = Off, 1 = Firing, 2 = Refractory
STATE_COLORS = {
    0: "#1C1C21",
    1: "#E4E4E7",
    2: "#52525B",
}
BG_COLOR = "#141414"
BORDER_COLOR = "#27272A"


def simulate_brians_brain(cols: int, rows: int, steps: int):
    """Run Brian's Brain on a 40x40 toroidal grid and record state transitions."""
    rng = random.Random(42)
    grid = [[0] * cols for _ in range(rows)]
    for y in range(13, 37):
        for x in range(13, 37):
            if rng.random() < 0.36:
                grid[y][x] = 1

    cell_events = {
        (cx, cy): [(0.0, STATE_COLORS[grid[cy][cx]])]
        for cy in range(rows)
        for cx in range(cols)
    }

    for step in range(1, steps + 1):
        t = step / steps
        next_grid = [[0] * cols for _ in range(rows)]
        for y in range(rows):
            for x in range(cols):
                state = grid[y][x]
                if state == 1:
                    nxt = 2  # Firing -> Refractory
                elif state == 2:
                    nxt = 0  # Refractory -> Off
                else:
                    firing_neighbors = 0
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dx == 0 and dy == 0:
                                continue
                            if grid[(y + dy) % rows][(x + dx) % cols] == 1:
                                firing_neighbors += 1
                    nxt = 1 if firing_neighbors == 2 else 0
                next_grid[y][x] = nxt
                if nxt != state:
                    cell_events[(x, y)].append((t, STATE_COLORS[nxt]))
        grid = next_grid

    return cell_events


def build_svg() -> str:
    cell_events = simulate_brians_brain(COLS, ROWS, STEPS)

    width = PAD_X * 2 + COLS * PITCH - GAP
    height = PAD_TOP + ROWS * PITCH - GAP + PAD_BOT

    lines = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg">',
        f'  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="8" fill="{BG_COLOR}" stroke="{BORDER_COLOR}" />',
        f'  <text x="{PAD_X}" y="16" fill="#71717A" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="9.5" font-weight="600" letter-spacing="0.8">BRIAN\'S BRAIN</text>',
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
    out_path = Path(__file__).resolve().parent.parent / "output" / "brians-brain.svg"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_svg(), encoding="utf-8")
    print(f"Generated {out_path}")
