#!/usr/bin/env python3
"""Ночной герой-летучая мышь: под синим ночным небом подъезжает чёрный угловатый
автомобиль, открывается фонарь кабины, герой в плаще выпрыгивает, бежит вправо,
на бегу бросает крутящиеся бэтаранги и убегает за край. Машина уезжает следом."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 70
GROUND = 13

# «чёрное» делаем тёмно-серым — иначе на диодах оно пропадёт
HERO = {
    "K": (105, 105, 130),     # маска и костюм
    "C": (80, 80, 110),       # плащ (темнее костюма, но выше порога)
    "E": (255, 200, 0),       # эмблема
    "Y": (210, 130, 0),       # пояс (темнее эмблемы, чтобы не слипались)
    "s": (255, 130, 70),      # низ лица
    "W": (255, 255, 255),     # глаза
}

# все спрайты лицом вправо; высота 11, ноги на последней строке
STAND = [
    "..K.K..",
    "..KKK..",
    "..WKW..",
    "..sss..",
    ".EKEKE.",
    "CKEEEKC",
    "CKKKKKC",
    "CKYYYKC",
    "CCK.KCC",
    "C.K.KC.",
    ".CK.KC.",
]
CROUCH = [                    # присел после прыжка
    "..K.K..",
    "..KKK..",
    "..WKW..",
    "..sss..",
    ".EKEKE.",
    "CKEEEKC",
    "CKKKKKC",
    "CKYYYKC",
    "CKK.KKC",
    "C.C.C.C",
]
RUN = [
    [
        ".....K.K",
        ".....KKK",
        ".....KKW",
        "....Kss.",
        "CCCKKKK.",
        ".CCKEEKs",
        "..CKKKK.",
        ".CCYYYK.",
        "C.CK.K..",
        "..K...K.",
        ".K.....K",
    ],
    [
        ".....K.K",
        ".....KKK",
        ".....KKW",
        "....Kss.",
        ".CCKKKK.",
        "CCCKEEK.",
        ".CCKKKKs",
        "C.CYYYK.",
        "...KK...",
        "...K.K..",
        "...K..K.",
    ],
]
THROW = [                     # рука выброшена вперёд
    ".....K.K..",
    ".....KKK..",
    ".....KKW..",
    "....Kss...",
    "CCCKKKKKKs",
    ".CCKEEK...",
    "..CKKKK...",
    ".CCYYYK...",
    "C.CK.K....",
    "..K...K...",
    ".K.....K..",
]
JUMP = [                      # в прыжке, плащ раскрыт как крылья
    "C.K.K..C",
    "CCKKK.CC",
    ".CWKWCC.",
    ".CsssC..",
    "CCKKKCC.",
    "CEKEKEC.",
    "C.EEE.C.",
    "..YYY...",
    "..K.K...",
    ".K...K..",
]

CAR = [                       # лицом вправо, 15×5: плавник сзади, низкий клин
    "h..............",
    "hh....gGGg.....",
    "hkkkkgGGGGgkhh.",
    "okkkkkkkkkkkkkL",
    "..tw.......twb.",
]
CAR_OPEN = [                  # фонарь кабины откинут назад
    "h..............",
    "hhgGg..........",
    "hkgGgkkkkkkkhh.",
    "okkkkkkkkkkkkkL",
    "..tw.......twb.",
]
CAR_PAL = {
    "k": (85, 85, 115),       # кузов
    "h": (140, 140, 175),     # светлые грани кузова
    "g": (40, 110, 220),      # рама фонаря
    "G": (90, 170, 255),      # стекло
    "L": (255, 255, 210),     # фара
    "b": (0, 120, 255),       # синий огонь спереди внизу
    "o": (255, 110, 0),       # турбина сзади
    "t": (120, 120, 130),     # шины
    "w": (200, 200, 220),     # диски
}
CAR_W = 15

BAT = [                       # бэтаранг крутится: 4 фазы
    ["S.S", "SSS", "..."],
    ["..S", ".S.", "SS."],
    [".S.", ".SS", ".S."],
    ["SS.", ".S.", "..S"],
]
BAT_PAL = {"S": (215, 225, 255)}

SKY_TOP = (0, 10, 95)
SKY_LOW = (20, 40, 150)
MOON = [".mm.", "mmmm", "mmmm", ".mm."]
MOON_PAL = {"m": (170, 170, 120)}
STARS = [(9, 1), (14, 0), (19, 2), (24, 1), (27, 3)]
# дома: (x0, x1, верх)
HOUSES = [(0, 3, 7), (4, 6, 5), (9, 12, 6), (13, 14, 8), (17, 20, 5), (24, 27, 7)]


def sky(y):
    k = y / (GROUND - 1)
    return tuple(round(a + (b - a) * k) for a, b in zip(SKY_TOP, SKY_LOW))


def scenery(f, t):
    for y in range(GROUND):
        c = sky(y)
        for x in range(W):
            f.set(x, y, c)
    for i, (sx, sy) in enumerate(STARS):
        if (t // 5 + i) % 4:
            f.set(sx, sy, (150, 150, 200))
    f.sprite(MOON, 2, 0, pal=MOON_PAL)
    for x0, x1, top in HOUSES:                       # чёрные силуэты на синем небе
        for x in range(x0, x1 + 1):
            for y in range(top, GROUND):
                f.set(x, y, (0, 0, 0))
        for wx in range(x0 + 1, x1, 2):
            for wy in range(top + 1, GROUND - 1, 2):
                if (wx * 5 + wy * 3) % 4 == 0:
                    f.set(wx, wy, (210, 150, 30))
    for x in range(W):
        f.set(x, GROUND, (90, 90, 105))


def draw_car(f, x, t, opened=False, beam=True, flame=0):
    f.sprite(CAR_OPEN if opened else CAR, x, GROUND - 5, pal=CAR_PAL)
    if beam:                                         # свет фар по дороге
        for d in range(1, 5):
            f.add(x + CAR_W - 1 + d, GROUND - 3 + (d > 2), (120 - d * 22, 120 - d * 22, 70 - d * 12))
    if flame:                                        # пламя турбины сзади
        for d in range(1, flame + 1):
            c = (255, 200, 60) if d == 1 else (255, 90 - 20 * d, 0)
            if d < flame or t % 2:
                f.set(x - d, GROUND - 2, c)
    if t % 4 < 2:                                    # спицы крутятся
        for wx in (x + 2, x + 11):
            f.set(wx, GROUND - 1, CAR_PAL["t"])


def build():
    frames = []
    t = 0
    STOP = 0

    def frame():
        f = gen.Frame()
        scenery(f, t)
        return f

    # 1. машина въезжает слева, тормозит
    n = 16
    for i in range(n):
        k = 1 - (1 - i / (n - 1)) ** 2
        x = round(-CAR_W + (STOP + CAR_W) * k)
        f = frame()
        draw_car(f, x, t if i < n - 2 else 0, flame=3 if i < n - 6 else (1 if i < n - 2 else 0))
        frames.append(f); t += 1
    # 2. фонарь откидывается
    for i in range(3):
        f = frame(); draw_car(f, STOP, 0, opened=i >= 1); frames.append(f); t += 1
    # 3. герой выпрыгивает из кабины по дуге и приземляется перед машиной
    HX = 15
    path = [(5, 3), (7, 1), (10, 0), (13, 1), (15, 3)]
    for jx, jy in path:
        f = frame(); draw_car(f, STOP, 0, opened=True)
        f.sprite(JUMP, jx, jy, pal=HERO)
        frames.append(f); t += 1
    for i in range(2):
        f = frame(); draw_car(f, STOP, 0, opened=True)
        f.sprite(CROUCH, HX, GROUND - len(CROUCH), pal=HERO)
        frames.append(f); t += 1
    for i in range(3):
        f = frame(); draw_car(f, STOP, 0, opened=True)
        f.sprite(STAND, HX, GROUND - len(STAND), pal=HERO)
        frames.append(f); t += 1
    # 4. бросает два бэтаранга (летят вверх-вправо, крутятся), потом убегает за край
    bats = []
    x = HX - 3                # профильные спрайты: голова в столбцах 5–7, у STAND — 2–4
    plan = ["T", "T", "S", "T", "T", "S"] + ["R"] * 16
    for i, act in enumerate(plan):
        f = frame(); draw_car(f, STOP, 0, opened=x < 22)
        if act == "T" and (i == 0 or plan[i - 1] != "T"):
            bats.append([x + 10.5, GROUND - 7.0 - len(bats) * 2, 0])
        for b in bats:
            b[0] += 1.2; b[1] -= 0.4; b[2] += 1
        if act == "R":
            spr = RUN[(i // 2) % 2]
            x += 1
        else:
            spr = THROW if act == "T" else STAND
        f.sprite(spr, x + (3 if spr is STAND else 0), GROUND - len(spr), pal=HERO)
        for b in bats:
            f.sprite(BAT[b[2] % 4], round(b[0]) - 1, round(b[1]) - 1, pal=BAT_PAL)
        frames.append(f); t += 1
    # 5. машина срывается следом
    n = 12
    for i in range(n):
        k = ((i + 1) / n) ** 1.7
        f = frame()
        draw_car(f, round(STOP + (W + 4 - STOP) * k), t, flame=3)
        frames.append(f); t += 1
    for i in range(4):
        f = frame(); frames.append(f); t += 1
    gen.save("bat_hero", frames, MS)


if __name__ == "__main__":
    build()
