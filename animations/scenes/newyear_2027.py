#!/usr/bin/env python3
"""«2026»: шестёрка расшатывается и падает, сверху с отскоком прилетает 7 → «2027», салют за цифрами."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
F = gen.FONT7
X0 = (W - gen.text_width("2026", F)) // 2   # левый край числа
Y0 = 3                                       # верх цифр
XL = X0 + 18                                 # место последней цифры

GOLD = (255, 170, 0)
GLINT = (255, 255, 190)
OLD6 = (255, 110, 40)     # уходящий год — потеплее


def digit(f, ch, x, y, color, tilt=0.0):
    """Цифра с наклоном: строки сдвигаются тем сильнее, чем выше от низа."""
    g = F[ch]
    for dy, row in enumerate(g):
        off = round(tilt * (len(g) - 1 - dy))
        for dx, v in enumerate(row):
            if v == "#":
                c = color(x + dx, y + dy) if callable(color) else color
                f.set(x + dx + off, round(y) + dy, c)


def shimmer(t):
    """Блик бежит по числу слева направо."""
    def c(x, y):
        k = max(0.0, math.cos((x + y * 0.5 - t * 0.9) * 0.45)) ** 6
        return tuple(round(a + (b - a) * k) for a, b in zip(GOLD, GLINT))
    return c


def base(f, color):
    x = X0
    for ch in "202":
        digit(f, ch, x, Y0, color)
        x += 6


def build():
    frames, ms = [], []
    rnd = random.Random(2027)

    def emit(f, t=60):
        frames.append(f)
        ms.append(t)

    # 1. «2026» спокойно горит
    for t in range(18):
        f = gen.Frame()
        base(f, GOLD)
        digit(f, "6", XL, Y0, OLD6)
        emit(f)

    # 2. шестёрка расшатывается — качание с растущей амплитудой
    for t in range(16):
        f = gen.Frame()
        base(f, GOLD)
        amp = 0.08 + 0.3 * t / 15
        digit(f, "6", XL, Y0, OLD6, tilt=amp * math.sin(t * 1.3))
        emit(f)

    # 3. падает вниз, кренясь всё сильнее
    y, vy = float(Y0), -1.0
    tilt = 0.0
    while y < H + 1:
        f = gen.Frame()
        base(f, GOLD)
        vy += 0.18
        y += vy
        tilt += 0.05
        digit(f, "6", XL + round(tilt * 2), y, OLD6, tilt=tilt)
        emit(f)

    # пустое место
    for t in range(3):
        f = gen.Frame()
        base(f, GOLD)
        emit(f)

    # 4. семёрка падает сверху и подпрыгивает на месте
    y, vy = -6.0, 0.3
    bounces = 0
    while True:
        vy += 0.22
        y += vy
        if y >= Y0:
            y = Y0
            bounces += 1
            vy = -vy * 0.4
            if bounces >= 3 or abs(vy) < 0.5:
                break
        f = gen.Frame()
        base(f, GOLD)
        digit(f, "7", XL, y, GLINT)
        emit(f)
    # приземлилась: вспышка
    for k in range(6):
        f = gen.Frame()
        base(f, GOLD)
        c = GLINT if k < 2 else gen.hsv(0.12 - 0.012 * k, 1 - 0.12 * (5 - k), 1)
        digit(f, "7", XL, Y0, c if k < 5 else GOLD)
        if k < 3:
            for dx in range(-1, 6):
                f.set(XL + dx + (k if dx > 2 else -k), Y0 + 7, (255, 220, 120) if k < 2 else (200, 150, 60))
        emit(f)

    # 5. салют вокруг и за числом, блик бежит
    shells = []
    spots = [(5, 2), (22, 2), (14, 1), (3, 10), (24, 11), (10, 12), (18, 11), (13, 2), (7, 3), (21, 3)]
    hues = [0.0, 0.33, 0.6, 0.85, 0.12, 0.5, 0.95, 0.75, 0.2, 0.55]
    for i, ((sx, sy), hue) in enumerate(zip(spots, hues)):
        shells.append({"t0": i * 7 + rnd.randint(0, 3), "x": sx, "y": sy,
                       "c": gen.hsv(hue), "n": rnd.choice([10, 12, 14]),
                       "v": rnd.uniform(0.75, 0.95), "rot": rnd.random()})
    RISE, LIFE = 5, 16
    N = 90
    for t in range(N):
        f = gen.Frame()
        for s in shells:
            dt = t - s["t0"]
            if dt < 0:
                continue
            x, top = s["x"], s["y"]
            if dt < RISE:
                yy = H - (H - top) * dt / RISE
                f.add(x, round(yy), (255, 200, 110))
                f.add(x, round(yy) + 1, (120, 80, 30))
            elif dt < RISE + LIFE:
                k = dt - RISE
                if k == 0:
                    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                        f.add(x + dx, top + dy, (255, 255, 255))
                    continue
                fade = (1 - k / LIFE) ** 1.2
                c = gen.scale(s["c"], 0.35 + 0.65 * fade)
                if fade < 0.25 and (t + s["x"]) % 2:
                    continue        # догорающие искры мигают
                for p in range(s["n"]):
                    a = 2 * math.pi * (p / s["n"] + s["rot"])
                    for kk, cc in ((k, c), (k - 1.5, gen.scale(c, 0.45))):   # искра + хвостик
                        if kk <= 0:
                            continue
                        r = s["v"] * (1 - math.exp(-kk / 5)) * 5     # разлёт тормозит
                        px = x + math.cos(a) * r * 1.3
                        py = top + math.sin(a) * r + 0.025 * kk * kk
                        f.add(round(px), round(py), cc)
        sh = shimmer(t)
        base(f, sh)
        digit(f, "7", XL, Y0, sh)
        emit(f)

    # 6. финал: число держится, блик пробегает ещё раз
    for t in range(30):
        f = gen.Frame()
        sh = shimmer(t + 4)
        base(f, sh)
        digit(f, "7", XL, Y0, sh)
        emit(f, 70)

    gen.save("newyear_2027", frames, ms)


if __name__ == "__main__":
    build()
