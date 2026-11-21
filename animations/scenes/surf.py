#!/usr/bin/env python3
"""Волна бежит слева направо, серфер скатывается с её макушки вниз, светит солнце."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
SEA = 10            # уровень спокойной воды
AMP = 5             # высота волны над морем
BACK, FRONT = 6.0, 3.6   # полуширина заднего (пологого) и переднего (крутого) склона
START, END = -9.0, W + 9.0
SPEED = 0.55        # пикселей за кадр
N = int((END - START) / SPEED)

SUN = (255, 200, 0)
RAY = (255, 130, 0)
BOARD = (255, 210, 0)
SURFER = [
    "..ss..",
    "s.rr.s",
    "..rr..",
    ".b..b.",
]


def surface(x, cx):
    """Верх воды в столбце x, когда макушка волны в cx."""
    u = x - cx
    k = BACK if u < 0 else FRONT
    return SEA - AMP * math.exp(-(u / k) ** 2)


def water_color(y, top, x, t):
    depth = y - top
    if depth < 0.5:
        return (120, 220, 255)                       # светлая кромка
    if y >= SEA + 1 and (x - t // 2 + y * 5) % 11 in (0, 1):
        return (50, 140, 255)                        # бегущие полосы
    k = min(depth / 6, 1)
    return (int(20 * (1 - k)), int(150 - 90 * k), 255 if k < 0.7 else 210)


def noise(x, y, t):
    v = (x * 73856093) ^ (y * 19349663) ^ (t * 83492791)
    return ((v >> 7) & 1023) / 1023


def smooth(a):
    a = min(max(a, 0.0), 1.0)
    return a * a * (3 - 2 * a)


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        cx = START + t * SPEED

        # солнце
        sx, sy = 25, 1
        for y in range(H):
            for x in range(W):
                if (x - sx) ** 2 + (y - sy) ** 2 <= 3.5:
                    f.set(x, y, SUN)
        for k in range(8):
            if (k + t // 4) % 2:
                continue
            a = k * math.pi / 4 + t * 0.03
            f.set(round(sx + math.cos(a) * 3.3), round(sy + math.sin(a) * 3.3), RAY)

        # вода
        for x in range(W):
            top = surface(x, cx)
            for y in range(round(top), H):
                f.set(x, y, water_color(y, top, x, t))
        # немного пены на самой макушке
        for dx in (0, 1):
            x = round(cx) + dx
            if 0 <= x < W and noise(x, 0, t) < 0.7:
                f.set(x, round(surface(x, cx)), (240, 250, 255))
        # блики солнца на ровной воде
        for x in range(W):
            if abs(x - cx) > 8 and noise(x, 9, t) > 0.86:
                f.set(x, SEA, (255, 230, 150))

        # серфер: сначала стоит на макушке, потом съезжает по переднему склону
        # …а внизу не стоит на месте, а уезжает вперёд по ровной воде (быстрее волны)
        s = t / N
        d = 5.5 * smooth((s - 0.2) / 0.32)
        ride = max(0.0, t - 0.44 * N)
        d += 0.012 * ride * ride if ride < 25 else 0.3 * ride - 7.5
        xs = cx + d
        board = []
        for i in range(-3, 3):
            bx = round(xs) + i
            # у подножия склон почти плоский и округление прыгало 9↔10 — там доска лежит ровно на воде
            by = SEA - 1 if d >= 5.0 else round(surface(bx, cx)) - 1
            board.append((bx, by))
        for (bx, by) in board:
            f.set(bx, by, BOARD)
        foot_y = board[3][1]                     # середина доски
        f.sprite(SURFER, round(xs) - 3, foot_y - len(SURFER))

        # брызги из-под хвоста доски, пока он едет вниз
        if 0.2 < s < 0.6:
            tx, ty = board[0]
            for i in range(3):
                if noise(i, 1, t) < 0.6:
                    f.add(tx - 1 - i, ty - (i + t) % 2, (190, 230, 255))

        frames.append(f)
    gen.save("surf", frames, 75)


if __name__ == "__main__":
    build()
