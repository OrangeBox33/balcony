#!/usr/bin/env python3
"""Вулкан: спит → дрожит и светится → извергается (фонтан, потоки лавы, дым) → остывает."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
CX = 14.0          # ось конуса (между столбцами 13 и 14)
TOP = 5            # строка кромки кратера
BASE = 12          # нижняя строка конуса, под ней земля
CRATER = range(12, 16)

ROCK_L = (165, 95, 45)    # освещённый склон
ROCK_R = (120, 70, 35)    # теневой склон
ROCK_D = (95, 55, 30)     # прожилки
GROUND = (40, 120, 20)

# фазы (номера кадров)
CALM, RUMBLE, ERUPT, COOL, N = 0, 20, 50, 104, 144


def half_width(y):
    return 4 + (y - TOP) * 1.4


def in_cone(x, y):
    return TOP <= y <= BASE and abs(x + 0.5 - CX) <= half_width(y)


def surface(x):
    """Верхняя строка конуса в столбце x (или земля)."""
    for y in range(TOP, BASE + 1):
        if in_cone(x, y) and not (y == TOP and x in CRATER):
            return y
    return BASE + 1


def stream(dirx, start, wiggle):
    """Путь потока лавы вниз по склону: каждая строка — сдвиг наружу."""
    x, y = start
    pts = [(x, y)]
    for i, w in enumerate(wiggle):
        y += 1
        x += dirx * w
        pts.append((x, y))
        pts.append((x - dirx, y))  # поток в 2 пикселя — виден издалека
    return pts


STREAMS = [
    stream(-1, (11, TOP + 1), [1, 1, 2, 1, 2, 1, 2]),
    stream(+1, (16, TOP + 1), [1, 2, 1, 2, 1, 2, 1]),
    [(13, TOP + 2), (14, TOP + 2), (13, TOP + 3), (14, TOP + 3), (14, TOP + 4), (15, TOP + 4),
     (14, TOP + 5), (15, TOP + 5), (13, TOP + 6), (14, TOP + 6), (13, TOP + 7), (14, TOP + 7)],
]
STREAM_START = [ERUPT + 4, ERUPT + 10, ERUPT + 18]


def lava_color(age):
    """Свежая лава жёлтая, потом оранжевая, красная, тёмно-красная."""
    stops = [(0, (255, 230, 80)), (6, (255, 140, 0)), (18, (255, 60, 0)), (40, (200, 20, 0))]
    for (a0, c0), (a1, c1) in zip(stops, stops[1:]):
        if age <= a1:
            k = (age - a0) / (a1 - a0)
            return tuple(int(u + (v - u) * k) for u, v in zip(c0, c1))
    return stops[-1][1]


def mix(a, b, k):
    return tuple(int(u + (v - u) * k) for u, v in zip(a, b))


def build():
    rnd = random.Random(7)
    sparks = []   # [x, y, vx, vy, age]
    smoke = []    # [x, y, r, age, life, bright]
    frames = []

    for cycle in range(2):
        for t in range(N):
            f = gen.Frame()
            # ---- интенсивности фаз
            if t < RUMBLE:
                glow, shake, fountain = 0.0, 0, 0.0
            elif t < ERUPT:
                k = (t - RUMBLE) / (ERUPT - RUMBLE)
                glow = 0.45 + 0.55 * k
                shake = (1 if (t // 2) % 2 else -1) if k > 0.15 else 0
                fountain = 0.0
            elif t < COOL:
                k = (t - ERUPT) / (COOL - ERUPT)
                glow = 1.0
                shake = (1 if t % 2 else -1) if k < 0.15 else 0
                fountain = 1.0 if k < 0.55 else max(0.0, 1 - (k - 0.55) / 0.45)
            else:
                k = (t - COOL) / (N - COOL)
                glow = max(0.0, 1 - k * 1.6)
                shake, fountain = 0, 0.0

            # ---- дым (рисуем первым — он позади)
            if t < RUMBLE:
                rate = 0.18
            elif t < ERUPT:
                rate = 0.35
            elif t < COOL:
                rate = 0.7 if fountain > 0.3 else 0.45
            else:
                rate = 0.35 * (1 - (t - COOL) / (N - COOL)) + 0.12
            if rnd.random() < rate:
                big = t >= ERUPT and t < COOL
                smoke.append([CX + 1 + rnd.uniform(-1, 1), TOP - 2, 1.0 if big else 0.7, 0,
                              rnd.randint(16, 24) if big else rnd.randint(10, 14),
                              1.0 if big else 0.8])
            for s in smoke:
                x, y, r, age, life, br = s
                fade = br * (1 - age / life)
                c = gen.scale((175, 170, 175), 0.55 + 0.45 * fade)
                if fade > 0.08:
                    for yy in range(int(y - r) - 1, int(y + r) + 2):
                        for xx in range(int(x - r) - 1, int(x + r) + 2):
                            if (xx + 0.5 - x) ** 2 + (yy + 0.5 - y) ** 2 <= r * r:
                                f.set(xx + shake, yy, c)
                s[1] -= 0.35
                s[0] += 0.3
                s[2] = min(2.3, s[2] + 0.07)
                s[3] += 1
            smoke[:] = [s for s in smoke if s[3] < s[4] and s[1] > -3]

            # ---- конус
            for y in range(TOP, BASE + 1):
                for x in range(W):
                    if not in_cone(x, y):
                        continue
                    if y == TOP and x in CRATER:
                        continue
                    c = ROCK_L if x + 0.5 < CX + 0.5 else ROCK_R
                    if y == TOP + 1 and x in CRATER:
                        c = ROCK_D  # дно кратера
                    f.set(x + shake, y, c)
            for x in range(W):
                f.set(x, H - 1, GROUND)

            # ---- свечение кратера
            if glow > 0:
                pulse = 0.7 + 0.3 * math.sin(t * 0.9)
                g = glow * (pulse if t < ERUPT else 1.0)
                for x in CRATER:
                    f.set(x + shake, TOP + 1, mix((120, 15, 0), (255, 200, 30), g))
                    if g > 0.45:
                        f.set(x + shake, TOP, mix((200, 30, 0), (255, 120, 0), g))

            # ---- потоки лавы по склонам
            for st, s0 in zip(STREAMS, STREAM_START):
                el = t - s0
                if el < 0:
                    continue
                head = min(len(st), el + 1)
                for i in range(head):
                    x, y = st[i]
                    age = el - i
                    if t >= COOL:
                        cool = (t - COOL) / (N - COOL - 6)
                        if cool >= 1:
                            continue
                        rock = ROCK_L if x + 0.5 < CX + 0.5 else ROCK_R
                        c = mix(lava_color(max(age, 22)), rock, min(1.0, cool * 1.1 + i * 0.015))
                    else:
                        c = lava_color(age)
                    f.set(x + shake, y, c)

            # ---- столб лавы над кратером
            if fountain > 0:
                hgt = fountain * 5 + rnd.choice([0, 1])
                for k in range(int(hgt)):
                    y = TOP - 1 - k
                    core = (255, 240, 140) if k < hgt - 1.5 else (255, 170, 0)
                    f.set(13 + shake, y, core)
                    f.set(14 + shake, y, core)
                    if k < hgt * 0.5:
                        f.set(12 + shake, y, (255, 110, 0))
                        f.set(15 + shake, y, (255, 110, 0))

            # ---- фонтан
            if t == ERUPT:
                for _ in range(26):
                    sparks.append([rnd.uniform(11.5, 16.5), TOP - 1.0, rnd.uniform(-1.1, 1.1),
                                   rnd.uniform(-1.9, -1.0), 0])
            n_new = fountain * 2.2
            n_new = int(n_new) + (1 if rnd.random() < n_new % 1 else 0)
            if t >= RUMBLE + 18 and t < ERUPT and rnd.random() < 0.25:
                # первые плевки перед взрывом
                sparks.append([rnd.uniform(12.5, 15.5), TOP - 1.0, rnd.uniform(-0.3, 0.3),
                               rnd.uniform(-0.9, -0.6), 0])
            for _ in range(n_new):
                sparks.append([rnd.uniform(12.5, 15.5), TOP - 1.0, rnd.uniform(-0.75, 0.75),
                               rnd.uniform(-1.75, -1.05), 0])
            alive = []
            for p in sparks:
                x, y, vx, vy, age = p
                xi, yi = round(x - 0.5), round(y - 0.5)
                c = lava_color(age * 0.7)
                f.set(xi + shake, yi, c)
                p[0] += vx
                p[1] += vy
                p[3] += 0.13
                p[4] += 1
                nx, ny = round(p[0] - 0.5), round(p[1] - 0.5)
                if p[3] > 0 and (ny >= surface(nx) or ny >= H - 1):
                    continue
                if nx < -1 or nx > W:
                    continue
                alive.append(p)
            sparks[:] = alive

            if cycle == 1:
                frames.append(f)

    gen.save("volcano", frames, 80)


if __name__ == "__main__":
    build()
