#!/usr/bin/env python3
"""Маленький зелёный мастер с огромными ушами тренируется с изумрудным мечом:
зажигает клинок, три быстрых взмаха со шлейфом, разворот с кругом меча,
прыжок назад с сальто-колесом, удар в воздухе со вспышкой и искрами, приземление в позу."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 60
GROUND = 13

# лицом вправо; центр вращения (5, 4), рука с мечом — (8, 5)
MASTER = [
    "....w..w....",
    "E...LLLL...E",
    ".EEiLeLeiEE.",
    "..EELlLLEE..",
    "....rrrr....",
    "...rRrrrh...",
    "...rrRrr....",
    "...rrrrrr...",
    "....f..f....",
]
SW = len(MASTER[0])
CX, CY = 6, 4
HAND = (2, 1)                  # рука относительно центра (лицом вправо)
C = {
    "w": (235, 235, 235),      # редкие седые волосы
    "E": (150, 200, 45),       # уши
    "i": (215, 150, 105),      # внутри уха
    "L": (150, 200, 45),       # оливково-салатовая кожа
    "l": (195, 230, 110),      # складка-морщина (светлее кожи)
    "e": (255, 235, 150),      # большие глаза
    "r": (195, 140, 70),       # накидка, беж
    "R": (140, 85, 35),        # складки накидки
    "h": (150, 200, 45),       # кисть
    "f": (150, 200, 45),       # ступни
}
CORE = (215, 255, 225)         # сердцевина клинка
BLADE = (40, 255, 130)         # кончик и свечение
TRAIL = (0, 230, 110)
HILT = (170, 170, 185)
BLEN = 6


def rot(dx, dy, th):
    c, s = math.cos(th), math.sin(th)
    return dx * c - dy * s, dx * s + dy * c


def hand_screen(x, y, th, flip):
    hx, hy = rot(HAND[0], HAND[1], th)
    return x + (-hx if flip else hx), y + hy


def blade_angle(a, th, flip):
    """a — угол меча в «лицом вправо» (0 — вперёд, −π/2 — вверх) → угол на экране."""
    s = a + th
    return math.pi - s if flip else s


def draw_body(f, x, y, th, flip, crouch=0):
    rows = MASTER
    if crouch:                 # присел: без ступней, накидка ниже
        rows = MASTER[:7] + [MASTER[7]]
    for py in range(H):
        for px in range(W):
            dx = px - x
            if flip:
                dx = -dx
            sx, sy = rot(dx, py - y, -th)
            ix, iy = round(sx + CX), round(sy + CY)
            if 0 <= iy < len(rows) and 0 <= ix < SW:
                ch = rows[iy][ix]
                if ch != ".":
                    f.set(px, py, C[ch])


def draw_blade(f, hx, hy, ang, ln):
    if ln <= 0:
        return
    f.set(round(hx), round(hy), HILT)
    n = int(round(ln))
    for r in range(1, n + 1):
        f.set(round(hx + r * math.cos(ang)), round(hy + r * math.sin(ang)),
              CORE if r < n else BLADE)


def draw_trail(f, hist, ln):
    """Шлейф: дуга между прошлыми положениями клинка, гаснет с возрастом."""
    if ln <= 0:
        return
    for age in range(min(2, len(hist) - 1)):
        (h1x, h1y, a1), (h0x, h0y, a0) = hist[-1 - age], hist[-2 - age]
        d = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        if abs(d) < 0.2:
            continue
        k = (0.7, 0.35)[age]
        steps = max(2, int(abs(d) / 0.12))
        seen = set()
        for s in range(steps):
            p = s / steps
            hx, hy, a = h0x + (h1x - h0x) * p, h0y + (h1y - h0y) * p, a0 + d * p
            for r in range(max(2, int(ln) - 2), int(ln) + 1):
                q = (round(hx + r * math.cos(a)), round(hy + r * math.sin(a)))
                if q not in seen:
                    seen.add(q)
                    kk = k * (0.55 + 0.45 * r / ln)
                    f.add(q[0], q[1], gen.scale(TRAIL, kk))


def ease(p):
    p = max(0.0, min(1.0, p))
    return p * p * (3 - 2 * p)


def build():
    rnd = random.Random(11)
    UP = -math.pi / 2
    GY = GROUND - 1 - (len(MASTER) - 1 - CY)      # y центра, когда стоит
    # кадр: dict(x, y, th, flip, a, ln, crouch, fx)
    st = []

    def add(x, y=0, th=0.0, flip=False, a=UP, ln=BLEN, crouch=0, fx=None):
        st.append(dict(x=x, y=GY + y + crouch, th=th, flip=flip, a=a, ln=ln, crouch=crouch, fx=fx))

    X0, X1 = 10, 17
    # 1) стоит, зажигает меч вверх-вперёд
    for t in range(3):
        add(X0, ln=0, a=-1.1)
    for t in range(5):
        add(X0, ln=min(BLEN, (t + 1) * 1.5), a=-1.1, fx="ignite" if t < 2 else None)
    for t in range(2):
        add(X0, a=-1.1)

    # 2) три быстрых взмаха с шагами вперёд: (замах, удар, шаг)
    x = X0
    for a0, a1, step in ((-2.3, 0.9, 2), (0.9, -2.4, 2), (-2.5, 0.25, 3)):
        add(x, a=a0, crouch=0)
        for k in range(1, 4):
            p = ease(k / 3)
            add(x + step * p, a=a0 + (a1 - a0) * p, crouch=1 if k == 2 else 0)
        x += step
        add(x, a=a1)
        add(x, a=a1)
    # 3) разворот: меч описывает полтора круга, мастер поворачивается лицом влево
    N = 9
    for k in range(1, N + 1):
        s = 0.25 + 3 * math.pi * k / N   # экранный угол меча
        flip = math.cos(s) < 0
        a = (math.pi - s) if flip else s                        # обратно в «лицом вправо»
        add(X1, a=a, flip=flip, crouch=1 if 3 <= k <= 6 else 0)
    # 4) присел перед прыжком
    for k in range(3):
        add(X1, flip=True, a=0.6 + 0.4 * k, crouch=1)
    # прыжок назад-влево: сальто-колесо вперёд (2 оборота) на подъёме
    NR, NH, NF = 8, 5, 5
    top = 4.5
    xs, xe = X1, X0
    path = NR + NH + NF
    for k in range(1, NR + 1):
        p = k / NR
        xx = xs + (xe - xs) * (k / path)
        add(xx, y=-top * (1 - (1 - p) ** 2), th=4 * math.pi * ease(p), flip=True, a=1.4)
    # зависает в верхней точке и бьёт сверху вниз
    for k in range(NH):
        xx = xs + (xe - xs) * ((NR + k + 1) / path)
        a = (-2.5, -2.5, -0.6, 0.9, 1.0)[k]
        fx = "impact" if k == 3 else ("glow" if k == 4 else None)
        add(xx, y=-top + 0.3 * k * (k > 2), flip=True, a=a, fx=fx)
    # падение
    for k in range(1, NF + 1):
        p = k / NF
        xx = xs + (xe - xs) * ((NR + NH + k) / path)
        add(xx, y=-top * (1 - p * p), flip=True, a=1.0 + 0.2 * p)
    # 5) приземление: присед, пыль, затем поза — меч отведён назад горизонтально
    for k in range(2):
        add(X0, flip=True, a=1.2, crouch=1, fx="dust" if k == 0 else "dust2")
    for k, a in enumerate((0.4, -0.4, -1.0)):
        add(X0, flip=True, a=a, crouch=1 if k == 0 else 0)
    for k in range(7):
        add(X0, flip=True, a=-1.0)
    # 6) поворачивается вправо, гасит меч
    for k in range(5):
        add(X0, flip=False, a=-1.1, ln=BLEN - (k + 1) * 1.2)
    for k in range(3):
        add(X0, ln=0, a=-1.1)

    # искры: появляются в момент удара
    sparks = []
    frames, hist = [], []
    for i, s in enumerate(st):
        f = gen.Frame()
        # болотная земля и кочки
        for gx in range(W):
            f.set(gx, GROUND, (45, 115, 35) if (gx * 7) % 5 else (70, 140, 45))
        for gx in (2, 6, 23, 26):
            f.set(gx, GROUND - 1, (60, 125, 40))
        # лёгкий туман, медленно ползёт, петля без шва
        T = len(st)
        for gx in range(W):
            v = math.sin(2 * math.pi * (gx / 14 + i / T)) + math.sin(2 * math.pi * (gx / 9 - 2 * i / T))
            if v > 1.1:
                f.set(gx, GROUND - 1, (80, 105, 100))

        x, y, th, flip = round(s["x"]), s["y"], s["th"], s["flip"]
        hx, hy = hand_screen(x, y, th, flip)
        ang = blade_angle(s["a"], th, flip)
        hist.append((hx, hy, ang))
        draw_trail(f, hist, s["ln"])
        draw_body(f, x, y, th, flip, s["crouch"])
        draw_blade(f, hx, hy, ang, s["ln"])

        tipx = hx + BLEN * math.cos(ang)
        tipy = hy + BLEN * math.sin(ang)
        fx = s["fx"]
        if fx == "ignite":
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                f.add(round(hx) + dx, round(hy) + dy, (90, 255, 160))
        if fx == "impact":
            cx, cy = round(tipx), round(tipy)
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    d = abs(dx) + abs(dy)
                    if d <= 2:
                        f.add(cx + dx, cy + dy, (255, 255, 255) if d == 0 else
                              (200, 255, 210) if d == 1 else (60, 220, 120))
            for _ in range(14):
                a = rnd.uniform(0, 2 * math.pi)
                v = rnd.uniform(0.6, 1.6)
                sparks.append([tipx, tipy, v * math.cos(a), v * math.sin(a) - 0.4,
                               rnd.choice(((255, 240, 160), (200, 255, 200), (255, 255, 255)))])
        if fx == "glow":
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                f.add(round(tipx) + dx, round(tipy) + dy, (120, 255, 170))
        if fx in ("dust", "dust2"):
            k = 0 if fx == "dust" else 1
            for dx in (-5 - k, -4 - k, 4 + k, 5 + k):
                f.set(x + dx, GROUND - 1 - (abs(dx) == 4 + k and k == 0), (150, 140, 110))
        alive = []
        for sp in sparks:
            sp[0] += sp[2]
            sp[1] += sp[3]
            sp[3] += 0.18
            sp[2] *= 0.92
            if 0 <= sp[0] < W and sp[1] < GROUND:
                f.set(round(sp[0]), round(sp[1]), sp[4])
                if rnd.random() < 0.85:
                    alive.append(sp)
        sparks = alive
        frames.append(f)
    gen.save("green_master", frames, MS)


if __name__ == "__main__":
    build()
