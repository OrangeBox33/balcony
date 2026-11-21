#!/usr/bin/env python3
"""Мандарины: три мандарина с листиками, средний сам «чистится» — шкурка раскрывается
пятью лепестками, видны дольки, потом закрывается обратно. Рядом веточка ёлки с огоньками."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 60
# раскладка петли по кадрам: закрыт → раскрывается → открыт → закрывается
CLOSED, OPENING, OPEN, CLOSING = 30, 34, 46, 34
N = CLOSED + OPENING + OPEN + CLOSING

PEEL = (255, 80, 0)
PEEL_SHADE = (220, 45, 0)
SHINE = (255, 190, 110)
FLESH = (255, 170, 20)
FLESH_LINE = (255, 225, 150)
LEAF = (0, 200, 30)
STEM = (0, 120, 20)
NEEDLE = (0, 150, 30)
NEEDLE_LIGHT = (60, 210, 60)
TWIG = (130, 60, 10)
BULB = (255, 215, 90)

CX, CY = 14.0, 7.0          # центр среднего мандарина (между пикселями — фигура симметрична)
RH = 3.9                    # радиус «шарика» = линия, где лепестки крепятся
L_OPEN = 2.8                # длина раскрытого лепестка
PETALS = 5
SEGS = 6                    # долек

SIDE = [(4.0, 9.0, 3.0), (24.0, 9.0, 3.0)]   # два целых мандарина: центр и радиус


def ease(k):
    return 0.5 - 0.5 * math.cos(math.pi * min(1.0, max(0.0, k)))


def openness(t):
    """0 — закрыт, 1 — раскрыт; в раскрытом виде лепестки чуть покачиваются."""
    if t < CLOSED:
        return 0.0
    t -= CLOSED
    if t < OPENING:
        return ease(t / OPENING)
    t -= OPENING
    if t < OPEN:
        return 1.0 - 0.06 * math.sin(math.pi * t / OPEN) ** 2
    t -= OPEN
    return 1.0 - ease(t / CLOSING)


def whole(f, cx, cy, r, leaf=True):
    for y in range(H):
        for x in range(W):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            if d <= r:
                f.set(x, y, PEEL_SHADE if (dx + dy > r * 0.9 and d > r - 1) else PEEL)
    x0, y0 = math.floor(cx - r * 0.45), math.floor(cy - r * 0.55)
    f.set(x0, y0, SHINE)
    if leaf:
        sprig(f, cx, cy, r)


def sprig(f, cx, cy, r):
    """Черешок над макушкой и листик вбок."""
    top = round(cy - r) - 1
    f.set(math.floor(cx), top, STEM)
    f.set(math.floor(cx) + 1, top, LEAF)
    f.set(math.floor(cx) + 2, top - 1, LEAF)


def peeling(f, p):
    a = math.pi * 0.96 * p                      # угол раскрытия лепестка: 0 — сложен, π — лёг
    ca = math.cos(a)
    lk = ease(1 - p)                            # закрытый лепесток длиннее: накрывает всю макушку
    L = L_OPEN + (RH - L_OPEN) * lk
    lo, hi = sorted((RH, RH - L * ca))
    pad = 0.55
    taper = ease(min(1.0, p * 1.6))             # чем раскрытее, тем острее кончики
    lines = set()
    for y in range(H):
        for x in range(W):
            dx, dy = x + 0.5 - CX, y + 0.5 - CY
            r = math.hypot(dx, dy)
            th = math.atan2(dy, dx) + math.pi / 2   # 0 — вверх
            # лепесток
            petal = False
            if lo - pad <= r <= hi + pad * 0.3:
                u = (RH - r) / ca if abs(ca) > 0.2 else L * 0.5
                u = min(max(u, 0.0), L)
                sector = 2 * math.pi / PETALS
                dth = (th + sector / 2) % sector - sector / 2
                hw = sector / 2 * (1 - taper * (0.2 + 0.55 * (u / L) ** 1.2))
                petal = abs(dth) <= hw
            flesh = r <= RH - 0.25
            over = a < math.pi / 2                  # пока лепестки не легли, они поверх долек
            if petal and (over or not flesh):
                f.set(x, y, PEEL)
            elif flesh:
                f.set(x, y, FLESH)
                lines.add((x, y))
    # границы долек — светлые лучики из середины (только там, где дольки видны)
    for i in range(SEGS):
        ang = 2 * math.pi * (i + 0.5) / SEGS - math.pi / 2
        for k in range(9, 12):
            rr = k * 0.25
            if rr > RH - 1.1:
                break
            q = (math.floor(CX + rr * math.cos(ang)), math.floor(CY + rr * math.sin(ang)))
            if q in lines:
                f.set(*q, FLESH_LINE)


# веточка ёлки в правом верхнем углу: пушистая зелёная полоса, у основания — коричневая ветка
TWIG_A, TWIG_B = (28.5, -0.2), (19.0, 2.6)
BULBS = [(21, 2, 0.0), (24, 1, 0.33), (26, 1, 0.66)]   # огоньки на ветке: x, y, фаза


def seg_dist(px, py, a, b):
    ax, ay = a
    bx, by = b
    vx, vy = bx - ax, by - ay
    k = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy)))
    return math.hypot(px - ax - k * vx, py - ay - k * vy), k


def branch(f, t):
    for y in range(0, 5):
        for x in range(17, W):
            d, k = seg_dist(x + 0.5, y + 0.5, TWIG_A, TWIG_B)
            width = 1.45 - 0.5 * k ** 2                 # к кончику веточка тоньше
            if d > width:
                continue
            if d < 0.5 and k < 0.25:
                f.set(x, y, TWIG)
            else:
                f.set(x, y, NEEDLE_LIGHT if (x * 2 + y) % 3 == 0 else NEEDLE)
    for x, y, ph in BULBS:
        v = 0.5 + 0.5 * math.sin(2 * math.pi * (t * 2 / N + ph))
        f.set(x, y, gen.scale(BULB, 0.65 + 0.35 * v))


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        branch(f, t)
        for cx, cy, r in SIDE:
            whole(f, cx, cy, r)
        p = openness(t)
        if p < 0.03:
            whole(f, CX, CY, RH)                # закрытый — такой же, как соседи
        else:
            peeling(f, p)
            if p < 0.2:                         # листик держится, пока шкурка только трогается
                sprig(f, CX, CY, RH)
        frames.append(f)
    gen.save("tangerine_peel", frames, MS)


if __name__ == "__main__":
    build()
