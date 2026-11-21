#!/usr/bin/env python3
"""Растущая снежинка: из точки вырастают шесть лучей, на них веточки; снежинка сияет,
потом рассыпается на искры, и они падают вниз, как снег. Петля без шва."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 70
CX, CY = 13, 7            # центр — в центре пикселя, иначе лучи становятся двойными
R = 7.0                   # длина луча: горизонтальные до x=6..20, косые до y=1..13
BRANCHES = [(4.3, 1.7)]   # (где на луче, длина веточки), под 60° наружу; больше пар на 28×14 слипаются в кашу

T_RAYS = 14               # растут лучи
T_BR = 16                 # растут веточки
T_SHINE = 40              # сияет
T_FALL = 40               # рассыпается
T_PAUSE = 2
N = T_RAYS + T_BR + T_SHINE + T_FALL + T_PAUSE

ICE = (90, 170, 255)
WHITE = (255, 255, 255)


def bg(y):
    # тёмно-синее небо, чуть светлее сверху; ≥ ~70 по синему, чтобы светилось
    return (0, 6, int(92 - 18 * y / (H - 1)))


def mix(a, b, k):
    return tuple(int(p + (q - p) * k) for p, q in zip(a, b))


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    k = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    qx, qy = ax + dx * k - px, ay + dy * k - py
    return math.hypot(qx, qy)


def segments(ray, br):
    """Отрезки снежинки: ray — длина лучей, br[i] — доля роста i-й пары веточек."""
    segs = []
    for k in range(6):
        a = math.pi / 3 * k
        ux, uy = math.cos(a), math.sin(a)
        if ray > 0:
            segs.append((0, 0, ux * ray, uy * ray))
        for (pos, ln), g in zip(BRANCHES, br):
            if g <= 0 or pos > ray:
                continue
            bx, by = ux * pos, uy * pos
            for s in (1, -1):
                b = a + s * math.pi / 3
                segs.append((bx, by, bx + math.cos(b) * ln * g, by + math.sin(b) * ln * g))
    return segs


def lit_pixels(ray, br):
    """{(x, y): яркость 0..1}. Порог жёсткий — полутона на диодах всё равно гаснут."""
    segs = segments(ray, br)
    out = {}
    for y in range(H):
        for x in range(W):
            px, py = x - CX, y - CY
            if not segs:
                d = math.hypot(px, py)
            else:
                d = min(seg_dist(px, py, *s) for s in segs)
            if d < 0.45:
                out[(x, y)] = 1.0 if d < 0.3 else 0.85
    out[(CX, CY)] = 1.0
    return out


def ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def flake_color(x, y, b, t, glow):
    r = math.hypot(x - CX, y - CY)
    # по лучам от центра наружу бегут волны белого
    w = 0.5 + 0.5 * math.cos(2 * math.pi * (r / 3.5 - t / 18))
    w = 0.25 + 0.75 * w * glow
    if r > R - 0.8:          # кончики всегда светлые
        w = max(w, 0.7)
    if r < 0.5:
        w = 1.0
    return gen.scale(mix(ICE, WHITE, w), 0.75 + 0.25 * b)


def background(f):
    for y in range(H):
        c = bg(y)
        for x in range(W):
            f.set(x, y, c)


rng = random.Random(11)
FULL = lit_pixels(R, [1.0] * len(BRANCHES))


class Spark:
    def __init__(self, x, y):
        self.x, self.y = x, y
        r = math.hypot(x - CX, y - CY)
        self.delay = int((R - r) * 1.2 + rng.uniform(0, 6))   # кончики осыпаются первыми
        self.vy = rng.uniform(0.28, 0.5)
        self.amp = rng.uniform(0.3, 1.2)
        self.ph = rng.uniform(0, 2 * math.pi)
        self.w = rng.uniform(0.15, 0.3)
        self.life = rng.randint(22, 32)
        self.tw = rng.randrange(4)


SPARKS = [Spark(x, y) for (x, y) in sorted(FULL)]
assert max(s.delay + s.life for s in SPARKS) <= T_FALL, "искры не успевают догореть до конца петли"


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        background(f)
        if t < T_RAYS + T_BR + T_SHINE:
            if t < T_RAYS:
                ray = R * ease((t + 1) / T_RAYS)
                br = [0.0] * len(BRANCHES)
                glow = 0.4
            elif t < T_RAYS + T_BR:
                k = (t - T_RAYS + 1) / T_BR
                ray = R
                br = [ease(k * 1.3)]
                glow = 0.6
            else:
                ray, br = R, [1.0]
                k = (t - T_RAYS - T_BR) / T_SHINE
                glow = 0.6 + 0.4 * math.sin(math.pi * k)
            for (x, y), b in lit_pixels(ray, br).items():
                f.set(x, y, flake_color(x, y, b, t, glow))
            # искорки на кончиках во время сияния
            if t >= T_RAYS + T_BR:
                k = t - T_RAYS - T_BR
                for i in range(6):
                    if (k + i * 5) % 30 < 3:
                        a = math.pi / 3 * i
                        f.set(round(CX + math.cos(a) * R), round(CY + math.sin(a) * R), WHITE)
        else:
            age0 = t - (T_RAYS + T_BR + T_SHINE)
            for s in SPARKS:
                age = age0 - s.delay
                if age < 0:      # ещё на месте
                    f.set(s.x, s.y, flake_color(s.x, s.y, FULL[(s.x, s.y)], t, 0.6))
                    continue
                if age >= s.life:
                    continue
                y = s.y + s.vy * age + 0.006 * age * age
                x = s.x + s.amp * math.sin(s.ph + s.w * age) - s.amp * math.sin(s.ph)
                fade = 1.0 if age < s.life - 8 else (s.life - age) / 8
                tw = 1.0 if (age + s.tw) % 4 else 0.7
                c = mix(ICE, WHITE, 0.5 + 0.5 * math.cos(age * 0.5 + s.ph))
                c = gen.scale(c, max(0.45, fade * tw))
                xi, yi = round(x), round(y)
                if 0 <= yi < H:
                    f.set(xi, yi, c)
        frames.append(f)
    gen.save("snowflake_grow", frames, MS)


if __name__ == "__main__":
    build()
