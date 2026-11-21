#!/usr/bin/env python3
"""Ночь, город. Подъезжает тёмный автомобиль ночного героя, из него выходит герой
в плаще, бежит вперёд, кидает сюрикены и убегает за край. Машина уезжает следом."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 70
GROUND = 13

CAR = [                      # лицом вправо, 17×5
    "......kkkkkk.....",
    "f...kkgggggggk...",
    "fkkkkkkkkkkkkkkkL",
    "rkkkkkkkekkkkkkkk",
    "..tWt.......tWt..",
]
CAR_PAL = {
    "k": (95, 95, 130),       # тёмный, но не ниже порога — иначе исчезнет
    "f": (120, 120, 160),
    "g": (60, 160, 220),
    "L": (255, 255, 200),
    "r": (255, 0, 0),
    "e": (255, 200, 0),       # своя эмблема — жёлтая молния-точка
    "t": (110, 110, 120),
    "W": (200, 200, 220),
}

HERO_PAL = {
    "H": (130, 130, 175),     # костюм стальной
    "C": (150, 40, 210),      # плащ фиолетовый
    "E": (255, 200, 0),       # эмблема
    "w": (255, 255, 255),
    "s": (255, 120, 60),
}
HERO_STAND = [
    "..H..",
    ".HHH.",
    ".wHw.",
    "CHEHC",
    "CHHHC",
    "CHHHC",
    "CH.HC",
    ".H.H.",
]
HERO_RUN = [                  # бежит вправо, плащ развевается назад
    [
        "....H..",
        "...HHH.",
        "...HwHw",
        "CCHHEHs",
        ".CCHHH.",
        "..CHHH.",
        "...H.H.",
        "..H...H",
    ],
    [
        "....H..",
        "...HHH.",
        "...HwHw",
        ".CCHEH.",
        "CCCHHHs",
        "..CHHH.",
        "....H..",
        "...HH..",
    ],
]
HERO_THROW = [
    "....H...",
    "...HHH..",
    "...HwHw.",
    "CCHHEHss",
    ".CCHHH..",
    "..CHHH..",
    "...H.H..",
    "..H...H.",
]
STAR_A = [".S.", "SoS", ".S."]
STAR_B = ["S.S", ".o.", "S.S"]
STAR_PAL = {"S": (210, 225, 255), "o": (255, 255, 255)}

STARS = [(1, 1), (6, 3), (11, 0), (15, 2), (21, 1), (26, 3), (3, 5)]
# силуэты домов: (x0, x1, высота)
HOUSES = [(0, 4, 5), (5, 8, 7), (9, 13, 4), (14, 16, 8), (17, 21, 5), (22, 27, 6)]


def scenery(f, t):
    for i, (sx, sy) in enumerate(STARS):
        if (t // 6 + i) % 5:
            f.set(sx, sy, (110, 110, 150))
    for x0, x1, h in HOUSES:
        for x in range(x0, x1 + 1):
            for y in range(GROUND - h, GROUND):
                f.set(x, y, (0, 0, 0))
            f.set(x, GROUND - h, (40, 60, 150))       # контур крыши
        for wx in range(x0 + 1, x1, 2):              # окошки
            for wy in range(GROUND - h + 2, GROUND - 1, 2):
                if (wx * 7 + wy * 3) % 4 == 0:
                    f.set(wx, wy, (200, 150, 30))
    for x in range(W):
        f.set(x, GROUND, (80, 80, 95))


def draw_car(f, x, t, lights=True):
    rows = CAR if lights else [r.replace("L", "k") for r in CAR]
    f.sprite(rows, x, GROUND - 5, pal=CAR_PAL)
    if lights:                                        # свет фар
        for d in range(1, 5):
            f.add(x + 16 + d, GROUND - 3, (110 - d * 15,) * 2 + (60,))
    if (t // 2) % 2:                                  # спицы крутятся
        for wx in (x + 3, x + 13):
            f.set(wx, GROUND - 1, CAR_PAL["t"])


def build():
    frames = []
    t = 0
    STOP = 0
    # 1. машина въезжает слева с торможением
    n = 22
    for i in range(n):
        k = 1 - (1 - i / (n - 1)) ** 2
        x = round(-18 + (STOP + 18) * k)
        f = gen.Frame(); scenery(f, t); draw_car(f, x, t if i < n - 3 else 0)
        frames.append(f); t += 1
    # 2. дверь открывается, герой выходит (поднимается из-за машины)
    hx = STOP + 8
    for i in range(10):
        f = gen.Frame(); scenery(f, t)
        rise = min(8, i + 1)
        draw_car(f, STOP, 0)
        top = GROUND - 4 - rise
        f.sprite(HERO_STAND[:rise], hx, top, pal=HERO_PAL)
        frames.append(f); t += 1
    # спрыгивает на землю перед машиной
    for i in range(4):
        f = gen.Frame(); scenery(f, t); draw_car(f, STOP, 0)
        f.sprite(HERO_STAND, hx + 3 + i, GROUND - 8 - (2 if i < 2 else 0) + (i // 3), pal=HERO_PAL)
        frames.append(f); t += 1
    for i in range(5):                                 # стоит, плащ колышется
        f = gen.Frame(); scenery(f, t); draw_car(f, STOP, 0)
        f.sprite(HERO_STAND, hx + 6, GROUND - 8, pal=HERO_PAL)
        frames.append(f); t += 1
    # 3. бежит, на ходу кидает сюрикены
    x = hx + 4
    stars = []
    throws = {5, 12, 19}
    for i in range(32):
        f = gen.Frame(); scenery(f, t); draw_car(f, STOP, 0)
        throwing = i in throws or i - 1 in throws
        if i in throws:
            stars.append([x + 8, GROUND - 6 + (i % 3) - 1])
        for s in stars:
            s[0] += 3
        if throwing:
            f.sprite(HERO_THROW, x, GROUND - 8, pal=HERO_PAL)
        else:
            f.sprite(HERO_RUN[(i // 2) % 2], x, GROUND - 8, pal=HERO_PAL)
        for s in stars:
            f.sprite(STAR_A if (t % 2) else STAR_B, s[0] - 1, s[1] - 1, pal=STAR_PAL)
        frames.append(f); t += 1
        x += 1 if i % 3 else 0
    # 4. машина гасит фары и уезжает следом
    for i in range(22):
        f = gen.Frame(); scenery(f, t)
        k = (i / 21) ** 2
        draw_car(f, round(STOP + (W + 2 - STOP) * k), t)
        frames.append(f); t += 1
    for i in range(8):                                 # пустая улица
        f = gen.Frame(); scenery(f, t); frames.append(f); t += 1
    gen.save("night_car", frames, MS)


if __name__ == "__main__":
    build()
