#!/usr/bin/env python3
"""Render the README hero GIF: an authentic terminal cast of demo/run.sh.

A leaked key is "committed" by an agent that claims done; the credential gate
catches it and the build goes red. This renders the same story demo/run.sh runs
live -- it is a recording aid, not a fake (the real demo is bash demo/run.sh).

Needs Pillow (not a framework dependency). Regenerate:  python demo/render_hero_gif.py
Output: docs/assets/hero-demo.gif
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BG, BAR_C = (13, 17, 23), (22, 27, 34)
FG, DIM, WHITE = (201, 209, 217), (139, 148, 158), (240, 246, 252)
GREEN, YELLOW, RED = (63, 185, 80), (210, 153, 34), (248, 81, 73)
DOTS = [(247, 95, 86), (245, 191, 79), (98, 197, 84)]

FS, LH, PAD, BAR = 18, 30, 28, 36
W = 760


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
    ([("$ ", GREEN), ("bash demo/run.sh", FG)], False),
    ([], False),
    ([("  an agent wrote ", DIM), ("config.env", FG), (" and reported ", DIM), ('"Done."', WHITE)], False),
    ([], False),
    ([("    DB_HOST=prod.internal", DIM)], False),
    ([("    aws_access_key_id = ", DIM), ("AKIA****************", YELLOW)], False),
    ([], False),
    ([("  $ ", GREEN), ("scan_credentials.py config.env", FG)], False),
    ([("  CREDENTIAL DETECTED", RED), ("  (value redacted)", DIM)], False),
    ([("    config.env:2: aws-access-key-id", RED)], False),
    ([], False),
    ([("  × BLOCKED", RED), ("  — the agent said done; the machine said no.", FG)], True),
]
H = BAR + PAD + len(LINES) * LH + PAD - 6

# (lines_shown, duration_ms, cursor)
STEPS = [(1, 750, True), (3, 850, False), (6, 850, False),
         (8, 800, True), (9, 500, False), (10, 650, False), (12, 3000, False)]


def render(n, cursor):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, BAR], fill=BAR_C)
    cy = BAR // 2
    for i, c in enumerate(DOTS):
        cx = 22 + i * 19
        d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=c)
    d.text((W // 2, cy), "agentic-os — demo", font=REG, fill=DIM, anchor="mm")
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
frames[0].save(out / "hero-demo.gif", save_all=True, append_images=frames[1:],
               duration=durs, loop=0, optimize=True, disposal=2)
frames[-1].save(out / "_qa_lastframe.png")
print(f"wrote {out/'hero-demo.gif'}  ({W}x{H}, {len(frames)} frames)")
