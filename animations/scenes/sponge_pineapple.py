#!/usr/bin/env python3
"""Жёлтая губка в белой рубашке с красным галстуком выходит из домика-ананаса,
дверь закрывается, губка машет нам рукой и уходит обратно. Дно: песок, водоросли, пузырьки."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 70

SAND_Y = 12             # первая строка песка
TOP = 2                 # верх губки
DOOR_X, DOOR_W = 4, 7   # дверной проём x 4..10, строки 2..11
HOME_X = 4              # губка стоит в проёме
OUT_X = 16              # где машет

COL = {
    "Y": (255, 215, 0),     # губка
    "P": (170, 190, 0),     # поры (зеленовато-жёлтые)
    "W": (255, 255, 255),
    "b": (40, 150, 255),    # голубые глаза
    "M": (230, 30, 40),     # рот
    "T": (255, 255, 255),   # зубы
    "H": (235, 235, 235),   # рубашка
    "R": (255, 0, 0),       # галстук
    "N": (175, 95, 30),     # коричневые шорты
    "S": (115, 115, 125),   # ботинки (тёмно-серые: чистый чёрный не светится)
}

# лицом вправо; ноги/руки дорисовываются отдельно
BODY = [
    "YPYYPYY",
    "YWWYWWY",
    "YWbYWbY",
    "PMYYYMY",
    "YYMMMYP",
    "YPTTYYY",
    "HHHRHHH",
    "NNNRNNN",
]
FRONT_EYES = "YWbYbWY"   # смотрит на нас
FRONT_MOUTH = ["YMYYYMP", "PYMMMYY", "YYTTYPY"]
BLINK = ["YPYYPYY", "YYYYYYY", "YPPYPPY"]  # строки 0..2 при моргании

WATER_TOP = (0, 20, 80)
WATER_BOT = (0, 40, 110)
SAND = (230, 175, 80)
SAND2 = (200, 145, 60)
PEBBLE = (255, 225, 160)
PINE = (255, 120, 0)        # ананас
PINE_L = (255, 200, 40)     # светлая сетка на ананасе
LEAF = (0, 170, 40)
LEAF_L = (110, 230, 60)
FRAME = (150, 150, 170)
DOOR = (60, 120, 210)
DOOR_L = (130, 190, 255)
KNOB = (255, 220, 60)
WIN = (120, 210, 255)
WEED = (0, 180, 50)
WEED_L = (120, 230, 60)
BUBBLE = (150, 210, 255)


LEAVES = {(x, 0) for x in range(4, 11)} | {(2, 0), (12, 0)}


def house_mask():
    rows = {1: (2, 12)}
    m = set(LEAVES)
    for y in range(1, SAND_Y):
        a, b = rows.get(y, (1, 13) if y < 3 or y == SAND_Y - 1 else (0, 14))
        for x in range(a, b + 1):
            m.add((x, y))
    return m


HOUSE = house_mask()


def draw_bg(f, t, rng_bub):
    for y in range(SAND_Y):
        k = y / (SAND_Y - 1)
        c = tuple(int(a + (b - a) * k) for a, b in zip(WATER_TOP, WATER_BOT))
        for x in range(W):
            f.set(x, y, c)
    for y in range(SAND_Y, H):
        for x in range(W):
            f.set(x, y, SAND if y == SAND_Y else SAND2)
    for x in (2, 9, 13, 19, 24):
        f.set(x, 13, PEBBLE)
    # водоросли: две ленты, качаются
    for base, hgt, ph in ((26, 7, 0.0), (27, 5, 1.7)):
        for i in range(hgt):
            y = SAND_Y - 1 - i
            sw = math.sin(2 * math.pi * t / 40 + ph + i * 0.5) * (i / hgt) * 1.3
            f.set(round(base + sw), y, WEED_L if i % 2 else WEED)


def bubbles(t, n):
    """Пузырьки со дна. Периодично по t % n."""
    out = []
    for x0, start, speed in ((14, 0, 0.3), (25, 20, 0.25), (22, 70, 0.3), (19, 45, 0.22)):
        y = (t - start) % n * speed
        if y < 12:
            x = x0 + round(math.sin((t - start) * 0.35))
            out.append((x, SAND_Y - 1 - round(y)))
    return out


def draw_house(f, door_w):
    for (x, y) in HOUSE:
        if (x, y) in LEAVES:
            continue
        grid = (x + y) % 3 == 0 or (x - y) % 3 == 0
        f.set(x, y, PINE_L if grid else PINE)
    for (x, y) in LEAVES:                               # ботва
        f.set(x, y, LEAF_L if (x + y) % 2 else LEAF)
    for y in range(TOP, SAND_Y):
        f.set(DOOR_X - 1, y, FRAME)
        f.set(DOOR_X + DOOR_W, y, FRAME)
    for wx in (1, 13):                                  # круглые окошки
        f.set(wx, 5, WIN)
        f.set(wx, 6, WIN)
    for y in range(TOP, SAND_Y):                        # проём тёмный
        for x in range(DOOR_X, DOOR_X + DOOR_W):
            f.set(x, y, (0, 0, 0))
    # дверь на петлях слева: видимая ширина door_w
    for y in range(TOP, SAND_Y):
        for i in range(door_w):
            x = DOOR_X + i
            c = DOOR_L if (door_w < DOOR_W and i == door_w - 1) or (door_w == DOOR_W and i in (2, 4)) else DOOR
            f.set(x, y, c)
    if door_w == DOOR_W:
        f.set(DOOR_X + 5, 7, KNOB)
    elif door_w >= 3:
        f.set(DOOR_X + door_w - 2, 7, KNOB)


def sponge(x, face, step=0, wave=None, front=False, blink=False, k=1.0):
    """Пиксели губки {(x, y): цвет}. face = 1 вправо, -1 влево."""
    rows = [r for r in BODY]
    if front:
        rows[2] = FRONT_EYES
        rows[3:6] = FRONT_MOUTH
    if blink:
        rows[0:3] = BLINK
    px = {}

    def put(dx, dy, ch):
        if face < 0 and not front:
            dx = 6 - dx
        px[(x + dx, TOP + dy)] = COL[ch]

    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            put(dx, dy, ch)
    # ноги и ботинки
    if step % 2 == 0:
        legs = (1, 5)
    else:
        legs = (2, 4)
    for lx in legs:
        put(lx, 8, "Y")
        put(lx, 9, "S")
        put(lx + (1 if front and lx > 3 else -1 if front else 1), 9, "S")
    # руки
    sw = 0 if step % 2 == 0 else 1
    put(-1, 6, "H")
    put(-1 - sw if not front else -1, 7, "Y")
    if wave is None:
        put(7, 6, "H")
        put(7 + sw if not front else 7, 7, "Y")
    else:
        # поднятая рука; wave = 0/1 — кисть качается
        put(7, 6, "H")
        put(8, 5, "Y")
        put(8, 4, "Y")
        put(7 + 2 * wave, 3, "Y")
    if k < 1:
        px = {p: gen.scale(c, k) for p, c in px.items()}
    return px


def build():
    rng = random.Random(7)  # noqa: F841 (всё детерминировано)
    timeline = []   # (door_w, sponge_px or None)

    def door_anim(opening):
        seq = [7, 5, 3, 1, 0] if opening else [0, 1, 3, 5, 7]
        return [w for w in seq for _ in range(2)]

    # 1. закрыто
    for _ in range(6):
        timeline.append((7, None))
    # 2. дверь открывается
    for w in door_anim(True):
        timeline.append((w, None))
    # 3. губка появляется из темноты
    for i, k in enumerate((0.25, 0.5, 0.75, 1.0)):
        timeline.append((0, sponge(HOME_X, 1, 0, k=k)))
    # 4. идёт вправо, дверь за ним закрывается
    close = door_anim(False)
    ci = None
    x = HOME_X
    step = 0
    while x < OUT_X:
        for sub in range(2):
            if x >= 12 and ci is None:
                ci = 0
            w = 0
            if ci is not None:
                w = close[min(ci, len(close) - 1)]
                ci += 1
            timeline.append((w, sponge(x, 1, step)))
        x += 1
        step += 1
    while ci < len(close):
        timeline.append((close[ci], sponge(x, 1, 0)))
        ci += 1
    # 5. поворачивается к нам и машет
    for i in range(32):
        blink = i in (20, 21)
        wave = None if i < 2 or i >= 30 else (i // 3) % 2
        timeline.append((7, sponge(x, 1, 0, wave=wave, front=True, blink=blink)))
    # 6. идёт обратно, дверь открывается заранее
    opn = door_anim(True)
    oi = None
    step = 0
    while x > HOME_X:
        for sub in range(2):
            if x <= 15 and oi is None:
                oi = 0
            w = 7
            if oi is not None:
                w = opn[min(oi, len(opn) - 1)]
                oi += 1
            timeline.append((w, sponge(x, -1, step)))
        x -= 1
        step += 1
    # 7. уходит в темноту, дверь закрывается
    for k in (0.75, 0.5, 0.25):
        timeline.append((0, sponge(HOME_X, -1, 0, k=k)))
    for w in door_anim(False):
        timeline.append((w, None))

    n = len(timeline)
    frames = []
    for t, (door_w, sp) in enumerate(timeline):
        f = gen.Frame()
        draw_bg(f, t, None)
        draw_house(f, door_w)
        for (bx, by) in bubbles(t, n):
            if (bx, by) not in HOUSE or by < 0:
                f.set(bx, by, BUBBLE)
        if sp:
            for (px, py), c in sp.items():
                f.set(px, py, c)
        frames.append(f)
    gen.save("sponge_pineapple", frames, MS)


if __name__ == "__main__":
    build()
