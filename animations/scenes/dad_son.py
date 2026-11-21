#!/usr/bin/env python3
"""Лысый толстый папа трясёт за шею вихрастого сынишку-хулигана:
сын болтается и дрыгает ногами, над головой кружат звёздочки, папа пыхтит."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 70
N = 90
GROUND = 13

# папа лицом вправо: лысина с бликом, усы, круглое пузо в майке
DAD = [
    "...ssss....",
    "..sWssss...",
    "..ssssss...",
    "..sssEsE...",
    "..ssskkss..",
    "...ssrss...",
    ".wwwwwwww..",
    "wwwwwwwwww.",
    "wwwwwwwwww.",
    "wwwwwwwwww.",
    ".wwwwwwww..",
    "..bbb.bbb..",
    "..bbb.bbb..",
]
# сын: вихры, злая мина, полосатая футболка
SON_HEAD = [
    "y.y.y",
    "yyyyy",
    "sEsEs",
    "sssss",
    ".sRs.",
]
SON_BODY = [
    "ooooo",
    "WWWWW",
]
LEGS = [
    [".b.b.", "n...n"],
    ["b..b.", "n...n"],
    [".b.b.", ".n.n."],
    [".b..b", "n...n"],
]
PAL = {"w": (230, 230, 240), "s": (255, 150, 90), "k": (150, 70, 20),
       "y": (255, 200, 0), "b": (40, 90, 255), "W": (255, 255, 255),
       "r": (255, 30, 30), "E": (0, 0, 0), "R": (255, 40, 40), "n": (170, 80, 20), "o": (255, 110, 0)}
STAR = (255, 230, 60)


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        for x in range(W):
            f.set(x, GROUND, (60, 60, 90))
        shake = [-1, 1][t % 2]
        sy = [0, -1][(t // 2) % 2]
        # папа: голова слегка трясётся вместе с сыном
        dx0 = 3
        f.sprite(DAD, dx0, 1 + (t % 4 == 0), pal=PAL)
        # руки к шее сына
        sx = 16 + shake
        hy = 4 + sy
        n = sx - (dx0 + 10)
        for i, x in enumerate(range(dx0 + 10, sx)):
            y = round(9 - (9 - (hy + 4)) * i / max(1, n - 1))
            f.set(x, y, PAL["s"]); f.set(x, y + 1, PAL["s"])
        # сын болтается
        f.sprite(SON_HEAD, sx, hy, pal=PAL)
        f.sprite(SON_BODY, sx, hy + 5, pal=PAL)
        f.sprite(LEGS[(t // 2) % 4], sx, hy + 7, pal=PAL)
        # руки папы сомкнуты на шее
        f.set(sx - 1, hy + 4, PAL["s"])
        f.set(sx, hy + 4, PAL["s"])
        f.set(sx + 4, hy + 4, PAL["s"])
        # звёздочки кружат над сыном
        for k in range(3):
            a = 2 * math.pi * (t / 18 + k / 3)
            px = round(sx + 2 + 4 * math.cos(a))
            py = round(hy - 2 + 1.0 * math.sin(a))
            f.set(px, py, STAR if math.sin(a) > -0.3 else gen.scale(STAR, 0.5))
        # пар из ушей папы / брызги
        if (t // 3) % 2:
            f.set(2, 1, (200, 200, 230))
            f.set(1, 0, (150, 150, 200))
        # чёрточки тряски
        if t % 2:
            f.set(sx + 6, hy + 3, (255, 255, 255))
            f.set(sx + 6, hy + 7, (255, 255, 255))
        else:
            f.set(sx - 2, hy + 7, (255, 255, 255))
        frames.append(f)
    gen.save("dad_son", frames, MS)


if __name__ == "__main__":
    build()
