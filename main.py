"""Make the AI judge happy - make.fun bounty ai-happy-01.

Entry for https://make.fun/bounty/ai-happy-01 (USD 250).

A deterministic, stdlib-only Python program. It paints one cheerful
picture (768 x 1024 PNG) for the AI judge: a pink ribbon that says
"DEAR JUDGE,", a hand-written style note, and a three-tier birthday
cake with candles, balloons and confetti.

Run:  python main.py

Output: exactly one image file, /output/output.png when /output exists,
otherwise ./output.png in the working directory. The picture is fully
deterministic: a fixed random seed, no time, no network, no files read.
Pixel text is drawn from a small 5x7 bitmap font defined below, and
the PNG is encoded by hand with zlib, so only the standard library
is used.
"""

import math
import os
import random
import struct
import zlib

W, H = 768, 1024

CREAM = (255, 246, 229)
WHITE = (255, 255, 255)
PLUM = (88, 40, 88)
PINK = (255, 92, 138)
DEEP_PINK = (226, 62, 110)
MINT = (124, 220, 178)
YELLOW = (255, 214, 102)
ORANGE = (255, 150, 60)
RED = (235, 70, 70)
BLUE = (90, 150, 255)
GREEN = (80, 190, 120)
SHADOW = (232, 222, 205)

PALETTE = [PINK, MINT, YELLOW, ORANGE, BLUE, (160, 120, 220), RED]

# 5x7 bitmap font: '#' is a filled pixel, '.' is empty.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", "01100", "01100"),
    ",": (".....", ".....", ".....", ".....", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", ".....", "00100"),
    "-": (".....", ".....", ".....", "01110", ".....", ".....", "....."),
    "'": ("00100", "00100", "01000", ".....", ".....", ".....", "....."),
    ":": (".....", "01100", "01100", ".....", "01100", "01100", "....."),
    "?": ("01110", "10001", "00001", "00110", "00100", ".....", "00100"),
}


class Img:
    """A plain RGB pixel buffer with small drawing helpers."""

    def __init__(self, w, h, colour):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.rect(0, 0, w, h, colour)

    def set(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = colour

    def rect(self, x, y, w, h, colour):
        for yy in range(max(0, y), min(self.h, y + h)):
            for xx in range(max(0, x), min(self.w, x + w)):
                self.set(xx, yy, colour)

    def rrect(self, x, y, w, h, r, colour):
        self.rect(x + r, y, w - 2 * r, h, colour)
        self.rect(x, y + r, w, h - 2 * r, colour)
        for cx, cy in ((x + r, y + r), (x + w - r - 1, y + r),
                       (x + r, y + h - r - 1), (x + w - r - 1, y + h - r - 1)):
            self.disc(cx, cy, r, colour)

    def disc(self, cx, cy, r, colour):
        self.ellipse(cx, cy, r, r, colour)

    def ellipse(self, cx, cy, rx, ry, colour):
        if rx <= 0 or ry <= 0:
            return
        for dy in range(-ry, ry + 1):
            dx = int(rx * math.sqrt(max(0.0, 1.0 - (dy * dy) / float(ry * ry))))
            self.rect(cx - dx, cy + dy, 2 * dx + 1, 1, colour)

    def line(self, x0, y0, x1, y1, colour, thick=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.disc(x, y, max(1, thick // 2), colour)
            if x == x1 and y == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def poly(self, pts, colour):
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            for i in range(len(pts)):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % len(pts)]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / float(y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.rect(int(xs[i]), y, int(xs[i + 1]) - int(xs[i]) + 1, 1, colour)

    def heart(self, cx, cy, s, colour):
        self.disc(cx - s // 2, cy - s // 4, s // 2, colour)
        self.disc(cx + s // 2, cy - s // 4, s // 2, colour)
        self.poly([(cx - s, cy - s // 4), (cx + s, cy - s // 4),
                   (cx, cy + s)], colour)

    def flower(self, cx, cy, r, petal, centre):
        for k in range(5):
            a = 2 * math.pi * k / 5.0 - math.pi / 2.0
            self.disc(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)),
                     r // 2 + 3, petal)
        self.disc(cx, cy, r // 2, centre)


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(img, x, y, s, scale, colour):
    for n, ch in enumerate(s):
        glyph = FONT.get(ch, FONT["?"])
        ox = x + n * 6 * scale
        for row, line in enumerate(glyph):
            for col, bit in enumerate(line):
                if bit == "#":
                    img.rect(ox + col * scale, y + row * scale,
                             scale, scale, colour)


def draw_centred(img, cx, y, s, scale, colour):
    draw_text(img, cx - text_width(s, scale) // 2, y, s, scale, colour)


def frosting(img, x, y, w, colour):
    img.rect(x, y, w, 16, colour)
    for i in range(6):
        cx = x + int((i + 0.5) * w / 6.0)
        img.disc(cx, y + 16, 9, colour)


def write_png(path, img):
    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data +
                struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", img.w, img.h, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + bytes(img.px[y * img.w * 3:(y + 1) * img.w * 3])
                    for y in range(img.h))
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) +
            chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


def draw():
    img = Img(W, H, CREAM)
    rng = random.Random(20261114)

    # Confetti scattered on the paper, behind everything else.
    for _ in range(140):
        x = rng.randrange(28, W - 28)
        y = rng.randrange(28, H - 28)
        c = rng.choice(PALETTE)
        if rng.random() < 0.5:
            img.rect(x, y, rng.choice([4, 5, 6]), rng.choice([3, 4]), c)
        else:
            img.disc(x, y, rng.choice([3, 4]), c)

    # Plum frame around the whole picture.
    img.rrect(14, 14, W - 28, H - 28, 22, PLUM)
    img.rrect(22, 22, W - 44, H - 44, 18, CREAM)

    # Pink ribbon header.
    img.rrect(48, 44, 672, 96, 24, PINK)
    img.heart(92, 92, 14, WHITE)
    img.heart(676, 92, 14, WHITE)
    draw_centred(img, W // 2, 74, "DEAR JUDGE,", 5, WHITE)

    # The note card.
    img.rrect(90, 182, 588, 284, 18, SHADOW)
    img.rrect(84, 176, 588, 284, 18, WHITE)
    lines = ["YOU JUDGE", "HUNDREDS OF", "PICTURES ALL DAY.",
             "THIS ONE COMES", "WITH CAKE.", "HAVE A SLICE,",
             "YOU EARNED IT!"]
    for i, line in enumerate(lines):
        draw_centred(img, W // 2, 198 + i * 34, line, 3, PLUM)
    img.heart(620, 420, 12, RED)

    # Balloons flanking the cake.
    for cx, cy, c in ((118, 560, RED), (650, 560, BLUE)):
        img.ellipse(cx, cy, 42, 54, c)
        img.poly([(cx - 10, cy + 52), (cx + 10, cy + 52), (cx, cy + 66)], c)
        img.line(cx, cy + 66, cx, cy + 150, PLUM, 3)

    # The three-tier cake on its plate.
    img.ellipse(W // 2, 790, 252, 26, SHADOW)
    img.ellipse(W // 2, 786, 246, 24, WHITE)
    img.rect(210, 676, 348, 92, PINK)
    frosting(img, 210, 676, 348, WHITE)
    img.rect(250, 596, 268, 80, MINT)
    frosting(img, 250, 596, 268, WHITE)
    img.rect(290, 522, 188, 74, YELLOW)
    frosting(img, 290, 522, 188, WHITE)
    for _ in range(60):
        x = rng.randrange(216, 552)
        y = rng.choice([rng.randrange(700, 760), rng.randrange(620, 668),
                        rng.randrange(544, 588)])
        img.rect(x, y, 6, 3, rng.choice(PALETTE))
    for cx, c in ((330, RED), (384, BLUE), (438, GREEN)):
        img.rect(cx - 7, 478, 14, 44, c)
        img.line(cx, 478, cx, 466, PLUM, 3)
        img.ellipse(cx, 452, 9, 13, ORANGE)
        img.ellipse(cx, 456, 5, 8, YELLOW)

    # Flowers in the bottom corners and the sign-off.
    img.flower(84, 936, 22, PINK, YELLOW)
    img.flower(684, 936, 22, MINT, YELLOW)
    draw_centred(img, W // 2, 846, "PAINTED IN PURE PYTHON - NO PHOTOS,", 2, PLUM)
    draw_centred(img, W // 2, 872, "NO NETWORK, JUST CODE.", 2, PLUM)
    draw_centred(img, W // 2, 908, "THANK YOU FOR READING EVERY ENTRY!", 2, DEEP_PINK)
    return img


def main():
    out_dir = "/output" if os.path.isdir("/output") else "."
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "output.png")
    size = write_png(path, draw())
    print("Wrote %s (%d bytes, %dx%d)" % (path, size, W, H))


if __name__ == "__main__":
    main()
