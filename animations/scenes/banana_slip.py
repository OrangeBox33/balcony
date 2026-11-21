#!/usr/bin/env python3
"""Человек идёт, поскальзывается на банановой кожуре и падает."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
FLOOR_Y = H - 1
MANPAL = {"c": (0, 190, 255), "b": (40, 60, 255)}

# человек в профиль, лицом вправо; низ спрайта стоит на полу
MAN = {
    "walk_a": [
        "..kkk...",
        "..ssss..",
        "..sss...",
        "...s....",
        "..ccc...",
        ".ccccc..",
        "s.ccc.s.",
        "..ccc...",
        "..bbb...",
        ".bb.bb..",
        ".b...b..",
        "xx...xx.",
    ],
    "walk_b": [
        "..kkk...",
        "..ssss..",
        "..sss...",
        "...s....",
        "..ccc...",
        "..ccc...",
        "..csc...",
        "..ccc...",
        "..bbb...",
        "..bb....",
        "..bb....",
        "..xxx...",
    ],
    # нога уехала вперёд-вверх, корпус откинут назад, руки вверх
    "oops": [
        "s.........",
        ".s.kkk....",
        "..ssss..s.",
        "...sss.s..",
        "....ccc...",
        "....ccc...",
        "....ccc...",
        "....bbbbbx",
        "....b...bx",
        "....b.....",
        "....b.....",
        "...xx.....",
    ],
    # в воздухе горизонтально: голова слева, ноги задраны вправо
    "air": [
        "..s.s.......xx",
        "..s.s......bbx",
        "kss.cccc.bbb..",
        "kssscccccbb...",
        "kss...........",
    ],
    # лежит на спине
    "down": [
        "..s..........x.",
        "kssscccccbbbbx.",
        "kss.ccccc.bbbx.",
    ],
    # сел и держится за голову
    "sit": [
        ".kkks...",
        ".sssss..",
        ".ssss...",
        "..ccc...",
        "..ccc...",
        "..cccbbbx",
        "..bbbbbbx",
    ],
}

# кожура: хвостик сверху, три «лепестка» свисают в стороны
PEEL = [
    "..n..",
    ".yyy.",
    "yy.yy",
    "y...y",
]
PEEL_PAL = {"y": (255, 220, 0), "n": (150, 70, 0)}
PEEL_X = 13          # где лежит кожура (левый край)


def draw_peel(f, x, y):
    """y — нижняя строка кожуры."""
    f.sprite(PEEL, round(x), round(y) - len(PEEL) + 1, pal=PEEL_PAL)


STAR_COLS = [(255, 230, 0), (255, 255, 255), (0, 220, 255)]


def build():
    frames, ms = [], []
    st = {"pose": None, "x": 0, "y": None, "peel": (PEEL_X, FLOOR_Y - 1)}

    def frame(dur=100, extra=None, shake=0):
        f = gen.Frame()
        for x in range(W):
            f.set(x, FLOOR_Y, (110, 90, 70))
        if st["peel"] is not None:
            draw_peel(f, *st["peel"])
        if st["pose"]:
            rows = MAN[st["pose"]]
            y = st["y"] if st["y"] is not None else FLOOR_Y - len(rows)
            f.sprite(rows, st["x"], y + shake, pal=MANPAL)
        if extra:
            extra(f, len(frames))
        frames.append(f)
        ms.append(dur)

    # 0. кожура прилетает сверху (кто-то выбросил) и шлёпается на пол
    st["peel"] = None
    for i in range(3):
        frame(120)
    for y in (0, 3, 7, 10, 12, 11, 12):
        st["peel"] = (PEEL_X, y)
        frame(70)
    st["peel"] = (PEEL_X, FLOOR_Y - 1)
    frame(200)

    # 1. человек идёт слева
    st["x"] = -8
    step = 0
    while st["x"] < PEEL_X - 4:
        st["pose"] = "walk_a" if (step // 2) % 2 == 0 else "walk_b"
        frame(110)
        st["x"] += 1
        step += 1
    # наступил на кожуру
    st["pose"] = "walk_a"
    frame(250)

    # 2. «ой!» — нога уезжает вперёд, кожура летит вправо
    def bang(f, t):
        # «!» над головой
        for yy in (0, 1, 2):
            f.set(st["x"] + 10, yy, (255, 40, 0))
        f.set(st["x"] + 10, 4, (255, 40, 0))

    st["pose"] = "oops"
    st["y"] = FLOOR_Y - 12
    for i in range(5):
        st["peel"] = (PEEL_X + 3 + i * 3, FLOOR_Y - 1)
        frame(90, extra=bang)

    # 3. полёт горизонтально
    st["pose"] = "air"
    st["peel"] = None
    for y, dx in ((5, 0), (4, 0), (4, 1), (5, 0), (7, 0)):
        st["y"] = y
        st["x"] += dx

        def lines(f, t):
            # штрихи движения под телом
            for xx in range(st["x"] + 3, st["x"] + 10, 3):
                f.set(xx, st["y"] + 6, (120, 120, 140))
        frame(100, extra=lines)

    # 4. бух! лежит на спине
    st["pose"] = "down"
    st["y"] = FLOOR_Y - 3
    hx = st["x"]

    def dust(f, t):
        for dx in (-2, -1, 16, 17):
            f.set(hx + dx, FLOOR_Y - 1, (200, 200, 200))
        f.set(hx - 2, FLOOR_Y - 2, (150, 150, 150))
        f.set(hx + 17, FLOOR_Y - 2, (150, 150, 150))

    frame(80, extra=dust, shake=-1)
    frame(80, extra=dust)
    frame(120, extra=dust)

    # звёздочки кружат над головой
    star_c = {"c": (hx + 2, FLOOR_Y - 6)}

    def stars(f, t):
        cx, cy = star_c["c"]
        for k in range(3):
            a = t * 0.55 + k * 2 * math.pi / 3
            x = cx + round(math.cos(a) * 3.2)
            y = cy + round(math.sin(a) * 1.4)
            c = STAR_COLS[k]
            f.set(x, y, c)
            if (t + k) % 2 == 0:
                for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    f.add(x + ddx, y + ddy, gen.scale(c, 0.55))

    for i in range(24):
        frame(100, extra=stars)

    # 5. сел, держится за голову
    st["pose"] = "sit"
    st["y"] = None
    st["x"] = hx + 1
    star_c["c"] = (hx + 3, 3)
    for i in range(10):
        frame(100, extra=stars if i < 6 else None)
    # 6. встал и ушёл вправо
    st["pose"] = "walk_b"
    st["x"] = hx + 2
    frame(300)
    step = 0
    while st["x"] < W:
        st["pose"] = "walk_a" if (step // 2) % 2 == 0 else "walk_b"
        frame(110)
        st["x"] += 1
        step += 1
    gen.save("banana_slip", frames, ms)


if __name__ == "__main__":
    build()
