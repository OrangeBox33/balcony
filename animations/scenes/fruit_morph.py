#!/usr/bin/env python3
"""Клубника → малина → виноград → апельсин → груша → яблоко → клубника, попиксельным перетеканием."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

C = {
    "r": (230, 0, 20),      # клубника
    "y": (255, 220, 60),    # семечки
    "g": (0, 200, 0),       # листья
    "G": (0, 130, 20),
    "n": (150, 70, 10),     # черешок
    "a": (175, 0, 55),      # малина: тень костянки
    "A": (255, 90, 160),    # малина: блик костянки
    "o": (255, 100, 0),     # апельсин
    "O": (255, 170, 40),
    "q": (220, 90, 0),
    "e": (170, 220, 0),     # груша
    "E": (230, 240, 60),
    "d": (110, 160, 0),
    "R": (220, 0, 0),       # яблоко
    "P": (255, 120, 120),
}

STRAWBERRY = [
    "....g.g.g....",
    "..ggggggggg..",
    ".rrgrrgrrgrr.",
    "rrrrrrrrrrrrr",
    "ryrrryrrryrry",
    "rrrrrrrrrrrrr",
    ".rryrrryrrry.",
    ".rrrrrrrrrrr.",
    "..ryrrryrrr..",
    "..rrrrrrrrr..",
    "...rrryrrr...",
    "....rrrrr....",
    "......r......",
]

RASPBERRY_MASK = [
    ".....g.g.....",
    "...ggggggg...",
    "...#######...",
    "..#########..",
    ".###########.",
    ".###########.",
    ".###########.",
    ".###########.",
    "..#########..",
    "..#########..",
    "...#######...",
    "....#####....",
    "......#......",
]


def raspberry():
    """Костянки: на тёмно-малиновом фоне светлые бугорки 1 px в шахматном порядке через ряд."""
    px = {}
    ox, oy = (gen.W - 13) // 2, 1
    for y, row in enumerate(RASPBERRY_MASK):
        for x, ch in enumerate(row):
            if ch == "g":
                px[(ox + x, oy + y)] = C["g"]
            elif ch == "#":
                bump = y % 2 == 0 and (x + y // 2) % 2 == 0
                px[(ox + x, oy + y)] = C["A"] if bump else C["a"]
    return px


def orange():
    """Круглый апельсин: блик слева сверху, тень справа снизу, сверху черешок и листик."""
    ox, oy = (gen.W - 13) // 2, 1
    cx, cy, r = 6, 7.3, 5.9
    px = {}
    for y in range(2, 13):
        for x in range(13):
            d = math.hypot(x - cx, y - cy)
            if d <= r:
                c = C["o"]
                if math.hypot(x - (cx - 2.6), y - (cy - 2.6)) < 1.3:
                    c = C["O"]
                elif d > r - 1.2 and (x - cx) + (y - cy) > 3:
                    c = C["q"]
                px[(ox + x, oy + y)] = c
    px[(ox + 6, oy + 0)] = C["n"]
    px[(ox + 6, oy + 1)] = C["n"]
    for p in ((7, 0), (8, 0), (7, 1), (8, 1), (9, 1)):
        px[(ox + p[0], oy + p[1])] = C["g"]
    return px


PEAR = [
    "......n......",
    "......nggg...",
    ".....eeegg...",
    "....eEeee....",
    "....eEeee....",
    "....eeeeed...",
    "...eEeeeeed..",
    "..eEeeeeeeed.",
    ".eEeeeeeeeed.",
    ".eeeeeeeeeed.",
    ".eeeeeeeeedd.",
    "..eeeeeeedd..",
    "....eeeee....",
]

APPLE = [
    "......n.gg...",
    "......ngg....",
    "..RRRR.RRRR..",
    ".RPPRRRRRRRR.",
    "RRPRRRRRRRRRR",
    "RPRRRRRRRRRRR",
    "RRRRRRRRRRRRR",
    "RRRRRRRRRRRRR",
    "RRRRRRRRRRRRR",
    ".RRRRRRRRRRR.",
    ".RRRRRRRRRRR.",
    "..RRRR.RRRR..",
    "...RR...RR...",
]

def grapes():
    """Гроздь 4-3-2-1 из круглых ягод 4×4, ряды вложены друг в друга (гексагонально).
    Возвращает координаты холста: гроздь шире и выше остальных фруктов."""
    # h — блик, B — ягода, d — тень снизу-справа: она и отделяет ягоды друг от друга
    berry = [".BB.", "BhBB", "BBBd", ".dd."]
    col = {"h": (235, 170, 255), "B": (160, 30, 240), "d": (80, 0, 130)}
    ox, oy = 6, 0
    px = {}
    for i, xs in enumerate(([0, 4, 8, 12], [2, 6, 10], [4, 8], [6])):
        for bx in xs:
            for dy, row in enumerate(berry):
                for dx, ch in enumerate(row):
                    if ch != ".":
                        px[(ox + bx + dx, oy + 1 + i * 3 + dy)] = col[ch]
    px[(ox + 8, oy)] = C["n"]
    px[(ox + 7, oy)] = C["n"]
    for p in ((9, 0), (10, 0), (11, 0)):
        px[(ox + p[0], oy + p[1])] = C["g"]
    return px


def sprite_px(rows, ox=(gen.W - 13) // 2, oy=1):
    return {(ox + x, oy + y): C[ch] for y, row in enumerate(rows) for x, ch in enumerate(row) if ch != "."}


def build():
    fruits = [sprite_px(STRAWBERRY), raspberry(), grapes(),
              orange(), sprite_px(PEAR), sprite_px(APPLE)]
    rnd = random.Random(4)
    HOLD, MORPH = 15, 10
    frames = []

    def draw(px):
        f = gen.Frame()
        for (x, y), c in px.items():
            f.set(x, y, c)
        frames.append(f)

    for i, cur in enumerate(fruits):
        nxt = fruits[(i + 1) % len(fruits)]
        for _ in range(HOLD):
            draw(cur)
        # каждая клетка меняется в свой момент: волна сверху вниз с шумом
        cells = set(cur) | set(nxt)
        when = {p: (p[1] / 13) * 0.6 + rnd.random() * 0.4 for p in cells}
        for k in range(1, MORPH + 1):
            t = k / (MORPH + 1)
            px = {}
            for p in cells:
                src = nxt if when[p] < t else cur
                if p in src:
                    px[p] = src[p]
                # в момент смены клетка вспыхивает белым
                if abs(when[p] - t) < 0.05 and p in nxt:
                    px[p] = (255, 255, 255)
            draw(px)
    gen.save("fruit_morph", frames, 90)


if __name__ == "__main__":
    build()
