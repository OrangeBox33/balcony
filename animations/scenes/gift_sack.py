#!/usr/bin/env python3
"""Мешок с подарками на снегу: стоит тихо, потом начинает шевелиться и подпрыгивать,
из горлышка выглядывают коробки, вылетают звёздочки — и мешок снова успокаивается.
Ночь, идёт снег. Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
N = 130                 # кадров в петле
MS = 70
GROUND = 12             # снег — строки 12–13
CX = 14                 # центр мешка

RED = (225, 15, 25)
RED_HI = (255, 120, 105)
RED_SH = (150, 0, 12)
GOLD = (255, 185, 0)
SNOW_GROUND = (175, 195, 235)
SNOW_TOP = (225, 235, 255)
FLAKE = (120, 140, 195)

# полуширина тела мешка по строкам снизу вверх
BODY = [4, 5, 5, 5, 5, 4, 2]
BOXES = [  # (dx от центра, цвет коробки, цвет ленты)
    (-2, (0, 200, 60), (255, 230, 0)),
    (1, (40, 110, 255), (255, 60, 160)),
]


def ease(p):
    p = max(0.0, min(1.0, p))
    return 0.5 - 0.5 * math.cos(math.pi * p)


def energy(t):
    """Насколько сильно «живое» внутри: 0 — тихо, 1 — прыгает вовсю."""
    if t < 18 or t >= 112:
        return 0.0
    if t < 40:
        return 0.35                           # чуть шевелится
    if t < 52:
        return 0.35 + 0.65 * ease((t - 40) / 12)
    if t < 84:
        return 1.0
    return 1.0 - ease((t - 84) / 28)          # успокаивается


def pose(t):
    """(наклон верха, подскок, сплющен ли) для кадра t."""
    e = energy(t)
    if e == 0:
        return 0, 0, False
    if e < 0.6:                               # редкие подёргивания
        lean = round(1.1 * math.sin(t * 0.55) * math.sin(t * 0.21))
    else:
        lean = round(e * 1.4 * math.sin(t * 0.9))
    hop, squash = 0, False
    if e > 0.6:
        ph = t % 8                            # прыжок раз в 8 кадров
        hop = (0, 1, 2, 2, 1, 0, 0, 0)[ph] if e > 0.85 else (0, 1, 1, 0, 0, 0, 0, 0)[ph]
        squash = ph == 5 and e > 0.85
    return lean, hop, squash


def draw_sack(f, t):
    lean, hop, squash = pose(t)
    e = energy(t)
    base = GROUND - 1 - hop                   # нижняя строка мешка
    body = BODY[:]
    if squash:                                # приземлился — сплющило
        body = [5, 6, 6, 6, 5, 2]

    # коробки выглядывают из горлышка, пока мешок прыгает вовсю
    neck_y = base - len(body)
    peek = 0
    if 50 <= t < 92:
        peek = 1 + (t // 4) % 2 if e > 0.85 else 1
    for i, (dx, col, rib) in enumerate(BOXES):
        p = peek - (1 if i == 1 and (t // 6) % 2 else 0)
        if p <= 0:
            continue
        bx = CX + dx + lean
        top = neck_y - 3 - p
        f.set(bx, top, col)
        f.set(bx + 1, top, rib)
        f.set(bx, top + 1, rib)
        f.set(bx + 1, top + 1, col)

    for i, hw in enumerate(body):
        y = base - i
        sh = round(lean * i / len(body))
        for x in range(CX - hw + sh, CX + hw + sh + 1):
            f.set(x, y, RED)
        f.set(CX + hw + sh, y, RED_SH)           # тень справа
        if 2 <= i <= 4:
            f.set(CX - hw + sh + 1, y, RED_HI)   # блик слева
    # горлышко перетянуто верёвкой, хвостики банта висят на боку
    nx = CX + lean
    for x in range(nx - 1, nx + 2):
        f.set(x, neck_y, GOLD)
    wig = 1 if e > 0.3 and (t // 3) % 2 else 0
    f.set(nx - 2, neck_y, GOLD)                   # петелька
    f.set(nx + 1, neck_y + 1, GOLD)               # хвостик
    f.set(nx + 2 - wig, neck_y + 2, GOLD)
    # оборка над верёвкой — расширяется кверху, по верху «зубчики»
    open_ = peek > 0
    for x in range(nx - 1, nx + 2):
        f.set(x, neck_y - 1, RED)
    for x in range(nx - 2, nx + 3):
        if open_ and abs(x - nx) <= 1:
            continue                              # раскрылось — коробки лезут
        f.set(x, neck_y - 2, RED_HI if (x - nx) % 2 == 0 else RED)
    f.set(nx - 3, neck_y - 3 + (0 if open_ else 1), RED)
    f.set(nx + 3, neck_y - 3 + (0 if open_ else 1), RED)
    return nx, neck_y - 3


class Star:
    def __init__(self, t0, vx, vy):
        self.t0, self.vx, self.vy = t0, vx, vy


STARS = [Star(56, -0.45, -0.3), Star(68, 0.5, -0.32), Star(80, -0.38, -0.36)]


def draw_star(f, x, y, k, big):
    c = gen.scale((255, 220, 40), k)
    w = gen.scale((255, 255, 230), k)
    f.set(x, y, w)
    if big:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            f.set(x + dx, y + dy, c)


def build():
    rnd = random.Random(23)
    # снежинки: за петлю каждая проходит экран целое число раз — шва нет
    flakes = []
    for _ in range(11):
        flakes.append((rnd.uniform(0, W), rnd.uniform(0, GROUND), rnd.choice((1, 1, 2)),
                       rnd.uniform(0, 6.28)))
    frames = []
    for t in range(N):
        f = gen.Frame()
        for x in range(W):
            f.set(x, GROUND, SNOW_TOP)
            f.set(x, GROUND + 1, SNOW_GROUND)
        for fx, fy, k, ph in flakes:
            y = (fy + t * GROUND * k / N) % GROUND
            x = (fx + 0.8 * math.sin(2 * math.pi * t / N * 2 + ph)) % W
            f.set(int(x), int(y), FLAKE)

        sx, sy = draw_sack(f, t)

        for s in STARS:
            age = t - s.t0
            if not 0 <= age < 26:
                continue
            x = sx + s.vx * age
            y = sy + 1 + s.vy * age + 0.022 * age * age
            if y > GROUND - 1:
                continue
            k = 1.0 if age < 18 else 1 - (age - 18) / 9
            k *= 0.75 + 0.25 * ((age // 2) % 2)
            draw_star(f, round(x), round(y), k, age >= 2)
        frames.append(f)
    gen.save("gift_sack", frames, MS)


if __name__ == "__main__":
    build()
