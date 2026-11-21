#!/usr/bin/env python3
"""Ретро-гирлянда: провисший провод с шестью большими лампочками-«каплями».
Режимы как у старого переключателя: по очереди → все вместе → через одну → мигание.
Провисание дышит на пиксель. Петля без шва."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 80

WIRE = (20, 105, 35)
SOCKET = (120, 120, 105)
COLORS = [
    (255, 20, 10),     # красная
    (255, 170, 0),     # жёлтая
    (30, 230, 40),     # зелёная
    (30, 80, 255),     # синяя
    (230, 30, 200),    # розовая
    (0, 210, 230),     # голубая
]
XS = [3, 7, 11, 16, 20, 24]      # левый край каждой лампочки (ширина 3), симметрично: 3..26
DIM = 95                         # погасшая лампочка: главный канал ~95, контур виден

BULB = [   # под цоколем; 'B' — тело, 'h' — блик
    "hBB",
    "BBB",
    "BBB",
    ".B.",
]

# режимы: (имя, кадров)
CHASE_STEP = 4
MODES = [("chase", 6 * CHASE_STEP * 2), ("all", 20), ("alt", 6 * 6), ("blink", 6 * 6)]
N = sum(n for _, n in MODES)      # 48 + 20 + 36 + 36 = 140 кадров ≈ 11 с
BREATH = 2                        # вдохов провода за петлю


def wire_y(x, sag):
    u = (x - 13.5) / 13.5
    return 2.2 + sag * (1 - u * u)


def states(t):
    """Яркость каждой лампочки 0..1 в кадре t."""
    for name, n in MODES:
        if t < n:
            break
        t -= n
    if name == "chase":
        # огонёк бежит слева направо и обратно, за ним короткий след
        step = t // CHASE_STEP
        seq = list(range(6)) + list(range(5, -1, -1))
        cur = seq[step % 12]
        prev = seq[(step - 1) % 12]
        out = [0.0] * 6
        out[prev] = 0.35
        out[cur] = 1.0
        return out
    if name == "all":
        # все вместе: включились и чуть дышат
        k = 0.88 + 0.12 * math.cos(2 * math.pi * t / n)
        return [k] * 6
    if name == "alt":
        ph = (t // 6) % 2
        return [1.0 if i % 2 == ph else 0.0 for i in range(6)]
    # мигание всеми: 3 кадра горят, 3 нет
    return [1.0 if (t // 3) % 2 == 0 else 0.0] * 6


def bulb_color(c, k):
    lo = DIM / max(c)
    return gen.scale(c, lo + (1 - lo) * k)


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        sag = 4.6 + 0.5 * math.sin(2 * math.pi * t / N * BREATH)
        # провод: по столбцам, без разрывов между соседними
        prev = None
        for x in range(W):
            y = round(wire_y(x, sag))
            if prev is not None and abs(y - prev) > 1:
                for yy in range(min(y, prev) + 1, max(y, prev)):
                    f.set(x, yy, WIRE)
            f.set(x, y, WIRE)
            prev = y
        lv = states(t)
        for i, x0 in enumerate(XS):
            cx = x0 + 1
            wy = round(wire_y(cx, sag))
            f.set(cx, wy + 1, SOCKET)
            k = lv[i]
            body = bulb_color(COLORS[i], k)
            shine = tuple(min(255, int(v + (255 - v) * 0.6)) for v in COLORS[i]) if k > 0.6 else body
            f.sprite(BULB, x0, wy + 2, pal={"B": body, "h": shine})
        frames.append(f)
    gen.save("retro_bulbs", frames, MS)


if __name__ == "__main__":
    build()
