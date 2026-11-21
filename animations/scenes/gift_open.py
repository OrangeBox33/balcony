#!/usr/bin/env python3
"""Подарок открывается: бант развязывается, крышка подпрыгивает и улетает, из коробки вылетает
облачко звёздочек и конфетти и медленно оседает; крышка опускается обратно, бант завязывается. Петля."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 70
N = 140                      # ≈ 9.8 с
rng = random.Random(23)

BODY = (200, 10, 20)
LID = (255, 45, 55)          # крышка светлее коробки — граница видна
RIB = (255, 200, 40)

BX0, BX1, BY0 = 8, 19, 8     # коробка: x 8..19, y 8..13
LX0, LX1, LY = 7, 20, 6      # крышка: x 7..20, y 6..7
RX = 13                      # лента: столбцы 13–14

# петли банта (левая; правая — зеркальная), узел 2×1 между ними
LOOP = ["##", "#.", "##"]

# расписание (кадры)
T_UNTIE, T_SHAKE, T_POP = 14, 30, 40
T_BACK, T_LAND, T_TIE, T_DONE = 100, 116, 120, 134


def ease(a):
    a = min(max(a, 0.0), 1.0)
    return a * a * (3 - 2 * a)


def untie(t):
    """0 — бант завязан, 0.6 — петли расползлись к краям крышки, 1 — концы ленты свисают с крышки."""
    if t < T_UNTIE or t >= T_DONE:
        return 0.0
    if t < T_SHAKE:
        return (t - T_UNTIE) / (T_SHAKE - T_UNTIE)
    if t < T_TIE:
        return 1.0
    return 1 - (t - T_TIE) / (T_DONE - T_TIE)


def lid_dy(t):
    if T_SHAKE <= t < T_POP:              # «кто-то толкается»: крышка подскакивает
        return [0, -1, 0, 0, -1, 0, 0, -1, -1, 0][t - T_SHAKE]
    if T_POP <= t < T_BACK:
        a = t - T_POP
        return -round(0.9 * a + 0.35 * a * a)   # с ускорением вверх и за край
    if T_BACK <= t < T_LAND:              # плавно опускается сверху
        a = (t - T_BACK) / (T_LAND - T_BACK)
        return round(-12 * (1 - ease(a)))
    if T_LAND <= t < T_LAND + 3:          # мягко садится
        return [-1, 0, 0][t - T_LAND]
    return 0


def draw_box(f, t):
    for y in range(BY0, H):
        for x in range(BX0, BX1 + 1):
            f.set(x, y, RIB if (RX <= x <= RX + 1 or y == 10) else BODY)


def draw_lid(f, t):
    dy = lid_dy(t)
    y0 = LY + dy
    for y in (y0, y0 + 1):
        for x in range(LX0, LX1 + 1):
            f.set(x, y, RIB if RX <= x <= RX + 1 else LID)
    u = untie(t)
    if u <= 0.6:                          # петли банта; развязываясь, ползут к краям крышки
        dx = round(5 * ease(u / 0.6))
        f.sprite(LOOP, RX - 2 - dx, y0 - 3, pal={"#": RIB})
        f.sprite(LOOP, RX + 2 + dx, y0 - 3, flip=True, pal={"#": RIB})
        if u == 0:
            f.set(RX, y0 - 2, RIB)
            f.set(RX + 1, y0 - 2, RIB)
    else:                                 # концы ленты свисают с краёв крышки и летают вместе с ней
        n = min(3, round(3 * (u - 0.6) / 0.4 + 0.5))
        for k in range(n):
            f.set(LX0 - 1, y0 + k, RIB)
            f.set(LX1 + 1, y0 + k, RIB)


COLORS = [(255, 210, 60), (240, 240, 255), (255, 60, 150), (255, 210, 60), (0, 200, 255)]


class Bit:
    def __init__(self, i):
        self.born = T_POP + 1 + i % 6
        self.x = rng.uniform(BX0 + 1.5, BX1 - 1.5)
        self.y = BY0 - 0.5
        self.vx = rng.uniform(-0.55, 0.55)
        self.vy = -rng.uniform(0.6, 1.0)
        self.col = COLORS[i % len(COLORS)]
        self.star = i < 4                  # несколько крупных звёздочек-крестиков
        self.sw = rng.uniform(0, 6.28)
        self.fall = rng.uniform(0.13, 0.2)
        self.life = rng.randrange(58, 72)


BITS = [Bit(i) for i in range(24)]


def simulate():
    """Траектории заранее: вверх с торможением, потом медленно оседают, покачиваясь."""
    paths = []
    for b in BITS:
        x, y, vx, vy = b.x, b.y, b.vx, b.vy
        p = []
        for a in range(b.life):
            p.append((x + 0.6 * math.sin(b.sw + a * 0.25) * min(1, a / 15), y))
            vy = min(vy + 0.09, b.fall)
            vx *= 0.93
            x += vx
            y += vy
        paths.append(p)
    return paths


PATHS = simulate()


def draw_bits(f, t):
    for b, p in zip(BITS, PATHS):
        a = t - b.born
        if not (0 <= a < len(p)):
            continue
        x, y = p[a]
        tw = 0.85 + 0.15 * math.sin(a * 0.9 + b.sw)
        fade = 1 if a < len(p) - 10 else 0.5 + 0.5 * (len(p) - a) / 10
        c = gen.scale(b.col, tw * fade)
        cx, cy = round(x), round(y)
        if b.star and a > 4 and fade > 0.9:
            f.add(cx, cy, (255, 255, 220))
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                f.add(cx + ddx, cy + ddy, c)
        else:
            f.add(cx, cy, c)


# мягко мерцающие искорки вокруг коробки, пока ничего не происходит
TWINK = [(3, 3), (24, 2), (2, 9), (25, 8), (5, 12), (22, 12)]


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        for i, (x, y) in enumerate(TWINK):
            k = 0.5 + 0.5 * math.sin(2 * math.pi * (t * 3 / N + i / len(TWINK)))
            if k > 0.4:
                f.set(x, y, gen.scale((255, 220, 150), 0.4 + 0.5 * k))
        draw_bits(f, t)
        draw_box(f, t)
        draw_lid(f, t)
        frames.append(f)
    gen.save("gift_open", frames, MS)


if __name__ == "__main__":
    build()
