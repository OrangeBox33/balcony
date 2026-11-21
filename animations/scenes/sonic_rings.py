#!/usr/bin/env python3
"""Синий ёж бежит с горки, собирает кольца, в конце подпрыгивает клубком и улетает за экран."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H

# ---------------------------------------------------------------- мир

TOP_END = 22          # до этого x — ровная вершина
SLOPE_END = 84        # тут склон заканчивается
DROP = 36             # на сколько пикселей склон опускается
WORLD = 132           # длина мира
JUMP_AT = WORLD - W + 12   # отталкивается ровно там, где камера встаёт
SLOPE_TOP_SPEED = 1.5
FLAT_TOP_SPEED = 2.4  # внизу фон не едет по диагонали, поэтому нужно быстрее
FEET_ROW = 9          # на какой строке экрана держим ноги, пока камера едет


def smooth(a):
    a = min(max(a, 0.0), 1.0)
    return a * a * (3 - 2 * a)


def ground(wx):
    """Верх земли (мировой y) в столбце wx; больше — ниже."""
    return DROP * smooth((wx - TOP_END) / (SLOPE_END - TOP_END))


def slope(wx):
    return ground(wx + 0.5) - ground(wx - 0.5)


GRASS = (0, 210, 0)
GRASS_D = (0, 130, 20)
DIRT_A = (180, 85, 10)
DIRT_B = (110, 45, 0)
RING = (255, 200, 0)
RING_D = (170, 110, 0)
SPARK = (255, 255, 210)

# ---------------------------------------------------------------- ёж (лицом вправо, низ — ноги)

HOG_PAL = {
    "b": (0, 70, 255),
    "B": (90, 160, 255),     # блик на клубке
    "s": (255, 150, 80),     # мордочка и живот
    "W": (255, 255, 255),
    "r": (255, 0, 0),
}

HOG = {
    "stand": [
        "..bbb...",
        "bbbbbb..",
        ".bbbWWb.",
        "bbbbWsss",
        "..bbss..",
        "..Wsbb..",
        "..b..b..",
        ".rr.rr..",
    ],
    "tap": [
        "..bbb...",
        "bbbbbb..",
        ".bbbWWb.",
        "bbbbWsss",
        "..bbss..",
        "..Wsbb..",
        "..b..b..",
        ".rr..rr.",
    ],
    "run_a": [
        "...bbb..",
        ".bbbbbb.",
        "bbbbWWb.",
        ".bbbWsss",
        "..bbss..",
        ".bbsbW..",
        ".b...b..",
        "rr....rr",
    ],
    "run_b": [
        "...bbb..",
        ".bbbbbb.",
        "bbbbWWb.",
        ".bbbWsss",
        "..bbss..",
        "..Wsbb..",
        "...bb...",
        "..rrr...",
    ],
    # быстрый бег: ноги «колесом»
    "dash_a": [
        "....bbb.",
        "..bbbbbb",
        "bbbbbWWb",
        ".bbbbWss",
        "...bbs..",
        "..bbsbW.",
        "..rr.r..",
        ".r..rr..",
    ],
    "dash_b": [
        "....bbb.",
        "..bbbbbb",
        "bbbbbWWb",
        ".bbbbWss",
        "...bbs..",
        "..bbsbW.",
        "..r.rr..",
        ".rr..r..",
    ],
}

# клубок 6×6, блик крутится
BALL = [
    [
        ".bbbb.",
        "bBbbbb",
        "bbBbbb",
        "bbbBbb",
        "bbbbBb",
        ".bbbb.",
    ],
    [
        ".bbbb.",
        "bbbBbb",
        "bbbBbb",
        "bbBbbb",
        "bbBbbb",
        ".bbbb.",
    ],
    [
        ".bbbb.",
        "bbbbbb",
        "bBBbbb",
        "bbbBBb",
        "bbbbbb",
        ".bbbb.",
    ],
]
HOG_W = 8

# ---------------------------------------------------------------- кольца

RING_FULL = [".y.", "y.y", ".y."]
RING_EDGE = [".y.", ".y.", ".y."]


def ring_spots():
    spots = []
    for wx in range(30, 84, 5):                 # цепочка вдоль склона
        spots.append((wx, ground(wx) - 4))
    for wx in range(92, 114, 4):                # по ровному
        spots.append((wx, ground(wx) - 4))
    for wx, up in ((JUMP_AT + 7, 7), (JUMP_AT + 12, 9)):   # в воздухе на траектории прыжка
        spots.append((wx, ground(wx) - up))
    return spots


def draw_ring(f, x, y, t):
    rows = RING_EDGE if (t // 3 + x) % 4 == 3 else RING_FULL
    f.sprite(rows, x - 1, y - 1, pal={"y": RING})
    if (t // 3 + x) % 4 == 1:
        f.set(x, y - 1, (255, 255, 160))         # блеск


def draw_sparkle(f, x, y, age):
    r = 1 + age
    k = 1 - age / 4
    c = gen.scale(SPARK, max(k, 0.3))
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        f.set(x + dx * r, y + dy * r, c)
    if age < 2:
        f.set(x, y, gen.scale(RING, k))


def draw_counter(f, n):
    """Счётчик колец в левом верхнем углу, на чёрной подложке, чтобы не сливался со склоном."""
    w = gen.text_width(str(n), gen.FONT3)
    for y in range(6):
        for x in range(w + 1):
            f.set(x, y, gen.BLACK)
    f.text(str(n), 0, 0, (255, 230, 0), gen.FONT3)


# ---------------------------------------------------------------- земля

def draw_ground(f, cam_x, cam_y):
    for sx in range(W):
        wx = sx + cam_x
        top = ground(wx)
        y0 = round(top - cam_y)
        for sy in range(max(y0, 0), H):
            wy = sy + cam_y
            d = sy - y0
            if d == 0:
                c = GRASS_D if (wx * 7) % 5 == 0 else GRASS
            elif d == 1:
                c = GRASS_D
            else:
                c = DIRT_A if (int(wx) // 3 + int(round(wy)) // 3) % 2 == 0 else DIRT_B
            f.set(sx, sy, c)


# ---------------------------------------------------------------- сценарий


def build():
    frames, ms = [], []
    rings = {i: p for i, p in enumerate(ring_spots())}
    sparks = []        # [x, y, age] в мировых координатах
    st = {"n": 0}
    cam_x_max = WORLD - W

    def frame(hx, hy, sprite, t, dur, cam=None, trail=0):
        """hx — середина ежа по x, hy — его низ (мировые координаты)."""
        if cam is None:
            cam_x = min(max(hx - 12, 0), cam_x_max)
            cam_y = min(ground(cam_x + 12) - FEET_ROW, ground(WORLD) - (H - 3))
        else:
            cam_x, cam_y = cam
        cam_x, cam_y = round(cam_x), round(cam_y)
        f = gen.Frame()
        draw_ground(f, cam_x, cam_y)
        for (rx, ry) in rings.values():
            draw_ring(f, round(rx) - cam_x, round(ry) - cam_y, t)
        for s in sparks:
            draw_sparkle(f, round(s[0]) - cam_x, round(s[1]) - cam_y, s[2])
        if sprite is not None:
            rows = sprite
            x0 = round(hx - len(rows[0]) / 2) - cam_x
            y0 = round(hy) - len(rows) - cam_y
            # полосы скорости за спиной
            for i in range(trail):
                yy = y0 + 2 + i * 2
                for k in range(2 + i):
                    c = gen.scale((120, 170, 255), 0.7 - 0.2 * k)
                    f.set(x0 - 2 - k - i, yy, c)
            f.sprite(rows, x0, y0, pal=HOG_PAL)
        draw_counter(f, st["n"])
        frames.append(f)
        ms.append(dur)
        return cam_x, cam_y

    def collect(hx, hy):
        for i, (rx, ry) in list(rings.items()):
            if abs(rx - hx) <= 2.5 and hy - 8 <= ry <= hy:
                del rings[i]
                sparks.append([rx, ry, 0])
                st["n"] += 1

    def tick_sparks():
        for s in sparks:
            s[2] += 1
        sparks[:] = [s for s in sparks if s[2] < 4]

    t = 0
    hx = 12.0

    # 1. стоит на вершине, постукивает ногой
    for i in range(14):
        pose = "tap" if i in (4, 5, 9, 10) else "stand"
        frame(hx, ground(hx), HOG[pose], t, 110)
        t += 1

    # 2. разгоняется и бежит вниз
    v = 0.25
    step = 0.0
    while hx < JUMP_AT:
        if hx < SLOPE_END - 6:
            v = min(v + 0.03 + 0.25 * max(slope(hx), 0), SLOPE_TOP_SPEED)
        else:
            v = min(v + 0.12, FLAT_TOP_SPEED)
        hx += v
        step += v
        collect(hx, ground(hx))
        if v < 0.9:
            pose = "run_a" if int(step / 1.6) % 2 == 0 else "run_b"
        else:
            pose = "dash_a" if t % 2 == 0 else "dash_b"
        trail = 0 if v < 0.9 else (1 if v < 1.25 else (2 if v < 2 else 3))
        cam = frame(hx, ground(hx), HOG[pose], t, 60, trail=trail)
        tick_sparks()
        t += 1

    # 3. прыжок клубком: камера встаёт, ёж улетает вправо за край
    base = ground(hx)
    vx, vy = v, -1.5
    hy = base
    k = 0
    while True:
        hx += vx
        vy += 0.12
        hy += vy
        collect(hx, hy + 1)
        frame(hx, hy, BALL[k % 3], t, 60, cam=cam, trail=2)
        tick_sparks()
        t += 1
        k += 1
        if hx - 3 - cam[0] >= W:
            break

    # 4. пустая сцена: догорают искры, кольца ещё крутятся
    for i in range(14):
        frame(0, 0, None, t, 90, cam=cam)
        tick_sparks()
        t += 1

    gen.save("sonic_rings", frames, ms)


if __name__ == "__main__":
    build()
