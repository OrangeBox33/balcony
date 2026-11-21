#!/usr/bin/env python3
"""Человек-паук: стоит на крыше слева, стреляет паутиной в середину верха,
пролетает на ней маятником и приземляется на крышу справа. Потом — обратно."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H

PAL = {"r": (235, 0, 0), "b": (0, 70, 255), "W": (255, 255, 255)}
WEB = (230, 230, 240)
BUILDING = (70, 80, 150)
WINDOW = (255, 190, 40)
STREET = (90, 90, 100)

ROOF = 8                 # верхняя строка крыш
BLD_W = 5                # ширина домов у краёв
ANCHOR = (13.5, 0.0)

# все спрайты — лицом вправо; у висящих рука (точка крепления паутины) в (4, 0)
STAND = [
    ".rrr.",
    ".WrW.",
    "brrrb",
    "rbrbr",
    ".bbb.",
    ".b.b.",
    ".r.r.",
]
SHOOT = [                # рука вытянута к якорю, кисть в (6, 1)
    ".rrr...",
    ".WrW.br",
    "brrrb..",
    "rbrb...",
    ".bbb...",
    ".b.b...",
    ".r.r...",
]
CROUCH = [
    ".rrr.",
    ".WrW.",
    "brrrb",
    "rbbbr",
    "b...b",
    "r...r",
]
HANG_BACK = [
    "....r",
    ".rrrb",
    ".WrWb",
    "brrrb",
    "rbrb.",
    "bbb..",
    "b.b..",
    "r.r..",
]
HANG = [
    "....r",
    ".rrrb",
    ".WrWb",
    "brrrb",
    "rbrb.",
    ".bbb.",
    ".b.b.",
    ".r.r.",
]
HANG_FWD = [
    "....r",
    ".rrrb",
    ".WrWb",
    "brrrb",
    "rbrb.",
    "..bbb",
    "...bb",
    "...rr",
]
TUCK = [
    ".rrr.",
    "rWrWr",
    "brrrb",
    "bbbbr",
    ".rr..",
]


def line(f, x0, y0, x1, y1, c):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    n = int(math.ceil(n))
    for i in range(n + 1):
        k = i / n
        f.set(round(x0 + (x1 - x0) * k), round(y0 + (y1 - y0) * k), c)


def scenery(f):
    for x in range(W):
        f.set(x, H - 1, STREET)
    for x0 in (0, W - BLD_W):
        for y in range(ROOF, H):
            for x in range(x0, x0 + BLD_W):
                f.set(x, y, BUILDING)
        for wy in (ROOF + 2, ROOF + 4):
            f.set(x0 + 1, wy, WINDOW)
            f.set(x0 + 3, wy, WINDOW)


def half_trip(flip):
    """Кадры перелёта слева направо; flip=True — зеркально (справа налево)."""
    out = []

    def put(spr, x, y, web=None, blob=False, ms=80):
        out.append((spr, x, y, web, blob, ms))

    sx = 0                       # стоит у левого края, на крыше
    sy = ROOF - len(STAND)
    for _ in range(8):
        put(STAND, sx, sy, ms=90)
    # выстрел паутиной: нить вытягивается к якорю
    hand = (sx + 6, sy + 1)
    for k in (0.3, 0.6, 1.0):
        tip = (hand[0] + (ANCHOR[0] - hand[0]) * k, hand[1] + (ANCHOR[1] - hand[1]) * k)
        put(SHOOT, sx, sy, web=(hand, tip), blob=k == 1.0, ms=70)
    for _ in range(4):
        put(SHOOT, sx, sy, web=(hand, ANCHOR), blob=True, ms=90)

    # маятник: рука идёт по дуге вокруг якоря, внизу верёвка «короче»
    dx0, dy0 = hand[0] - ANCHOR[0], hand[1] - ANCHOR[1]
    th_max = math.atan2(-dx0, dy0)
    r_end = math.hypot(dx0, dy0)
    r_bot = H - 1 - len(HANG) - ANCHOR[1]
    T = 18
    th_rel = 0.82                # отпускает чуть раньше верхней точки
    for i in range(T + 1):
        u = i / T
        # θ от −θmax до +th_rel·θmax, быстрее всего внизу
        th = -th_max * math.cos(u * math.acos(-th_rel))
        r = r_bot + (r_end - r_bot) * (th / th_max) ** 2
        hx = ANCHOR[0] + r * math.sin(th)
        hy = ANCHOR[1] + r * math.cos(th)
        spr = HANG_BACK if th < -0.35 else (HANG if th < 0.35 else HANG_FWD)
        put(spr, round(hx) - 4, round(hy), web=((round(hx), round(hy)), ANCHOR), blob=True, ms=70)
    # отпустил: летит кувырком вверх-вправо и садится на правую крышу
    lx, ly = round(hx) - 4, round(hy)
    ex = W - 5
    ey = ROOF - len(CROUCH)
    hops = [(0.3, -1.5), (0.55, -2), (0.8, -1.2), (1.0, 0)]
    for k, lift in hops:
        x = lx + (ex - lx) * k
        y = ly + (ey - ly) * k + lift
        put(TUCK, round(x), round(y), blob=k < 0.5, ms=80)
    for _ in range(3):
        put(CROUCH, ex, ey, ms=90)

    if flip:
        res = []
        for spr, x, y, web, blob, ms in out:
            w = gen.width(spr)
            mweb = None
            if web:
                (a, b), (c, d) = web
                mweb = ((W - 1 - a, b), (W - 1 - c, d))
            res.append((spr, W - x - w, y, mweb, blob, ms, True))
        return res
    return [o + (False,) for o in out]


def build():
    seq = half_trip(False) + half_trip(True)
    frames, ms = [], []
    for spr, x, y, web, blob, d, flip in seq:
        f = gen.Frame()
        scenery(f)
        if blob:
            for bx in (12, 13, 14, 15):
                f.set(bx, 0, (180, 180, 190))
            f.set(13, 0, WEB)
            f.set(14, 0, WEB)
            f.set(13, 1, (180, 180, 190))
            f.set(14, 1, (180, 180, 190))
        if web:
            (x0, y0), (x1, y1) = web
            line(f, x0, y0, x1, y1, WEB)
        f.sprite(spr, x, y, flip=flip, pal=PAL)
        frames.append(f)
        ms.append(d)
    gen.save("spiderman", frames, ms)


if __name__ == "__main__":
    build()
