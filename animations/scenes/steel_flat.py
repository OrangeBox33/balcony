#!/usr/bin/env python3
"""Человек из стали гордо стоит, руки на поясе, плащ колышется. Слева подкрадывается гопник
с битой, подпрыгивает и бьёт его сверху по голове — герой мгновенно сплющивается в лепёшку,
над ним кружат звёздочки, гопник удирает. Потом лепёшка с «боинг» встаёт обратно."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 70
GROUND = 13
GROUND_C = (110, 90, 70)

HPAL = {
    "K": (110, 125, 180),   # волосы (на диодах тёмно-синие)
    "s": (255, 150, 90),    # кожа
    "B": (20, 70, 255),     # костюм
    "R": (255, 20, 10),     # эмблема
    "Y": (255, 210, 0),     # эмблема, пряжка
    "r": (235, 20, 10),     # трусы, сапоги
    "c": (200, 15, 10),     # плащ
}
CAPE = HPAL["c"]

# анфас, руки на поясе; K в середине лба — завитушка
HERO = [
    "...KKK...",
    "...sKs...",
    "...sss...",
    ".BBBBBBB.",
    "B.BRYRB.B",
    "B.BBRBB.B",
    ".sBBBBBs.",
    "..rrYrr..",
    "..BB.BB..",
    "..B...B..",
    ".rr...rr.",
    ".rr...rr.",
]
HX = 10                       # левый край героя (центр — столбец 14)
HY = GROUND - len(HERO)       # верх героя

# лепёшка: голова-блин, руки в стороны, плащ и сапоги торчат по краям
FLAT = [
    ".....KKKKK.....",
    "....ssKsKss....",
    "ccsBBBRYRBBBscc",
    ".rrr.BBBBB.rrr.",
]
FLATTER = [                   # первый кадр удара — ещё площе и шире
    "......KKKKK......",
    "cccsBBBRYRYRBBsccc",
    "rrrr..BBBBBBB.rrrr",
]
HALF = [                      # пружинит обратно
    "....KKK....",
    "....sKs....",
    "..BBBBBBB..",
    ".sBBRYRBBs.",
    "..rrrYrrr..",
    ".rrBB.BBrr.",
    "rrr.....rrr",
]

GPAL = {
    "C": (150, 150, 175),   # кепка
    "s": (255, 150, 90),
    "T": (120, 120, 145),   # спортивный костюм
    "W": (235, 235, 245),   # лампасы и кроссовки
}
BAT_HANDLE = (150, 80, 20)
BAT_BARREL = (200, 110, 35)

# гопник в профиль лицом вправо; hand — где держит биту
GOP = {
    "walk_a": ([
        ".CCC..",
        ".CCCCC",
        ".sss..",
        "..ss..",
        "TTWs..",
        "TTWT..",
        ".TWT..",
        ".T.T..",
        "T...T.",
        "W...WW",
    ], (3, 4)),
    "walk_b": ([
        ".CCC..",
        ".CCCCC",
        ".sss..",
        "..ss..",
        "TTWs..",
        "TTWT..",
        ".TWT..",
        "..TT..",
        "..TT..",
        "..WWW.",
    ], (3, 4)),
    "crouch": ([
        ".CCC..",
        ".CCCCC",
        ".sss..",
        ".sss..",
        "TTWTs.",
        "TTWT..",
        "TT.TT.",
        "WW..WW",
    ], (4, 4)),
    "jump": ([
        "...s..",
        ".CCs..",
        ".CCCCC",
        ".sss..",
        ".sss..",
        ".TWT..",
        ".TWT..",
        ".TTT..",
        "TT.TT.",
        "W...W.",
    ], (3, 0)),
    "swing": ([
        ".CCC..",
        ".CCCCC",
        ".sss..",
        ".sssss",
        ".TWT..",
        ".TWT..",
        ".TTT..",
        "TT.TT.",
        "W...W.",
    ], (5, 3)),
}


def draw_bat(f, hx, hy, ang, length=7):
    a = math.radians(ang)
    pts = []
    for i in range(length):
        p = (round(hx + math.cos(a) * i), round(hy + math.sin(a) * i))
        if p not in pts:
            pts.append(p)
    for i, (x, y) in enumerate(pts):
        f.set(x, y, BAT_HANDLE if i < 3 else BAT_BARREL)


def draw_gop(f, pose, gx, dy=0, bat=None, flip=False):
    rows, (hx, hy) = GOP[pose]
    w = gen.width(rows)
    top = GROUND - len(rows) + dy
    if flip:
        hx = w - 1 - hx
        if bat is not None:
            bat = 180 - bat
    f.sprite(rows, gx, top, flip=flip, pal=GPAL)
    if bat is not None:
        draw_bat(f, gx + hx, top + hy, bat)


def draw_cape(f, t, n, x0, y0, wind=1.0):
    """Плащ за спиной героя: виден по бокам от плеч до колен, правый край развевается."""
    ph = 2 * math.pi * 3 * t / n
    for r in range(3, 11):
        k = (r - 3) / 7
        left = 1 - k * 1.6 + math.sin(ph - r * 0.8) * 0.6 * k
        right = 7 + k * 3.2 * wind + math.sin(ph - r * 0.8 + 1.0) * 1.2 * k * wind
        for x in range(round(left), round(right) + 1):
            if 1 <= x <= 7:          # за телом — не виден (ноги и руки остаются читаемыми)
                continue
            f.set(x0 + x, y0 + r, CAPE)


STAR_COLS = [(255, 230, 0), (255, 255, 255), (0, 220, 255)]


def stars(f, t, cx, cy):
    for k in range(3):
        a = t * 0.6 + k * 2 * math.pi / 3
        x = cx + round(math.cos(a) * 3.5)
        y = cy + round(math.sin(a) * 1.2)
        c = STAR_COLS[k]
        f.set(x, y, c)
        if (t + k) % 2 == 0:
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                f.add(x + ddx, y + ddy, gen.scale(c, 0.5))


def build():
    # сценарий: список состояний, потом рисуем (плащ зависит от t/N — петля без шва)
    S = []

    def add(n=1, **st):
        for _ in range(n):
            S.append(dict(st))

    # 1. герой стоит в позе
    add(12, hero="stand")
    # 2. гопник подходит слева, бита на плече
    for i, gx in enumerate(range(-7, 2)):
        add(hero="stand", gop=("walk_a" if (i // 2) % 2 == 0 else "walk_b", gx, 0, -50, False))
    # 3. пауза: присел, замахнулся
    add(7, hero="stand", gop=("crouch", 2, 0, -110, False))
    # 4. прыжок — бита над головой
    add(hero="stand", gop=("jump", 3, -1, -95, False))
    add(hero="stand", gop=("jump", 4, -2, -80, False))
    add(hero="stand", gop=("jump", 5, -3, -60, False))
    # 5. удар сверху по голове
    add(hero="stand", gop=("jump", 5, -3, 8, False), hit=True, ms=100)
    # 6. мгновенно — лепёшка
    add(hero="flatter", gop=("swing", 5, -2, 25, False), shake=1)
    add(hero="flat", gop=("crouch", 4, 0, 40, False))
    add(hero="flatter", gop=("crouch", 3, 0, 20, False))
    add(3, hero="flat", gop=("crouch", 3, 0, 10, False), star=True)
    # 7. гопник оглядывается и удирает
    add(4, hero="flat", gop=("walk_b", 3, 0, -40, True), star=True)
    for i, gx in enumerate(range(2, -9, -2)):
        add(hero="flat", gop=("walk_a" if i % 2 == 0 else "walk_b", gx, 0, -60, True), star=True,
            dust=gx + 6)
    # 8. лежит со звёздочками
    add(14, hero="flat", star=True)
    # 9. боинг — обратно
    add(2, hero="half")
    add(hero="stand", jump=-1)
    add(hero="stand", jump=0, ms=90)
    add(5, hero="stand")

    N = len(S)
    frames, ms = [], []
    for t, st in enumerate(S):
        f = gen.Frame()
        for x in range(W):
            f.set(x, GROUND, GROUND_C)
        hero = st["hero"]
        if hero == "stand":
            y0 = HY + st.get("jump", 0)
            draw_cape(f, t, N, HX, y0)
            f.sprite(HERO, HX, y0, pal=HPAL)
        else:
            rows = {"flat": FLAT, "flatter": FLATTER, "half": HALF}[hero]
            w = gen.width(rows)
            f.sprite(rows, HX + 4 - w // 2, GROUND - len(rows), pal=HPAL)
        if st.get("star"):
            stars(f, t, HX + 4, GROUND - 6)
        g = st.get("gop")
        if g:
            pose, gx, dy, bat, flip = g
            draw_gop(f, pose, gx, dy, bat, flip)
        if st.get("hit"):
            for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (2, -1), (-2, -1)):
                f.add(HX + 4 + dx, HY + dy, (255, 255, 200))
        if st.get("shake"):
            for dx in (-3, -2, 12, 13):
                f.set(HX + dx + (1 if dx > 0 else -1), GROUND - 1, (200, 200, 200))
        if st.get("dust") is not None:
            f.set(st["dust"], GROUND - 1, (170, 170, 170))
        frames.append(f)
        ms.append(st.get("ms", MS))
    gen.save("steel_flat", frames, ms)


if __name__ == "__main__":
    build()
