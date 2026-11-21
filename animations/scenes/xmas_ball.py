#!/usr/bin/env python3
"""Ёлочный шар: с еловой ветки на ниточке свисает большой красный шар с золотым колпачком,
медленно качается маятником, по нему скользит блик, иногда в нём отражается гирлянда.
Петля без шва."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 60
SWING = 60                 # кадров на полное качание туда-обратно
N = SWING * 2              # 7,2 с
CX, CY = 14.0, 9.0         # центр шара в покое: круг 10×10 на x 9..18, y 4..13
R = 4.75
SWING_PX = 2               # качание ±2 пикселя

EDGE = (145, 0, 16)        # край шара — ещё светится на диодах
MID = (225, 12, 28)
LIGHT = (255, 70, 70)
GOLD = (255, 170, 0)
GOLD_HI = (255, 230, 120)
STRING = (150, 150, 140)
NEEDLE = (0, 135, 35)
NEEDLE_HI = (50, 185, 60)
TWIG = (130, 65, 20)
SNOW = (230, 235, 255)
FLAKE_ARM = (120, 170, 255)
REFLECT = [(255, 220, 0), (60, 255, 80), (60, 140, 255), (0, 240, 240)]


def mix(a, b, k):
    k = max(0.0, min(1.0, k))
    return tuple(int(p + (q - p) * k) for p, q in zip(a, b))


def branch(f, t):
    # ветка через весь верх: сучок, хвоя свисает пучками, на ней снег
    for x in range(W):
        f.set(x, 0, NEEDLE_HI if x % 3 == 0 else NEEDLE)
        if x % 4 != 1:
            f.set(x, 1, NEEDLE if x % 2 else NEEDLE_HI)
        if x % 4 == 3 and not 11 <= x <= 16:
            f.set(x, 2, NEEDLE)
    for x in (6, 7, 19, 20, 21):
        f.set(x, 0, TWIG)
    for x in (2, 3, 9, 24, 25):         # снег на ветке
        f.set(x, 0, SNOW)


FLAKES = [(4, 6, 0), (23, 8, 37)]      # две снежинки-«плюсика»: x, y, сдвиг мерцания


def flakes(f, t):
    for fx, fy, ph in FLAKES:
        k = 0.5 + 0.5 * math.cos(2 * math.pi * ((t + ph) / N * 3))
        f.set(fx, fy, mix((170, 200, 255), (255, 255, 255), k))
        arm = mix((90, 130, 220), FLAKE_ARM, k)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            f.set(fx + dx, fy + dy, arm)


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        branch(f, t)
        flakes(f, t)
        s = math.sin(2 * math.pi * t / SWING)
        # шар сдвигаем на целые пиксели: при дробном сдвиге круг на 28×14 «рвётся» по краю
        ox = round(SWING_PX * s)
        bx, by = CX + ox, CY

        # ниточка от ветки к ушку
        f.set(math.floor(CX + ox * 0.5), 1, STRING)

        # свет: блик бежит навстречу качанию — шар уходит вправо, блик сползает влево
        lx, ly, lz = -0.45 - 0.4 * s, -0.55, 0.72
        ln = math.sqrt(lx * lx + ly * ly + lz * lz)
        lx, ly, lz = lx / ln, ly / ln, lz / ln
        hx, hy, hz = lx, ly, lz + 1                    # «полувектор» к зрителю
        hn = math.sqrt(hx * hx + hy * hy + hz * hz)
        hx, hy, hz = hx / hn, hy / hn, hz / hn

        # отражения гирлянды: во второй половине петли по дуге справа мигают цветные огоньки
        rk = (t - N * 0.5) / (N * 0.42)
        refl = {}
        if 0 <= rk <= 1:
            for i, c in enumerate(REFLECT):
                on = (t // 5 + i) % 4 != 0          # огоньки мигают по очереди
                edge = min(rk, 1 - rk) * 8          # в начале и в конце — только часть точек
                if not on or i >= edge * len(REFLECT):
                    continue
                ang = math.radians(-35 + i * 22)
                refl[(math.floor(bx + 3.2 * math.cos(ang)), math.floor(by + 3.2 * math.sin(ang)))] = c

        for y in range(H):
            for x in range(W):
                ux, uy = x + 0.5 - bx, y + 0.5 - by
                if ux * ux + uy * uy > R * R:
                    continue
                nx, ny = ux / R, uy / R
                nz = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
                d = max(0.0, nx * lx + ny * ly + nz * lz)
                sp = max(0.0, nx * hx + ny * hy + nz * hz) ** 40
                c = mix(EDGE, MID, d * 1.6) if d < 0.62 else mix(MID, LIGHT, (d - 0.62) / 0.38)
                c = mix(c, (255, 255, 255), sp * 1.4)
                if (x, y) in refl:
                    c = refl[(x, y)]
                f.set(x, y, c)

        # колпачок с ушком
        cx = math.floor(bx) - 2
        for i in range(4):
            f.set(cx + i, 3, GOLD_HI if i == 1 else GOLD)
        f.set(cx + 1, 2, GOLD)
        f.set(cx + 2, 2, GOLD)
        frames.append(f)
    gen.save("xmas_ball", frames, MS)


if __name__ == "__main__":
    build()
