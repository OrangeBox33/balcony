#!/usr/bin/env python3
"""Ночной зимний лес: ёлки в снегу, жёлтая луна, около неё вспыхивают звёздочки, медленно идёт снег.
Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
N = 160
MS = 60
GROUND = 13

SNOW = (200, 200, 225)
SNOW_DIM = (120, 120, 145)
DRIFT = (150, 150, 175)
NEEDLE = (10, 115, 40)
TRUNK = (120, 65, 25)
MOON = (235, 195, 70)
MOON_LIGHT = (255, 230, 130)
STAR = (255, 240, 170)

TREE_PAL = {"G": NEEDLE, "W": SNOW, "T": TRUNK}

TREE_L = ["....W....", "...WGW...", "..WGGGW..", "...GGG...", "..WGGGW..", ".WGGGGGW.",
          "..GGGGG..", ".WGGGGGW.", "WGGGGGGGW", ".GGGGGGG.", "....T...."]
TREE_M = ["...W...", "..WGW..", ".WGGGW.", "..GGG..", ".WGGGW.", "WGGGGGW", ".GGGGG.", "...T..."]
TREE_S = ["..W..", ".WGW.", "..G..", ".WGW.", "WGGGW", "..T.."]
TREE_XS = [".W.", "WGW", ".G.", "WGW", ".T."]
TREES = [(TREE_M, 0), (TREE_L, 8), (TREE_XS, 18), (TREE_S, 22)]

MOON_X, MOON_Y = 21, 1
MOON_SPR = [".MMM.", "MLMMM", "MMMMM", "MMMLM", ".MMM."]
MOON_PAL = {"M": MOON, "L": MOON_LIGHT}
STARS = [(18, 2, 10), (27, 6, 60), (19, 6, 95), (27, 1, 130)]
STAR_LIFE = 26

rng = random.Random(11)


class Flake:
    def __init__(self):
        self.x0 = rng.uniform(0, W)
        self.ph = rng.random()
        self.k = rng.choice((1, 2, 2, 3))
        self.sw = rng.choice((1, 2, 3))
        self.amp = rng.uniform(0.4, 1.2)
        self.sph = rng.random()
        self.bright = rng.random() < 0.6

    def pos(self, t):
        span = H + 2
        y = (self.ph * span + t * self.k * span / N) % span - 1
        x = self.x0 + self.amp * math.sin(2 * math.pi * (t * self.sw / N + self.sph))
        return round(x) % W, round(y)


FLAKES = [Flake() for _ in range(15)]


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        for x, y, born in STARS:
            age = (t - born) % N
            if age >= STAR_LIFE:
                continue
            k = math.sin(math.pi * age / STAR_LIFE)
            if k < 0.25:
                continue
            f.set(x, y, gen.scale(STAR, 0.45 + 0.55 * k))
            if k > 0.75:
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    f.set(x + dx, y + dy, gen.scale(STAR, 0.5 * k))
        f.sprite(MOON_SPR, MOON_X, MOON_Y, pal=MOON_PAL)
        for fl in FLAKES:
            if not fl.bright:
                x, y = fl.pos(t)
                if 0 <= y < GROUND:
                    f.set(x, y, SNOW_DIM)
        for x in range(W):
            f.set(x, GROUND, SNOW_DIM)
        for x in (3, 4, 7, 17, 21, 27):
            f.set(x, GROUND - 1, DRIFT)
        for spr, x in TREES:
            f.sprite(spr, x, GROUND - len(spr), pal=TREE_PAL)
        for fl in FLAKES:
            if fl.bright:
                x, y = fl.pos(t)
                if 0 <= y < GROUND:
                    f.set(x, y, SNOW)
        frames.append(f)
    gen.save("winter_forest_v2", frames, MS)


if __name__ == "__main__":
    build()
