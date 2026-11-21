#!/usr/bin/env python3
"""Гора подарков: пирамида коробок с лентами и бантиками. По очереди по коробкам пробегает блик,
иногда верхняя коробка подпрыгивает — будто внутри кто-то сидит. Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 70
SLOT = 28                    # кадров на один блик (≈2 с)
rng = random.Random(11)

GOLD = (255, 200, 40)
SILVER = (210, 220, 255)
RED_RIB = (255, 40, 60)

# коробка: x, y (верх), ширина, высота, цвет, лента
BOXES = {
    "blue":   (0, 9, 9, 5, (20, 70, 255), SILVER),
    "gold":   (10, 9, 8, 5, (255, 150, 0), RED_RIB),
    "green":  (19, 9, 9, 5, (0, 170, 40), RED_RIB),
    "red":    (6, 4, 7, 5, (220, 15, 20), GOLD),
    "purple": (15, 4, 7, 5, (150, 20, 230), SILVER),
}
ORDER_DRAW = ["blue", "gold", "green", "red", "purple"]
GLINT_ORDER = ["red", "purple", "green", "gold", "blue"]   # кому блик в каком слоте
N = SLOT * len(GLINT_ORDER)                                # 140 кадров ≈ 9.8 с

BOW1 = ["#.#", "###"]        # бантик над лентой в 1 пиксель (нечётная ширина)
BOW2 = ["#..#", "####"]      # и в 2 пикселя (чётная)

# подпрыгивания: (коробка, кадр начала); прыжок «тук-тук» — два подскока
HOP = [0, -1, -2, -2, -1, 0, 0, 0, -1, 0]
HOPS = [("red", 38), ("purple", 104)]

# мерцающие звёздочки в пустых углах
STARS = [(1, 1), (4, 4), (2, 6), (25, 1), (23, 3), (26, 6), (13, 0)]


def hop_dy(name, t):
    for n, t0 in HOPS:
        if n == name:
            a = (t - t0) % N
            if a < len(HOP):
                return HOP[a]
    return 0


def glint(name, t):
    """Положение диагональной полосы блика (x+y) или None."""
    slot = (t // SLOT) % len(GLINT_ORDER)
    if GLINT_ORDER[slot] != name:
        return None
    p = t % SLOT
    if p >= 12:
        return None
    x, y, w, h = BOXES[name][:4]
    return x + y - 1 + p * (w + h + 1) / 11


def draw_box(f, name, t):
    x, y, w, h, col, rib = BOXES[name]
    y += hop_dy(name, t)
    g = glint(name, t)
    rw = 2 - w % 2                      # вертикальная лента: 1 столбец у нечётной ширины, 2 у чётной
    rx = x + (w - rw) // 2
    ry = y + h // 2                     # горизонтальная лента
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            c = rib if (rx <= xx < rx + rw or yy == ry) else col
            if g is not None:
                d = abs(xx + yy - g)
                if d < 1.5:
                    k = 0.65 if d < 0.6 else 0.3
                    c = tuple(int(v + (255 - v) * k) for v in c)
            f.set(xx, yy, c)
    f.sprite(BOW1 if rw == 1 else BOW2, rx - 1, y - 2, pal={"#": rib})


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        for i, (sx, sy) in enumerate(STARS):
            k = 0.5 + 0.5 * math.sin(2 * math.pi * (t * (2 + i % 3) / N + i * 0.37))
            if k > 0.35:
                f.set(sx, sy, gen.scale((255, 220, 150), 0.45 + 0.55 * k))
        for name in ORDER_DRAW:
            draw_box(f, name, t)
        frames.append(f)
    gen.save("gift_pile", frames, MS)


if __name__ == "__main__":
    build()
