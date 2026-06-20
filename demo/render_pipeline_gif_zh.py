#!/usr/bin/env python3
"""繁體中文 pipeline GIF — zh-TW twin of render_pipeline_gif.py.

Title, lane labels and notes localized (Microsoft JhengHei); the phase pills
stay English because those are the framework's actual phase names. Same story:
a tiny-fix takes the short path; a feature is blocked at ship for skipping
tests, then passes. Pillow + JhengHei. Output: docs/assets/pipeline-demo-zh.gif
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 900, 372
BG = (13, 17, 23)
BORDER = (48, 54, 61)
DIM = (120, 128, 138)
WHITE = (240, 246, 252)
FG = (201, 209, 217)
AMBER = (210, 153, 34)
GREEN = (63, 185, 80)
RED = (248, 81, 73)
DIMBG = (26, 31, 38)
GREENBG = (17, 42, 26)
REDBG = (52, 24, 23)


def _f(names, s):
    for n in names:
        try:
            return ImageFont.truetype(n, s)
        except Exception:
            continue
    return ImageFont.load_default()


def SANS(s):  return _f(["C:/Windows/Fonts/segoeui.ttf", "DejaVuSans.ttf"], s)
def HAN(s):   return _f(["C:/Windows/Fonts/msjh.ttc", "msjh.ttf"], s)
def HANB(s):  return _f(["C:/Windows/Fonts/msjhbd.ttc", "msjhbd.ttf"], s)


PAD = 44
PW, PH, GAP = 100, 40, 15
LANE_X = PAD + 176


def pill(d, x, y, name, st):
    fill = {'p': DIMBG, 'd': GREENBG, 'b': REDBG}[st]
    edge = {'p': BORDER, 'd': GREEN, 'b': RED}[st]
    tc = {'p': DIM, 'd': WHITE, 'b': WHITE}[st]
    d.rounded_rectangle([x, y, x + PW, y + PH], radius=9, fill=fill, outline=edge, width=2)
    f = SANS(15)
    tw = d.textlength(name, font=f)
    d.text((x + (PW - tw) / 2, y + (PH - 15) / 2 - 1), name, font=f, fill=tc)


def lane(d, y, chip, cls, clscolor, nodes, states, note, notecolor, endmark=None):
    d.text((PAD, y + 1), chip, font=HANB(18), fill=FG)
    d.text((PAD, y + 26), cls, font=SANS(14), fill=clscolor)
    x = LANE_X
    for i, (nm, st) in enumerate(zip(nodes, states)):
        if i > 0:
            d.line([(x - GAP - 1, y + PH / 2), (x + 1, y + PH / 2)],
                   fill=GREEN if states[i - 1] == 'd' else BORDER, width=2)
        pill(d, x, y, nm, st)
        x += PW + GAP
    if endmark:
        d.text((x + 2, y + (PH - 16) / 2), endmark, font=HANB(16), fill=GREEN)
    if note:
        d.text((LANE_X, y + PH + 11), note, font=HAN(15), fill=notecolor)


TINY = ["classify", "execute", "done"]
FEAT = ["bootstrap", "plan", "implement", "review", "test", "ship"]


def frame(a_states, a_end, b_states, b_note, b_color):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 5, H], fill=GREEN)
    d.text((PAD, 28), "一套工作流,依任務縮放。", font=HANB(23), fill=WHITE)
    d.text((PAD, 64), "每個任務只跑它需要的閘門 —— 而且跳不掉。", font=HAN(16), fill=DIM)
    lane(d, 124, "修個 typo", "tiny-fix", DIM, TINY, a_states, None, DIM, endmark=a_end)
    lane(d, 238, "加 rate limiting", "feature", AMBER, FEAT, b_states, b_note, b_color)
    return img


F = [
    (["d", "p", "p"], None,       ["d", "p", "p", "p", "p", "p"], None, DIM),
    (["d", "d", "p"], None,       ["d", "d", "d", "p", "p", "p"], None, DIM),
    (["d", "d", "d"], "已 ship",  ["d", "d", "d", "d", "p", "p"], None, DIM),
    (["d", "d", "d"], "已 ship",  ["d", "d", "d", "d", "p", "b"], "×  ship 被擋 —— test 從沒跑過", RED),
    (["d", "d", "d"], "已 ship",  ["d", "d", "d", "d", "d", "p"], "test 完成 —— 證據已記錄", DIM),
    (["d", "d", "d"], "已 ship",  ["d", "d", "d", "d", "d", "d"], "帶著證據 ship 了", GREEN),
]
DUR = [850, 850, 1500, 1950, 1100, 3300]

frames = [frame(*x) for x in F]
out = Path("docs/assets")
out.mkdir(parents=True, exist_ok=True)
frames[0].save(out / "pipeline-demo-zh.gif", save_all=True, append_images=frames[1:],
               duration=DUR, loop=0, optimize=True, disposal=2)
frames[3].save(out / "_qa_pzh_block.png")
frames[-1].save(out / "_qa_pzh_last.png")
print(f"wrote {out/'pipeline-demo-zh.gif'}  ({W}x{H}, {len(frames)} frames)")
