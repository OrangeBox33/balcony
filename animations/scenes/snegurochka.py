#!/usr/bin/env python3
"""Снегурочка: голубая шубка с белой опушкой, кокошник, длинная коса.
Стоит, моргает — потом кружится на месте (полы шубки разлетаются), от неё разлетаются снежинки.
Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 70
X = 8                   # левый край спрайта 11×14 — центр фигуры в колонке 13
CX = X + 5
rng = random.Random(33)

FRONT = [
    "....cWc....",
    "..cWcWcWc..",
    "...hhhhh...",
    "..hsksksh..",
    "..hpsmsph..",
    "..h.sss.h..",
    "..hWWWWWh..",
    "..bbbWbbb..",
    ".bbbbWbbbb.",
    ".WbbbWbbbW.",
    "..bbbWbbb..",
    ".bbbbWbbbb.",
    "bbbbbWbbbbb",
    "WWWWWWWWWWW",
]
BACK = [
    "....cWc....",
    "..cWcWcWc..",
    "...hhhhh...",
    "..hhhhhhh..",
    "..hhhhhhh..",
    "...hhhhh...",
    "...WWhWW...",
    "..bbbhbbb..",
    ".bbbbhbbbb.",
    ".WbbbhbbbW.",
    "..bbbhbbb..",
    ".bbbbrbbbb.",
    "bbbbbbbbbbb",
    "WWWWWWWWWWW",
]
SIDE = [                # лицом вправо, коса висит за спиной
    "....cWc....",
    "..cWcWcWc..",
    "...hhhhh...",
    "...hhssks..",
    "...hhsps...",
    "...h.ss....",
    "...hWWW....",
    "...hbbbb...",
    "..hbbbbbb..",
    "..hbbbbbW..",
    "..hbbbbb...",
    "..rbbbbbb..",
    ".bbbbbbbbb.",
    ".WWWWWWWWW.",
]
PAL = {
    "c": (70, 170, 255),      # кокошник
    "W": (255, 255, 255),
    "h": (255, 200, 0),       # коса и волосы
    "s": (255, 150, 105),
    "k": (0, 0, 0),
    "p": (255, 60, 110),      # румянец
    "m": (255, 40, 80),
    "b": (40, 120, 255),      # шубка
    "r": (255, 30, 120),      # бант на косе
}
FLAKE = (210, 225, 255)
SNOW_DIM = (110, 120, 160)

# сценарий: стоит → три оборота (разгон, быстро, торможение) → стоит
IDLE1 = 26
SPIN = [4] * 4 + [3] * 4 + [2] * 4 + [3] * 4 + [4] * 4      # кадров на позу
POSES = ["front", "side_r", "back", "side_l"] * 5
IDLE2 = 112 - IDLE1 - sum(SPIN)
N = IDLE1 + sum(SPIN) + IDLE2
SPIN_START = IDLE1
SPIN_END = IDLE1 + sum(SPIN)


def pose_at(t):
    if t < SPIN_START or t >= SPIN_END:
        return "front", 0.0
    k = t - SPIN_START
    for p, d in zip(POSES, SPIN):
        if k < d:
            break
        k -= d
    # насколько быстро кружится (0..1) — для разлёта шубки
    u = (t - SPIN_START) / (SPIN_END - SPIN_START)
    return p, math.sin(math.pi * u)


# снежинки, вылетающие при кружении: (рождение, угол, скорость, жизнь)
BURST = []
for t in range(SPIN_START + 2, SPIN_END + 4):
    u = (t - SPIN_START) / (SPIN_END - SPIN_START)
    for _ in range(2):
        if rng.random() < 0.3 + 0.6 * math.sin(math.pi * min(u, 1)):
            a = rng.uniform(0, 2 * math.pi)
            BURST.append((t, a, rng.uniform(0.3, 0.5), rng.randint(14, 22), rng.random()))


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


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        for fl in FALL:
            x, y = fl.pos(t)
            f.set(x, y, SNOW_DIM)

        for t0, a, v, life, tw in BURST:
            age = t - t0
            if 0 <= age < life:
                r = 2.5 + v * age
                aa = a + 0.04 * age                         # чуть закручиваются
                x = CX + r * math.cos(aa) * 1.5             # по горизонтали места больше
                y = 7.5 + r * math.sin(aa) * 0.8 + age * 0.05
                k = 1 - age / life
                k = 0.6 + 0.4 * k * (0.75 + 0.25 * math.sin(2 * math.pi * (age / 4 + tw)))
                f.set(round(x), round(y), gen.scale(FLAKE, k))

        pose, speed = pose_at(t)
        rows = {"front": FRONT, "back": BACK, "side_r": SIDE, "side_l": SIDE}[pose]
        flip = pose == "side_l"
        if pose == "front" and (t % 56) in (12, 13, 40):
            rows = [r.replace("k", "s") for r in rows]     # моргнула
        f.sprite(rows, X, 0, flip=flip, pal=PAL)
        # шубка разлетается в кружении: подол шире
        flare = round(speed * 1.6)
        for y, extra in ((11, flare - 1), (12, flare), (13, flare)):
            row = rows[y]
            left = len(row) - len(row.lstrip("."))
            right = len(row.rstrip(".")) - 1
            for e in range(1, extra + 1):
                c = PAL["W"] if y == 13 else PAL["b"]
                f.set(X + left - e, y, c)
                f.set(X + right + e, y, c)
        # пока стоит — на кокошнике вспыхивает искорка
        if pose == "front":
            g = (t % 28) / 28
            if g < 0.3:
                k = math.sin(math.pi * g / 0.3)
                sx, sy = (CX + 2, 0) if (t // 28) % 2 else (CX - 2, 0)
                f.set(sx, sy, gen.scale((255, 255, 255), 0.5 + 0.5 * k))
                if k > 0.6:
                    f.set(sx + (1 if sx > CX else -1), sy, gen.scale(FLAKE, 0.7))
        frames.append(f)
    gen.save("snegurochka", frames, MS)


if __name__ == "__main__":
    build()
