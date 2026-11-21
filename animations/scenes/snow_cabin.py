#!/usr/bin/env python3
"""Домик в снегу: бревенчатая избушка с толстой снежной шапкой и сосульками, из трубы
колечками идёт дым, в окне тёплый свет и раз за петлю мимо окна проходит тень. Вокруг
ёлочки и сугробы, ночь, звёзды, падает снег. Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
N = 160                 # кадров в петле (9,6 с)
MS = 60
rng = random.Random(160)

SNOW = (205, 215, 240)
SNOW_DIM = (150, 165, 205)
LOG_A = (175, 92, 35)
LOG_B = (150, 78, 28)
LOG_END = (215, 150, 85)
ROOF_EDGE = (120, 55, 20)
WINDOW = (255, 190, 50)
SHADOW = (120, 60, 5)
DOOR = (110, 50, 18)
ICE = (120, 190, 255)
BRICK = (175, 60, 40)
SMOKE = (210, 210, 220)

TREE = [
    "..W..",
    ".WGW.",
    ".GGG.",
    "WGGGW",
    ".GGG.",
    "WGGGW",
    "GGGGG",
    "..b..",
]
TREE_PAL = {"W": (220, 230, 250), "G": (20, 150, 50), "b": (140, 70, 25)}

WALL_X = (9, 18)
WALL_Y = (9, 12)
WIN_X, WIN_Y = 10, 10           # окно 4×2
ICICLES = [(7, 2), (9, 1), (10, 1), (12, 1), (13, 1), (15, 1), (16, 1), (18, 1), (20, 2)]


def roof_rows():
    # снежная шапка-трапеция: (y, x_from, x_to)
    return [(4, 11, 16), (5, 9, 18), (6, 7, 20)]


# звёзды расставлены вручную: не за крышей и не на пути дыма
STARS = [(x, y, rng.uniform(0, 1)) for x, y in
         [(1, 1), (5, 3), (8, 0), (12, 2), (15, 0), (3, 0), (24, 4), (27, 4), (10, 1)]]


class Flake:
    def __init__(self):
        self.x = rng.uniform(0, W)
        self.y0 = rng.uniform(0, 14)
        self.laps = rng.choice((2, 3))
        self.wob = rng.uniform(0.3, 0.8)
        self.ph = rng.uniform(0, 2 * math.pi)


FLAKES = [Flake() for _ in range(10)]

RING = [".s.", "s.s", ".s."]
SMOKE_EVERY = 32               # новое колечко каждые 32 кадра (5 за петлю)
SMOKE_LIFE = 48
CHIMNEY_TOP = (17.5, 2.2)      # откуда выходит дым


def draw_scene(f, t):
    # ёлочки
    f.sprite(TREE, 1, 5, pal=TREE_PAL)
    f.sprite(TREE, 22, 5, pal=TREE_PAL)
    # стены из брёвен с торцами
    for y in range(WALL_Y[0], WALL_Y[1] + 1):
        for x in range(WALL_X[0], WALL_X[1] + 1):
            f.set(x, y, LOG_A if y % 2 == 0 else LOG_B)
        f.set(WALL_X[0] - 1, y, LOG_END)
        f.set(WALL_X[1] + 1, y, LOG_END)
    # окно с тенью: раз за петлю мимо проходит кто-то (голова + плечи)
    for y in range(WIN_Y, WIN_Y + 2):
        for x in range(WIN_X, WIN_X + 4):
            f.set(x, y, WINDOW)
    p = (t - 70) / 24                       # тень идёт с кадра 70 по 94
    if 0 <= p <= 1:
        sx = WIN_X - 1.5 + p * 7            # центр силуэта слева направо
        for x in range(WIN_X, WIN_X + 4):
            dx = abs(x - sx)
            if dx < 0.6:
                f.set(x, WIN_Y, SHADOW)     # голова
            if dx < 1.6:
                f.set(x, WIN_Y + 1, SHADOW)  # плечи
    # дверь с ручкой
    for y in range(10, 13):
        for x in (15, 16, 17):
            f.set(x, y, DOOR)
    f.set(16, 11, (255, 200, 60))
    # крыша: торец и толстая снежная шапка
    for x in range(7, 21):
        f.set(x, 7, ROOF_EDGE)
    for y, a, b in roof_rows():
        for x in range(a, b + 1):
            f.set(x, y, SNOW if y < 6 else SNOW_DIM)
    # труба торчит из снега
    f.set(17, 3, SNOW)
    f.set(18, 3, SNOW)
    f.set(17, 4, BRICK)
    f.set(18, 4, BRICK)
    # сосульки, по ним пробегает блик
    glint = (t % 80) / 80 * 22 + 2          # бежит слева направо дважды за петлю
    for x, n in ICICLES:
        near = abs(x - glint) < 1.2
        for k in range(n):
            if k == 0 or not WALL_X[0] - 1 <= x <= WALL_X[1] + 1:
                f.set(x, 8 + k, (255, 255, 255) if near else ICE)
    # сугробы
    for x in range(W):
        f.set(x, 13, SNOW_DIM)
    drift = [(0, 12), (1, 12), (2, 12), (3, 12), (4, 12), (5, 12), (6, 12), (8, 12), (9, 12), (10, 12),
             (19, 12), (20, 12), (21, 12), (22, 12), (23, 12), (24, 12), (25, 12), (26, 12), (27, 12),
             (0, 11), (1, 11), (26, 11), (27, 11)]
    for x, y in drift:
        f.set(x, y, SNOW if y == 11 or x in (3, 4, 22, 23) else SNOW_DIM)


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        # звёзды мерцают
        for x, y, ph in STARS:
            k = 0.5 + 0.5 * math.sin(2 * math.pi * (t / N * 3 + ph))
            f.set(x, y, gen.scale((255, 240, 190), 0.45 + 0.55 * k))
        # снег падает (за домом)
        for fl in FLAKES:
            y = (fl.y0 + t / N * 14 * fl.laps) % 14
            x = (fl.x + fl.wob * math.sin(2 * math.pi * t / N * 2 + fl.ph)) % W
            f.set(int(x), int(y), (170, 180, 215))
        # дым колечками: каждое уплывает вправо-вверх и тает
        for i in range(N // SMOKE_EVERY):
            age = (t - i * SMOKE_EVERY) % N
            if age >= SMOKE_LIFE:
                continue
            k = age / SMOKE_LIFE
            cx = CHIMNEY_TOP[0] + age * 0.2
            cy = CHIMNEY_TOP[1] - min(age, 10) * 0.08 + 0.3 * math.sin(age * 0.2)
            col = gen.scale(SMOKE, 1 - 0.4 * k)
            if age < 6:               # только вышло из трубы — маленький клубок
                f.set(round(cx), round(cy), col)
            else:
                f.sprite(RING, round(cx) - 1, round(cy) - 1, pal={"s": col})
        draw_scene(f, t)
        frames.append(f)
    gen.save("snow_cabin", frames, MS)


if __name__ == "__main__":
    build()
