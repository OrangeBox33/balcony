#!/usr/bin/env python3
"""Конфетный снегопад: вместо снежинок медленно падают и кувыркаются конфеты —
мини-тросточки, круглые леденцы-спиральки и фантики «бантиком». Внизу они
ложатся горкой и тают в искры. Петля без шва: расписание конфет повторяется
каждые N кадров, а прогон начинается за две петли до записываемой."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
N = 160                 # кадров в петле
MS = 70
FLOOR = 13              # нижняя строка
LIE = 34                # сколько кадров конфета лежит
MELT = 16               # сколько кадров тает в искры

R = (255, 0, 20)
WH = (255, 255, 255)

# мини-тросточка 3×5
CANE = [
    "RWR",
    "W.W",
    "R..",
    "W..",
    "R..",
]
# фантик-бантик 5×3: хвостики по бокам, конфета в середине
WRAP = [
    "t.c.t",
    "tcLct",
    "t.c.t",
]


def rot(rows):
    """Поворот спрайта на 90° по часовой."""
    h, w = len(rows), len(rows[0])
    return ["".join(rows[h - 1 - y][x] for y in range(h)) for x in range(w)]


def rots(rows, n):
    out = [rows]
    for _ in range(n - 1):
        out.append(rot(out[-1]))
    return out


CANE_R = rots(CANE, 4)
WRAP_R = [WRAP, rot(WRAP)]
RING = [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2), (0, 1)]   # по кругу

WRAP_COLORS = [  # (конфета, хвостики, блик)
    ((160, 0, 255), (255, 200, 0), (255, 170, 255)),
    ((0, 190, 70), (255, 60, 150), (190, 255, 190)),
    ((0, 110, 255), (255, 230, 0), (170, 210, 255)),
]
LOLLY_COLORS = [(255, 0, 140), (0, 200, 60), (255, 120, 0), (0, 150, 255)]


def candy_rows(c, phase):
    """Спрайт и палитра конфеты c в фазе кувырка phase."""
    if c["kind"] == "cane":
        return CANE_R[phase % 4], {"R": R, "W": WH}
    if c["kind"] == "wrap":
        body, tail, hi = c["col"]
        return WRAP_R[phase % 2], {"c": body, "t": tail, "L": hi}
    # леденец-спиралька: кольцо цвет/цвет/белый крутится, центр светлый
    rows = [list("...") for _ in range(3)]
    pal = {"a": c["col"], "b": WH, "o": (255, 240, 170)}
    for i, (x, y) in enumerate(RING):
        rows[y][x] = "b" if (i + phase) % 4 == 0 else "a"
    rows[1][1] = "o"
    return ["".join(r) for r in rows], pal


def make_candies():
    rnd = random.Random(31)
    kinds = ["cane", "lolly", "wrap", "lolly", "cane", "wrap", "lolly", "cane", "wrap"]
    xs = [2, 19, 9, 24, 14, 4, 11, 21, 16]
    out = []
    for i, kind in enumerate(kinds):
        c = {"kind": kind, "t0": round(i * N / len(kinds)) + rnd.randint(-3, 3),
             "x": xs[i] + rnd.uniform(-0.6, 0.6),
             "v": rnd.uniform(0.16, 0.26),
             "spin": rnd.choice((5, 6, 7, 8)),
             "dir": rnd.choice((1, -1)),
             "sway": rnd.uniform(0, 6.28)}
        if kind == "wrap":
            c["col"] = WRAP_COLORS[i // 3 % 3]
        elif kind == "lolly":
            c["col"] = LOLLY_COLORS[i % len(LOLLY_COLORS)]
        out.append(c)
    return out


def sprite_size(rows):
    return len(rows[0]), len(rows)


def draw_candy(f, c, age):
    """Возвращает False, если конфета уже растаяла."""
    # падает, пока нижний край не коснётся пола
    land = 0
    while True:
        rows, _ = candy_rows(c, (land // c["spin"]) * c["dir"])
        if -4 + land * c["v"] >= FLOOR + 1 - len(rows):
            break
        land += 1
    x = c["x"] + 0.8 * math.sin(c["sway"] + age * 0.12)
    if age < land:
        phase = (age // c["spin"]) * c["dir"]
        rows, pal = candy_rows(c, phase)
        w, h = sprite_size(rows)
        y = -4 + age * c["v"]
        f.sprite(rows, round(x - w / 2), round(y), pal=pal)
        return True
    # лежит в «горке»: в спокойной позе, по низу
    rest_phase = 0 if c["kind"] != "cane" else 1
    rows, pal = candy_rows(c, rest_phase if c["kind"] != "lolly" else (land // c["spin"]))
    w, h = sprite_size(rows)
    xl = c["x"] + 0.8 * math.sin(c["sway"] + land * 0.12)
    px0, py0 = round(xl - w / 2), FLOOR + 1 - h
    lie = age - land
    if lie < LIE:
        f.sprite(rows, px0, py0, pal=pal)
        return True
    m = lie - LIE
    if m >= MELT:
        return False
    # тает: пиксели по очереди вспыхивают искоркой, она взлетает и гаснет
    p = {**gen.PAL, **pal}
    k = 0
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch == ".":
                continue
            k += 1
            start = (k * 5) % 9                 # когда этот пиксель «вспыхнет»
            if m < start:
                f.set(px0 + dx, py0 + dy, p[ch])
                continue
            a = m - start
            if a > 6 or k % 2:                  # искрит только каждый второй
                continue
            br = 1 - a / 7
            spark = (255, 250, 210) if a % 2 == 0 else (255, 200, 60)
            f.add(px0 + dx, py0 + dy - a // 2, gen.scale(spark, 0.4 + 0.6 * br))
    return True


def render(t, candies):
    f = gen.Frame()
    for c in candies:
        # конфета повторяется каждые N кадров — рисуем все её «копии», что ещё живы
        for k in range(0, 3):
            age = t - (c["t0"] + (t // N - k) * N)
            if age >= 0:
                draw_candy(f, c, age)
    return f


def build():
    candies = make_candies()
    frames = [render(t + 2 * N, candies) for t in range(N)]
    # проверка шва: кадр после последнего совпадает с первым
    nxt = render(3 * N, candies)
    assert nxt.px == frames[0].px, "петля со швом"
    gen.save("candy_snow", frames, MS)


if __name__ == "__main__":
    build()
