#!/usr/bin/env python3
"""Ёлочные шары: сверху на ниточках висят четыре шара разного цвета на разной высоте,
слегка покачиваются, по каждому медленно скользит белый блик. Между ними падает снег.
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
rng = random.Random(21)

THREAD = (150, 125, 70)
CAP = (190, 170, 110)
FLAKE = (190, 190, 215)
FLAKE_DIM = (120, 120, 145)
GLINT = (255, 255, 255)
SS = 4                     # субпиксели на сторону — шар качается плавно, без рывков


class Ball:
    def __init__(self, x, cy, r, color, sway_k, sway_ph, glint_ph):
        self.x, self.cy, self.r, self.color = x, cy, r, color
        self.sway_k, self.sway_ph, self.glint_ph = sway_k, sway_ph, glint_ph

    def angle(self, t):
        return 0.055 * math.sin(2 * math.pi * (t * self.sway_k / N + self.sway_ph))

    def center(self, t):
        a = self.angle(t)
        return self.x + self.cy * math.sin(a), self.cy * math.cos(a)

    def glint(self, t):
        """Блик проходит по шару слева направо по верхней дуге; раз за петлю, потом его не видно."""
        p = (t / N + self.glint_ph) % 1.0
        u = -1.6 + 3.2 * p / 0.6 if p < 0.6 else 9.0        # 0.6 петли идёт, 0.4 — отдыхает
        cx, cy = self.center(t)
        return cx + u * self.r * 0.6, cy - self.r * 0.45 + abs(u) * self.r * 0.18


BALLS = [
    #     x    y центра  r    цвет              качание   блик
    Ball(4.5, 5.2, 2.6, (220, 20, 30), 2, 0.00, 0.00),
    Ball(11.0, 9.6, 2.9, (30, 80, 255), 2, 0.30, 0.27),
    Ball(17.0, 4.2, 2.4, (255, 160, 0), 3, 0.60, 0.52),
    Ball(23.5, 8.4, 2.7, (0, 185, 80), 2, 0.85, 0.77),
]


class Flake:
    def __init__(self):
        self.x0 = rng.uniform(0, W)
        self.ph = rng.random()
        self.k = rng.choice((2, 2, 3))
        self.sw = rng.choice((1, 2))
        self.amp = rng.uniform(0.3, 0.9)
        self.sph = rng.random()
        self.bright = rng.random() < 0.55

    def pos(self, t):
        span = H + 2
        y = (self.ph * span + t * self.k * span / N) % span - 1
        x = self.x0 + self.amp * math.sin(2 * math.pi * (t * self.sw / N + self.sph))
        return round(x) % W, round(y)


FLAKES = [Flake() for _ in range(16)]


def draw_ball(f, b, t):
    cx, cy = b.center(t)
    gx, gy = b.glint(t)
    for y in range(max(0, int(cy - b.r) - 1), min(H, int(cy + b.r) + 2)):
        for x in range(max(0, int(cx - b.r) - 1), min(W, int(cx + b.r) + 2)):
            cov, light = 0, 0.0
            for i in range(SS):
                for j in range(SS):
                    px, py = x + (i + 0.5) / SS, y + (j + 0.5) / SS
                    dx, dy = (px - cx) / b.r, (py - cy) / b.r
                    if dx * dx + dy * dy <= 1:
                        cov += 1
                        light += 1.0 - 0.45 * max(0.0, 0.5 * dx + 0.85 * dy)   # тень снизу-справа
            if not cov:
                continue
            k = cov / SS / SS
            if k < 0.3:
                continue
            c = gen.scale(b.color, light / cov * min(1.0, k * 1.25))
            d2 = (x + 0.5 - gx) ** 2 + (y + 0.5 - gy) ** 2
            w = math.exp(-d2 / 0.55) * k                         # белый блик
            c = tuple(min(255, int(a + (v - a) * w)) for a, v in zip(c, GLINT))
            f.set(x, y, c)


def draw_thread(f, b, t):
    """Ниточка от потолка до колпачка; качается вместе с шаром."""
    cx, cy = b.center(t)
    top = cy - b.r - 0.6
    a = b.angle(t)
    for y in range(0, int(round(top))):
        x = b.x + (y + 0.5) * math.sin(a)
        f.set(round(x - 0.5), y, THREAD)
    cap_y = round(top)
    cap_x = round(cx - 0.5)
    f.set(cap_x, cap_y, CAP)


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        for fl in FLAKES:
            x, y = fl.pos(t)
            f.set(x, y, FLAKE if fl.bright else FLAKE_DIM)
        for b in BALLS:
            draw_thread(f, b, t)
            draw_ball(f, b, t)
        frames.append(f)
    gen.save("xmas_balls", frames, MS)


if __name__ == "__main__":
    build()
