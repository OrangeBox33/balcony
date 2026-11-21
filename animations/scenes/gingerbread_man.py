#!/usr/bin/env python3
"""Пряничный человечек танцует: поднимает руки, переминается с ноги на ногу, улыбается.
На руках и ногах белая глазурь-зигзаг, пуговицы — цветные драже. Вокруг падает снег,
по бокам всплывают нотки. Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
BEAT = 6
MS = 70
rng = random.Random(44)

GINGER = (185, 80, 20)
ICING = (255, 255, 255)
DRAGEE = {"R": (255, 20, 40), "Y": (255, 200, 0), "G": (0, 220, 60)}
CHEEK = (255, 70, 110)
NOTE = (255, 220, 120)
SNOW_DIM = (110, 115, 150)

# голова и туловище, 7 колонок; g — пряник, W — глазурь
HEAD = [
    ".ggggg.",
    "ggggggg",
    "ggWgWgg",
    "gWgggWg",
    ".gWWWg.",
]
SMILE_BIG = [          # на «ура» улыбка шире и щёчки
    ".ggggg.",
    "ggggggg",
    "ggWgWgg",
    "pWgggWp",
    ".gWWWg.",
]
BODY = [
    "ggggggg",
    ".ggRgg.",
    ".ggYgg.",
    ".ggGgg.",
    ".ggggg.",
]
PAL = {"g": GINGER, "W": ICING, "p": CHEEK, **DRAGEE}

# левая рука относительно левого края туловища; i — глазурь. Правая — зеркально.
ARMS = {
    "out": [
        "iggg",        # строка 5
        "gigg",        # строка 6
    ],
    "up": [
        "ig..",        # строка 2
        "gi..",        # 3
        ".gg.",        # 4
        "..gg",        # 5
    ],
    "down": [
        "..gg",        # 6
        ".gg.",        # 7
        "gi..",        # 8
        "ig..",        # 9
    ],
}
ARM_TOP = {"out": 5, "up": 2, "down": 6}

# ноги: две колонки, строки 10–13; глазурь зигзагом у ступни
LEG = [
    "gg",
    "gg",
    "Wg",
    "gW",
]

# танец по долям: (левая рука, правая рука, поднятая нога, сдвиг туловища, улыбка шире)
DANCE = [
    ("up", "up", "R", -1, True),
    ("out", "out", None, 0, False),
    ("up", "up", "L", 1, True),
    ("out", "out", None, 0, False),
    ("up", "down", "R", -1, False),
    ("down", "up", "L", 1, False),
    ("up", "down", "R", -1, False),
    ("out", "out", None, 0, False),
    ("out", "out", "L", 1, False),
    ("out", "out", "R", -1, False),
    ("out", "out", "L", 1, False),
    ("out", "out", None, 0, False),
    ("up", "up", None, 0, True),
    ("up", "up", "R", -1, True),
    ("up", "up", "L", 1, True),
    ("out", "out", None, 0, False),
]
N = BEAT * len(DANCE)
X0 = 11                 # левый край туловища в покое — фигура (с руками) по центру


class Fall:
    def __init__(self):
        self.x0 = rng.uniform(0, W)
        self.ph = rng.random()
        self.sph = rng.random()

    def pos(self, t):
        span = H + 2
        y = (self.ph * span + t * span / N) % span - 1
        x = self.x0 + 0.8 * math.sin(2 * math.pi * (t * 2 / N + self.sph))
        return round(x) % W, round(y)


FALL = [Fall() for _ in range(10)]

NOTE_SPR = [".##", ".#.", ".#.", "##."]
NOTES = [(1, 0.0), (24, 0.5)]          # (x, фаза) — всплывают по очереди слева и справа


def draw_arm(f, kind, bx, right):
    rows = ARMS[kind]
    top = ARM_TOP[kind]
    w = len(rows[0])
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch == ".":
                continue
            c = ICING if ch == "i" else GINGER
            if right:
                f.set(bx + 6 + w - dx, top + dy, c)     # зеркально справа от туловища
            else:
                f.set(bx - w + dx, top + dy, c)


def draw_leg(f, x, lifted, outward):
    dy = -2 if lifted else 0
    dx = outward if lifted else 0
    for ry, row in enumerate(LEG):
        for rx, ch in enumerate(row):
            if outward > 0:
                ch = row[1 - rx]                         # правая нога — зеркально
            y = 10 + ry + dy
            if y >= 10:
                f.set(x + rx + dx, y, ICING if ch == "W" else GINGER)


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        for fl in FALL:
            x, y = fl.pos(t)
            f.set(x, y, SNOW_DIM)

        for nx, ph in NOTES:
            p = (t / N * 2 + ph) % 1
            if p < 0.6:
                q = p / 0.6
                k = math.sin(math.pi * q)
                ny = round(10 - q * 9)
                f.sprite(NOTE_SPR, nx + round(math.sin(q * 6) * 0.7), ny,
                         pal={"#": gen.scale(NOTE, 0.45 + 0.55 * k)})

        la, ra, leg, shift, big = DANCE[t // BEAT]
        bx = X0 + shift
        # ноги: поднятая — выше и в сторону
        draw_leg(f, bx + 1, leg == "L", -1)
        draw_leg(f, bx + 4, leg == "R", 1)
        f.sprite(BODY, bx, 5, pal=PAL)
        draw_arm(f, la, bx, False)
        draw_arm(f, ra, bx, True)
        f.sprite(SMILE_BIG if big else HEAD, bx, 0, pal=PAL)
        frames.append(f)
    gen.save("gingerbread_man", frames, MS)


if __name__ == "__main__":
    build()
