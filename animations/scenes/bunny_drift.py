#!/usr/bin/env python3
"""Зайчик за сугробом: ночной лес, большой сугроб. Из-за него медленно поднимаются уши,
потом выглядывает мордочка — заяц шевелит носом и прядает ушами. На ухо садится снежинка,
он встряхивается и прячется обратно. Снег идёт всё время. Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
N = 140                 # 8,4 с
MS = 60
TAU = 2 * math.pi

DRIFT_TOP = (185, 200, 240)
DRIFT = (115, 135, 195)       # сугроб голубоватый и тусклее зайца — белое на нём не сливается
FLAKE = (200, 215, 250)
EAR_FLAKE = (150, 220, 255)

PAL = {
    "W": (255, 255, 255),
    "g": (175, 180, 215),     # тень по краю мордочки
    "P": (255, 120, 165),     # внутри ушей
    "n": (255, 70, 130),      # нос
    "K": (0, 0, 0),
    "G": (25, 115, 50),
    "f": (40, 150, 65),
    "w": (225, 235, 255),
    "t": (130, 75, 30),
}

EARS = [
    ".W...W.",
    "WP...PW",
    "WP...PW",
]
EARS_TWITCH = [         # правое ухо отогнулось кончиком наружу
    ".W.....",
    "WP...WW",
    "WP...PW",
]
EARS_FLOP = [           # при встряхивании оба уха разлетаются
    "W.....W",
    ".WP.PW.",
    ".WP.PW.",
]
FACE = [
    ".gWWWg.",
    "gWWWWWg",
    "WWKWKWW",
    "WWWnWWW",
    "WWWWWWW",
]
NOSE_WIG = "WWnnnWW"
BLINK = "WWgWgWW"

FIR_L = [
    "...w...",
    "..wfw..",
    "..Gff..",
    ".wGffw.",
    ".GGfff.",
    "wGGfffw",
    "GGGffff",
    ".wGffw.",
    "wGGfffw",
    "GGGffff",
    "...t...",
]
FIR_R = [
    "....w....",
    "...wfw...",
    "...Gff...",
    "..wGffw..",
    "..GGfff..",
    ".wGGfffw.",
    ".GGGffff.",
    "..wGffw..",
    ".wGGfffw.",
    "wGGGffffw",
    "GGGGfffff",
    "....t....",
]

BX = 10                 # левый столбец зайца (ширина 7 → центр на 13)
Y_HIDE, Y_EARS, Y_PEEK = 10, 6, 2

T_EARS = (10, 28)       # уши медленно вылезают
T_HEAD = (40, 50)       # выглядывает мордочка
T_LAND = 100            # снежинка садится на ухо
T_SHAKE = (110, 118)    # встряхивается
T_DUCK = (118, 124)     # прячется


def drift_top(x):
    return min(12.0, 9.0 + 0.045 * (x + 0.5 - 13.5) ** 2)


def top_row(x):
    return round(drift_top(x))


def lerp_y(t, a, b, ya, yb):
    k = (t - a) / (b - a)
    k = k * k * (3 - 2 * k)
    return round(ya + (yb - ya) * k)


def bunny_state(t):
    """(y, dx, уши, нос шевелится?, моргает?)"""
    ears, nose, blink, dx = EARS, False, False, 0
    if t < T_EARS[0] or t >= T_DUCK[1]:
        y = Y_HIDE
    elif t < T_EARS[1]:
        y = lerp_y(t, *T_EARS, Y_HIDE, Y_EARS)
    elif t < T_HEAD[0]:
        y = Y_EARS
        if 32 <= t < 36:
            ears = EARS_TWITCH
    elif t < T_HEAD[1]:
        y = lerp_y(t, *T_HEAD, Y_EARS, Y_PEEK)
    elif t < T_SHAKE[0]:
        y = Y_PEEK
        nose = 54 <= t < 66 or 84 <= t < 94
        blink = t in (70, 71)
        if 76 <= t < 80:
            ears = EARS_TWITCH
    elif t < T_SHAKE[1]:
        y = Y_PEEK
        dx = (-1, 1)[t % 2]
        ears = EARS_FLOP if t % 2 else EARS
    else:
        y = lerp_y(t, *T_DUCK, Y_PEEK, Y_HIDE)
    return y, dx, ears, nose, blink


def build():
    rnd = random.Random(8)
    stars = []
    while len(stars) < 8:
        sx, sy = rnd.randrange(7, 20), rnd.randrange(0, 6)
        if any(abs(sx - a) + abs(sy - b) < 3 for a, b, *_ in stars):
            continue
        stars.append((sx, sy, rnd.uniform(0, TAU), rnd.choice((2, 3, 4))))
    flakes = [(rnd.uniform(0, W), rnd.uniform(0, 1), rnd.choice((1, 2, 2)), rnd.uniform(0, TAU), rnd.choice((1, 2)))
              for _ in range(9)]

    ear_tip = (BX + 5, Y_PEEK - 1)          # куда садится снежинка: над правым ухом
    frames = []
    for t in range(N):
        f = gen.Frame()
        for sx, sy, ph, k in stars:
            v = 0.5 + 0.5 * math.sin(TAU * k * t / N + ph)
            if v > 0.3:
                f.set(sx, sy, gen.scale((235, 220, 150), 0.5 + 0.5 * v))
        # ели по краям
        f.sprite(FIR_L, 0, top_row(3) - len(FIR_L) + 1, pal=PAL)
        f.sprite(FIR_R, W - 9, top_row(23) - len(FIR_R) + 1, pal=PAL)

        # заяц (за сугробом)
        y, dx, ears, nose, blink = bunny_state(t)
        face = FACE[:]
        if nose and (t // 2) % 2:
            face[3] = NOSE_WIG
        if blink:
            face[2] = BLINK
        f.sprite(ears + face, BX + dx, y, pal=PAL)

        # сугроб и земля
        for x in range(W):
            ty = top_row(x)
            for yy in range(ty, H):
                f.set(x, yy, DRIFT_TOP if yy == ty else DRIFT)

        # снежинка, что летит на ухо, сидит и слетает при встряхивании
        fall = 22
        if T_LAND - fall <= t < T_LAND:
            k = (t - (T_LAND - fall)) / fall
            fx = ear_tip[0] - 2 + round(2 * k + 0.8 * math.sin(k * 5))
            fy = round(-1 + (ear_tip[1] + 1) * k)
            f.set(fx, fy, EAR_FLAKE)
        elif T_LAND <= t < T_SHAKE[0]:
            f.set(ear_tip[0], ear_tip[1], EAR_FLAKE)
        elif T_SHAKE[0] <= t < T_SHAKE[0] + 6:
            k = t - T_SHAKE[0]
            for sx_, sy_ in ((1, -0.4), (1.3, 0.3), (0.6, 0.6)):
                px, py = ear_tip[0] + 1 + sx_ * k, ear_tip[1] + sy_ * k
                if (k + int(sx_ * 10)) % 3 != 2:
                    f.set(round(px), round(py), (255, 255, 255) if k < 3 else EAR_FLAKE)

        # снег идёт всё время
        for x0, ph, cyc, wph, sw in flakes:
            u = (ph + cyc * t / N) % 1
            yy = round(u * (H + 2)) - 1
            x = round(x0 + sw * math.sin(TAU * 2 * t / N + wph)) % W
            if yy < top_row(x):
                f.set(x, yy, FLAKE)
        frames.append(f)
    gen.save("bunny_drift", frames, MS)


if __name__ == "__main__":
    build()
