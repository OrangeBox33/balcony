#!/usr/bin/env python3
"""Птичка пролетает и какает человеку на голову. Он злится, достаёт ружьё — БАХ — птичка падает."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H

PAL = {
    "c": (0, 170, 255),    # птичка
    "w": (150, 230, 255),  # крыло
    "y": (255, 200, 0),    # клюв, лапки
    "W": (255, 255, 255),
    "n": (170, 80, 10),    # волосы / приклад
    "s": (255, 130, 70),   # кожа
    "a": (255, 20, 0),     # злое лицо
    "r": (0, 190, 40),     # рубашка
    "b": (0, 80, 255),     # штаны
    "x": (150, 150, 165),  # ботинки
    "g": (200, 200, 215),  # ствол
}
GROUND = (40, 120, 20)

# ---------------------------------------------------------------- человек (лицом вправо, 8 строк)
MAN_TOP = 5


def man_rows(pose, legs, angry=False):
    f = "a" if angry else "s"
    head = ["..nnn...", f"..{f}{f}{f}{f}..", f"..{f}{f}{f}..."]
    body = [".rrrrr..", ".rrrrr..", ".sbbbs.."]
    if pose == "fist_hi":       # кулак над головой
        head = ["..nnn..s", f"..{f}{f}{f}{f}.r", f"..{f}{f}{f}.r."]
        body = [".rrrrr..", ".rrrr...", ".sbbb..."]
    elif pose == "fist_lo":     # кулак ниже — трясёт им
        head = ["..nnn...", f"..{f}{f}{f}{f}.s", f"..{f}{f}{f}.r."]
        body = [".rrrrr..", ".rrrr...", ".sbbb..."]
    elif pose == "gun":         # ружьё горизонтально у груди
        body = [".rrrrrgggg", ".rrrnss...", ".sbbb....."]
    elif pose == "aim":         # ружьё вверх-вправо
        head = ["..nnn...g", f"..{f}{f}{f}{f}.g.", f"..{f}{f}{f}.g.."]
        body = [".rrrrs...", ".rrrn....", ".sbbb...."]
    lg = {0: ["..b.b...", ".xx.xx.."],
          1: [".b...b..", "xx...xx."],
          2: ["...bb...", "...xx..."]}[legs]
    return head + body + lg


# ---------------------------------------------------------------- птичка (лицом вправо)
BY = -1   # строка спрайта птички: тело на строках 1–2
BIRD = {
    "up": [
        "..ww....",
        "...ww...",
        "c.cccccy",
        ".cccc...",
    ],
    "mid": [
        "........",
        "........",
        "cwwwcccy",
        ".cccc...",
    ],
    "down": [
        "........",
        "........",
        "c.cccccy",
        ".cwwc...",
        "..ww....",
    ],
    "dead": [            # вверх лапками
        "..y.y...",
        ".cccc...",
        "c.cccccy",
    ],
}
FLAP = ["up", "mid", "down", "mid"]

# свой мини-шрифт 3×5 для «БАХ!»
BAH = {
    "Б": ["###", "#..", "###", "#.#", "###"],
    "А": [".#.", "#.#", "###", "#.#", "#.#"],
    "Х": ["#.#", "#.#", ".#.", "#.#", "#.#"],
    "!": ["#", "#", "#", ".", "#"],
}


def build():
    frames, ms = [], []
    S = {
        "man_x": -8, "pose": "stand", "legs": 0, "angry": False,
        "bird": None,          # (x, kind, flip)
        "poop": None,          # (x, y)
        "splat": False, "excl": False, "bang": 0,
        "parts": [],           # [x, y, vx, vy, color, life, gravity]
        "dead_bird": None,     # (x, y, upside_down)
    }

    def draw(n=1, dur=100):
        for _ in range(n):
            f = gen.Frame()
            gen.floor(f, GROUND)
            mx = S["man_x"]
            f.sprite(man_rows(S["pose"], S["legs"], S["angry"]), mx, MAN_TOP, pal=PAL)
            if S["splat"]:
                for dx in (2, 3, 4):
                    f.set(mx + dx, MAN_TOP, PAL["W"])
                f.set(mx + 3, MAN_TOP - 1, PAL["W"])
                f.set(mx + 2, MAN_TOP + 1, PAL["W"])
            if S["excl"]:
                f.sprite(["W", "W", "W", ".", "W"], mx, MAN_TOP - 5, pal={"W": (255, 220, 0)})
            if S["poop"]:
                px, py = S["poop"]
                f.set(px, py, PAL["W"])
                f.set(px, py - 1, (170, 170, 170))
            if S["bird"]:
                bx, kind, flip = S["bird"]
                f.sprite(BIRD[kind], bx, BY, flip=flip, pal=PAL)
            if S["dead_bird"]:
                bx, by, up = S["dead_bird"]
                rows = BIRD["dead"] if up else BIRD["dead"][::-1]
                f.sprite(rows, bx, by, pal=PAL)
            for p in S["parts"]:
                f.set(round(p[0]), round(p[1]), p[4])
            if S["bang"]:
                col = (255, 230, 0) if S["bang"] % 2 else (255, 60, 0)
                x = 0
                for ch in "БАХ!":
                    for dy, row in enumerate(BAH[ch]):
                        for dx, v in enumerate(row):
                            if v == "#":
                                f.set(x + dx, dy, col)
                    x += len(BAH[ch][0]) + 1
            frames.append(f)
            ms.append(dur)
            alive = []
            for p in S["parts"]:
                p[0] += p[2]
                p[1] += p[3]
                p[3] += p[6]
                p[5] -= 1
                if p[5] > 0 and p[1] < H - 1:
                    alive.append(p)
            S["parts"] = alive

    st = {"bx": -16, "t": 0}

    def fly(dx, flip=False, dur=100):
        S["bird"] = (st["bx"], FLAP[st["t"] % 4], flip)
        st["bx"] += dx
        st["t"] += 1
        draw(dur=dur)

    # 1. человек входит слева, птичка летит следом поверху
    MX = 5
    while S["man_x"] < MX:
        S["man_x"] += 1
        S["legs"] = 1 + st["t"] % 2
        fly(1)
    S["legs"] = 0
    drop_x = MX + 3                       # над макушкой
    while st["bx"] + 2 < drop_x:          # «попа» птички — 2-й столбец спрайта
        fly(1)

    # 2. какает: капля падает строго вниз, птичка летит дальше
    for py in (3, 4):
        S["poop"] = (drop_x, py)
        fly(1, dur=160)
        fly(1, dur=160)
    S["poop"] = None
    S["splat"] = True
    for dx, dy in ((-1, -0.5), (1, -0.5)):
        S["parts"].append([drop_x, MAN_TOP - 1, dx, dy, PAL["W"], 3, 0.3])

    # 3. ошарашен — «!»
    S["excl"] = True
    for _ in range(6):
        fly(1, dur=110)
    S["excl"] = False

    # 4. злится, лицо краснеет, трясёт кулаком; птичка у края разворачивается
    S["angry"] = True
    for i in range(10):
        S["pose"] = "fist_hi" if i % 2 == 0 else "fist_lo"
        if st["bx"] < 21 and not S.get("turned"):
            fly(1, dur=140)
        else:
            S["turned"] = True
            fly(-1, flip=True, dur=140)

    # 5. достаёт ружьё, целится вверх; птичка летит назад, на линию огня
    S["pose"] = "gun"
    for i in range(4):
        fly(-(i % 2), flip=True, dur=120)
    S["pose"] = "aim"
    target = MX + 7
    while st["bx"] > target:
        fly(-1, flip=True, dur=130)
    fly(0, flip=True, dur=250)

    # 6. БАХ! вспышка у дула, дробь летит по диагонали к птичке
    muzzle = (MX + 8, MAN_TOP)
    trail = [(muzzle[0] + k, muzzle[1] - k) for k in range(1, 4)]
    for k in range(2):
        S["bang"] = k + 1
        for (x, y) in (trail[:2] if k == 0 else trail[1:]):
            S["parts"].append([x, y, 0, 0, (255, 255, 120), 1, 0])
        for dx, dy in ((1, -1), (0, -1), (1, 0), (2, -1), (1, -2)):
            S["parts"].append([muzzle[0] + dx, muzzle[1] + dy, 0, 0,
                               (255, 255, 255) if k == 0 else (255, 160, 0), 1, 0])
        fly(0, flip=True, dur=90)

    # 7. попадание: перья во все стороны, птичка кувыркается вниз
    bx = st["bx"]
    S["bird"] = None
    for i in range(10):
        a = 2 * math.pi * i / 10
        col = PAL["c"] if i % 2 else PAL["W"]
        S["parts"].append([bx + 3.5, 1.5, math.cos(a) * 0.9, math.sin(a) * 0.6, col, 14, 0.05])
    by, vy, k = 0.0, 0.0, 0
    land_y = H - 1 - 3
    while by < land_y:
        S["dead_bird"] = (bx, round(by), k % 2 == 1)
        S["bang"] = S["bang"] + 1 if k < 4 else 0
        draw(dur=100)
        vy += 0.22
        by = min(land_y, by + vy)
        k += 1
    S["bang"] = 0
    S["dead_bird"] = (bx, land_y, True)
    for dx in (-0.8, 0.8):
        S["parts"].append([bx + 3.5, H - 2, dx, -0.25, (160, 160, 160), 3, 0])

    # 8. опускает ружьё, из ствола дымок, лицо успокаивается
    for i in range(6):
        if i == 2:
            S["pose"] = "gun"
        if i % 2 == 0:
            sx, sy = (muzzle[0] + 0.5, muzzle[1] - 1) if i < 2 else (MX + 10, MAN_TOP + 2)
            S["parts"].append([sx, sy, 0.1, -0.35, (160, 160, 170), 5, 0])
        draw(dur=110)
    S["angry"] = False
    draw(12, dur=120)

    # 9. темнота — и всё сначала
    S.update(bird=None, dead_bird=None, parts=[], splat=False, man_x=-20)
    draw(3, dur=120)

    gen.save("bird_poop", frames, ms)


if __name__ == "__main__":
    build()
