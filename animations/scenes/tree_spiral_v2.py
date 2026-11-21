#!/usr/bin/env python3
"""Ёлка со спиральной гирляндой: огоньки бегут по спирали снизу вверх и зажигают её,
добегают до звезды — звезда вспыхивает, гирлянда гаснет, и всё по новой. Петля без шва."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 65
RUN = 66                  # кадров на подъём огонька от низа до звезды
FLASH = 12                # звезда вспыхивает, гирлянда горит вся
FADE = 22                 # всё плавно гаснет
REST = 10                 # пауза в полутьме
N = RUN + FLASH + FADE + REST
CX = 13

HALF = {3: 1, 4: 2, 5: 3, 6: 2, 7: 3, 8: 4, 9: 5, 10: 4, 11: 5, 12: 6}
TIER_EDGE = {5, 9, 12}
NEEDLE = (10, 125, 35)
NEEDLE_DARK = (0, 95, 30)
TRUNK = (150, 75, 20)

STAR = (255, 200, 30)
STAR_CORE = (255, 240, 150)
STAR_PX = [(13, 0), (12, 1), (14, 1), (13, 2)]
STAR_GLOW = [(12, 0), (14, 0), (12, 2), (14, 2), (11, 1), (15, 1)]
STAR_RAYS = [((10, 1), (16, 1)), ((9, 1), (17, 1), (11, 0), (15, 0), (11, 2), (15, 2))]

BULB_C = [(255, 25, 15), (255, 170, 0), (40, 100, 255), (230, 40, 200)]
HEAD = (255, 250, 220)
TURNS = 2.0
FRONT = 0.62               # доля витка, видная спереди; остальное — за ёлкой
PHASE = 0.0
BOT, TOP = 12, 3


def spiral_bulbs():
    """Лампочки по спирали снизу вверх; s — доля пути. Спереди виток идёт прямой косой линией
    слева направо (синус по краям слипается в горизонтальные полоски), сзади — скрыт."""
    pts, seen = [], set()
    steps = 2000
    for i in range(steps + 1):
        s = i / steps
        frac = (s * TURNS + PHASE) % 1
        if frac >= FRONT:
            continue
        y = BOT + 0.3 - s * (BOT - TOP + 0.6)
        yr = round(y)
        if yr not in HALF:
            continue
        hw = HALF[yr] + 0.4
        p = (round(CX - hw + 2 * hw * frac / FRONT), yr)
        if p in seen:
            continue
        seen.add(p)
        pts.append((p, s))
    return pts


BULBS = spiral_bulbs()


def smooth(a):
    a = min(max(a, 0.0), 1.0)
    return a * a * (3 - 2 * a)


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        for y, hw in HALF.items():
            for x in range(CX - hw, CX + hw + 1):
                f.set(x, y, NEEDLE_DARK if y in TIER_EDGE else NEEDLE)
        for x in range(CX - 1, CX + 2):
            f.set(x, 13, TRUNK)

        head = smooth(t / RUN) * 1.04 if t < RUN else 2.0     # где бегущий огонёк (доля пути)
        if t < RUN + FLASH:
            glow = 1.0
        else:
            glow = 1 - smooth((t - RUN - FLASH) / FADE)       # общее угасание
        flash = 0.0
        if RUN - 2 <= t < RUN + FLASH + 6:
            flash = math.sin(math.pi * (t - RUN + 2) / (FLASH + 8))

        for i, ((x, y), s) in enumerate(BULBS):
            col = BULB_C[i % len(BULB_C)]
            if s <= head:
                d = head - s
                k = 0.85 + 0.15 * math.sin(2 * math.pi * (t / 8 - i / 4))   # лёгкое мерцание
                c = gen.scale(col, (0.35 + 0.65 * k * glow))
                if d < 0.06 and t < RUN:                       # голова «кометы» — почти белая
                    w = 1 - d / 0.06
                    c = tuple(int(a + (b - a) * w) for a, b in zip(c, HEAD))
                c = tuple(min(255, int(a + 120 * flash)) for a in c)
            else:
                c = gen.scale(col, 0.35)                       # погашенная лампочка
            f.set(x, y, c)

        base = 0.7 + 0.1 * math.sin(2 * math.pi * t / N * 2)
        k = min(1.0, base + 0.3 * flash)
        for p in STAR_GLOW:
            f.set(*p, gen.scale(STAR, 0.35 + 0.65 * flash))
        for p in STAR_PX:
            f.set(*p, tuple(min(255, int(a * k + 120 * flash)) for a in STAR))
        f.set(13, 1, tuple(min(255, int(a * k + 120 * flash)) for a in STAR_CORE))
        for r, ray in enumerate(STAR_RAYS):        # лучи на вспышке
            v = flash * (1 - 0.45 * r)
            if v > 0.3:
                for p in ray:
                    f.set(*p, gen.scale((255, 220, 90), v))
        frames.append(f)
    gen.save("tree_spiral_v2", frames, MS)


if __name__ == "__main__":
    build()
