#!/usr/bin/env python3
"""Вид сверху, пустыня. Гусеничный танк въезжает слева, сворачивает и встаёт в центре,
крутит башней. К нему по дуге ползёт бугор — под песком червь. Вокруг танка раскрывается
круглая пасть с кольцом зубов, танк проваливается в глотку, пасть смыкается и уходит в песок;
остаётся воронка, песок затягивается. Петля начинается и кончается чистым песком."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 70
rng = random.Random(11)

# ---------------------------------------------------------------- песок (приглушённый — ток)

SAND = (120, 82, 25)
CREST = (150, 103, 34)        # гребни ряби
TROUGH = (108, 72, 20)


def sand(x, y):
    v = math.sin(0.5 * x + 1.0 * y + 0.9 * math.sin(0.28 * x))
    if v > 0.82:
        return CREST
    if v < -0.85:
        return TROUGH
    return SAND


def mix(a, b, k):
    k = min(max(k, 0.0), 1.0)
    return tuple(int(p + (q - p) * k) for p, q in zip(a, b))


def q(c, step=8):
    """Квантуем цвет — меньше цветов в палитре GIF."""
    return tuple(min(255, int(round(v / step) * step)) for v in c)


# ---------------------------------------------------------------- танк (рисуется по формуле — можно вертеть)

HULL = (105, 135, 200)       # серо-синий — не сливается с тёплым песком
TURRET = (185, 205, 245)
HATCH = (255, 255, 255)
BARREL = (235, 235, 245)
TRACK_HI = (225, 220, 205)    # траки тёплые серые — отличаются от синего корпуса
TRACK_LO = (120, 112, 100)

TCX, TCY = 13, 7             # пиксель центра танка, когда стоит (корпус 7 + ствол 1 → по центру 28)


def tank_pixel(x, y, cx, cy, head, gun, phase, s=1.0):
    """Цвет пикселя (x, y) у танка с центром в пикселе (cx, cy), курсом head, башней gun; None — мимо."""
    dx, dy = (x - cx) / s, (y - cy) / s
    ch, sh = math.cos(head), math.sin(head)
    u = dx * ch + dy * sh            # вдоль корпуса
    v = -dx * sh + dy * ch           # поперёк
    cg, sg = math.cos(gun), math.sin(gun)
    ub = dx * cg + dy * sg
    vb = -dx * sg + dy * cg
    if abs(u) < 1.5 and abs(v) < 1.5:
        return HATCH if abs(u) < 0.5 and abs(v) < 0.5 else TURRET
    if 1.5 <= ub < 4.7 and abs(vb) < 0.5:
        return BARREL
    if abs(u) < 3.5:
        if abs(v) < 1.5:
            return HULL
        if abs(v) < 2.5:             # гусеницы: траки бегут полосками
            return TRACK_HI if (math.floor(u + 0.5) + phase) % 3 == 0 else TRACK_LO
    return None


def track_spots(cx, cy, head):
    """Пиксели под гусеницами — тут останутся следы."""
    out = []
    for x in range(cx - 4, cx + 5):
        for y in range(cy - 4, cy + 5):
            dx, dy = x - cx, y - cy
            u = dx * math.cos(head) + dy * math.sin(head)
            v = -dx * math.sin(head) + dy * math.cos(head)
            if abs(u) < 3.5 and 1.5 <= abs(v) < 2.5:
                out.append((x, y))
    return out


def tank_path():
    """Клетки пути: слева по низу, по диагонали вверх-вправо, потом прямо в центр."""
    pts = []
    for x in range(-5, 7):
        pts.append((x, 11, 0.0))
    for k in range(1, 5):
        pts.append((6 + k, 11 - k, -math.pi / 4))
    for x in range(11, TCX + 1):
        pts.append((x, 7, 0.0))
    return pts


# ---------------------------------------------------------------- червь

LIP = (215, 135, 100)
RIM = (245, 180, 135)
TOOTH = (255, 250, 225)
TOOTH2 = (235, 200, 150)
MX, MY = TCX, TCY            # центр пасти — центр танка


def throat(k):
    """k = d / радиус раскрытия: 1 у зубов, 0 в глубине."""
    if k > 0.78:
        return (255, 115, 20)
    if k > 0.52:
        return (225, 55, 0)
    if k > 0.27:
        return (165, 15, 0)
    return (100, 0, 0)


def worm_pixel(x, y, R, rin, t):
    """Голова червя: губы-лепестки от rin до R, у края раскрытия кольцо зубов, внутри глотка."""
    dx, dy = x - MX, y - MY
    d = math.hypot(dx, dy)
    if d >= R:
        return None
    a = math.atan2(dy, dx)
    if d < rin:
        if d > rin - 1.0:                                        # зубы по краю
            n = max(6, round(rin * 2.2))
            return TOOTH if math.sin(n * a) > -0.2 else (255, 140, 40)
        k = d / max(rin, 0.01)
        if rin > 3 and 0.5 < k < 0.66 and math.sin(7 * (a + t * 0.12)) > 0.3:
            return TOOTH2                                        # второй ряд зубов, медленно крутится
        return throat(k)
    if d > R - 1.0:
        return RIM
    if rin < R - 2.5:                                            # швы, где сомкнулись губы
        for sa in (0.5, 0.5 + 2 * math.pi / 3, 0.5 - 2 * math.pi / 3):
            da = (a - sa + math.pi) % (2 * math.pi) - math.pi
            if abs(da) * max(d, 0.7) < 0.55 and d > rin:
                return RIM
    petal = 0.82 + 0.18 * math.cos(3 * a + 0.5)                 # три лепестка-губы
    return gen.scale(LIP, petal)


# ---------------------------------------------------------------- частицы песка

class Grain:
    def __init__(self, x, y, vx, vy, life, col=(205, 150, 70)):
        self.x, self.y, self.vx, self.vy, self.life, self.col = x, y, vx, vy, life, col
        self.age = 0


def spray(grains, n, r, speed):
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi)
        v = rng.uniform(0.6, 1.0) * speed
        grains.append(Grain(MX + math.cos(a) * r, MY + math.sin(a) * r,
                            math.cos(a) * v, math.sin(a) * v, rng.randrange(5, 10)))


# ---------------------------------------------------------------- сборка

def build():
    frames = []
    marks = {}                   # (x, y) -> кадр, когда оставлен след
    wake = []                    # (x, y, кадр) — светлый след от бугра
    grains = []
    S = {"tank": None, "head": 0.0, "gun": 0.0, "phase": 0, "scale": 1.0, "dim": 1.0,
         "bump": None, "heave": 0.0, "R": 0.0, "rin": 0.0, "under": False, "crater": 0.0}

    def frame():
        t = len(frames)
        f = gen.Frame()
        # песок + воронка
        for y in range(H):
            for x in range(W):
                c = sand(x, y)
                if (x, y) in marks:                              # следы гусениц тускнеют и затягиваются
                    age = t - marks[(x, y)]
                    c = mix((88, 58, 16), c, age / 45)
                cr = S["crater"]
                if cr > 0:                                       # воронка: светлый край, две спирали внутрь
                    d = math.hypot(x - MX, y - MY)
                    rad = 1.5 + 5.0 * cr
                    if d < rad + 0.5:
                        a = math.atan2(y - MY, x - MX)
                        if d > rad - 0.6:
                            ring = (200, 145, 55)
                        elif d < 1.2:
                            ring = (60, 35, 8)
                        else:
                            sw = math.sin(2 * a + 1.5 * d - t * 0.3)
                            ring = (180, 126, 46) if sw > 0.35 else (98, 64, 17)
                        c = mix(c, ring, min(1.0, cr * 1.6))
                if S["heave"] > 0:                               # песок вспучивается кольцом
                    d = math.hypot(x - MX, y - MY)
                    rr = 2.5 + 3.5 * S["heave"]
                    if abs(d - rr) < 0.8:
                        c = (175, 122, 45)
                    elif d < rr:
                        c = mix(c, (150, 104, 36), 0.6)
                f.set(x, y, q(c))
        # след бугра
        for wx, wy, born in wake:
            age = t - born
            if age < 26:
                k = 1 - age / 26
                for ox, oy in ((0, 0), (0, 1), (0, -1), (1, 0), (-1, 0)):
                    kk = k if (ox, oy) == (0, 0) else k * 0.6
                    f.set(wx + ox, wy + oy, q(mix(sand(wx + ox, wy + oy), (185, 130, 48), kk)))
        # бугор: светлое пятно с гребнем
        if S["bump"]:
            bx, by = S["bump"]
            for y in range(H):
                for x in range(W):
                    d = math.hypot(x - bx, y - by)
                    if d < 2.6:
                        f.set(x, y, q(mix((170, 118, 42), (255, 200, 100), 1 - d / 2.6)))
        R, rin = S["R"], S["rin"]
        cells = []
        if S["tank"]:
            cx, cy = S["tank"]
            for y in range(cy - 6, cy + 7):
                for x in range(cx - 6, cx + 7):
                    c = tank_pixel(x, y, cx, cy, S["head"], S["gun"], S["phase"], S["scale"])
                    if c:
                        cells.append((x, y, q(gen.scale(c, S["dim"]))))

        def draw_worm():
            for y in range(H):
                for x in range(W):
                    c = worm_pixel(x, y, R, rin, t)
                    if c:
                        f.set(x, y, q(c))

        if R > 0 and S["under"]:     # танк уже в пасти: губы смыкаются поверх него
            for y in range(H):
                for x in range(W):
                    if math.hypot(x - MX, y - MY) < rin:
                        f.set(x, y, q(worm_pixel(x, y, R, rin, t)))
            for x, y, c in cells:
                if math.hypot(x - MX, y - MY) < rin - 0.9:
                    f.set(x, y, c)
            for y in range(H):
                for x in range(W):
                    if math.hypot(x - MX, y - MY) >= rin - 1.0:
                        c = worm_pixel(x, y, R, rin, t)
                        if c:
                            f.set(x, y, q(c))
        else:
            if R > 0:
                draw_worm()
            for x, y, c in cells:
                f.set(x, y, c)
        # песчинки
        for g in grains:
            if g.age < g.life:
                k = 1 - g.age / g.life
                f.set(round(g.x), round(g.y), q(mix((140, 96, 32), g.col, k)))
        for g in grains:
            g.x += g.vx
            g.y += g.vy
            g.vx *= 0.8
            g.vy *= 0.8
            g.age += 1
        grains[:] = [g for g in grains if g.age < g.life]
        frames.append(f)

    def hold(n):
        for _ in range(n):
            frame()

    # 1. тишина
    hold(3)

    # 2. танк едет: шаг клетки — 2 кадра, в конце притормаживает; за ним следы и пыль
    path = tank_path()
    for i, (x, y, hd) in enumerate(path):
        left = len(path) - i
        steps = 2 if left > 3 else 3
        S["tank"], S["head"] = (x, y), hd
        S["gun"] = hd
        for p in track_spots(x, y, hd):
            marks[p] = len(frames)
        for _ in range(steps):
            S["phase"] = (S["phase"] + 1) % 3
            if rng.random() < 0.7:                               # пыль из-под гусениц сзади
                side = rng.choice((-2, 2))
                bx = x - 4 * math.cos(hd) - side * math.sin(hd)
                by = y - 4 * math.sin(hd) + side * math.cos(hd)
                grains.append(Grain(bx, by, -0.35 * math.cos(hd) + rng.uniform(-0.15, 0.15),
                                    -0.35 * math.sin(hd) + rng.uniform(-0.15, 0.15), rng.randrange(4, 7),
                                    (190, 140, 65)))
            frame()

    # 3. встал, крутит башней; справа по дуге подбирается бугор, башня следит за ним
    def bump_at(k):
        """Квадратичная кривая: из-за правого верхнего края, через низ — к танку."""
        p0, p1, p2 = (31.0, 0.0), (25.0, 15.0), (MX + 2.5, MY + 0.5)
        x = (1 - k) ** 2 * p0[0] + 2 * (1 - k) * k * p1[0] + k * k * p2[0]
        y = (1 - k) ** 2 * p0[1] + 2 * (1 - k) * k * p1[1] + k * k * p2[1]
        return x, y

    look = [-math.pi / 4, -math.pi / 2, -math.pi / 2, -3 * math.pi / 4, -3 * math.pi / 4, -math.pi / 2, -math.pi / 4]
    BUMP_N = 34
    LOOK_STEP = 3
    total = len(look) * LOOK_STEP + BUMP_N - 8
    for i in range(total):
        j = i - (len(look) * LOOK_STEP - 8)                      # бугор стартует, пока башня ещё крутится
        if j >= 0:
            k = j / (BUMP_N - 1)
            k = 1 - (1 - k) ** 1.3 if k < 1 else 1
            bx, by = bump_at(k)
            S["bump"] = (bx, by)
            wake.append((round(bx), round(by), len(frames)))
        if i < len(look) * LOOK_STEP:
            S["gun"] = look[i // LOOK_STEP]
        if j >= 6:                                               # заметил — целится в бугор (по 45°)
            bx, by = S["bump"]
            a = math.atan2(by - MY, bx - MX)
            S["gun"] = round(a / (math.pi / 4)) * (math.pi / 4)
        frame()

    # 4. бугор ушёл под танк: песок вспучивается, танк трясёт
    S["bump"] = None
    for i in range(8):
        S["heave"] = i / 7
        S["tank"] = (TCX + (1 if i % 2 else 0), TCY)
        if i % 2 == 0:
            spray(grains, 3, 3.0 + 3.0 * S["heave"], 0.9)
        frame()
    S["tank"] = (TCX, TCY)
    S["heave"] = 0.0

    # 5. пасть раскрывается вокруг танка
    OPEN = 9
    RMAX = 6.7
    for i in range(OPEN):
        k = (i + 1) / OPEN
        k = 1 - (1 - k) ** 2
        S["R"] = RMAX * k
        S["rin"] = max(0.0, S["R"] - 1.7)
        S["tank"] = (TCX + (1 if i % 2 else 0), TCY) if i < 4 else (TCX, TCY)
        spray(grains, 4, S["R"] + 0.3, 1.3)
        frame()
    S["R"], S["rin"] = RMAX, RMAX - 1.7

    # 6. танк проваливается в глотку (уменьшается и темнеет)
    S["under"] = True
    hold(2)
    FALL = 9
    for i in range(FALL):
        k = (i + 1) / FALL
        S["scale"] = 1 - 0.75 * k
        S["dim"] = 1 - 0.55 * k
        S["gun"] += 0.35                                         # закручивает в воронку глотки
        S["head"] += 0.35
        frame()
    S["tank"] = None

    # 7. губы смыкаются
    CLOSE = 7
    for i in range(CLOSE):
        S["rin"] = (RMAX - 1.7) * (1 - (i + 1) / CLOSE)
        frame()
    S["rin"] = 0.0
    hold(3)

    # 8. голова уходит в песок, остаётся воронка
    SINK = 9
    for i in range(SINK):
        k = (i + 1) / SINK
        S["R"] = RMAX * (1 - k)
        S["crater"] = k
        if i % 2 == 0:
            spray(grains, 3, S["R"] + 0.5, -0.5)                 # песок сыплется внутрь
        frame()
    S["R"] = 0.0

    # 9. воронка затягивается
    SETTLE = 22
    for i in range(SETTLE):
        k = (i + 1) / SETTLE
        S["crater"] = 1 - k
        frame()
    S["crater"] = 0.0
    marks.clear()
    hold(2)
    gen.save("dune_worm", frames, MS)


if __name__ == "__main__":
    build()
