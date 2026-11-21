#!/usr/bin/env python3
"""Ёлка со спиральной гирляндой: по спирали снизу вверх по очереди бегут волны
красного, жёлтого, синего, зелёного; сверху пульсирует звезда, под ёлкой три подарка.
Петля без шва."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 60
N = 120                     # 7,2 с
CX = 13                     # ось ёлки
TOP, BOT = 3, 11            # верх и низ кроны
TURNS = 2.0                 # витков спирали
FRONT = 0.7                 # доля витка, видная спереди
PHASE = 0.0
WAVE = N // 4               # кадров на одну цветную волну
CLIMB = 0.75                # за какую долю WAVE волна поднимается от низа до верха

# полуширина кроны по строкам
HALF = {3: 0, 4: 1, 5: 2, 6: 3, 7: 3, 8: 4, 9: 5, 10: 6, 11: 7}

NEEDLE = (0, 130, 30)
NEEDLE_HI = (40, 165, 40)   # светлая кромка
TRUNK = (140, 65, 15)
LIGHTS = [(255, 20, 10), (255, 190, 0), (30, 90, 255), (170, 255, 120)]

STAR = [
    "..y..",
    "yyYyy",
    ".y.y.",
]
GIFTS = [  # (спрайт, x, y)
    (["Y.Y.", "rYrr", "YYYY", "rYrr"], 4, 10),
    (["W.W", "bWb", "bWb"], 16, 11),
    ([".Y.Y", "mmYm", "YYYY", "mmYm"], 20, 10),
]
GPAL = {
    "r": (220, 0, 10), "b": (20, 70, 255), "m": (190, 0, 200),
    "W": (255, 255, 255), "Y": (255, 210, 0),
}


def crown():
    cells = []
    for y, hw in HALF.items():
        for x in range(CX - hw, CX + hw + 1):
            cells.append((x, y))
    return cells


def spiral_bulbs():
    """Пиксели гирлянды по спирали снизу вверх. Спереди виток идёт прямой косой линией
    слева направо (синус по краям слипается в горизонтальные полоски), сзади — скрыт."""
    pts = []
    seen = set()
    steps = 800
    for i in range(steps + 1):
        s = i / steps
        a = s * TURNS + PHASE
        frac = a % 1
        if frac >= FRONT:          # за ёлкой
            continue
        y = BOT + 0.3 - s * (BOT - TOP + 0.3)
        yr = round(y)
        if yr not in HALF:
            continue
        hw = HALF[yr] + 0.4
        x = CX - hw + 2 * hw * frac / FRONT
        p = (round(x), yr)
        if p in seen:
            continue
        seen.add(p)
        pts.append(p)
    return pts


def build():
    cells = crown()
    cellset = set(cells)
    bulbs = [p for p in spiral_bulbs() if p in cellset]
    n = len(bulbs)
    frames = []
    for t in range(N):
        f = gen.Frame()
        # ствол и крона
        for y in (12, 13):
            for x in (CX - 1, CX, CX + 1):
                f.set(x, y, TRUNK)
        for (x, y) in cells:
            edge = abs(x - CX) == HALF[y]
            f.set(x, y, NEEDLE_HI if edge else NEEDLE)

        # гирлянда: каждая новая волна снизу вверх перекрашивает спираль; за петлю 4 волны
        u = t / WAVE
        for i, (x, y) in enumerate(bulbs):
            local = u - i / n * CLIMB
            k = math.floor(local)
            frac = local - k
            col = LIGHTS[k % 4]
            if frac < 0.12:              # фронт волны — вспышка
                c = tuple(min(255, int(v + (255 - v) * 0.55)) for v in col)
            else:
                c = gen.scale(col, 1.0 - 0.22 * frac)
            if (i + t // 3) % 4 == 0 and frac >= 0.12:   # лёгкое мерцание вдоль провода
                c = gen.scale(c, 0.8)
            f.set(x, y, c)

        # звезда пульсирует медленно: 2 вдоха за петлю
        p = 0.5 + 0.5 * math.cos(2 * math.pi * t / N * 2)
        gold = (255, int(150 + 60 * p), int(10 + 80 * p * p))
        core = (255, 255, int(120 + 135 * p))
        f.sprite(STAR, CX - 2, 0, pal={"y": gold, "Y": core})
        if p > 0.75:                     # на пике верхний луч вспыхивает
            f.set(CX, 0, core)

        for rows, gx, gy in GIFTS:
            f.sprite(rows, gx, gy, pal=GPAL)
        frames.append(f)
    gen.save("tree_spiral", frames, MS)


if __name__ == "__main__":
    build()
