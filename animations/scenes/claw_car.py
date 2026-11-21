#!/usr/bin/env python3
"""Когтистый мутант в жёлто-синем костюме: «шинк» — выдвигает когти, на него едет красная машина.
Прыгает сквозь неё (вспышка, искры), приземляется за ней спиной, когти втягиваются.
Машина тормозит… пауза… и разваливается по линии разреза на две половинки, искры, дым."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 70
GROUND = 13

HP = {
    "Y": (255, 185, 0),      # жёлтый костюм / маска
    "B": (0, 70, 255),       # синие «рожки», плечи, бока, трусы, сапоги, перчатки
    "W": (255, 255, 255),    # глаз
    "s": (255, 120, 60),     # кожа
    "k": (150, 70, 15),      # бакенбарды
}
CLAW = (175, 190, 220)
CLAW_TIP = (230, 235, 255)

# все спрайты лицом вправо; кулаки — точки, откуда растут когти
STAND = [                    # руки опущены
    ".B...B.",
    ".BYYYB.",
    "..YYW..",
    "..kss..",
    ".BYYYB.",
    ".YYYYY.",
    ".YBYBY.",
    ".B.B.B.",
    "..YYY..",
    "..Y.Y..",
    "..Y.Y..",
    ".BB.BB.",
]
STAND_FISTS = [(1, 7), (5, 7)]

STANCE = [                   # боевая стойка: руки в стороны, ноги шире
    ".B...B.",
    ".BYYYB.",
    "..YYW..",
    "..kss..",
    "BBYYYBB",
    "Y.YYY.Y",
    "B.BYB.B",
    "..BBB..",
    ".YY.YY.",
    ".Y...Y.",
    "BB...BB",
]
STANCE_FISTS = [(0, 6), (6, 6)]

CROUCH = [                   # присел перед прыжком / после приземления
    ".B...B.",
    ".BYYYB.",
    "..YYW..",
    "..kss..",
    "BBYYYBB",
    "Y.YYY.Y",
    "B.BBB.B",
    ".YY.YY.",
    "Y.....Y",
    "BB...BB",
]
CROUCH_FISTS = [(0, 6), (6, 6)]

LEAP = [                     # летит вправо горизонтально, рука с когтями вперёд
    "........B.B",
    ".....BBBYYW",
    "BYYBBYYYkss",
    "B..BB.YYYYB",
]
LEAP_FIST = (10, 3)

CAR = [                      # лицом влево, едет влево
    "....RRRRR....",
    "...RggRgggR..",
    "LRRRRRRRRRRRR",
    "RRRRRRRRRRRRo",
    "..ww.....ww..",
]
CAR_PAL = {
    "R": (220, 15, 15),
    "g": (70, 170, 230),
    "L": (255, 255, 190),
    "o": (255, 120, 0),
    "w": (120, 120, 130),
}
CAR_Y = GROUND - len(CAR)


def cut_left(x, y):
    """Линия разреза «\\» через середину кабины."""
    return x < 6 + y * 0.5


def draw_claws(f, fx, fy, d, n, glint=-1, spread2=2):
    """Три когтя из кулака (fx, fy) в сторону d (±1), длина n; glint — номер точки с бликом."""
    for k in range(1, n + 1):
        for i in (-1, 0, 1):
            sp = i if k == 1 else i * spread2
            c = CLAW_TIP if k == n else CLAW
            if k == glint:
                c = (255, 255, 255)
            f.set(fx + d * k, fy + sp, c)
    if glint == n and n > 0:                      # звёздочка блеска на кончике
        tx = fx + d * (n + 1)
        f.add(tx, fy - 2, (200, 200, 200))
        f.add(tx, fy + 2, (200, 200, 200))


def draw_hero(f, rows, fists, ox, oy, claws=0, glint=-1):
    f.sprite(rows, ox, oy, pal=HP)
    if claws:
        (lx, ly), (rx, ry) = fists
        draw_claws(f, ox + lx, oy + ly, -1, claws, glint)
        draw_claws(f, ox + rx, oy + ry, 1, claws, glint)


def car_pixels(lights=True):
    px = {}
    for y, row in enumerate(CAR):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            if ch == "L" and not lights:
                c = (150, 150, 120)
            else:
                c = CAR_PAL[ch]
            px[(x, y)] = c
    return px


def draw_car(f, x, t, lights=True, beam=True):
    x = round(x)
    for (cx, cy), c in car_pixels(lights).items():
        f.set(x + cx, CAR_Y + cy, c)
    if t % 2:                                     # колёса крутятся
        f.set(x + 3, GROUND - 1, (200, 200, 210))
        f.set(x + 10, GROUND - 1, (200, 200, 210))
    else:
        f.set(x + 2, GROUND - 1, (200, 200, 210))
        f.set(x + 9, GROUND - 1, (200, 200, 210))
    if lights and beam:
        for d in range(1, 5):
            f.add(x - d, CAR_Y + 2, (120 - d * 15, 120 - d * 15, 70 - d * 10))


def draw_split(f, x, sep, sag, lights):
    """Машина разрезана: левая часть уезжает влево на sep, правая вправо; концы у разреза оседают на sag."""
    x = round(x)
    for (cx, cy), c in car_pixels(lights).items():
        if cut_left(cx, cy):
            dx = -sep
            k = cx / 7                                # чем ближе к разрезу, тем ниже
        else:
            dx = sep
            k = min(1.0, (12 - cx) / 6)
        dy = round(sag * k)
        y = CAR_Y + cy + dy
        if cy == 4:                                    # колёса остаются на земле
            y = CAR_Y + cy
        f.set(x + cx + dx, min(GROUND - 1, y), c)


class Sparks:
    def __init__(self, seed):
        self.rnd = random.Random(seed)
        self.p = []

    def burst(self, x, y, n, speed=1.2, up=0.6):
        for _ in range(n):
            self.p.append([x, y, self.rnd.uniform(-speed, speed),
                           self.rnd.uniform(-speed - up, speed * 0.4), self.rnd.randint(4, 8)])

    def step(self, f):
        alive = []
        for s in self.p:
            x, y, vx, vy, life = s
            if life <= 0:
                continue
            c = (255, 255, 200) if life > 5 else ((255, 200, 40) if life > 2 else (255, 110, 0))
            f.add(round(x), round(y), c)
            s[0] += vx
            s[1] += vy
            s[3] += 0.3
            if s[1] > GROUND - 1:
                s[1] = GROUND - 1
                s[3] = -s[3] * 0.4
            s[4] -= 1
            alive.append(s)
        self.p = alive


class Smoke:
    def __init__(self, seed):
        self.rnd = random.Random(seed)
        self.p = []

    def puff(self, x, y):
        self.p.append([x, y, self.rnd.uniform(-0.25, 0.25), 0])

    def step(self, f):
        alive = []
        for s in self.p:
            x, y, vx, age = s
            if age > 14:
                continue
            v = 140 - age * 4
            c = (v, v, v + 10)
            f.add(round(x), round(y), c)
            if age < 7:
                f.add(round(x) + 1, round(y), gen.scale(c, 0.8))
            s[0] += vx + 0.05 * ((age % 4) - 1.5)
            s[1] -= 0.4
            s[3] += 1
            alive.append(s)
        self.p = alive


def build():
    rnd = random.Random(7)
    stars = [(rnd.randrange(W), rnd.randrange(0, 7), rnd.randrange(5)) for _ in range(8)]
    sparks = Sparks(11)
    smoke = Smoke(12)
    frames = []

    def bg():
        f = gen.Frame()
        t = len(frames)
        for sx, sy, ph in stars:
            if (t // 5 + ph) % 6:
                f.set(sx, sy, (100, 100, 145))
        for x in range(W):
            f.set(x, GROUND, (70, 70, 95))
        return f, t

    HX0 = 4                               # где стоит в начале
    HX1 = 17                              # где приземляется
    Y_STAND = GROUND - len(STAND)
    Y_STANCE = GROUND - len(STANCE)
    Y_CROUCH = GROUND - len(CROUCH)

    # машина: въезжает справа, едет влево; после прыжка тормозит у левого края
    CAR_START, CAR_V = 29.0, 1.2
    T_CAR0 = 10
    T_LEAP = 22
    LEAP_N = 10
    T_LAND = T_LEAP + LEAP_N
    car_x_leap_end = CAR_START - CAR_V * (T_LAND - T_CAR0)
    T_STOP = T_LAND + 7
    CAR_END = 2.0

    def car_x(t):
        if t < T_CAR0:
            return None
        if t <= T_LAND:
            return CAR_START - CAR_V * (t - T_CAR0)
        p = min(1.0, (t - T_LAND) / (T_STOP - T_LAND))
        # равнозамедленно до остановки
        return car_x_leap_end + (CAR_END - car_x_leap_end) * (1 - (1 - p) ** 2)

    # ---- 1. стоит, «шинк» — выдвигает когти; машина приближается
    for i in range(T_LEAP):
        f, t = bg()
        cx = car_x(t)
        if cx is not None:
            draw_car(f, cx, t)
        if i < 4:
            draw_hero(f, STAND, STAND_FISTS, HX0, Y_STAND)
        elif i < 6:
            draw_hero(f, CROUCH, CROUCH_FISTS, HX0, Y_CROUCH)  # рывок в стойку
        else:
            n = min(4, i - 5)
            glint = i - 9 if i >= 10 else -1                   # блик бежит по когтям
            draw_hero(f, STANCE, STANCE_FISTS, HX0, Y_STANCE, n, glint)
        frames.append(f)

    # ---- 2. присед и прыжок сквозь машину
    flash_t = None
    for i in range(LEAP_N):
        f, t = bg()
        cx = car_x(t)
        draw_car(f, cx, t)
        p = (i + 1) / (LEAP_N + 1)
        lx = HX0 - 2 + (HX1 - HX0 + 1) * p
        ly = 4 - 4 * p * (1 - p) * 3 + 3 * p * p        # дуга: вверх, потом вниз сквозь кабину
        ly = round(min(ly, 7))
        ox = round(lx)
        car_mid = cx + 7
        if i > 0 and flash_t is None and ox + 11 >= car_mid:
            flash_t = t
            sparks.burst(car_mid, CAR_Y + 1, 12, 1.4)
        if flash_t is not None and t - flash_t < 3:      # вспышка на кабине, под героем
            mx, my = round(car_mid), CAR_Y + 1
            r = [1, 2, 1][t - flash_t]
            for yy in range(my - r, my + r + 1):
                for xx in range(mx - r, mx + r + 1):
                    d = abs(xx - mx) + abs(yy - my)
                    if d <= r:
                        f.add(xx, yy, (255, 255, 255) if d < r else (200, 200, 150))
        if i == 0:
            draw_hero(f, CROUCH, CROUCH_FISTS, HX0, Y_CROUCH, 4)
        else:
            f.sprite(LEAP, ox, ly, pal=HP)
            draw_claws(f, ox + LEAP_FIST[0], ly + LEAP_FIST[1], 1, 4, spread2=1)
        sparks.step(f)
        frames.append(f)

    # ---- 3. приземлился за машиной, спиной к ней; когти втягиваются; машина тормозит
    hero_after = []                                     # (спрайт, кулаки, y, когти, блик)
    hero_after += [(CROUCH, CROUCH_FISTS, Y_CROUCH, 4, -1)] * 3
    hero_after += [(STANCE, STANCE_FISTS, Y_STANCE, 4, -1)] * 4
    hero_after += [(STANCE, STANCE_FISTS, Y_STANCE, n, n) for n in (3, 2, 1)]
    hero_after += [(STANCE, STANCE_FISTS, Y_STANCE, 0, -1)] * 2
    T_SPLIT = T_STOP + 18                               # комедийная пауза ~1 с после остановки
    SPLIT_N = 34
    t_end = T_SPLIT + SPLIT_N
    t = len(frames)
    while t < t_end:
        f, t = bg()
        k = t - T_LAND
        cx = car_x(t)
        moving = t < T_STOP
        if k < 2:
            for dx in (-2, -1, 1, 2, 3, 4, 5, 6, 7, 8):  # пыль от приземления
                if abs(dx - 3) == 3 + k * 2 or (k == 0 and abs(dx - 3) == 4):
                    f.add(HX1 + dx, GROUND - 1, (130, 120, 100))
        # машина
        if t < T_SPLIT:
            draw_car(f, cx, t if moving else 0, beam=True)
            if T_SPLIT - 3 <= t:                       # по разрезу пробегает светящаяся линия
                j = (t - (T_SPLIT - 3)) * 2
                for yy in range(5):
                    if yy <= j + 1:
                        xx = round(cx) + 6 + round(yy * 0.5 - 0.01)
                        f.set(xx, CAR_Y + yy, (255, 255, 230) if yy == j + 1 else (255, 200, 120))
        else:
            s = t - T_SPLIT
            sep = min(2, (s + 1) // 2)
            sag = min(1.0, s * 0.35)
            lights = s < 2 or (s < 6 and s % 2 == 0)
            draw_split(f, cx, sep, sag, lights)
            gx = round(cx) + 7
            if s == 0:
                sparks.burst(gx, CAR_Y + 2, 16, 1.3, 0.8)
            if s == 3:
                sparks.burst(gx, CAR_Y + 3, 8, 1.0, 0.5)
            if s < 22 and s % 2 == 0:
                smoke.puff(gx + (s // 2) % 3 - 1, CAR_Y - 1)
        # герой
        if k < len(hero_after):
            rows, fists, hy, n, g = hero_after[k]
        else:
            rows, fists, hy, n, g = STAND, STAND_FISTS, Y_STAND, 0, -1
        draw_hero(f, rows, fists, HX1, hy, n, g)
        smoke.step(f)
        sparks.step(f)
        frames.append(f)
        t += 1

    # мягкий шов петли: обломки гаснут, герой проявляется
    def dim(f, k):
        for y in range(H):
            for x in range(W):
                f.px[y][x] = gen.scale(f.px[y][x], k)
    for i, k in enumerate((0.8, 0.6, 0.4, 0.2, 0.0)):
        dim(frames[-5 + i], k)
    for i, k in enumerate((0.3, 0.6, 0.85)):
        dim(frames[i], k)
    gen.save("claw_car", frames, MS)


if __name__ == "__main__":
    build()
