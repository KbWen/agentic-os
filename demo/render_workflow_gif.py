#!/usr/bin/env python3
"""Render the README hero GIF: a terminal cast of one task, start to ship.

An agent classifies a task, attaches skills, and tries to ship -- the gate
blocks it for skipping review + tests, and only passes once evidence is real.
The gate-block format (gate/verdict/missing) is the real one from AGENTS.md;
validate.sh genuinely fails a feature work log that records a ship receipt
without review/test receipts. This is a recording aid depicting that behavior,
not a runnable script -- the runnable proof is the credential gate, bash demo/run.sh.

Needs Pillow (not a framework dependency). Regenerate:  python demo/render_workflow_gif.py
Output: docs/assets/workflow-demo.gif
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BG, BAR_C = (13, 17, 23), (22, 27, 34)
FG, DIM, WHITE = (201, 209, 217), (139, 148, 158), (240, 246, 252)
GREEN, YELLOW, RED = (63, 185, 80), (210, 153, 34), (248, 81, 73)
DOTS = [(247, 95, 86), (245, 191, 79), (98, 197, 84)]

FS, LH, PAD, BAR = 18, 30, 28, 36
W = 780


def _font(names, size):
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except Exception:
            continue
    return ImageFont.load_default()


REG = _font(["C:/Windows/Fonts/consola.ttf", "consola.ttf", "DejaVuSansMono.ttf"], FS)
BOLD = _font(["C:/Windows/Fonts/consolab.ttf", "consolab.ttf", "DejaVuSansMono-Bold.ttf"], FS)

# (segments=[(text,color)...], bold)
LINES = [
    ([("> ", GREEN), ("Add rate limiting to POST /login", FG)], False),
    ([], False),
    ([("  classification  ", DIM), ("feature", YELLOW), ("      skills  ", DIM), ("auth-security, tdd", FG)], False),
    ([], False),
    ([("  agent  ", DIM), ('"Done - rate limiting added. Shipping it."', WHITE)], False),
    ([("> ", GREEN), ("/ship", FG)], False),
    ([], False),
    ([("  gate: ship     verdict: ", DIM), ("FAIL", RED), ("     missing: ", DIM), ("[review, test]", RED)], False),
    ([('  ×  "done" - but the work trail has no review, no tests', RED)], True),
    ([], False),
    ([("  review ", DIM), ("done", GREEN), ("    test ", DIM), ("done", GREEN), ("    evidence recorded", DIM)], False),
    ([("> ", GREEN), ("/ship", FG)], False),
    ([("  verdict: ", DIM), ("PASS", GREEN), (" - shipped, evidence on file", FG)], True),
]
H = BAR + PAD + len(LINES) * LH + PAD - 6

# (lines_shown, duration_ms, cursor)
STEPS = [
    (1, 850, True),
    (3, 1100, False),
    (5, 1400, True),
    (9, 2100, False),
    (11, 1000, False),
    (13, 3600, False),
]


def render(n, cursor):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, BAR], fill=BAR_C)
    cy = BAR // 2
    for i, c in enumerate(DOTS):
        cx = 22 + i * 19
        d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=c)
    d.text((W // 2, cy), "agentic-os", font=REG, fill=DIM, anchor="mm")
    y = BAR + PAD - 4
    for li in range(n):
        segs, bold = LINES[li]
        f = BOLD if bold else REG
        x = PAD
        for text, color in segs:
            d.text((x, y), text, font=f, fill=color)
            x += d.textlength(text, font=f)
        if cursor and li == n - 1:
            d.rectangle([x + 3, y + 2, x + 13, y + FS + 2], fill=FG)
        y += LH
    return img


frames = [render(n, c) for (n, _, c) in STEPS]
durs = [d for (_, d, _) in STEPS]
out = Path("docs/assets")
out.mkdir(parents=True, exist_ok=True)
frames[0].save(out / "workflow-demo.gif", save_all=True, append_images=frames[1:],
               duration=durs, loop=0, optimize=True, disposal=2)
render(10, False).save(out / "_qa_block.png")   # the enforcement beat
frames[-1].save(out / "_qa_last.png")           # the pass beat
print(f"wrote {out/'workflow-demo.gif'}  ({W}x{H}, {len(frames)} frames)")
