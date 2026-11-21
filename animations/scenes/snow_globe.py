#!/usr/bin/env python3
"""Снежный шар: внутри ёлочка и домик с жёлтым окошком. Шар встряхивается,
снег закручивается вихрем и медленно оседает. Петля."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 80
CX, CY, R = 13.5, 5.8, 6.4          # шар
GROUND = 9.5                         # верх снежного «пола» внутри

GLASS = (110, 170, 220)
SHINE = (230, 245, 255)
WATER = (0, 25, 95)
SNOW_FLOOR = (200, 215, 240)
FLAKE = (255, 255, 255)
FLAKE_DIM = (150, 175, 225)

TREE = [
    "..y..",
    "..g..",
    ".ggg.",
    "..g..",
    ".ggg.",
    "ggggg",
    "..n..",
]
HOUSE = [
    "..R..",
    ".RRR.",
    "RRRRR",
    "hhhhh",
    "hhwhh",
]
PAL = {"g": (0, 170, 40), "y": (255, 220, 0), "n": (130, 60, 10), "R": (220, 30, 20),
       "h": (150, 80, 25), "w": (255, 210, 40)}

BASE = [
    "..GGGGGGGGGGGG..",
    ".BBBBBBBBBBBBBB.",
    "BBBBBBBBBBBBBBBB",
]
BASE_PAL = {"G": (255, 180, 0), "B": (150, 70, 15)}


def inside(x, y, r=R - 0.9):
    return (x - CX) ** 2 + (y - CY) ** 2 <= r * r


def draw_globe(f, dx, flakes, t):
    # вода и снежный пол
    for y in range(H):
        for x in range(W):
            d = math.hypot(x - CX, y - CY)
            if d <= R - 0.5:
                f.set(x + dx, y, SNOW_FLOOR if y >= GROUND else WATER)
    f.sprite(TREE, 8 + dx, 3, pal=PAL)
    f.sprite(HOUSE, 14 + dx, 5, pal=PAL)
    # снежинки
    for (x, y), bright in flakes:
        f.set(round(x) + dx, round(y), FLAKE if bright else FLAKE_DIM)
    # стекло
    for y in range(H):
        for x in range(W):
            d = math.hypot(x - CX, y - CY)
            if R - 0.5 < d <= R + 0.5:
                f.set(x + dx, y, GLASS)
    for x, y in ((9, 2), (8, 3)):                       # блик
        f.set(x + dx, y, SHINE)
    f.sprite(BASE, 6 + dx, 11, pal=BASE_PAL)


def build():
    rnd = random.Random(3)
    REST = 12
    SHAKE = [0, -1, -2, -1, 0, 1, 2, 1, 0, -1, -2, -1, 0, 1, 1, 0]
    SPIN = REST + len(SHAKE) + 10                   # до этого кадра — вихрь
    flakes = []
    for i in range(22):
        fl = {"x0": rnd.uniform(CX - 4.5, CX + 4.5),
              "rho": 1.2 + 4.0 * math.sqrt(rnd.random()),
              "th": rnd.uniform(0, 2 * math.pi),
              "w": rnd.uniform(0.28, 0.42),
              "fall": rnd.uniform(0.09, 0.16),
              "ph": rnd.uniform(0, 6.28),
              "bright": rnd.random() < 0.7}
        flakes.append(fl)

    def orbit(fl, t):
        # угол растёт всё медленнее: вихрь выдыхается к SPIN
        k = t - REST
        span = SPIN - REST
        p = min(k, span) / span
        ang = fl["th"] + fl["w"] * span * (p - p * p / 2) * 1.6
        rho = fl["rho"] * (0.8 + 0.2 * math.sin(fl["ph"] + k * 0.3))
        return CX + rho * math.cos(ang), CY - 0.5 + rho * 0.9 * math.sin(ang)

    def pos(fl, t):
        if t < REST:
            return None
        if t < SPIN:
            ox, oy = orbit(fl, t)
            lift = min(1.0, (t - REST) / 5)          # срывается с пола
            return fl["x0"] + (ox - fl["x0"]) * lift, GROUND + (oy - GROUND) * lift
        sx, sy = orbit(fl, SPIN)
        a = t - SPIN
        y = sy + fl["fall"] * a
        if y >= GROUND - 0.4:
            return None
        x = sx + 0.6 * math.sin(fl["ph"] + a * 0.18) - 0.6 * math.sin(fl["ph"])
        return x, y

    end = SPIN + max(math.ceil((GROUND - 0.4 - orbit(fl, SPIN)[1]) / fl["fall"]) for fl in flakes)
    frames = []
    for t in range(end + 8):
        dx = SHAKE[t - REST] if REST <= t < REST + len(SHAKE) else 0
        pts = []
        for fl in flakes:
            p = pos(fl, t)
            if p and inside(*p):
                pts.append((p, fl["bright"]))
        f = gen.Frame()
        draw_globe(f, dx, pts, t)
        frames.append(f)
    gen.save("snow_globe", frames, MS)


if __name__ == "__main__":
    build()
