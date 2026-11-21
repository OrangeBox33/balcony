#!/usr/bin/env python3
"""Костёр: языки пламени над поленьями, угли тлеют, вверх летят искры. Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
N = 160                 # кадров в петле (8 с)
MS = 50
CX = 13.5               # центр костра
HALF = 8.5              # полуширина пламени у основания
BASE_Y = 11.5           # где пламя «сидит» на поленьях

# шкала жара: от тёмно-красного (ещё видного на диодах) до почти белого
RAMP = [
    (0.00, (0, 0, 0)),
    (0.18, (0, 0, 0)),
    (0.22, (120, 8, 0)),
    (0.38, (210, 30, 0)),
    (0.55, (255, 90, 0)),
    (0.72, (255, 160, 10)),
    (0.86, (255, 215, 60)),
    (1.00, (255, 245, 170)),
]
LEVELS = 28             # жар квантуем по ступеням — цветов немного, GIF маленький


def heat_color(v):
    v = min(max(v, 0.0), 1.0)
    v = round(v * LEVELS) / LEVELS
    for (a, ca), (b, cb) in zip(RAMP, RAMP[1:]):
        if v <= b:
            k = (v - a) / (b - a) if b > a else 0
            return tuple(int(p + (q - p) * k) for p, q in zip(ca, cb))
    return RAMP[-1][1]


rng = random.Random(7)


class Noise:
    """Сглаженный шум на решётке, по оси времени замкнут в кольцо длиной period."""

    def __init__(self, nx, period):
        self.nx, self.period = nx, period
        self.v = [[rng.random() for _ in range(period)] for _ in range(nx)]

    def __call__(self, x, z):
        def s(a):
            return a * a * (3 - 2 * a)
        x0, z0 = math.floor(x), math.floor(z)
        fx, fz = s(x - x0), s(z - z0)
        def g(i, k):
            return self.v[i % self.nx][k % self.period]
        a = g(x0, z0) + (g(x0 + 1, z0) - g(x0, z0)) * fx
        b = g(x0, z0 + 1) + (g(x0 + 1, z0 + 1) - g(x0, z0 + 1)) * fx
        return a + (b - a) * fz


# три слоя шума: крупные языки, средние, мелкая рябь; каждый за петлю прокручивается целое число раз
OCT = [(Noise(64, 12), 0.42, 0.40, 12, 0.45), (Noise(64, 20), 0.80, 0.85, 20, 0.38), (Noise(64, 32), 1.5, 1.6, 32, 0.17)]


def heat(x, y, t):
    h = (BASE_Y - y) / BASE_Y                     # 0 у поленьев, 1 вверху экрана
    sway = 0.9 * math.sin(2 * math.pi * (t / N * 3 + y * 0.08))   # пламя покачивается
    n = 0.0
    for noise, fx, fy, period, amp in OCT:
        z = y * fy + t * period / N * 4          # шум бежит вверх; за петлю — 4 полных круга
        n += amp * noise((x + sway * (1 + h)) * fx, z % period * 1.0 + 0.0)
    n = n / sum(o[4] for o in OCT)
    hh = max(h, 0)
    width = HALF * (1 - 0.5 * hh) + 0.5
    side = abs(x - CX) / width
    # чем выше, тем сильнее шум: пламя рвётся на отдельные языки
    v = 0.92 - 1.2 * h + (n - 0.5) * (0.7 + 1.9 * hh) - side * side * 0.9
    if y > BASE_Y:                                # под поленьями — угли
        v = 0.75 - side * 0.5 + (n - 0.5) * 0.6
    return v


LOGS = [  # два скрещённых полена
    [(x, 13 - (x - 6) // 5) for x in range(6, 22)],
    [(x, 11 + (x - 6) // 5) for x in range(6, 22)],
]
BARK = (150, 70, 25)


class Spark:
    def __init__(self):
        self.born = rng.randrange(N)
        self.life = rng.randrange(14, 30)
        self.x0 = CX + rng.uniform(-4.5, 4.5)
        self.y0 = rng.uniform(4.0, 8.0)
        self.vy = rng.uniform(0.32, 0.6)
        self.wob = rng.uniform(0.6, 1.8)
        self.ph = rng.uniform(0, 2 * math.pi)
        self.drift = rng.uniform(-0.08, 0.08)


SPARKS = [Spark() for _ in range(22)]


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        for y in range(H):
            for x in range(W):
                c = heat_color(heat(x + 0.5, y + 0.5, t))
                if c != (0, 0, 0):
                    f.set(x, y, c)
        # поленья с тлеющими трещинами
        for log in LOGS:
            for i, (x, y) in enumerate(log):
                glow = 0.5 + 0.5 * math.sin(2 * math.pi * (t / N * 5 + i * 0.7))
                if i % 4 == 1 and glow > 0.55:
                    f.set(x, y, (255, int(60 + 80 * glow), 0))
                else:
                    f.set(x, y, BARK)
        # искры: у каждой свой момент рождения, возраст считаем по кругу — петля без шва
        for s in SPARKS:
            age = (t - s.born) % N
            if age >= s.life:
                continue
            k = age / s.life
            x = s.x0 + s.drift * age + s.wob * math.sin(s.ph + age * 0.45)
            y = s.y0 - s.vy * age
            if y < -0.5:
                continue
            col = (255, int(230 - 170 * k), int(120 * (1 - k) ** 2))
            f.set(round(x), round(y), gen.scale(col, 1 - 0.45 * k))
        frames.append(f)
    gen.save("campfire", frames, MS)


if __name__ == "__main__":
    build()
