#!/usr/bin/env python3
"""Пряничный человечек с белой глазурью танцует на снегу рядом с пряничным
домиком: машет руками, переступает с ноги на ногу, подпрыгивает. Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 80
BEAT = 5                # кадров на одно движение
GROUND = 13

BROWN = (185, 95, 35)
ICING = (255, 255, 255)
SNOW = (165, 185, 225)
FLAKE = (110, 130, 185)
PAL = {
    "b": BROWN,
    "W": ICING,
    "r": (255, 0, 30),
    "g": (0, 220, 60),
    "h": (215, 120, 50),      # стены домика — светлее человечка
    "d": (150, 70, 20),       # дверь
    "y": (255, 200, 0),       # окно светится
    "p": (255, 40, 160),
    "c": (0, 170, 255),
}

# голова и туловище (без рук и ног); ширина 11, центр — колонка 5
HEAD_BODY = [
    "....bbb....",
    "...bbbbb...",
    "..bbWbWbb..",
    "..bWbbbWb..",
    "...bWWWb...",
    "....bbb....",
    "...bbbbb...",
    "...bbrbb...",
    "...bbbbb...",
    "...bbgbb...",
]
# руки: от плеча (строка 6) — три положения для каждой стороны (левая; правая — зеркально)
ARM = {
    "down": [(2, 6), (1, 7), (0, 8), (2, 7), (1, 8)],
    "out":  [(2, 6), (1, 6), (0, 6), (2, 7), (1, 7), (0, 7)],
    "up":   [(2, 6), (1, 5), (0, 4), (2, 5), (1, 4), (0, 3)],
}
ARM_ICING = {"down": [(0, 8)], "out": [(0, 6), (0, 7)], "up": [(0, 3), (0, 4)]}
# ноги: строки 10–12, на ногах — полоски глазури
LEGS = {
    "stand":  ["...bb.bb...", "...Wb.bW...", "..bbb.bbb.."],
    "lift_l": ["..bbb.bb...", ".bWb..bW...", "......bbb.."],
    "lift_r": ["...bb.bbb..", "...Wb..bWb.", "..bbb......"],
    "jump":   ["...bb.bb...", "..bW...Wb..", "..b.....b.."],
}

HOUSE = [
    "....W....",
    "...WbW...",
    "..WrbcW..",
    ".WbbybbW.",
    "WWWWWWWWW",
    ".hhhhhhh.",
    ".hyWhhdh.",
    ".hWyhhdh.",
    ".hhhhhdh.",
]

# танец: (левая рука, правая рука, ноги, подскок) — по такту
DANCE = [
    ("down", "down", "stand", 0),
    ("down", "up", "stand", 0),
    ("down", "out", "stand", 0),
    ("down", "up", "stand", 0),
    ("up", "down", "stand", 0),
    ("out", "down", "stand", 0),
    ("up", "down", "stand", 0),
    ("out", "out", "stand", 0),
    ("out", "out", "lift_l", 0),
    ("out", "out", "stand", 0),
    ("out", "out", "lift_r", 0),
    ("out", "out", "stand", 0),
    ("out", "out", "lift_l", 0),
    ("out", "out", "lift_r", 0),
    ("down", "down", "stand", 0),
    ("out", "out", "stand", 0),
    ("up", "up", "jump", 1),
    ("up", "up", "jump", 1),
    ("down", "down", "stand", 0),
    ("down", "down", "stand", 0),
]
N = len(DANCE) * BEAT


def draw_man(f, x, y, la, ra, legs):
    f.sprite(HEAD_BODY, x, y, pal=PAL)
    f.sprite(LEGS[legs], x, y + 10, pal=PAL)
    for side, pose in ((0, la), (1, ra)):
        for ax, ay in ARM[pose]:
            px = x + ax if side == 0 else x + 10 - ax
            f.set(px, y + ay, BROWN)
        for ax, ay in ARM_ICING[pose]:
            px = x + ax if side == 0 else x + 10 - ax
            f.set(px, y + ay, ICING)


def build():
    rnd = random.Random(17)
    flakes = [(rnd.uniform(0, W), rnd.uniform(0, GROUND), rnd.uniform(0, 6.28)) for _ in range(6)]
    frames = []
    for t in range(N):
        f = gen.Frame()
        for fx, fy, ph in flakes:
            y = (fy + t * GROUND / N) % GROUND
            x = (fx + 0.6 * math.sin(2 * math.pi * t / N * 2 + ph)) % W
            f.set(int(x), int(y), FLAKE)
        for x in range(W):
            f.set(x, GROUND, SNOW)
        f.sprite(HOUSE, 17, GROUND - len(HOUSE), pal=PAL)
        la, ra, legs, hop = DANCE[t // BEAT]
        # ступни стоят прямо в снегу (строка 13), в прыжке — над ним
        draw_man(f, 3, GROUND - 12 - hop, la, ra, legs)
        frames.append(f)
    gen.save("gingerbread", frames, MS)


if __name__ == "__main__":
    build()
