#!/usr/bin/env python3
"""Дед Мороз у окна: вид из тёмной комнаты, за окном ночь и снег. Дед Мороз заглядывает,
машет варежкой, прижимается носом к стеклу и уходит; запотевшее пятнышко медленно тает. Петля."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 80
N = 120

# окно: рама x 4..23, верх y 0, импост y 4, стекло низа y 5..12, подоконник y 13
GX0, GX1 = 5, 22
WOOD = (200, 135, 60)
SILL = (235, 175, 95)
SKY = (5, 20, 90)
FOG = (150, 185, 200)

DM = [
    "...RRRRR...",
    "..RRRRRRR..",
    ".WWWWWWWWW.",
    ".bsesssesb.",
    ".bcssnsscb.",
    "bbMMMMMMMbb",
    "bbbbmmmbbbb",
    "RbbbbbbbbbR",
]
DM_PRESS = [            # прижался: нос приплюснут, щёки шире, глаза зажмурены от удовольствия
    "...RRRRR...",
    "..RRRRRRR..",
    ".WWWWWWWWW.",
    ".bsLsssLsb.",
    "bccsNNNsccb",
    "bbMMMMMMMbb",
    "bbbbmmmbbbb",
    "RbbbbbbbbbR",
]
PAL = {
    "R": (225, 20, 30), "W": (255, 255, 255), "b": (215, 215, 228), "s": (255, 175, 125),
    "e": (0, 0, 0), "c": (255, 95, 115), "n": (255, 75, 55), "M": (140, 190, 255),
    "m": (190, 0, 35), "L": (120, 45, 20), "N": (255, 190, 185),
}
MITTEN = [".RR", "RRR", "WWW"]


def clip_set(f, x, y, c, dm=False):
    if GX0 <= x <= GX1 and 1 <= y <= 12:
        f.set(x, y, c)
        if dm:
            f.dm.add((x, y))


def draw_dm(f, x, y, press=False, wave=None, hands=False):
    rows = DM_PRESS if press else DM
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != ".":
                clip_set(f, x + dx, y + dy, PAL[ch], True)
    if wave is not None:                       # варежка поднята справа от головы
        mx = x + 11 + wave
        for dy, row in enumerate(MITTEN):
            for dx, ch in enumerate(row):
                if ch != ".":
                    clip_set(f, mx + dx, y + 2 + dy, PAL[ch])
        clip_set(f, x + 11, y + 6, PAL["R"])    # рукав
        clip_set(f, x + 11, y + 7, PAL["R"])
    if hands:                                  # обе варежки прижаты к стеклу
        for mx in (x - 3, x + 11):
            for dy, row in enumerate(MITTEN):
                for dx, ch in enumerate(row):
                    if ch != ".":
                        clip_set(f, mx + dx, y + 3 + dy, PAL[ch])


def draw_frame(f):
    for y in range(0, 13):
        f.set(4, y, WOOD)
        f.set(23, y, WOOD)
    for x in range(4, 24):
        f.set(x, 0, WOOD)
        f.set(x, 4, WOOD)
    for y in range(1, 4):                      # форточки
        f.set(13, y, WOOD)
        f.set(14, y, WOOD)
    for x in range(2, 26):
        f.set(x, 13, SILL)


def build():
    rnd = random.Random(21)
    flakes = []
    for _ in range(16):
        flakes.append((rnd.uniform(GX0, GX1 + 1), rnd.uniform(0, 13), rnd.choice((2, 3)),
                       rnd.uniform(0, 6.28), rnd.random() < 0.5))

    ENTER0, ENTER1 = 12, 27          # входит справа
    WAVE1 = 47                       # машет
    PRESS0, PRESS1 = 50, 68          # прижался к стеклу
    BYE1 = 74
    LEAVE1 = 88                      # ушёл влево
    CX = 8                           # где стоит (DM 11 шириной → x 8..18)
    fog_x, fog_y = CX + 5, 5 + 4

    frames = []
    for t in range(N):
        f = gen.Frame()
        f.dm = set()                       # где нарисован Дед Мороз — туда туман слабее
        for y in range(1, 13):
            for x in range(GX0, GX1 + 1):
                f.set(x, y, SKY)
        for x0, y0, k, ph, bright in flakes:
            y = (y0 + 13 * k * t / N) % 13
            x = x0 + 0.7 * math.sin(2 * math.pi * t / N * 3 + ph)
            col = (210, 220, 255) if bright else (140, 160, 220)
            clip_set(f, round(x), round(y), col)

        # Дед Мороз
        y_dm = 5
        if ENTER0 <= t < ENTER1:
            p = (t - ENTER0) / (ENTER1 - ENTER0 - 1)
            x = round(GX1 + 1 + (CX - GX1 - 1) * p)
            draw_dm(f, x, y_dm + (t // 2) % 2)
        elif ENTER1 <= t < WAVE1:
            wave = [0, 1, 0, -1][((t - ENTER1) // 2) % 4] if t >= ENTER1 + 2 else None
            draw_dm(f, CX, y_dm, wave=wave)
        elif WAVE1 <= t < PRESS0:
            draw_dm(f, CX, y_dm, hands=True)
        elif PRESS0 <= t < PRESS1:
            draw_dm(f, CX, y_dm, press=True, hands=True)
        elif PRESS1 <= t < BYE1:
            draw_dm(f, CX, y_dm, wave=[0, 1, 0, -1][((t - PRESS1) // 2) % 4])
        elif BYE1 <= t < LEAVE1:
            p = (t - BYE1) / (LEAVE1 - BYE1 - 1)
            x = round(CX + (GX0 - 12 - CX) * p)
            draw_dm(f, x, y_dm + (t // 2) % 2)

        # запотевшее пятнышко: растёт, пока прижат, потом медленно тает
        if t >= PRESS0:
            if t < PRESS1:
                k = min(1.0, (t - PRESS0 + 1) / 8)
            else:
                k = max(0.0, 1 - (t - PRESS1) / (N - 4 - PRESS1)) ** 0.7
            r = 0.9 + 1.2 * k
            for y in range(fog_y - 3, fog_y + 4):
                for x in range(fog_x - 4, fog_x + 5):
                    d = math.hypot((x - fog_x) / 1.3, y - fog_y)
                    v = k * min(1.0, max(0.0, (r - d) / 1.2 + 0.2))
                    if v > 0.05 and GX0 <= x <= GX1 and 5 <= y <= 12:
                        f.add(x, y, gen.scale(FOG, v * (0.3 if (x, y) in f.dm else 1)))
        draw_frame(f)
        frames.append(f)
    gen.save("ded_moroz_window", frames, MS)


if __name__ == "__main__":
    build()
