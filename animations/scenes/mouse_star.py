#!/usr/bin/env python3
"""Маленькая серая мышка бежит по вечерней земле, на неё падает звезда —
вспышка, и из неё выходит чёрный мультяшный мышонок с огромными круглыми ушами,
в красных шортах с белыми пуговицами, жёлтых ботинках и белых перчатках. «Та-да» и подмигивание."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 70
GROUND = H - 1

PAL = {
    "x": (150, 150, 168),     # серая мышка
    "X": (205, 205, 220),     # светлое брюшко/голова
    "P": (255, 120, 160),     # розовое ухо / нос
    "K": (255, 255, 255),     # глаз-бусинка (светлый — тёмный пропадёт)
    "b": (0, 0, 0),           # чёрная шерсть мышонка (силуэт на фиолетовом фоне)
    "f": (255, 200, 140),     # лицо
    "W": (255, 255, 255),     # белки глаз
    "e": (0, 0, 0),           # зрачки
    "n": (0, 0, 0),           # нос
    "r": (255, 30, 30),       # рот и красные шорты
    "G": (255, 255, 255),     # белые перчатки
    "Y": (255, 210, 0),       # жёлтые ботинки
}

# ---------------------------------------------------------------- маленькая мышка (бок, лицом вправо)
SMALL = [
    "....PP..",
    ".xxxxxxK",
    "xxxxxxXXP",
]
SMALL_LEGS = [".x...x..", "..x.x..."]
TAIL = (205, 140, 160)

# ---------------------------------------------------------------- мышонок-герой (анфас, 13×14)
HERO = [
    ".bbb.....bbb.",
    "bbbbb...bbbbb",
    "bbbbb...bbbbb",
    ".bbbbbbbbbbb.",
    "..bbffbffbb..",
    "..bfWfffWfb..",
    "..bfefnfefb..",
    "...bfrrrfb...",
    "....bfffb....",
    "...bbbbbbb...",
    "...rrrrrrr...",
    "...rWrrrWr...",
    "....b...b....",
    "..YYYY.YYYY..",
]
HW = len(HERO[0])
# подмигивание: правый для нас глаз закрыт чёрточкой
WINK = {(8, 5): "f", (8, 6): "b", (9, 6): "b"}


def background(f, t):
    for y in range(H):
        k = y / (H - 1)
        c = (int(40 + 30 * k), int(20 + 15 * k), int(110 + 40 * k))
        for x in range(W):
            f.set(x, y, c)
    for x in range(W):
        f.set(x, GROUND, (95, 55, 150))
    # мерцающие звёздочки на небе (периодично по t)
    for i, (sx, sy, ph) in enumerate(STARS):
        v = 0.5 + 0.5 * math.sin(2 * math.pi * (t / 28 + ph))
        f.set(sx, sy, tuple(min(255, int(a + (b - a) * v)) for a, b in zip(f.px[sy][sx], (210, 210, 255))))


rnd = random.Random(7)
STARS = [(rnd.randrange(W), rnd.randrange(0, 6), rnd.random()) for _ in range(7)]


def small_mouse(f, x, t, run=True):
    y = GROUND - 4
    f.sprite(SMALL, x, y, pal=PAL)
    f.sprite([SMALL_LEGS[(t // 2) % 2 if run else 0]], x, y + 3, pal=PAL)
    # тонкий хвост волной
    for i in range(1, 6):
        ty = y + 2 + (0 if i < 2 else round(-math.sin(i * 0.9 + t * 0.6) * 1.0) - (i > 3))
        f.set(x - i, ty, TAIL)


def hero(f, x, y, wink=False, arms_up=False):
    f.sprite(HERO, x, y, pal=PAL)
    if wink:
        for (dx, dy), ch in WINK.items():
            f.set(x + dx, y + dy, PAL[ch])
    # руки
    hand, fur = PAL["G"], PAL["b"]
    if arms_up:
        for side, sx in ((-1, x + 2), (1, x + HW - 3)):
            f.set(sx + side, y + 9, fur)
            f.set(sx + 2 * side, y + 8, fur)
            f.set(sx + 2 * side, y + 7, hand)
    else:
        for sx in (x + 2, x + HW - 3):
            f.set(sx, y + 9, fur)
            f.set(sx, y + 10, fur)
            f.set(sx, y + 11, hand)
    # хвост справа
    for i, (dx, dy) in enumerate(((HW - 3, 12), (HW - 2, 12), (HW - 1, 11), (HW, 10), (HW, 9))):
        f.set(x + dx + 1, y + dy, fur)


def star(f, cx, cy, c=(255, 230, 80), core=(255, 255, 220)):
    cx, cy = round(cx), round(cy)
    for dx, dy in ((0, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)):
        f.set(cx + dx, cy + dy, c)
    f.set(cx, cy, core)


def build():
    frames, ms = [], []
    MX = 10                        # где мышка остановится (центр ≈ 14)
    HX = (W - HW - 2) // 2         # герой + хвост (2 px справа) по центру
    HY = 0
    T_RUN, T_STOP, T_FALL, T_FLASH = 26, 6, 12, 9
    t = 0

    def push(f, d=MS):
        frames.append(f)
        ms.append(d)

    # 1) бежит слева
    for k in range(T_RUN):
        f = gen.Frame(); background(f, t)
        small_mouse(f, round(-9 + (MX + 9) * k / (T_RUN - 1)), t)
        push(f); t += 1
    # 2) остановилась, принюхивается; сверху летит звезда
    sx0, sy0 = 25, -2
    tx, ty = MX + 5, GROUND - 5
    trail = []
    for k in range(T_STOP + T_FALL):
        f = gen.Frame(); background(f, t)
        small_mouse(f, MX, 0, run=False)
        if (k // 2) % 2:            # дёргает носом
            f.set(MX + 8, GROUND - 2, PAL["X"])
        if k >= T_STOP:
            p = (k - T_STOP + 1) / T_FALL
            p = p * p
            cx, cy = sx0 + (tx - sx0) * p, sy0 + (ty - sy0) * p
            # сплошной хвост кометы: от звезды назад по траектории, гаснет
            pts = [(cx, cy)] + list(reversed(trail[-4:]))
            seg = 0
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                n = max(1, round(math.hypot(bx - ax, by - ay)))
                for q in range(1, n + 1):
                    seg += 1
                    f.add(round(ax + (bx - ax) * q / n), round(ay + (by - ay) * q / n),
                          gen.scale((255, 190, 60), max(0, 0.95 - 0.09 * seg)))
            star(f, cx, cy)
            trail.append((cx, cy))
        push(f); t += 1
    # 3) вспышка: светлый диск растёт и гаснет, под ним проявляется герой
    ccx, ccy = tx, ty
    for k in range(T_FLASH):
        f = gen.Frame(); background(f, t)
        if k >= 4:
            hero(f, HX, HY)
        else:
            small_mouse(f, MX, 0, run=False)
        r = [2, 5, 8, 11, 13, 15, 17, 19, 21][k]
        a = [1.0, 1.0, 1.0, 1.0, 0.75, 0.5, 0.3, 0.15, 0.05][k]
        for y in range(H):
            for x in range(W):
                d = math.hypot(x - ccx, (y - ccy) * 1.3)
                if d < r:
                    kk = a * (1 - 0.5 * d / r)
                    o = f.px[y][x]
                    f.set(x, y, tuple(int(c0 + (255 - c0) * kk) for c0 in o))
        push(f); t += 1
    # 4) «та-да»: руки вверх, искры разлетаются; потом руки вниз с подскоком
    rays = [(math.cos(i * math.pi / 4 + 0.3), math.sin(i * math.pi / 4 + 0.3)) for i in range(8)]
    for k in range(12):
        f = gen.Frame(); background(f, t)
        hero(f, HX, HY - (1 if k in (1, 2, 3) else 0), arms_up=True)
        rr = 5 + k * 1.3
        for i, (dx, dy) in enumerate(rays):
            px, py = round(ccx - 1 + dx * rr * 1.4), round(7 + dy * rr)
            col = [(255, 230, 80), (255, 255, 255), (120, 220, 255)][i % 3]
            f.add(px, py, gen.scale(col, max(0, 1 - k / 12)))
        push(f); t += 1
    for k in range(8):
        f = gen.Frame(); background(f, t)
        hero(f, HX, HY + (0 if k % 4 < 2 else 0))
        push(f); t += 1
    # 5) подмигивает: глаз закрывается, рядом блестит искорка
    for k in range(16):
        f = gen.Frame(); background(f, t)
        w = 2 <= k <= 11
        hero(f, HX, HY, wink=w)
        if 3 <= k <= 10:
            s = [0.4, 0.8, 1.0, 1.0, 0.8, 0.6, 0.4, 0.2][k - 3]
            ex, ey = HX + HW + 1, HY + 4
            f.add(ex, ey, gen.scale((255, 255, 200), s))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                f.add(ex + dx, ey + dy, gen.scale((255, 220, 80), s * 0.7))
        push(f); t += 1
    # 6) стоит, улыбается, затем «пуф» — звёздная пыль, и снова пусто (для петли)
    for k in range(8):
        f = gen.Frame(); background(f, t)
        hero(f, HX, HY)
        push(f); t += 1
    rng = random.Random(3)
    dust = [(HX + rng.random() * HW, rng.random() * 13, rng.uniform(-0.3, 0.3), rng.uniform(-0.6, -0.1))
            for _ in range(26)]
    for k in range(8):
        f = gen.Frame(); background(f, t)
        if k < 2:
            hero(f, HX, HY)
        for (x0, y0, vx, vy) in dust:
            x, y = x0 + vx * k * 1.5, y0 + vy * k * 1.5
            if k >= 1:
                f.add(round(x), round(y), gen.scale((255, 220, 120), max(0, 1 - k / 8)))
        push(f); t += 1
    for k in range(4):
        f = gen.Frame(); background(f, t)
        push(f); t += 1
    gen.save("mouse_star", frames, ms)


if __name__ == "__main__":
    build()
