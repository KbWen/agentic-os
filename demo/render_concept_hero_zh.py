#!/usr/bin/env python3
"""Render the 繁體中文 concept hero — the zh-TW twin of render_concept_hero.py.

Same joke (the agent's confident claim gets a "[ citation needed ]" stamp; the
"[citation needed]" meme and the agent's English claim are kept verbatim — both
read the same to a Traditional-Chinese developer), tagline + sub-line in 繁中.

Needs Pillow + Microsoft JhengHei (Windows CJK font). Regenerate:
  python demo/render_concept_hero_zh.py     Output: docs/assets/concept-hero-zh.png
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 900, 470
BG = (13, 17, 23)
CARD = (22, 27, 34)
BORDER = (48, 54, 61)
DIM = (139, 148, 158)
WHITE = (240, 246, 252)
GREEN = (63, 185, 80)
RED = (248, 81, 73)


def _font(names, size):
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except Exception:
            continue
    return ImageFont.load_default()


def HAN(s):  return _font(["C:/Windows/Fonts/msjh.ttc", "C:/Windows/Fonts/msjh.ttf", "msjh.ttc"], s)
def HANB(s): return _font(["C:/Windows/Fonts/msjhbd.ttc", "C:/Windows/Fonts/msjhbd.ttf", "msjhbd.ttc"], s)
def MONO(s): return _font(["C:/Windows/Fonts/consola.ttf", "consola.ttf", "DejaVuSansMono.ttf"], s)
def MONOB(s): return _font(["C:/Windows/Fonts/consolab.ttf", "consolab.ttf", "DejaVuSansMono-Bold.ttf"], s)


img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
d.rectangle([0, 0, 5, H], fill=GREEN)

PAD = 52
d.text((PAD, 34), "agentic-os", font=MONO(20), fill=DIM)
d.text((PAD, 96), "你的 AI coding agent", font=HAN(20), fill=DIM)

# chat bubble + claim (kept English — the agent's own output)
bx0, by0, bx1, by1 = PAD, 128, PAD + 540, 214
d.rounded_rectangle([bx0, by0, bx1, by1], radius=16, fill=CARD, outline=BORDER, width=1)
cx, cy = bx0 + 30, by0 + 44
d.line([(cx, cy), (cx + 8, cy + 9), (cx + 22, cy - 13)], fill=GREEN, width=4, joint="curve")
d.text((bx0 + 64, by0 + 26), "Done. Tests pass. Shipping it.", font=MONO(25), fill=WHITE)

# red rubber stamp "[ citation needed ]" (kept English meme)
sw, sh = 340, 96
st = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
sd = ImageDraw.Draw(st)
ink = (248, 81, 73, 230)
sd.rounded_rectangle([5, 5, sw - 5, sh - 5], radius=12, outline=ink, width=5)
sf = MONOB(31)
tw = sd.textlength("[ citation needed ]", font=sf)
sd.text(((sw - tw) / 2, (sh - 38) / 2), "[ citation needed ]", font=sf, fill=ink)
st = st.rotate(8, expand=True, resample=Image.BICUBIC)
img.paste(st, (bx1 - 150, by0 - 6), st)

# tagline (繁中)
d.text((PAD, 268), "你的 AI 說它做完了。", font=HANB(38), fill=WHITE)
d.text((PAD, 320), "Agentic OS", font=HANB(38), fill=GREEN)
tlen = d.textlength("Agentic OS", font=HANB(38))
d.text((PAD + tlen, 320), " 要它拿出證據。", font=HANB(38), fill=WHITE)

# concrete sub-line (繁中)
d.text((PAD, 388), "外洩的密鑰、沒寫的測試、被跳過的 review —— 由 git hooks 和 CI 把關,",
       font=HAN(20), fill=DIM)
d.text((PAD, 418), "不是聽 agent 自己說。", font=HAN(20), fill=DIM)

out = Path("docs/assets")
out.mkdir(parents=True, exist_ok=True)
img.save(out / "concept-hero-zh.png")
print(f"wrote {out/'concept-hero-zh.png'}  ({W}x{H})")
