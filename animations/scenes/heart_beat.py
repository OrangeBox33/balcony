#!/usr/bin/env python3
"""Сердце бьётся «тук-тук», и с каждым ударом от него расходится волна-контур в форме сердца."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
CX, CY = 13.5, 7.4         # у формулы «дольки» выше кончика: так сердце ровно по центру и на ударе не обрезается
BEAT = 22                  # кадров на удар
BEATS = 3                  # петля из трёх ударов — у волн три цвета
MS = 55
BASE, PULSE = 4.3, 0.75    # размер сердца и насколько оно раздувается
RING_SPEED = 0.42          # на сколько растёт волна за кадр (в «размерах сердца»)
RING_W = 1.0               # толщина волны

HEART = (255, 20, 70)
SHINE = (255, 150, 180)
RINGS = [(255, 0, 170), (255, 40, 90), (190, 0, 255)]


def inside(u, v):
    """Классическое сердце: (u²+v²−1)³ − u²v³ ≤ 0."""
    return (u * u + v * v - 1) ** 3 - u * u * v ** 3 <= 0


def heart_size(x, y):
    """Минимальный размер сердца, при котором точка попадает внутрь (подбираем делением пополам)."""
    lo, hi = 0.01, 60.0
    for _ in range(30):
        s = (lo + hi) / 2
        if inside((x - CX) / s, -(y - CY) / s):
            hi = s
        else:
            lo = s
    return hi


# у каждой точки экрана свой «размер», на котором через неё проходит контур
R = [[heart_size(x + 0.5, y + 0.5) for x in range(W)] for y in range(H)]


def beat(p):
    """«Тук-тук»: два толчка за удар, второй слабее."""
    a = math.exp(-((p - 0.06) / 0.07) ** 2)
    b = 0.6 * math.exp(-((p - 0.30) / 0.08) ** 2)
    return a + b


def build():
    frames = []
    for t in range(BEAT * BEATS):
        f = gen.Frame()
        p = (t % BEAT) / BEAT
        size = BASE + PULSE * beat(p)

        # волны: каждая родилась на своём ударе и растёт; кадр зависит только от t по модулю петли
        for k in range(4):
            age = (t % (BEAT * BEATS)) - ((t // BEAT) - k) * BEAT
            idx = ((t // BEAT) - k) % BEATS
            s = BASE + 0.4 + age * RING_SPEED
            fade = max(0.0, 1 - age / (BEAT * 1.9))
            if fade <= 0:
                continue
            col = gen.scale(RINGS[idx], 0.35 + 0.65 * fade)
            for y in range(H):
                for x in range(W):
                    if s - RING_W < R[y][x] <= s:
                        f.set(x, y, col)

        # само сердце поверх волн
        for y in range(H):
            for x in range(W):
                if R[y][x] <= size:
                    f.set(x, y, HEART)
        # блик слева сверху, на ударе ярче
        bx, by = round(CX - size * 0.6), round(CY - size * 0.8)
        f.set(bx, by, SHINE)
        if beat(p) > 0.5:
            f.set(bx + 1, by, SHINE)
            f.set(bx, by + 1, gen.scale(SHINE, 0.8))
        frames.append(f)
    gen.save("heart_beat", frames, MS)


if __name__ == "__main__":
    build()
