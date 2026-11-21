#!/usr/bin/env python3
"""Три леденца-тросточки разной высоты стоят в снегу. Красные полосы на них
бегут по кругу, как у столба барбершопа, тросточки чуть качаются вразнобой.
Тёмный фон, редкие снежинки. Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
N = 112                 # кадров в петле
MS = 70
STEP = 4                # полоса сдвигается на пиксель раз в STEP кадров
PERIOD = 4              # 2 красных + 2 белых
GROUND = 13

RED = (255, 0, 18)
WHITE = (255, 255, 255)
SNOW = (150, 170, 215)
FLAKE = (110, 130, 185)

# крючок: палочка в колонках 0–1, кончик крючка — в колонках 4–5
HOOK = [
    ".####.",
    "######",
    "##..##",
    "##..##",
]


def cane_pixels(height):
    """Пиксели тросточки (x, y, s) от верха; s — «длина вдоль палки» для полос."""
    px = []
    stick = height - len(HOOK)
    # палочка: снизу вверх, правая колонка сдвинута на 1 — полосы диагональные
    for i in range(stick):
        y = height - 1 - i
        px.append((0, y, i))
        px.append((1, y, i + 1))
    s0 = stick
    # крючок: идём по дуге от левой ножки через верх к кончику
    cx, cy = 2.5, 2.0
    for y, row in enumerate(HOOK):
        for x, ch in enumerate(row):
            if ch != "#":
                continue
            ang = math.atan2(cy - y, x - cx)          # π — слева, π/2 — сверху, 0 — справа
            if y >= 2 and x >= 4:                     # спускающийся кончик
                ang = -(y - 1.5) * 0.6
            r = math.hypot(x - cx, y - cy)
            s = s0 + (math.pi - ang) / math.pi * 6 + (1 if r > 2.4 else 0)
            px.append((x, y, s))
    return px


CANES = [  # (левый край, высота, отражён, частота качания, фаза)
    (2, 13, False, 2, 0.0),
    (11, 9, True, 3, 1.7),
    (20, 11, False, 2, 3.6),
]


def build():
    rnd = random.Random(5)
    flakes = [(rnd.uniform(0, W), rnd.uniform(0, GROUND), rnd.choice((1, 1, 2)), rnd.uniform(0, 6.28))
              for _ in range(7)]
    shapes = [cane_pixels(h) for _, h, _, _, _ in CANES]
    frames = []
    for t in range(N):
        f = gen.Frame()
        for fx, fy, k, ph in flakes:
            y = (fy + t * GROUND * k / N) % GROUND
            x = (fx + 0.7 * math.sin(2 * math.pi * t / N * 2 + ph)) % W
            f.set(int(x), int(y), FLAKE)
        for x in range(W):
            f.set(x, GROUND, SNOW)

        phase = t // STEP
        for (x0, h, flip, freq, ph), px in zip(CANES, shapes):
            top = GROUND - h + 1            # нижний пиксель — в строке 12, в снегу
            sway = math.sin(2 * math.pi * freq * t / N + ph)
            # качается только в сторону кончика: назад крючок нависал бы буквой «f»
            lean = (1 if sway > 0.35 else 0) * (-1 if flip else 1)
            for x, y, s in px:
                yy = top + y
                if yy >= GROUND:
                    continue
                # крючок сдвигается на пиксель — тросточка качается
                dx = lean if y < len(HOOK) else 0
                xx = (5 - x) if flip else x
                stripe = math.floor(s - phase) % PERIOD < 2
                f.set(x0 + xx + dx, yy, RED if stripe else WHITE)
        frames.append(f)
    gen.save("candy_canes", frames, MS)


if __name__ == "__main__":
    build()
