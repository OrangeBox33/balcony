#!/usr/bin/env python3
"""Медведь в красной футболке летит вверх на воздушном шарике вдоль дерева.
Мимо проплывает улей, пчёлы вылетают и кусают медведя, он машет лапами
и кричит «Я тучка, я тучка!». Пчёлы улетают вниз за ульем — и снова тихий подъём."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H

N = 150                  # кадров в петле
MS = 70
SPEED = 1 / 3            # подъём: пикселей за кадр (ствол едет вниз)
PERIOD = 25              # период узора коры/листвы; N*SPEED кратно ему

FUR = (225, 130, 20)
BELLY = (255, 195, 100)
MUZZLE = (255, 210, 140)
SHIRT = (230, 0, 20)
BALLOON = (255, 0, 0)
SHINE = (255, 170, 170)
STRING = (170, 170, 180)

BARK = (150, 70, 10)
BARK_HI = (195, 105, 30)
BARK_LO = (110, 50, 5)
LEAF = (0, 150, 20)
LEAF_HI = (70, 210, 30)
HIVE = (255, 215, 40)
HIVE_D = (200, 110, 0)

BEE = (255, 245, 40)
BEE_DIM = (170, 110, 0)
TEXT = (255, 255, 255)
BUBBLE = (60, 130, 255)

TRUNK_X = 23             # ствол x 23..26, листва слева от него и на x 27
BX, BY = 5, 4            # левый верхний угол медведя (9×10)

BEAR = [
    ".ff...ff.",
    ".fffffff.",
    ".f.fff.f.",
    ".ffm.mff.",
    "..fmmmf..",
    ".rrrrrrr.",
    "rrrrrrrrr",
    "fbbbbbbbf",
    ".fbbbbbf.",
    ".ff...ff.",
]
BEAR_PAL = {"f": FUR, "b": BELLY, "m": MUZZLE, "r": SHIRT, "o": (255, 60, 40)}

BALLOON_ROWS = [
    ".rrr.",
    "rwrrr",
    "rrrrr",
    ".rrr.",
    "..r..",
]

HIVE_ROWS = [
    ".hh.",
    "HHHH",
    "hh.h",
    "HHHH",
    ".hh.",
]

# FONT5 «Я ТУЧКА, Я ТУЧКА!»
PHRASE = "Я ТУЧКА, Я ТУЧКА!"
BUB_X0 = 14              # пузырь-реплика: x 14..27, строки 0..6
TEXT_T0 = 40
TEXT_SPEED = 1


def smooth(k):
    k = min(1.0, max(0.0, k))
    return k * k * (3 - 2 * k)


# ---------------------------------------------------------------- дерево

rnd = random.Random(7)
BARK_MAP = [[rnd.random() for _ in range(4)] for _ in range(PERIOD)]
# листва: (строка в периоде, x0, ширина, высота) — слева от ствола и справа
CLUMPS = [(1, 20, 3, 3), (5, 27, 1, 4), (9, 21, 2, 2), (14, 20, 3, 3), (19, 27, 1, 3), (21, 21, 2, 2)]


def scroll(t):
    return int(t * SPEED)


def draw_tree(f, t):
    s = scroll(t)
    for y in range(H):
        row = (y - s) % PERIOD
        for i in range(4):
            v = BARK_MAP[row][i]
            c = BARK_HI if v > 0.8 else BARK_LO if v < 0.22 else BARK
            f.set(TRUNK_X + i, y, c)
    for r0, x0, w, h in CLUMPS:
        for k in range(-1, 2):               # копии периода, чтобы клумбы не обрезались на шве
            y0 = (r0 + s) % PERIOD + k * PERIOD
            for dy in range(h):
                for dx in range(w):
                    edge = w >= 3 and h >= 3 and dx in (0, w - 1) and dy in (0, h - 1)
                    if edge:
                        continue
                    c = LEAF_HI if (dx + dy + r0) % 3 == 0 else LEAF
                    f.set(x0 + dx, y0 + dy, c)


def hive_top(t):
    """Строка ветки с ульем (улей висит под ней)."""
    return scroll(t) - 6


def draw_hive(f, t):
    yb = hive_top(t)
    for x in range(16, TRUNK_X):
        f.set(x, yb, BARK)
    f.set(16, yb - 1, LEAF_HI)
    f.set(20, yb - 1, LEAF)
    f.sprite(HIVE_ROWS, 16, yb + 1, pal={"h": HIVE, "H": HIVE_D})


def hive_hole(t):
    return 18.0, hive_top(t) + 3.0


# ---------------------------------------------------------------- пчёлы

CX, CY = BX + 4.0, BY + 5.0      # центр медведя
BEES = []
for i in range(5):
    BEES.append({
        "out": 16 + 4 * i,           # вылет из улья
        "leave": TEXT_T0 + 72 + 5 * i,        # улетают вниз вправо
        "ph": i * 2 * math.pi / 5 + 0.4,
        "w": (0.21 + 0.03 * i) * (1 if i % 2 else -1),
        "dive_w": 0.13 + 0.02 * i,
        "dive_ph": i * 1.7,
    })


def orbit(b, t):
    a = b["ph"] + b["w"] * t
    dive = max(0.0, math.sin(b["dive_w"] * t + b["dive_ph"])) ** 6
    r = 1 - 0.75 * dive
    return CX + 6.5 * r * math.cos(a), CY + 4.2 * r * math.sin(a), dive


def bee_pos(b, t):
    """(x, y, кусает?) или None, если пчелы нет на экране."""
    if t < b["out"]:
        return None
    ox, oy, dive = orbit(b, t)
    k = (t - b["out"]) / 14
    if k < 1:
        hx, hy = hive_hole(t)
        e = smooth(k)
        return hx + (ox - hx) * e, hy + (oy - hy) * e + math.sin(t * 0.9) * 0.6 * (1 - e), False
    k = (t - b["leave"]) / 16
    if k >= 1:
        return None
    if k > 0:
        e = smooth(k)
        tx, ty = 21.0, 17.0
        return ox + (tx - ox) * e, oy + (ty - oy) * e, False
    return ox, oy, dive > 0.55


def draw_bee(f, x, y, t, i):
    xi, yi = round(x), round(y)
    lit = (t + i) % 2 == 0
    f.set(xi, yi, BEE if lit else BEE_DIM)
    # второй пиксель — чёрная полоска-хвост (видна на медведе, на небе просто пусто)
    tail = 1 if math.cos(i + t * 0.3) > 0 else -1
    under = f.px[yi][xi + tail] if 0 <= yi < H and 0 <= xi + tail < W else gen.BLACK
    f.set(xi + tail, yi, gen.BLACK if under != gen.BLACK else (BEE_DIM if lit else BEE))


# ---------------------------------------------------------------- медведь

def draw_bear(f, t, panic, shout):
    jolt = 0
    if panic:
        jolt = (0, 1, 0, -1)[(t // 2) % 4] if panic > 1 else 0
    x0 = BX + jolt
    rows = list(BEAR)
    if shout and (t // 3) % 3 != 2:
        rows[4] = "..fmomf.."
    if panic:
        rows[9] = (".ff...ff.", "ff.....ff", ".ff...ff.", "..ff.ff..")[(t // 2) % 4]
    f.sprite(rows, x0, BY, pal=BEAR_PAL)

    # левая лапа держит нитку шарика (вверх-влево)
    paw = (x0 - 1, BY + 4)
    f.set(x0, BY + 5, FUR)
    f.set(*paw, FUR)
    # шарик: дёргается, когда медведь машет
    bob = (0, 0, 1, 0)[(t // 3) % 4] if panic else 0
    bx = BX - 4 + bob
    f.sprite(BALLOON_ROWS, bx, 0, pal={"r": BALLOON, "w": SHINE})
    knot = (bx + 2, 4)
    sx0, sy0 = paw[0], paw[1] - 1
    n = max(abs(knot[0] - sx0), abs(knot[1] + 1 - sy0), 1)
    for k in range(n + 1):
        f.set(round(sx0 + (knot[0] - sx0) * k / n), round(sy0 + (knot[1] + 1 - sy0) * k / n), STRING)

    # правая лапа: висит или машет
    rx = x0 + 9
    if not panic:
        arm = [(rx, BY + 7)]
    else:
        arm = ([(rx, BY + 5), (rx + 1, BY + 4)],
               [(rx, BY + 6), (rx + 1, BY + 6)],
               [(rx, BY + 7), (rx + 1, BY + 8)],
               [(rx, BY + 6), (rx + 1, BY + 6)])[(t // 2) % 4]
    for p in arm:
        f.set(*p, FUR)


# ---------------------------------------------------------------- реплика

PHRASE_W = gen.text_width(PHRASE, gen.FONT5)
BUB_W = W - BUB_X0
TEXT_LEN = PHRASE_W + BUB_W - 2


def draw_bubble(f, t):
    k = t - TEXT_T0
    if not 0 <= k < TEXT_LEN + 4:
        return False
    # пузырь: тёмное поле с голубой рамкой и хвостиком к морде
    for y in range(0, 7):
        for x in range(BUB_X0, W):
            border = y in (0, 6) or x == BUB_X0
            f.set(x, y, BUBBLE if border else gen.BLACK)
    f.set(BUB_X0, 0, gen.BLACK)
    f.set(BUB_X0, 6, gen.BLACK)
    f.set(BUB_X0 - 1, 7, BUBBLE)
    f.set(BUB_X0 - 2, 8, BUBBLE)
    tx = W - 1 - k * TEXT_SPEED
    x = tx
    for ch in PHRASE:
        g = gen.FONT5[ch]
        for dy, row in enumerate(g):
            for dx, v in enumerate(row):
                xx = x + dx
                if v == "#" and BUB_X0 < xx < W:
                    f.set(xx, 1 + dy, TEXT)
        x += len(g[0]) + 1
    return True


# ---------------------------------------------------------------- сборка

def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        draw_tree(f, t)
        draw_hive(f, t)

        bees = [(i, bee_pos(b, t)) for i, b in enumerate(BEES)]
        bees = [(i, p) for i, p in bees if p]
        near = sum(1 for _, p in bees if abs(p[0] - CX) < 9 and p[1] > -1)
        panic = 2 if near >= 2 else 1 if near else 0
        shout = TEXT_T0 - 4 <= t < TEXT_T0 + TEXT_LEN
        draw_bear(f, t, panic, shout)

        for i, (x, y, bite) in bees:
            draw_bee(f, x, y, t, i)
            if bite:
                # укус — белая искра рядом с пчелой
                f.set(round(x), round(y) - 1, (255, 255, 255))

        draw_bubble(f, t)
        frames.append(f)
    gen.save("bear_balloon", frames, MS)


if __name__ == "__main__":
    build()
