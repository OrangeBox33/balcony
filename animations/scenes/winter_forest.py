#!/usr/bin/env python3
"""Лес под луной: четыре ели в снегу на волнистых сугробах, справа луна с ореолом,
мерцают звёзды, падает редкий снег. Раз за петлю с ветки срывается комок снега
и рассыпается искорками. Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
N = 160                 # 9,6 с
MS = 60

MOON = (23.0, 3.0, 2.6)
MOON_C = (205, 175, 70)
MOON_D = (175, 145, 55)
HALO = (95, 80, 30)

SNOW_TOP = (230, 235, 255)
SNOW_BODY = (150, 160, 205)
FLAKE = (200, 210, 245)

PAL = {
    "G": (25, 120, 50),
    "g": (40, 150, 65),      # светлая сторона кроны
    "w": (225, 235, 255),    # снег на ветках
    "n": (130, 75, 30),      # ствол
}

BIG = [
    "....w....",
    "...wgw...",
    "...Ggg...",
    "..wGggw..",
    "..GGggg..",
    ".wGGgggw.",
    ".GGGgggg.",
    "wGGGggggw",
    "GGGGggggg",
    "....n....",
    "....n....",
]
MID = [
    "...w...",
    "..wgw..",
    "..Ggg..",
    ".wGggw.",
    ".GGggg.",
    "wGGgggw",
    "GGGgggg",
    "...n...",
    "...n...",
]
SMALL = [
    "..w..",
    ".wgw.",
    ".Ggg.",
    "wGggw",
    "GGggg",
    "..n..",
    "..n..",
]
TINY = [
    "..w..",
    ".wgw.",
    "wGggw",
    "GGggg",
    "..n..",
]
# (спрайт, левый столбец) — основание ствола ставим на сугроб
TREES = [(MID, 0), (BIG, 6), (SMALL, 17), (TINY, 22)]
CLUMP_TREE = 1          # с какой ели падает комок
CLUMP_TIP = (7, 5)      # кончик ветки в спрайте (dx, dy): правая лапа BIG

T_FALL = 40             # когда срывается
T_BACK = 150            # когда на ветку снова ложится снег


def ground(x):
    return 11.4 + 1.0 * math.sin(x * 0.45 + 0.3) + 0.4 * math.sin(x * 1.1 + 2.1)


def top_row(x):
    return math.ceil(ground(x + 0.5))


def tree_y(rows, x0):
    c = x0 + len(rows[0]) // 2
    return top_row(c) - len(rows) + 1


def in_moon(x, y, extra=0.0):
    cx, cy, r = MOON
    return math.hypot(x - cx, y - cy) <= r + extra


def build():
    rnd = random.Random(21)
    stars = []
    while len(stars) < 11:
        sx, sy = rnd.randrange(W), rnd.randrange(0, 7)
        if in_moon(sx, sy, 2.0) or any(abs(sx - a) + abs(sy - b) < 3 for a, b, *_ in stars):
            continue
        stars.append((sx, sy, rnd.uniform(0, 2 * math.pi), rnd.choice((2, 3, 4))))

    # снежинки по кругу: за петлю каждая падает целое число раз
    flakes = [(rnd.uniform(0, W), rnd.uniform(0, 1), rnd.choice((1, 1, 2)), rnd.uniform(0, 6.28), rnd.choice((1, 2)))
              for _ in range(8)]

    rows, tsx = TREES[CLUMP_TREE]
    tsy = tree_y(rows, tsx)
    tip = (tsx + CLUMP_TIP[0], tsy + CLUMP_TIP[1])

    # искорки от комка: заранее
    sparks = []
    for i in range(12):
        a = math.pi * (0.08 + 0.84 * i / 11) + rnd.uniform(-0.15, 0.15)
        sp = rnd.uniform(0.3, 0.6)
        sparks.append((math.cos(a) * sp, -math.sin(a) * sp * 1.6, rnd.randrange(14, 22),
                       rnd.choice(((255, 255, 255), (170, 220, 255), (255, 230, 150)))))

    # траектория комка
    cx, cy = tip[0] + 0.0, tip[1] + 1.0
    path = []
    vx, vy = 0.2, -0.15
    while cy < top_row(round(cx)) - 1:
        path.append((cx, cy))
        vy += 0.035
        vx *= 0.93
        cx += vx
        cy += vy
    t_hit = T_FALL + len(path)
    hit = (round(cx), top_row(round(cx)) - 1)

    frames = []
    for t in range(N):
        f = gen.Frame()
        # звёзды
        for sx, sy, ph, k in stars:
            v = 0.5 + 0.5 * math.sin(2 * math.pi * k * t / N + ph)
            if v > 0.2:
                f.set(sx, sy, gen.scale((235, 220, 150), 0.5 + 0.5 * v))
        # луна
        mx, my, r = MOON
        for y in range(H):
            for x in range(W):
                d = math.hypot(x - mx, y - my)
                if d <= r:
                    f.set(x, y, MOON_D if (x, y) in ((22, 2), (24, 4), (25, 2)) else MOON_C)
                elif d <= r + 1.0:
                    f.set(x, y, HALO)
        # ели
        for i, (rows, x0) in enumerate(TREES):
            y0 = tree_y(rows, x0)
            f.sprite(rows, x0, y0, pal=PAL)
        # снег ушёл с ветки — лапа без шапки, сразу после срыва чуть пружинит
        if T_FALL <= t < T_BACK:
            f.set(tip[0], tip[1], PAL["G"])
            if t - T_FALL < 4 and (t - T_FALL) % 2 == 0:
                f.set(tip[0], tip[1], (0, 0, 0))
                f.set(tip[0], tip[1] + 1, PAL["G"])
        # сугробы
        for x in range(W):
            ty = top_row(x)
            for y in range(ty, H):
                f.set(x, y, SNOW_TOP if y == ty else SNOW_BODY)
        # падающий комок
        if T_FALL <= t < t_hit:
            px, py = path[t - T_FALL]
            f.set(round(px), round(py), SNOW_TOP)
            f.set(round(px) + 1, round(py), (190, 200, 240))
        # искорки
        age = t - t_hit
        if 0 <= age < 24:
            for vx_, vy_, life, col in sparks:
                if age >= life:
                    continue
                x = hit[0] + vx_ * age
                y = hit[1] + vy_ * age + 0.03 * age * age
                k = 1 - age / life
                if (age + int(vx_ * 10)) % 3 == 2 and age > 3:
                    continue           # мерцают
                f.set(round(x), round(y), gen.scale(col, 0.65 + 0.35 * k))
            if age < 3:            # «пуф» в момент удара
                for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1)):
                    f.set(hit[0] + dx, hit[1] + dy, (255, 255, 255))
        # снежинка, что приносит шапку обратно на ветку
        if T_BACK - 24 <= t < T_BACK:
            k = (t - (T_BACK - 24)) / 24
            f.set(round(tip[0] + 2 - 2 * k), round(tip[1] - 9 + 9 * k), FLAKE)
        # падающий снег
        for x0, ph, cyc, wph, sw in flakes:
            u = (ph + cyc * t / N) % 1
            y = round(u * (H + 2)) - 1
            x = round(x0 + sw * math.sin(2 * math.pi * 2 * t / N + wph)) % W
            if 0 <= y < top_row(x) and not in_moon(x, y, 1.0):
                f.set(x, y, FLAKE)
        frames.append(f)
    gen.save("winter_forest", frames, MS)


if __name__ == "__main__":
    build()
