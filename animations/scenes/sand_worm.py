#!/usr/bin/env python3
"""Вид сверху. Танк въезжает на песок и останавливается; под песком к нему ползёт бугор;
песок закручивается воронкой, под танком раскрывается круглая пасть с зубами — танк проваливается,
пасть смыкается и уходит в песок, воронка затягивается."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 70

# танк сверху, ствол вправо
TANK = [
    "kkkkkkk..",
    "hhttthh..",
    "hhtttbbbb",
    "hhttthh..",
    "kkkkkkk..",
]
TANK_PAL = {"t": (140, 165, 220), "b": (190, 200, 220), "h": (80, 100, 165), "k": (75, 75, 90)}
TREAD = (150, 150, 165)
STOP_X = 9                       # левый край танка, когда стоит
TY = 5                           # верхняя строка танка
CX, CY = STOP_X + 3, TY + 2      # центр корпуса — тут откроется пасть


def sand(x, y):
    v = math.sin(x * 0.55 + y * 1.25) + 0.5 * math.sin(x * 0.21 - y * 0.7 + 1.1)
    n = ((x * 73856093) ^ (y * 19349663)) >> 4 & 31
    if n == 0:
        return (170, 105, 35)                       # камешек
    if v > 0.8:
        return (255, 210, 110)
    if v < -0.75:
        return (165, 100, 28)
    return (220, 150, 55)


def tank_cells(t, moving):
    """Клетки танка (dx, dy, цвет); траки на гусеницах бегут, пока едет."""
    out = []
    for dy, row in enumerate(TANK):
        for dx, ch in enumerate(row):
            if ch == ".":
                continue
            c = TANK_PAL[ch]
            if ch == "k" and (dx + (t if moving else 0)) % 2 == 0:
                c = TREAD
            out.append((dx, dy, c))
    return out


def build():
    rnd = random.Random(4)
    frames = []
    ruts = set()                 # колеи от гусениц
    wake = []                    # борозда за бугром [x, y, рождён]
    grains = []                  # песчинки [x, y, vx, vy, рождён]
    t = 0

    def base(f):
        for y in range(H):
            for x in range(W):
                c = sand(x, y)
                if (x, y) in ruts:
                    c = gen.scale(c, 0.6)
                f.set(x, y, c)
        for wx, wy, born in wake:
            age = t - born
            if age < 40:
                for yy in (wy - 1, wy, wy + 1):
                    f.set(wx, yy, gen.scale(sand(wx, yy), 0.5 + 0.5 * age / 40))

    def draw_grains(f):
        for g in grains:
            age = t - g[4]
            if 0 <= age < 8:
                g[0] += g[2]
                g[1] += g[3]
                f.set(round(g[0]), round(g[1]), (255, 215, 120))

    def puff(x, y, n, speed=0.7):
        for _ in range(n):
            a = rnd.uniform(0, 2 * math.pi)
            s = rnd.uniform(0.3, speed)
            grains.append([x, y, math.cos(a) * s, math.sin(a) * s, t])

    def tank(f, x, moving, dx=0, dy=0, scale=1.0, dark=1.0):
        for cx_, cy_, c in tank_cells(t, moving):
            if scale < 1.0:
                px = CX + (x + cx_ - CX) * scale
                py = CY + (TY + cy_ - CY) * scale
                f.set(round(px), round(py), gen.scale(c, dark))
            else:
                f.set(x + cx_ + dx, TY + cy_ + dy, gen.scale(c, dark))

    # 1. танк въезжает, за ним колея
    N_IN = 30
    for i in range(N_IN):
        f = gen.Frame()
        x = round(-10 + (STOP_X + 10) * min(1.0, i / 26) ** 0.85)
        moving = i < 27
        for k in range(-12, 0):
            if 0 <= x + k + 3 < W:
                ruts.add((x + k + 3, TY))
                ruts.add((x + k + 3, TY + 4))
        base(f)
        if moving and i % 3 == 0:
            puff(x - 1, TY + 2 + rnd.choice((-2, 2)), 1, 0.4)
        draw_grains(f)
        tank(f, x, moving)
        frames.append(f)
        t += 1

    # 2. под песком ползёт бугор, за ним борозда
    N_WORM = 24
    sx, sy = W + 2, 12
    for i in range(N_WORM):
        f = gen.Frame()
        p = i / (N_WORM - 1)
        bx = sx + (CX + 4 - sx) * p
        by = sy + (CY + 1 - sy) * p + 1.2 * math.sin(p * 7)
        wake.append([round(bx), round(by), t])
        base(f)
        for dx in range(-5, 6):
            for dy in range(-5, 6):
                d = math.hypot(dx, dy)
                if d <= 1.8:
                    c = (255, 235, 160)                       # макушка бугра
                elif d <= 3.4:
                    c = (250, 200, 95)
                elif d <= 4.3 and dx + dy > 1:
                    c = (130, 75, 20)                         # тень с нижней стороны
                else:
                    continue
                f.set(round(bx) + dx, round(by) + dy, c)
        if i % 2 == 0:
            puff(bx, by, 1, 0.5)
        draw_grains(f)
        tank(f, STOP_X, False)
        frames.append(f)
        t += 1

    # 3. песок закручивается воронкой вокруг танка
    N_VORTEX = 10
    for i in range(N_VORTEX):
        f = gen.Frame()
        base(f)
        r = 2 + i * 0.6
        for y in range(H):
            for x in range(W):
                d = math.hypot(x - CX, y - CY)
                if d <= r:
                    ang = math.atan2(y - CY, x - CX)
                    swirl = math.sin(ang * 3 + d * 1.4 - t * 0.9)
                    f.set(x, y, (235, 165, 60) if swirl > 0 else (115, 65, 18))
        puff(CX, CY, 2, 0.9)
        draw_grains(f)
        tank(f, STOP_X, False)
        frames.append(f)
        t += 1

    # 4. пасть раскрывается — танк проваливается внутрь
    def mouth(f, R, open_k=1.0):
        for y in range(H):
            for x in range(W):
                d = math.hypot(x - CX, y - CY)
                if d > R + 1.3:
                    continue
                if d > R:
                    f.set(x, y, (205, 135, 70))                       # губа
                elif d > R - 1.0:
                    ang = math.atan2(y - CY, x - CX)
                    f.set(x, y, (255, 250, 230) if math.sin(ang * 9) > -0.3 else (120, 20, 20))  # зубы
                else:
                    k = d / max(R, 1)
                    f.set(x, y, (int(60 + 120 * k), 0, int(10 + 20 * k)))   # глотка темнеет к центру
        return

    N_OPEN = 9
    for i in range(N_OPEN):
        f = gen.Frame()
        base(f)
        R = 1.5 + 4.5 * (i + 1) / N_OPEN
        mouth(f, R)
        puff(CX + rnd.uniform(-R, R), CY + rnd.uniform(-R, R), 2, 1.0)
        draw_grains(f)
        s = 1.0 - 0.6 * i / (N_OPEN - 1)
        tank(f, STOP_X, False, scale=s, dark=1.0 - 0.6 * i / (N_OPEN - 1))
        frames.append(f)
        t += 1
    for i in range(4):
        f = gen.Frame()
        base(f)
        mouth(f, 6.0)
        draw_grains(f)
        if i < 2:
            tank(f, STOP_X, False, scale=0.3, dark=0.35)
        frames.append(f)
        t += 1

    # 5. пасть смыкается и уходит, остаётся воронка
    N_CLOSE = 9
    for i in range(N_CLOSE):
        f = gen.Frame()
        base(f)
        R = 6.0 * (1 - (i + 1) / N_CLOSE)
        if R > 0.6:
            mouth(f, R)
        for y in range(H):
            for x in range(W):
                d = math.hypot(x - CX, y - CY)
                if R + 1.3 < d <= 6.5:
                    f.set(x, y, (175, 110, 35))
        puff(CX, CY, 2, 0.8)
        draw_grains(f)
        frames.append(f)
        t += 1
    N_FILL = 14
    for i in range(N_FILL):
        f = gen.Frame()
        base(f)
        rr = 6.5 * (1 - (i + 1) / N_FILL)
        for y in range(H):
            for x in range(W):
                if math.hypot(x - CX, y - CY) <= rr:
                    f.set(x, y, gen.scale(sand(x, y), 0.75))
        draw_grains(f)
        frames.append(f)
        t += 1
    # колеи и борозда тают перед новым кругом
    for i in range(6):
        if i == 0:
            ruts.clear()
        f = gen.Frame()
        base(f)
        frames.append(f)
        t += 1
    gen.save("sand_worm", frames, MS)


if __name__ == "__main__":
    build()
