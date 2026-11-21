#!/usr/bin/env python3
"""Пляж: песок, пальма, солнце; волна с белой пеной накатывает на песок и откатывает."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

N = 100            # кадров в петле (две волны)
HORIZON = 4        # первая строка моря
SHORE = 8.5        # где кончается вода в покое

SEA_FAR = (0, 70, 200)
SEA_NEAR = (0, 140, 230)
SHIMMER = (120, 210, 255)
FOAM = (255, 255, 255)
SAND = (255, 170, 50)
WET = (215, 125, 25)
SUN = (255, 200, 0)
SUN_RIM = (255, 110, 0)
TRUNK = (160, 75, 10)
TRUNK_D = (115, 45, 0)
LEAF = (0, 200, 30)
LEAF_D = (0, 130, 20)
NUT = (150, 80, 0)


def mix(a, b, k):
    k = max(0.0, min(1.0, k))
    return tuple(round(x + (y - x) * k) for x, y in zip(a, b))


def wave_front(t):
    """Кромка воды (строка, дробная) и стадия: накат (True/False) и доля отката 0..1.
    Две волны за петлю, вторая чуть меньше."""
    u = (t % (N // 2)) / (N // 2)
    amp = 3.0 if t < N // 2 else 2.3
    # набегает быстрее (40% периода), сползает медленнее (60%)
    if u < 0.4:
        k = 0.5 - 0.5 * math.cos(math.pi * u / 0.4)
        return SHORE + amp * k, True, 0.0
    p = (u - 0.4) / 0.6
    return SHORE + amp * (0.5 + 0.5 * math.cos(math.pi * p)), False, p


# крона: g — лист, G — тёмная сторона листа, n — кокосы; кончики (T) покачиваются
CROWN = [
    "..gggg.gggg..",
    ".gGGGgggGGGg.",
    "gG...gGg...Gg",
    "T...gGnGg...T",
    "...g..n..g...",
]


def draw_palm(f, t):
    # изогнутый ствол из песка к кроне
    trunk = [(2, 13), (3, 12), (3, 11), (4, 10), (4, 9), (4, 8), (5, 7), (5, 6), (5, 5), (6, 4)]
    for i, (x, y) in enumerate(trunk):
        f.set(x, y, TRUNK if i % 2 == 0 else TRUNK_D)
        f.set(x + 1, y, TRUNK_D if i % 2 == 0 else TRUNK)
    ox = 0
    droop = 1 if math.sin(2 * math.pi * t / N * 2) > 0.3 else 0   # кончики листьев качаются
    for y, row in enumerate(CROWN):
        for x, ch in enumerate(row):
            if ch == "T":
                f.set(ox + x, y + droop, LEAF_D)
            elif ch != ".":
                f.set(ox + x, y, {"g": LEAF, "G": LEAF_D, "n": NUT}[ch])


def build():
    frames = []
    wet_line = SHORE
    # мокрый песок — след последней волны, медленно высыхает; прогреваем одну петлю
    for t in range(-N, N):
        front, rising, p = wave_front(t)
        wet_line = max(front, wet_line - 0.035)
        if t < 0:
            continue
        u = (t % (N // 2)) / (N // 2)
        # гребень (полоса посветлее) идёт от горизонта к берегу в последние 40% отката
        crest, crest_k = None, 0.0
        if u >= 0.6:
            crest_k = (u - 0.6) / 0.4
            crest = HORIZON + 1 + (round(SHORE) - 1 - HORIZON - 1) * crest_k

        f = gen.Frame()
        for y in range(0, 5):
            for x in range(19, 27):
                d = math.hypot(x - 22.5, y - 1.5)
                if d <= 2.0:
                    f.set(x, y, SUN)
                elif d <= 2.9:
                    f.set(x, y, SUN_RIM)
        for x in range(gen.W):
            wob = 0.4 * math.sin(x * 0.5 + 2 * math.pi * t / N * 2)
            foam_y = round(front + wob) - 1          # строка пены = последняя строка воды
            wet_y = round(wet_line + 0.4 * math.sin(x * 0.5)) - 1
            for y in range(HORIZON, gen.H):
                if y < foam_y:
                    c = SEA_FAR if y < HORIZON + 2 else SEA_NEAR
                    if crest is not None and round(crest) == y:
                        # гребень белеет по мере подхода к берегу и сам становится пеной
                        c = mix(SHIMMER, FOAM, crest_k ** 2)
                elif y == foam_y:
                    if rising:
                        c = FOAM
                    else:
                        # на откате пена рассыпается на пузырьки и тает
                        bubbly = (x * 7 + y * 3 + t // 2) % 4 == 0
                        c = mix(FOAM, SEA_NEAR, p * 1.3) if not bubbly else mix(FOAM, SEA_NEAR, p * 0.5)
                else:
                    c = WET if y <= wet_y else SAND
                f.set(x, y, c)
        # дорожка от солнца у горизонта
        for x in (21, 22, 23, 24):
            if (x + t // 5) % 3:
                f.set(x, HORIZON, (255, 160, 40))
        draw_palm(f, t)
        frames.append(f)
    gen.save("beach", frames, 100)


if __name__ == "__main__":
    build()
