#!/usr/bin/env python3
"""繁體中文 workflow GIF — zh-TW twin of render_workflow_gif.py.

Same lying-agent story, prose localized. English tokens (verdict, /ship, FAIL)
stay in Consolas (terminal feel); 繁中 prose uses Microsoft JhengHei, picked
per text segment. Pillow + JhengHei. Output: docs/assets/workflow-demo-zh.gif
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BG, BAR_C = (13, 17, 23), (22, 27, 34)
FG, DIM, WHITE = (201, 209, 217), (139, 148, 158), (240, 246, 252)
GREEN, YELLOW, RED = (63, 185, 80), (210, 153, 34), (248, 81, 73)
DOTS = [(247, 95, 86), (245, 191, 79), (98, 197, 84)]
FS, LH, PAD, BAR = 18, 30, 28, 36
W = 800


def _f(names, s):
    for n in names:
        try:
            return ImageFont.truetype(n, s)
        except Exception:
            continue
    return ImageFont.load_default()


REG = _f(["C:/Windows/Fonts/consola.ttf", "DejaVuSansMono.ttf"], FS)
BOLD = _f(["C:/Windows/Fonts/consolab.ttf", "DejaVuSansMono-Bold.ttf"], FS)
HAN = _f(["C:/Windows/Fonts/msjh.ttc", "msjh.ttf"], FS)
HANB = _f(["C:/Windows/Fonts/msjhbd.ttc", "msjhbd.ttf"], FS)


def has_cjk(t):
    return any('一' <= c <= '鿿' or '　' <= c <= '〿' or '＀' <= c <= '￯' for c in t)


def pick(text, bold):
    if has_cjk(text):
        return HANB if bold else HAN
    return BOLD if bold else REG


LINES = [
    ([("> ", GREEN), ("為 POST /login 加上 rate limiting", FG)], False),
    ([], False),
    ([("  分類 ", DIM), ("feature", YELLOW), ("      技能 ", DIM), ("auth-security, tdd", FG)], False),
    ([], False),
    ([("  agent  ", DIM), ("「Done — rate limiting 加好了,要 ship。」", WHITE)], False),
    ([("> ", GREEN), ("/ship", FG)], False),
    ([], False),
    ([("  gate: ship     verdict: ", DIM), ("FAIL", RED), ("     missing: ", DIM), ("[review, test]", RED)], False),
    ([("  ×  說「done」,但 work trail 裡沒有 review、沒有 test", RED)], True),
    ([], False),
    ([("  review ", DIM), ("done", GREEN), ("    test ", DIM), ("done", GREEN), ("    證據已記錄", DIM)], False),
    ([("> ", GREEN), ("/ship", FG)], False),
    ([("  verdict: ", DIM), ("PASS", GREEN), (", 帶著證據 ship 了", FG)], True),
]
H = BAR + PAD + len(LINES) * LH + PAD - 6

STEPS = [(1, 850, True), (3, 1100, False), (5, 1400, True), (9, 2100, False), (11, 1000, False), (13, 3600, False)]


def render(n, cursor):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, BAR], fill=BAR_C)
    cy = BAR // 2
    for i, c in enumerate(DOTS):
        d.ellipse([22 + i * 19 - 6, cy - 6, 22 + i * 19 + 6, cy + 6], fill=c)
    d.text((W // 2, cy), "agentic-os", font=REG, fill=DIM, anchor="mm")
    y = BAR + PAD - 4
    for li in range(n):
        segs, bold = LINES[li]
        x = PAD
        for text, color in segs:
            f = pick(text, bold)
            d.text((x, y), text, font=f, fill=color)
            x += d.textlength(text, font=f)
        if cursor and li == n - 1:
            d.rectangle([x + 3, y + 2, x + 13, y + FS + 2], fill=FG)
        y += LH
    return img


frames = [render(n, c) for (n, _, c) in STEPS]
out = Path("docs/assets")
out.mkdir(parents=True, exist_ok=True)
frames[0].save(out / "workflow-demo-zh.gif", save_all=True, append_images=frames[1:],
               duration=[d for (_, d, _) in STEPS], loop=0, optimize=True, disposal=2)
render(13, False).save(out / "_qa_wzh.png")
print(f"wrote {out/'workflow-demo-zh.gif'}  ({W}x{H}, {len(frames)} frames)")
