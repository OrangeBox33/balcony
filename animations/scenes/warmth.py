#!/usr/bin/env python3
"""«ТЕПЛА»: буквы мерцают, как пламя свечи, над ними поднимаются и гаснут искры. Бесшовная петля."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
N = 125                 # кадров в петле
MS = 80                 # 125 × 80 мс = 10 с
TY = 7                  # верх букв (буквы до нижнего края, над ними место искрам)
WORD = "ТЕПЛА"

# узкая Е (4 px): 5+4+5+5+5 + 4 промежутка = 28 — ровно во всю ширину
FONT = {**gen.FONT7, "Е": ["####", "#...", "#...", "###.", "#...", "#...", "####"]}

# от тёмно-оранжевого к жёлтому; все цвета ярко видны после гаммы WLED
HEAT = [(220, 35, 0), (255, 60, 0), (255, 90, 0), (255, 120, 0), (255, 150, 0), (255, 185, 20), (255, 215, 70)]


def heat_color(h):
    h = min(max(h, 0.0), 1.0)
    return HEAT[round(h * (len(HEAT) - 1))]


def letter_pixels():
    f = gen.Frame()
    f.text(WORD, 0, TY, (1, 1, 1), FONT)
    return [(x, y) for y in range(H) for x in range(W) if f.px[y][x] != gen.BLACK]


def build():
    rnd = random.Random(7)
    pix = letter_pixels()
    tops = {}
    for x, y in pix:
        tops[x] = min(tops.get(x, H), y)

    # у каждого пикселя — своя смесь синусов с целыми частотами (так петля бесшовна)
    waves = {}
    for p in pix:
        waves[p] = [(rnd.randint(4, 22), rnd.uniform(0, 2 * math.pi)) for _ in range(3)]
    # общее медленное «дыхание» по столбцам — как от сквозняка
    col_ph = [rnd.uniform(0, 2 * math.pi) for _ in range(W)]

    # искры: рождаются над верхом букв, ползут вверх и гаснут
    sparks = []
    for _ in range(34):
        x = rnd.choice(list(tops))
        sparks.append({
            "t0": rnd.randrange(N),
            "x": x,
            "y": tops[x] - 1,
            "life": rnd.randint(10, 18),
            "drift": rnd.choice((-1, 0, 0, 1)),
        })

    frames = []
    for t in range(N):
        f = gen.Frame()
        tt = 2 * math.pi * t / N
        for (x, y) in pix:
            row = y - TY                       # 0 — верх буквы
            top = 1.0 - row / 6               # верх мерцает сильнее
            n = sum(math.sin(k * tt + ph) for k, ph in waves[(x, y)]) / 3
            sway = math.sin(3 * tt + col_ph[x] + 0.4 * x)
            h = 0.62 - 0.12 * top + n * (0.18 + 0.32 * top) + 0.12 * sway
            f.set(x, y, heat_color(h))
        # язычки пламени: иногда над верхом буквы вспыхивает пиксель
        for x, y0 in tops.items():
            v = math.sin(7 * tt + col_ph[x] * 3) + math.sin(11 * tt + x * 1.7)
            if v > 1.8:
                f.set(x, y0 - 1, HEAT[1])
        for s in sparks:
            age = (t - s["t0"]) % N
            if age >= s["life"]:
                continue
            k = age / s["life"]
            y = s["y"] - round(age * 0.5)
            x = s["x"] + round(s["drift"] * k * 2 + 0.6 * math.sin(age * 0.9))
            c = (255, 220, 90) if k < 0.3 else (255, 140, 0) if k < 0.6 else (230, 50, 0) if k < 0.85 else (150, 20, 0)
            if y >= 0:
                f.add(x, y, c)
        frames.append(f)

    gen.save("warmth", frames, [MS] * N)


if __name__ == "__main__":
    build()
