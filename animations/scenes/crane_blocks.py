#!/usr/bin/env python3
"""Большой жёлтый башенный кран: тележка едет по стреле, крюк опускается в привозной ящик,
достаёт оттуда блок (внутри ящика блоков не видно), ставит один на другой — растёт дом,
в окнах зажигается свет. Потом дом тает — петля."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 60
GROUND = 13
rng = random.Random(11)

Y1 = (255, 175, 0)          # жёлтый
Y2 = (190, 110, 0)          # тень решётки (ещё видна на диодах)
CONCRETE = (120, 120, 135)
EARTH = (130, 90, 50)
MAST_X = 21                 # мачта — колонки 21 и 22
JIB_Y = 1
JIB_X0 = 2                  # конец стрелы
CAB_WIN = (255, 210, 120)
RED = (255, 0, 0)
MOON = (230, 220, 150)

PANEL = (95, 130, 210)
WIN_OFF = (0, 0, 0)
WIN_ON = (255, 200, 40)
HOUSE_CX = 7
PILE_CX = 15                # ящик с деталями
NB = 4
BOX_X0, BOX_X1, BOX_TOP = 12, 18, 9
BOX = (135, 65, 20)
BOX_LIGHT = (240, 170, 70)  # рёбра и доски светлее — тёмное на диодах пропадает
HOOK_IN_BOX = BOX_TOP       # крюк ныряет в ящик, блок целиком внутри


def ease(a, b, n):
    out = []
    for k in range(1, n + 1):
        u = k / n
        u = u * u * (3 - 2 * u)
        out.append(round(a + (b - a) * u))
    return out


def timeline():
    """Состояние крана по кадрам: tx — тележка, hy — крюк, carry — блок на крюке."""
    st = {"tx": PILE_CX, "hy": 3, "carry": False, "house": 0}
    seq = []

    def push():
        seq.append(dict(st))

    def vert(to):
        step = 1 if to > st["hy"] else -1
        while st["hy"] != to:
            st["hy"] += step
            push()

    def horiz(to):
        for x in ease(st["tx"], to, 11):
            st["tx"] = x
            push()

    def wait(n):
        for _ in range(n):
            push()

    for i in range(NB):
        vert(HOOK_IN_BOX)               # в ящик
        wait(3)
        st["carry"] = True
        wait(1)
        vert(3)
        horiz(HOUSE_CX)
        vert(10 - 2 * i)                # ставим на дом
        wait(2)
        st["carry"] = False
        st["house"] += 1
        wait(1)
        vert(3)
        horiz(PILE_CX)
    return seq


def block(f, cx, top, win, k=1.0):
    for dx in range(5):
        for dy in range(2):
            c = PANEL
            if dy == 0 and dx in (1, 3):
                c = win[dx // 2]
            f.set(cx - 2 + dx, top + dy, gen.scale(c, k))


def crate(f):
    for x in range(BOX_X0, BOX_X1 + 1):
        for y in range(BOX_TOP, GROUND):
            edge = x in (BOX_X0, BOX_X1) or y in (BOX_TOP, BOX_TOP + 2)
            f.set(x, y, BOX_LIGHT if edge else BOX)


def build():
    seq = timeline()
    order = [(j, w) for j in range(NB) for w in range(2)]
    rng.shuffle(order)
    LIGHT_EACH, HOLD, FADE = 3, 28, 12
    n_build = len(seq)
    N = n_build + len(order) * LIGHT_EACH + HOLD + FADE

    frames = []
    for t in range(N):
        f = gen.Frame()
        s = seq[min(t, n_build - 1)]
        lit, fade = set(), 0.0
        if t >= n_build:
            lit = set(order[:min(len(order), (t - n_build) // LIGHT_EACH + 1)])
            ft = t - (N - FADE)
            if ft >= 0:
                fade = (ft + 1) / (FADE + 1)

        for x in range(W):
            f.set(x, GROUND, EARTH)
        for x, y in ((1, 3), (2, 3), (0, 4), (1, 4), (2, 4), (1, 5), (2, 5)):   # луна
            f.set(x, y, MOON)

        # кран: основание, мачта, оголовок, стрела, кабина, противовес
        for x in range(MAST_X - 1, MAST_X + 3):
            f.set(x, GROUND - 1, CONCRETE)
        for y in range(JIB_Y + 1, GROUND - 1):
            for dx in range(2):
                f.set(MAST_X + dx, y, Y1 if (y + dx) % 2 else Y2)
        f.set(MAST_X, 0, Y1)
        f.set(MAST_X + 1, 0, Y2)
        for x in range(JIB_X0, W):
            f.set(x, JIB_Y, Y1 if x % 3 else Y2)
        f.set(MAST_X - 2, 2, Y1)
        f.set(MAST_X - 1, 2, CAB_WIN)
        f.set(MAST_X - 2, 3, Y2)
        f.set(MAST_X - 1, 3, Y1)
        for x in (25, 26, 27):
            for y in (2, 3):
                f.set(x, y, CONCRETE)
        if (t * 12 / N) % 1 < 0.25:              # огни на верхушке и конце стрелы
            f.set(MAST_X, 0, RED)
            f.set(JIB_X0, JIB_Y - 1, RED)

        for j in range(s["house"]):
            win = tuple(WIN_ON if (j, w) in lit else WIN_OFF for w in range(2))
            block(f, HOUSE_CX, 11 - 2 * j, win, 1 - fade)

        tx, hy = s["tx"], s["hy"]
        f.set(tx, 2, (170, 170, 185))            # тележка
        for y in range(3, hy):
            f.set(tx, y, (100, 100, 115))        # трос
        f.set(tx, hy, (210, 210, 225))           # крюк
        if s["carry"]:
            block(f, tx, hy + 1, (WIN_OFF, WIN_OFF))
        crate(f)                                 # поверх: что внутри ящика — не видно
        frames.append(f)
    gen.save("crane_blocks", frames, MS)


if __name__ == "__main__":
    build()
