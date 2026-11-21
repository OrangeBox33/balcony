#!/usr/bin/env python3
"""Варежки на верёвочке: красная и синяя варежки с белой снежинкой висят на верёвочке, перекинутой
через гвоздик, и покачиваются в такт. По снежинке пробегает искорка, падает снег. Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 70
N = 140                      # ≈ 9.8 с
SWINGS = 4                   # качаний за петлю
rng = random.Random(41)

# варежка большим пальцем вправо; W — манжета, r — вязка, S — снежинка
MITTEN = [
    ".WWWWW...",
    ".WrWrW...",             # резинка манжеты
    ".rrrrr...",
    "rrrSrrr..",
    "rSrSrSrr.",
    "rrSSSrrrr",
    "rSSSSSrrr",
    "rrSSSrr.r",
    "rSrSrSr..",
    "rrrSrrr..",
    ".rrrrr...",
]
MW = gen.width(MITTEN)
MY = 3                       # верх манжеты
LEFT_X, RIGHT_X = 3, 16      # левая (красная) и правая (синяя, зеркальная) — по центру экрана
HOOK = (13, 14)              # гвоздик в ряду 0

RED = (210, 15, 20)
BLUE = (20, 70, 255)
WHITE = (215, 215, 235)
CUFF = (240, 240, 255)
YARN = (235, 170, 60)
NAIL = (150, 150, 165)
SPARK = (255, 235, 110)

# путь искорки по снежинке — по кругу вокруг центра, потом в центр
FLAKE = [(x, y) for y, row in enumerate(MITTEN) for x, ch in enumerate(row) if ch == "S"]
FCX = sum(x for x, _ in FLAKE) / len(FLAKE)
FCY = sum(y for _, y in FLAKE) / len(FLAKE)
PATH = sorted(FLAKE, key=lambda p: (math.hypot(p[0] - FCX, p[1] - FCY) < 1.2,
                                     math.atan2(p[1] - FCY, p[0] - FCX)))
SPARK_STEP = 2               # кадров на пиксель
SPARK_LEN = len(PATH) * SPARK_STEP


class Flake:
    def __init__(self):
        self.x0 = rng.uniform(0, W)
        self.ph = rng.random()
        self.k = rng.choice((2, 2, 3))           # оборотов падения за петлю
        self.sw = rng.choice((1, 2))
        self.amp = rng.uniform(0.4, 1.0)
        self.sph = rng.random()
        self.bright = rng.random() < 0.55

    def pos(self, t):
        span = H + 2
        y = (self.ph * span + t * self.k * span / N) % span - 1
        x = self.x0 + self.amp * math.sin(2 * math.pi * (t * self.sw / N + self.sph))
        return round(x) % W, round(y)


FLAKES = [Flake() for _ in range(16)]


def swing(t):
    """Сдвиг варежек по горизонтали: −1, 0, +1 — плавное качание в такт."""
    return round(1.1 * math.sin(2 * math.pi * t * SWINGS / N))


def line(f, x0, y0, x1, y1, c):
    n = max(abs(x1 - x0), abs(y1 - y0))
    for i in range(n + 1):
        f.set(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), c)


def spark_at(t, start):
    """Индекс пикселя снежинки под искоркой (или None)."""
    a = (t - start) % N
    if a >= SPARK_LEN:
        return None
    return a // SPARK_STEP


def draw_mitten(f, x0, flip, body, spark):
    rows = [r[::-1] for r in MITTEN] if flip else MITTEN
    pal = {"W": CUFF, "r": body, "S": WHITE}
    f.sprite(rows, x0, MY, pal=pal)
    if spark is None:
        return
    for back, k in ((0, 1.0), (1, 0.55)):
        i = spark - back
        if i < 0:
            continue
        px, py = PATH[i]
        if flip:
            px = MW - 1 - px
        c = SPARK if back == 0 else tuple(int(w + (s - w) * k) for w, s in zip(WHITE, SPARK))
        f.set(x0 + px, MY + py, c)
        if back == 0:                 # вокруг искорки вязка чуть подсвечивается
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x0 + px + dx, MY + py + dy
                if 0 <= xx < W and 0 <= yy < H and f.px[yy][xx] == body:
                    f.set(xx, yy, tuple(min(255, int(v * 0.6 + 110)) for v in body))


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        for fl in FLAKES:
            x, y = fl.pos(t)
            if 0 <= y < H:
                f.set(x, y, (200, 200, 225) if fl.bright else (130, 130, 150))

        s = swing(t)
        lx, rx = LEFT_X + s, RIGHT_X + s
        # верёвочка: от гвоздика к серединам манжет
        line(f, HOOK[0], 1, lx + 3, MY - 1, YARN)
        line(f, HOOK[1], 1, rx + MW - 4, MY - 1, YARN)
        f.set(HOOK[0], 0, NAIL)
        f.set(HOOK[1], 0, NAIL)

        draw_mitten(f, lx, False, RED, spark_at(t, 10))
        draw_mitten(f, rx, True, BLUE, spark_at(t, 10 + N // 2))
        frames.append(f)
    gen.save("mittens", frames, MS)


if __name__ == "__main__":
    build()
