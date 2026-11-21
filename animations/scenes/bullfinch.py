#!/usr/bin/env python3
"""Снегирь на ветке: на заснеженной ветке с гроздью рябины сидит круглый снегирь —
крутит головой, пару раз клюёт ягоду, распушается и снова сидит. Идёт снег.
Фон — зимнее синее небо, чтобы чёрная шапочка читалась. Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
N = 150                 # 10,5 с
MS = 70
TAU = 2 * math.pi

SKY_TOP = (50, 100, 190)
SKY_BOT = (35, 75, 160)
BARK = (135, 80, 40)
BARK_D = (100, 58, 28)
SNOW = (235, 240, 255)
FLAKE = (225, 235, 255)

PAL = {
    "K": (0, 0, 0),
    "x": (150, 152, 170),     # серая спинка
    "R": (240, 70, 95),       # розово-красная грудка
    "W": (240, 240, 245),     # белая полоса на крыле, подхвостье
    "e": (255, 255, 255),     # блик в глазу
    "r": (255, 100, 0),       # рябина — оранжевее грудки, чтобы не сливались
    "d": (220, 45, 0),
    "s": BARK,
}

# тело (без головы), лицом вправо; голова рисуется поверх отдельно
BODY = [
    "............",
    "............",
    "............",
    ".....xxxx...",
    "...xxxxxxRR.",
    "..xxxxxxRRRR",
    ".xWWWWWxRRRR",
    "KKKKKKKxRRRR",
    "KKK.KKKKRRR.",
    ".....WWRRR..",
]
# головы: 6 столбцов, ставятся в столбцы 6–11 спрайта
HEADS = {
    "right": [
        ".KKK..",
        "KKKKK.",
        "KKeKKK",
        "xxRRR.",
    ],
    "front": [
        ".KKK..",
        "KKKKK.",
        "KeKeK.",
        "RRKRR.",
    ],
    "left": [
        "..KKK.",
        ".KKKKK",
        "KKKeKK",
        ".RRRxx",
    ],
    "blink": [
        ".KKK..",
        "KKKKK.",
        "KKKKKK",
        "xxRRR.",
    ],
}
HEAD_DX = {"left": -1}
BX, BY = 4, 1           # где сидит снегирь (левый верх спрайта)

BERRIES = [
    "..s.",
    ".rdr",
    "rdrd",
    ".rdr",
    "..r.",
]
BERRY_POS = (17, 2)


def fluffed(rows):
    """Распушился: тело на пиксель шире с каждой стороны."""
    out = []
    for i, r in enumerate(rows):
        r = "." + r + "."
        if 3 <= i <= 9:
            cs = [k for k, ch in enumerate(r) if ch != "."]
            if cs:
                a, b = cs[0], cs[-1]
                r = r[:a - 1] + r[a] + r[a:b + 1] + r[b] + r[b + 2:]
        out.append(r)
    return out


def branch_y(x):
    return 12.0 - 3.0 * x / 27


def pose(t):
    """(голова, сдвиг головы dx, dy, распушён?, сдвиг всей птицы dx)."""
    head, hdx, hdy, fluff, sx = "right", 0, 0, False, 0
    if t in (9, 10, 137, 138):
        head = "blink"
    if 16 <= t < 22 or 32 <= t < 37 or 118 <= t < 128:
        head = "front"
    elif 22 <= t < 32:
        head = "left"
    # клевки
    for p in (48, 58):
        k = t - p
        if 0 <= k < 3:
            hdx, hdy = 1, 1
        elif 3 <= k < 5:
            hdx, hdy = 1, 0
    # распушается: сначала дрожь, потом сидит пухлый
    if 78 <= t < 86:
        fluff = (t // 2) % 2 == 0
        sx = 0
    elif 86 <= t < 106:
        fluff = True
    if 106 <= t < 109:
        hdy = -1 if t < 108 else 0     # встряхнул головой и успокоился
    return head, hdx, hdy, fluff, sx


def build():
    rnd = random.Random(5)
    flakes = [(rnd.uniform(0, W), rnd.uniform(0, 1), rnd.choice((1, 2, 2)), rnd.uniform(0, TAU), rnd.choice((1, 2)))
              for _ in range(9)]

    frames = []
    for t in range(N):
        f = gen.Frame()
        for y in range(H):
            c = tuple(int(a + (b - a) * y / (H - 1)) for a, b in zip(SKY_TOP, SKY_BOT))
            for x in range(W):
                f.set(x, y, c)
        # снег за птицей
        for x0, ph, cyc, wph, sw in flakes:
            u = (ph + cyc * t / N) % 1
            y = round(u * (H + 2)) - 1
            x = round(x0 + sw * math.sin(TAU * 2 * t / N + wph)) % W
            f.set(x, y, FLAKE)
        # ветка со снегом
        for x in range(W):
            y = round(branch_y(x))
            f.set(x, y, BARK)
            if x < 16:
                f.set(x, y + 1, BARK_D)
            if x % 7 not in (3, 4) and not (BX <= x <= BX + 11):
                f.set(x, y - 1, SNOW)
        # веточка вверх к грозди
        for x, y in ((24, 8), (23, 7), (23, 6), (22, 5), (22, 4), (21, 3), (21, 2), (20, 1)):
            f.set(x, y, BARK)
        f.set(20, 0, SNOW)
        f.set(21, 1, SNOW)
        f.set(22, 3, SNOW)
        # гроздь рябины (в момент клевка вздрагивает)
        head, hdx, hdy, fluff, sx = pose(t)
        jig = 1 if any(0 <= t - p < 2 for p in (49, 59)) else 0
        f.sprite(BERRIES[:2], BERRY_POS[0], BERRY_POS[1], pal=PAL)
        f.sprite(BERRIES[2:], BERRY_POS[0] + jig, BERRY_POS[1] + 2, pal=PAL)
        # снегирь
        body = fluffed(BODY) if fluff else ["." + r + "." for r in BODY]
        x0 = BX - 1 + sx
        f.sprite(body, x0, BY, pal=PAL)
        f.sprite(HEADS[head], x0 + 7 + hdx + HEAD_DX.get(head, 0), BY + hdy - (1 if fluff else 0), pal=PAL)
        frames.append(f)
    gen.save("bullfinch", frames, MS)


if __name__ == "__main__":
    build()
