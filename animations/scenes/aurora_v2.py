#!/usr/bin/env python3
"""Северное сияние над тёмным лесом: на сине-зелёном небе медленно переливаются волны —
зелёные, бирюзовые, с фиолетовой каймой; чёрные силуэты ёлок; падают крупные снежинки.
Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
N = 140
MS = 70
TAU = 2 * math.pi

SKY_TOP = (12, 5, 85)
SKY_LOW = (0, 45, 115)
GREEN = (30, 255, 100)
TEAL = (0, 210, 210)
VIOLET = (170, 60, 255)
FLAKE = (235, 235, 255)
FLAKE_ARM = (150, 150, 185)
STAR = (200, 200, 230)

rng = random.Random(31)

# силуэт леса: ёлки ярусами (полуширина по рядам сверху вниз), вершина — ряд top
TIERS = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]
TREES = [(2, 6), (7, 4), (12, 7), (16, 5), (21, 7), (25, 5)]   # (центр, ряд вершины)
GROUND = 11                # с этого ряда — сплошная чернота


def forest_mask():
    m = {(x, y) for x in range(W) for y in range(GROUND, H)}
    for cx, ty in TREES:
        for i, hw in enumerate(TIERS):
            for x in range(cx - hw, cx + hw + 1):
                m.add((x, ty + i))
        for y in range(ty + len(TIERS), GROUND):      # ниже ярусов — сплошная крона
            for x in range(cx - 4, cx + 5):
                m.add((x, y))
    return m


FOREST = forest_mask()



def sky(y):
    k = min(1.0, y / 11) ** 1.6     # у горизонта небо светлее — силуэты ёлок видны
    return tuple(int(a + (b - a) * k) for a, b in zip(SKY_TOP, SKY_LOW))


def mix(a, b, k):
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(3))


def aurora(x, y, t):
    """Яркость и цвет сияния в точке. Все фазы — целое число оборотов за петлю."""
    p = t / N
    # нижняя кромка занавеса волнуется
    edge = 7.0 + 1.6 * math.sin(TAU * (x / 30 + p)) + 0.7 * math.sin(TAU * (x / 13 - 2 * p))
    d = edge - y                        # >0 — выше кромки
    if d < -2 or d > 9:
        return 0.0, (0, 0, 0)
    if d < 0:
        prof = 1 + d / 2                # под кромкой быстро гаснет
    else:
        prof = math.exp(-d / 4.0)       # вверх — плавно
    # вертикальные лучи медленно бегут вдоль занавеса
    rays = 0.7 + 0.3 * math.sin(TAU * (x / 7 + 2 * p))
    # общая яркость дышит волной
    breath = 0.75 + 0.25 * math.sin(TAU * (x / 28 - p))
    v = prof * rays * breath
    # цвет: внизу зелёный, выше бирюзовый, верхняя кайма фиолетовая; плюс сдвиг вдоль неба
    hue = d / 9 - 0.12 + 0.15 * math.sin(TAU * (x / 20 + p))
    if hue < 0.45:
        col = mix(GREEN, TEAL, max(0.0, hue) / 0.45)
    else:
        col = mix(TEAL, VIOLET, min(1.0, (hue - 0.45) / 0.4))
    return v, col


STARS = [(2, 1, 0.1), (9, 0, 0.6), (17, 1, 0.35), (24, 0, 0.8), (13, 2, 0.5)]


class Flake:
    def __init__(self, i):
        self.x0 = 2 + i * 5.5 + rng.uniform(-1, 1)
        self.ph = i / 5 + rng.uniform(-0.05, 0.05)
        self.sw = rng.choice((1, 2))
        self.sph = rng.random()

    def pos(self, t):
        span = H + 3
        y = (self.ph + t / N) % 1 * span - 1.5
        x = self.x0 + 1.3 * math.sin(TAU * (t * self.sw / N + self.sph))
        return round(x) % W, round(y)


FLAKES = [Flake(i) for i in range(5)]


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        for y in range(H):
            for x in range(W):
                if (x, y) in FOREST:
                    continue                   # лес — чёрный силуэт
                base = sky(y)
                v, col = aurora(x, y, t)
                c = mix(base, col, min(1.0, 1.5 * v))
                f.set(x, y, tuple(min(255, int(q)) for q in c))
        for sx, sy, ph in STARS:
            tw = 0.5 + 0.5 * math.sin(TAU * (2 * t / N + ph))
            if tw > 0.3:
                f.set(sx, sy, gen.scale(STAR, 0.6 + 0.4 * tw))
        for fl in FLAKES:
            x, y = fl.pos(t)
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                f.set((x + dx) % W, y + dy, FLAKE_ARM)
            f.set(x, y, FLAKE)
        frames.append(f)
    # квантуем каналы: иначе >4096 цветов — тяжёлый GIF и галерея не собирается
    for f in frames:
        f.px = [[tuple(min(255, round(v / 12) * 12) for v in c) for c in row] for row in f.px]
    gen.save("aurora_v2", frames, MS)


if __name__ == "__main__":
    build()
