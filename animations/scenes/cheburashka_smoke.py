#!/usr/bin/env python3
"""Чебурашка с красными глазами курит сигарету."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
BROWN = (200, 100, 25)
EAR_IN = (255, 150, 110)
FACE = (255, 175, 95)
NOSE = (120, 40, 0)
EYE = (255, 0, 0)
CIG = (230, 230, 230)
EMBER = (255, 70, 0)
EMBER_HOT = (255, 230, 120)

HX, HY = 9.5, 6.6     # центр головы
EARS = [(3.3, 3.4), (15.7, 3.4)]
MOUTH = (12, 9)
CIG_PX = [(13, 9), (14, 9), (15, 9), (16, 9)]
TIP = (17, 9)


BODY = [
    "..BBBBBB..",
    ".BBBffBBB.",
    "BBBffffBBB",
]


def inside(x, y, cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1


def draw_cheb(f, ember, eyes_closed=False):
    for y in range(H):
        for x in range(W):
            c = None
            for ex, ey in EARS:
                if inside(x, y, ex, ey, 3.5):
                    c = EAR_IN if inside(x, y, ex, ey, 2.1) else BROWN
            if inside(x, y, HX, HY, 4.6, 4.3):
                c = FACE if inside(x, y, HX, HY + 1.0, 3.3, 3.0) else BROWN
            if c:
                f.set(x, y, c)
    # тельце: коричневые плечи, светлое пузико
    f.sprite(BODY, 5, 11, pal={"B": BROWN, "f": FACE})
    # красные глаза
    for ex in (8, 11):
        if eyes_closed:
            f.set(ex, 7, EYE)
        else:
            f.set(ex, 6, EYE)
            f.set(ex, 7, EYE)
    f.set(9, 8, NOSE)
    f.set(10, 8, NOSE)
    # лапка держит сигарету у рта
    f.set(13, 10, BROWN)
    f.set(14, 10, BROWN)
    for x, y in CIG_PX:
        f.set(x, y, CIG)
    f.set(*TIP, ember)


class Smoke:
    """Клубы дыма: каждый — (рождение, x0, y0, vx, vy, радиус в конце, жизнь, кольцо?)."""

    def __init__(self, n):
        self.n = n
        self.p = []

    def emit(self, t0, x0, y0, vx, vy, r1, life, ring=False, bright=170):
        self.p.append((t0, x0, y0, vx, vy, r1, life, ring, bright))

    def draw(self, f, t):
        for t0, x0, y0, vx, vy, r1, life, ring, bright in self.p:
            age = (t - t0) % self.n
            if age >= life:
                continue
            k = age / life
            x = x0 + vx * age + 0.6 * math.sin(age / 3 + x0)
            y = y0 + vy * age
            r = 0.5 + (r1 - 0.5) * k
            fade = 1.0 if k < 0.6 else 1 - (k - 0.6) / 0.4 * 0.45
            col = gen.scale((bright, bright, bright + 15), fade)
            for yy in range(int(y - r) - 1, int(y + r) + 2):
                for xx in range(int(x - r) - 1, int(x + r) + 2):
                    d = math.hypot(xx - x, yy - y)
                    on = (r - 0.75 <= d <= r + 0.35) if ring else d <= r + 0.15
                    if on and f.px[yy][xx] == gen.BLACK if 0 <= xx < W and 0 <= yy < H else False:
                        f.set(xx, yy, col)


def build():
    N = 110
    smoke = Smoke(N)
    # тонкая струйка с кончика всё время
    for t0 in range(0, N, 5):
        smoke.emit(t0, TIP[0] + 1, TIP[1] - 1, 0.28, -0.3, 0.5, 26, bright=140)
    # затяжка 1 (t 10..22) → выдох облаком (t 26..)
    for i, t0 in enumerate(range(26, 40, 2)):
        smoke.emit(t0, MOUTH[0] + 3, MOUTH[1] + 1, 0.3, -0.22, 1.6, 30, bright=190)
    # затяжка 2 (t 60..72) → выдох кольцами (t 76..)
    for t0 in (76, 92):
        smoke.emit(t0, MOUTH[0] + 5, MOUTH[1], 0.3, -0.26, 2.1, 30, ring=True, bright=210)

    drags = [(10, 22), (60, 72)]
    frames = []
    for t in range(N):
        f = gen.Frame()
        dragging = any(a <= t < b for a, b in drags)
        if dragging:
            ember = EMBER_HOT if t % 3 else (255, 160, 40)
        else:
            ember = EMBER
        draw_cheb(f, ember)
        if dragging:
            # огонёк разгорается — вокруг кончика оранжевое свечение
            for dx, dy in ((1, 0), (0, -1), (0, 1)):
                f.add(TIP[0] + dx, TIP[1] + dy, (150, 50, 0))
        smoke.draw(f, t)
        frames.append(f)
    gen.save("cheburashka_smoke", frames, 100)


if __name__ == "__main__":
    build()
