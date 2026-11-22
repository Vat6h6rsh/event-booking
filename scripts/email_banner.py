"""Generate the pixel-art marquee banner used in the booking confirmation email.

Drawn at true low resolution (120x36) and upscaled nearest-neighbour, so every
"pixel" is a crisp square. Output: frontend/public/images/email/marquee.gif,
which the deployed frontend serves publicly for email clients to load.

Build-time only (not an app dependency):
    pip install pillow
    python scripts/email_banner.py
"""
from pathlib import Path

from PIL import Image

W, H, SCALE, FRAMES = 120, 36, 5, 6
OUT = Path(__file__).resolve().parent.parent / "frontend/public/images/email/marquee.gif"

NIGHT, NIGHT2 = (27, 16, 53), (38, 22, 74)
RED, RED_DK, YELLOW, CREAM, OFF = (215, 38, 61), (130, 18, 36), (255, 201, 60), (255, 244, 220), (92, 58, 70)

FONT = {  # 5x7 bitmap glyphs
    "A": [" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"],
    "C": [" ####", "#    ", "#    ", "#    ", "#    ", "#    ", " ####"],
    "D": ["#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "],
    "E": ["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"],
    "I": ["#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "#####"],
    "J": ["  ###", "   # ", "   # ", "   # ", "   # ", "#  # ", " ##  "],
    "K": ["#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"],
    "M": ["#   #", "## ##", "# # #", "# # #", "#   #", "#   #", "#   #"],
    "N": ["#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"],
    "O": [" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "],
    "S": [" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "],
    "T": ["#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "],
    " ": ["     "] * 7,
}
STAR = [" # ", "###", " # "]


def text(px, s, x0, y0, color, shadow=None):
    for i, ch in enumerate(s):
        for y, row in enumerate(FONT[ch]):
            for x, bit in enumerate(row):
                if bit == "#":
                    if shadow: px[x0 + i * 6 + x + 1, y0 + y + 1] = shadow
                    px[x0 + i * 6 + x, y0 + y] = color


def centered(s):
    return (W - (len(s) * 6 - 1)) // 2


def bulbs():
    """Positions of marquee bulbs around the border, in chase order."""
    top = [(x, 1) for x in range(2, W - 2, 4)]
    right = [(W - 3, y) for y in range(5, H - 2, 4)]
    bottom = [(x, H - 3) for x in range(W - 6, 1, -4)]
    left = [(1, y) for y in range(H - 7, 4, -4)]
    return top + right + bottom + left


def frame(n):
    img = Image.new("RGB", (W, H), NIGHT)
    px = img.load()
    for y in range(4, H - 4):  # subtle striped "tent" backdrop
        for x in range(4, W - 4):
            if ((x + y) // 6) % 2: px[x, y] = NIGHT2
    for i, (x, y) in enumerate(bulbs()):  # 3-phase chasing lights
        c = YELLOW if (i + n) % 3 == 0 else OFF
        for dx in (0, 1):
            for dy in (0, 1):
                px[x + dx, y + dy] = c
    text(px, "JTICKETS", centered("JTICKETS"), 8, YELLOW, shadow=RED_DK)
    for x in range(centered("ADMIT ONE") - 2, W - centered("ADMIT ONE") + 2):  # red ribbon
        for y in range(18, 29):
            px[x, y] = RED
    text(px, "ADMIT ONE", centered("ADMIT ONE"), 20, CREAM, shadow=RED_DK)
    for k, (sx, sy) in enumerate([(12, 12), (104, 10), (16, 24), (100, 24)]):  # twinkling stars
        if (n + k) % 2 == 0:
            for y, row in enumerate(STAR):
                for x, bit in enumerate(row):
                    if bit == "#": px[sx + x, sy + y] = CREAM
    return img.resize((W * SCALE, H * SCALE), Image.NEAREST)


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frames = [frame(n) for n in range(FRAMES)]
    frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=160, loop=0, optimize=True)
    frames[0].save(OUT.with_suffix(".png"))  # still preview / fallback
    print(OUT, OUT.stat().st_size, "bytes")
