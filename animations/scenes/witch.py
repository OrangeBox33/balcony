#!/usr/bin/env python3
"""Ночь, большая луна. Ведьма проносится на метле вправо нырком через луну (на её фоне — чёрный силуэт),
за ней хвост волшебных искр, следом летит стайка летучих мышей."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 50
MOON = (19.0, 5.2, 4.8)     # центр и радиус

# профиль, лицом вправо: шляпа с загнутым назад кончиком, волосы, нос крючком, плащ, метла
WITCH = [
    "..pp.........",
    "...pp........",
    "...ppp.......",
    "..ppppp......",
    "pppppppppp...",
    "oo..ggg......",
    "ooo.gggggg...",
    "cc.dddgg.....",
    "yyyddddnnnnnn",
    "yyy.dd.k.....",
]
FLAP = {   # плащ и волосы хлопают на ветру
    5: ["oo..ggg......", ".oo.ggg......"],
    7: ["cc.dddgg.....", "ccc.ddgg....."],
    9: ["yyy.dd.k.....", "yyyc.d.k....."],
}
PAL = {
    "p": (140, 0, 220),
    "o": (255, 80, 0),
    "g": (60, 225, 40),
    "c": (210, 0, 110),
    "d": (100, 0, 190),
    "n": (160, 80, 20),
    "y": (255, 190, 40),
    "k": (130, 130, 140),
}
BAT = [["b.b.b", ".bbb."], [".bbb.", "b.b.b"]]
MAGIC = [(120, 255, 80), (200, 80, 255), (255, 230, 80), (255, 255, 255)]


def in_moon(x, y):
    cx, cy, r = MOON
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def draw_witch(f, x, y, t, flip):
    rows = WITCH[:]
    for r, variants in FLAP.items():
        rows[r] = variants[(t // 2) % 2]
    w = len(rows[0])
    for dy, row in enumerate(rows):
        if flip:
            row = row[::-1]
        for dx, ch in enumerate(row):
            if ch == ".":
                continue
            px, py = x + dx, y + dy
            # на фоне луны — чёрный силуэт
            f.set(px, py, (0, 0, 0) if in_moon(px, py) else PAL[ch])
    # откуда сыплются искры: конец прутьев
    return (x - 1, y + 8.5) if not flip else (x + w, y + 8.5)


def build():
    rnd = random.Random(13)
    stars = [(rnd.randrange(W), rnd.randrange(H - 1), rnd.randrange(8)) for _ in range(14)]
    stars = [(sx, sy, ph) for sx, sy, ph in stars if not in_moon(sx, sy)]
    sparks = []
    frames = []

    LEAD = 4            # пустое небо в начале
    PASS = 40           # ведьма слева направо, нырком через луну
    AFTER = LEAD + PASS + 3     # мыши вылетают, когда ведьма уже скрылась за правым краем
    BATS = [            # (старт, строка, скорость, фаза взмахов) — врассыпную, чтобы каждую было видно
        (AFTER, 2, 1.3, 0),
        (AFTER + 5, 9, 1.2, 1),
        (AFTER + 9, 5, 1.4, 0),
        (AFTER + 13, 11, 1.25, 1),
    ]
    total = AFTER + 13 + 30
    for t in range(total):
        f = gen.Frame()
        for sx, sy, ph in stars:
            if (t // 3 + ph) % 8:
                f.set(sx, sy, (150, 150, 200))
        cx, cy, r = MOON
        for y in range(H):
            for x in range(W):
                d = math.hypot(x - cx, y - cy)
                if d <= r:
                    crater = (x, y) in ((17, 3), (21, 6), (18, 7), (20, 3))
                    f.set(x, y, (200, 160, 40) if crater else (235, 205, 90))
                elif d <= r + 1.1:
                    f.set(x, y, (90, 75, 20))      # лёгкое свечение вокруг

        tail = None
        if LEAD <= t < LEAD + PASS:
            p = (t - LEAD) / (PASS - 1)
            x = round(-14 + 43 * p)
            y = round(3.5 - 3.5 * math.sin(math.pi * p) + 2.5 * p)    # нырок сверху вниз через луну
            tail = draw_witch(f, x, y, t, flip=False)

        # летучие мыши летят следом вправо
        for start_t, by0, sp, ph in BATS:
            k = t - start_t
            if k < 0:
                continue
            bx = round(-6 + sp * k)
            if bx > W:
                continue
            by = by0 + round(math.sin(k * 0.8 + ph * 2))
            for dy, row in enumerate(BAT[(k // 2 + ph) % 2]):
                for dx, ch in enumerate(row):
                    if ch == "b":
                        f.set(bx + dx, by + dy, (0, 0, 0) if in_moon(bx + dx, by + dy) else (170, 90, 230))

        # хвост волшебных искр
        if tail:
            for _ in range(3):
                sparks.append([tail[0] + rnd.uniform(-1, 1), tail[1] + rnd.uniform(-1, 1), t, rnd.choice(MAGIC), rnd.uniform(0.05, 0.25)])
        for s in sparks:
            age = t - s[2]
            if 0 <= age < 9:
                s[1] += s[4]
                if (age + t) % 3:
                    f.set(round(s[0]), round(s[1]), gen.scale(s[3], 1 - age / 11))
        frames.append(f)
    gen.save("witch", frames, MS)


if __name__ == "__main__":
    build()
