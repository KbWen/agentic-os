#!/usr/bin/env python3
"""Render the README concept hero: a marketing-flavored image, not a terminal.

The joke every dev gets: an AI agent confidently claims "Done. Tests pass."
and Agentic OS stamps it "[ citation needed ]". Conveys the concept (claims
need evidence) with a bit of tech humor. Static PNG, designed to read in 2s.

Needs Pillow (not a framework dependency). Regenerate:  python demo/render_concept_hero.py
Output: docs/assets/concept-hero.png
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 900, 460
BG = (13, 17, 23)
CARD = (22, 27, 34)
BORDER = (48, 54, 61)
FG = (201, 209, 217)
DIM = (139, 148, 158)
FAINT = (94, 102, 112)
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


def SANS(s):  return _font(["C:/Windows/Fonts/segoeui.ttf", "segoeui.ttf", "DejaVuSans.ttf"], s)
def SANSB(s): return _font(["C:/Windows/Fonts/segoeuib.ttf", "segoeuib.ttf", "DejaVuSans-Bold.ttf"], s)
def MONO(s):  return _font(["C:/Windows/Fonts/consola.ttf", "consola.ttf", "DejaVuSansMono.ttf"], s)
def MONOB(s): return _font(["C:/Windows/Fonts/consolab.ttf", "consolab.ttf", "DejaVuSansMono-Bold.ttf"], s)


img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

# thin green accent bar, left edge — a designed touch
d.rectangle([0, 0, 5, H], fill=GREEN)

PAD = 52

# wordmark
d.text((PAD, 34), "agentic-os", font=MONO(20), fill=DIM)

# agent label
d.text((PAD, 96), "your AI coding agent", font=SANS(20), fill=DIM)

# chat bubble with the confident claim
bx0, by0, bx1, by1 = PAD, 128, PAD + 540, 214
d.rounded_rectangle([bx0, by0, bx1, by1], radius=16, fill=CARD, outline=BORDER, width=1)
# little green check, then the claim
cx, cy = bx0 + 30, by0 + 44
d.line([(cx, cy), (cx + 8, cy + 9), (cx + 22, cy - 13)], fill=GREEN, width=4, joint="curve")
d.text((bx0 + 64, by0 + 26), "Done. Tests pass. Shipping it.", font=MONO(25), fill=WHITE)

# red rubber stamp "[ citation needed ]" slammed over the bubble
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

# tagline — the value, with wit
d.text((PAD, 268), "Your AI agent says it's done.", font=SANSB(38), fill=WHITE)
d.text((PAD, 314), "Agentic OS", font=SANSB(38), fill=GREEN)
tlen = d.textlength("Agentic OS", font=SANSB(38))
d.text((PAD + tlen, 314), " wants the receipts.", font=SANSB(38), fill=WHITE)

# concrete sub-line
d.text((PAD, 380), "Leaked secrets, missing tests, skipped reviews — caught by your git hooks",
       font=SANS(20), fill=DIM)
d.text((PAD, 408), "and CI, not the agent's word.", font=SANS(20), fill=DIM)

out = Path("docs/assets")
out.mkdir(parents=True, exist_ok=True)
img.save(out / "concept-hero.png")
print(f"wrote {out/'concept-hero.png'}  ({W}x{H})")
