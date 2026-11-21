#!/usr/bin/env python3
"""Смайлик рисуется по пикселям: кольцо за кольцом снаружи внутрь, потом глаза и улыбка."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

CX, CY, R = 13.5, 6.5, 7.0
YELLOW = (255, 190, 0)
PEN = (255, 255, 200)      # свежий пиксель на мгновение светлее — видно «перо»
DARK = (0, 0, 0)

EYE_L = [(10, 3), (11, 3), (10, 4), (11, 4), (10, 5), (11, 5)]
EYE_R = [(16, 3), (17, 3), (16, 4), (17, 4), (16, 5), (17, 5)]
WINK_L = [(10, 5), (11, 5)]  # закрытый глаз — одна полоска
MOUTH = [(8, 8), (9, 9), (10, 10), (11, 10), (12, 11), (13, 11), (14, 11), (15, 11),
         (16, 10), (17, 10), (18, 9), (19, 8)]


def disc():
    return {(x, y) for y in range(gen.H) for x in range(gen.W)
            if math.hypot(x - CX, y - CY) <= R}


def rings():
    """Снимаем диск слоями по контуру; каждый слой — по часовой стрелке от верха."""
    left = disc()
    out = []
    while left:
        edge = [p for p in left
                if any((p[0] + dx, p[1] + dy) not in left for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        edge.sort(key=lambda p: math.atan2(p[0] - CX, -(p[1] - CY)) % (2 * math.pi))
        out.append(edge)
        left -= set(edge)
    return out


def build():
    frames, ms = [], []
    color = {}          # (x, y) -> цвет поверх чёрного
    fresh = []          # пиксели, нарисованные в этом кадре

    def emit(t, n=1):
        for _ in range(n):
            f = gen.Frame()
            for (x, y), c in color.items():
                f.set(x, y, c)
            for (x, y), c in fresh:
                f.set(x, y, c)
            frames.append(f)
            ms.append(t)
        fresh.clear()

    emit(90, 6)  # пустота перед началом

    # круг: кольцо за кольцом, по 3 пикселя за кадр
    order = [p for ring in rings() for p in ring]
    step = 3
    for i in range(0, len(order), step):
        for p in order[i:i + step]:
            color[p] = YELLOW
            fresh.append((p, PEN))
        emit(55)
    emit(90, 4)

    # глаза — по пикселю, каждый глаз отдельно
    for eye in (EYE_L, EYE_R):
        for p in eye:
            color[p] = DARK
            fresh.append((p, PEN))
            emit(70)
        emit(90, 2)

    # улыбка слева направо
    emit(90, 2)
    for p in MOUTH:
        color[p] = DARK
        fresh.append((p, PEN))
        emit(75)

    emit(100, 12)
    # подмигнул
    for p in EYE_L:
        color[p] = YELLOW
    for p in WINK_L:
        color[p] = DARK
    emit(100, 6)
    for p in EYE_L:
        color[p] = DARK
    emit(100, 12)

    # гаснет
    base = dict(color)
    for k in (0.75, 0.5, 0.3, 0.15):
        color = {p: gen.scale(c, k) for p, c in base.items()}
        emit(80)
    color = {}
    emit(100, 4)

    gen.save("smiley_draw", frames, ms)


if __name__ == "__main__":
    build()
