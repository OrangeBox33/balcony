#!/usr/bin/env python3
"""Юный волшебник (очки, шрам, красно-золотой шарф) ночью в тумане. Подплывает дементор —
ночь холодеет, звёзды гаснут. Волшебник вскидывает палочку, кончик вспыхивает,
из искр рождается олень-патронус, бросается на дементора и выбрасывает его за край."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 70
GROUND = 13

PAL = {
    "k": (95, 85, 95),      # чёрные волосы — тёмно-серые, чтобы светились
    "s": (255, 140, 90),    # кожа
    "z": (255, 220, 0),     # шрам-молния
    "G": (230, 240, 255),   # круглые очки
    "r": (220, 0, 0),       # шарф: красный
    "y": (255, 170, 0),     # шарф: золото
    "x": (100, 100, 125),   # «чёрная» мантия
    "n": (150, 80, 30),     # ботинки
    "w": (190, 120, 50),    # палочка
}

# волшебник лицом к зрителю, правая рука — к дементору
WIZ = {
    "idle": [
        ".kkk.",
        "kszsk",
        ".GsG.",
        ".ryr.",
        "xxyxx",
        "sxrxs",
        ".xxx.",
        ".x.x.",
        ".n.n.",
    ],
    "draw": [
        ".kkk..",
        "kszsk.",
        ".GsG..",
        ".ryr..",
        "xxyxx.",
        "sxrxsw",
        ".xxx..",
        ".x.x..",
        ".n.n..",
    ],
    "cast": [
        ".kkk....",
        "kszsk...",
        ".GsG....",
        ".ryr....",
        "xxyxxsww",
        "sxrx....",
        ".xxx....",
        ".x.x....",
        ".n.n....",
    ],
}
WIZ_X = 2
WIZ_Y = GROUND - len(WIZ["idle"])
TIP = (WIZ_X + 7, WIZ_Y + 4)   # кончик палочки в позе cast

# дементор летит горизонтально головой вперёд (влево): капюшон, пустота лица,
# вытянутые вперёд руки; рваный шлейф плаща тянется вправо и рисуется отдельно
DEM = [
    "...hhh.......",
    "..hvvhhddd...",
    "..hvvhdddddd.",
    "...hhhdddddd.",
    "......dddd...",
]
DEM_PAL = {
    "h": (120, 120, 140),   # капюшон чуть светлее плаща — на нём читается пустота
    "v": (0, 0, 0),         # лицо — настоящая пустота
    "d": (95, 95, 115),     # плащ (тёмный, но ещё светится)
    "a": (150, 165, 150),   # мертвенные руки
}
HEM = (80, 80, 100)

# олень-патронус лицом вправо, две фазы галопа
_STAG_TOP = [
    "......a.a.a",
    ".......aaa.",
    "........W..",
    "........WWW",
    ".WWWWWWWW..",
    "WWWWWWWW...",
    ".WWWWWWW...",
]
STAG = [
    _STAG_TOP + [".W.W..W.W..", "W...W.W...W"],
    _STAG_TOP + ["..WW..WW...", "..W.W.W.W.."],
]
CORE = (225, 245, 255)
ANTLER = (150, 215, 255)
GLOW = (60, 110, 190)

N = 52
T_DRAW, T_CAST = 13, 16     # дементор всё ближе — волшебник не ждёт и выхватывает палочку
T_BEAM = 19                 # вспышка на кончике палочки (без луча)
T_STAG = 21                 # олень проявляется
T_RUN = 24                  # бросается вперёд
T_HIT = 26                  # удар — дементор вылетает
T_LOWER = 40                # волшебник опускает палочку
STAG_X = 10


def ease(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


SKY = (0, 12, 100)
FOG = (40, 55, 140)
FOG2 = (70, 90, 170)
GROUND_C = (45, 75, 105)
GLOW1 = (40, 70, 160)
GLOW2 = (90, 140, 230)


def background(f, t, cold, light):
    """Ночное небо, туман у земли (2 оттенка), свечение (2 оттенка) — минимум цветов."""
    ph = 2 * math.pi * t / N
    for y in range(H):
        for x in range(W):
            c = SKY
            if 8 <= y < GROUND:
                k = (y - 7) / 5
                fog = 0.5 + 0.25 * math.sin(x * 0.55 + ph) + 0.25 * math.sin(x * 0.23 - 2 * ph + y)
                fog *= k * (0.6 + 0.8 * cold)
                if fog > 0.75:
                    c = FOG2
                elif fog > 0.35:
                    c = FOG
            if y == GROUND:
                c = GROUND_C
            l = light(x, y)
            if l > 0.55:
                c = GLOW2
            elif l > 0.2 and y != GROUND:
                c = GLOW1
            f.set(x, y, c)


def draw_dem(f, x, y, t, tilt=0, reach=0):
    # костлявые руки тянутся вперёд из-под капюшона; reach — длина в пикселях
    for j, dy in enumerate((2, 3)):
        ln = reach - j
        for i in range(ln):
            ax = x + 1 - i
            ay = y + dy + (1 if i == ln - 1 and (t + j) % 4 < 2 else 0) * (1 if ln > 2 else 0)
            f.set(ax, ay, DEM_PAL["d"] if i == 0 else DEM_PAL["a"])
    for dy, row in enumerate(DEM):
        for dx, ch in enumerate(row):
            if ch != ".":
                f.set(x + dx, y + dy + (tilt if dx > 5 else 0), DEM_PAL[ch])
    # рваный шлейф — ленты вправо, волной
    for i, dy in enumerate((1, 2, 3, 4)):
        ln = 3 + round(1.5 + 1.5 * math.sin(i * 2.1 + t * 0.7))
        for k in range(ln):
            if (i + k + t // 2) % 4 == 3 and k > 0:
                continue
            wy = round(0.8 * math.sin(t * 0.8 - k * 0.9 + i))
            f.set(x + 12 + k, y + dy + wy + tilt, HEM if k else DEM_PAL["d"])


def draw_stag(f, x, y, phase, k):
    """k — доля проявившихся пикселей: олень собирается из искр."""
    rows = STAG[phase]
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != "." and ((dx * 7 + dy * 13) % 10) / 10 < k:
                f.set(x + dx, y + dy, CORE if ch == "W" else ANTLER)


def build():
    rnd = random.Random(7)
    stars = [(rnd.randrange(W), rnd.randrange(7), rnd.randrange(6)) for _ in range(12)]
    sparks = []
    frames = []
    for t in range(N):
        f = gen.Frame()

        # ---- дементор: x, y, наклон
        dem = None
        if t < T_BEAM:
            # летит без остановки, всё ближе и ниже — прямо на волшебника
            u = t / T_BEAM
            dem = (round(28 - 16 * u), round(4.5 * u ** 1.4 + 0.5 * math.sin(t * 0.4)), 0, round(1 + 4 * u))
        elif t < T_HIT:
            # свет с палочки отталкивает
            dem = (round(12 + 1.5 * (t - T_BEAM)), 4, 0, max(1, 5 - (t - T_BEAM)))
        else:
            k = t - T_HIT
            dem = (round(22 + 2 * k + 0.5 * k * k), round(4 - 0.8 * k - 0.15 * k * k), -min(2, k), 0)
        cold = 0.0
        if dem[0] < W:
            cold = max(0.0, min(1.0, (W - dem[0]) / 10))
        if t >= T_BEAM:
            cold *= max(0.0, 1 - (t - T_BEAM) / 10)

        # ---- олень
        stag = None
        if T_STAG <= t:
            if t < T_RUN:
                sx, sk = STAG_X, 0.35 + 0.65 * (t - T_STAG) / (T_RUN - T_STAG - 1)
            else:
                k = t - T_RUN
                sx, sk = round(STAG_X + 2 * k), 1.0
            if sx < W + 1:
                run = t >= T_RUN
                stag = (sx, 3 - (1 if run and t % 2 else 0), t % 2 if run else 0, min(1.0, sk))

        # ---- источники света
        lights = []
        if T_CAST + 1 <= t < T_BEAM:
            lights.append((TIP[0], TIP[1], 2.5, 0.6 + 0.4 * (t % 2)))
        if T_BEAM <= t < T_STAG + 1:
            lights.append((TIP[0], TIP[1], 3.5, 0.9))
        if stag:
            sx, sy, _, sk = stag
            lights.append((sx + 5, sy + 5, 5, 0.6 * sk))
        if T_HIT <= t < T_HIT + 3:
            lights.append((24, 6, 8, 1.0 - (t - T_HIT) / 3))

        def light(x, y):
            s = 0
            for lx, ly, r, a in lights:
                d = math.hypot(x - lx, (y - ly) * 1.3)
                if d < r:
                    s += a * (1 - d / r)
            return min(1.4, s)

        # звёзды на фоне неба
        background(f, t, cold, light)
        for sx_, sy_, ph in stars:
            if (t // 3 + ph) % 6 and cold < 0.5 and f.px[sy_][sx_] == SKY:
                f.set(sx_, sy_, (200, 210, 255))

        # ---- волшебник
        pose = "idle"
        if T_DRAW <= t < T_CAST or T_LOWER <= t < T_LOWER + 4:
            pose = "draw"
        elif T_CAST <= t < T_LOWER:
            pose = "cast"
        f.sprite(WIZ[pose], WIZ_X, WIZ_Y, pal=PAL)

        if dem:
            draw_dem(f, dem[0], dem[1], t, dem[2], dem[3])

        # ---- кончик палочки мерцает (луча нет)
        if T_CAST + 1 <= t < T_STAG + 2:
            f.set(TIP[0], TIP[1], CORE if t % 2 else (150, 200, 255))
        if T_BEAM <= t < T_STAG:
            for i in range(6):
                a = i * math.pi / 3 + t
                r = 1 + (t - T_BEAM) * 0.7
                f.set(round(TIP[0] + r * math.cos(a)), round(TIP[1] + r * math.sin(a) * 0.7), ANTLER)

        # ---- олень
        if stag:
            sx, sy, phase, sk = stag
            draw_stag(f, sx, sy, phase, sk)
            if t >= T_RUN:
                for _ in range(2):
                    sparks.append([sx + rnd.uniform(-1, 2), sy + rnd.uniform(3, 8), t])
        if T_HIT <= t < T_HIT + 2:
            for i in range(10):
                a = i * 2 * math.pi / 10
                f.set(round(24 + 3 * math.cos(a) * (t - T_HIT + 1)), round(6 + 2 * math.sin(a) * (t - T_HIT + 1)), ANTLER)

        # искры-следы патронуса
        for s in sparks:
            age = t - s[2]
            if 0 <= age < 12:
                s[1] += 0.12
                if (age + int(s[0])) % 3:
                    f.set(round(s[0]), round(s[1]), CORE if age < 6 else ANTLER)
        frames.append(f)
    gen.save("wizard_patronus", frames, MS)


if __name__ == "__main__":
    build()
