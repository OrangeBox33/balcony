#!/usr/bin/env python3
"""Голый человечек; справа лежит одежда. Вещи по одной подлетают и надеваются, он радуется,
потом одежда разлетается обратно на свои места — и всё сначала."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

X, Y = 3, 1   # левый верхний угол человечка (строка 0 остаётся под шляпу)

BODY = {
    "stand": [
        "..kkkk..",
        "..ssss..",
        "..ssss..",
        "...ss...",
        ".ssssss.",
        "s.ssss.s",
        "s.ssss.s",
        "s.ssss.s",
        "..ssss..",
        "..s..s..",
        "..s..s..",
        "..s..s..",
        ".ss..ss.",
    ],
    "cheer": [
        "..kkkk..",
        "s.ssss.s",
        "s.ssss.s",
        ".s.ss.s.",
        ".ssssss.",
        "..ssss..",
        "..ssss..",
        "..ssss..",
        "..ssss..",
        "..s..s..",
        "..s..s..",
        "..s..s..",
        ".ss..ss.",
    ],
}

# одежда в координатах человечка (строка -1 — над головой); по позам
ITEMS = {
    "pants": {"pal": {"b": (0, 80, 255)}, "stand": {8: "..bbbb..", 9: "..b..b..", 10: "..b..b..", 11: "..b..b.."}},
    "shirt": {"pal": {"r": (255, 0, 0), "y": (255, 200, 0)},
              "stand": {4: ".rrrrrr.", 5: "r.ryrr.r", 6: "r.rrrr.r", 7: "..ryrr.."},
              "cheer": {3: ".r....r.", 4: ".rrrrrr.", 5: "..ryrr..", 6: "..rrrr..", 7: "..ryrr.."}},
    "shoes": {"pal": {"w": (230, 230, 255)}, "stand": {12: ".ww..ww."}},
    "hat": {"pal": {"g": (0, 210, 0), "y": (255, 200, 0)}, "stand": {-1: "..gggg..", 0: ".gyyyyg."}},
}
ORDER = ["pants", "shirt", "shoes", "hat"]

# где ждёт каждая вещь (сдвиг относительно места на теле): рубашка и штаны висят
# на плечиках под штангой, шляпа лежит на табуретке, ботинки стоят на полу
HOME = {
    "shirt": (10, -3),
    "pants": (18, -7),
    "hat": (11, 9),
    "shoes": (18, 0),
}
RACK = (110, 110, 125)


def draw_rack(f):
    for x in range(12, gen.W):
        f.set(x, 0, RACK)                 # штанга
    for x in (16, 17, 24, 25):
        f.set(x, 1, RACK)                 # крючки плечиков
    for x in range(15, 21):
        f.set(x, 11, RACK)                # табуретка
    for y in (12, 13):
        f.set(15, y, RACK)
        f.set(20, y, RACK)


SPARK = [".W.", "WyW", ".W."]


def ease(k):
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, k)))


def build():
    frames = []
    worn = set()
    st = {"pose": "stand"}

    def draw(flying=(), sparks=()):
        """flying: [(item, dx, dy)] — вещи в полёте/на полке."""
        f = gen.Frame()
        draw_rack(f)
        pose = st["pose"]
        y0 = Y
        f.sprite(BODY[pose], X, y0)
        for name in ORDER:
            if name in worn:
                it = ITEMS[name]
                rows = it.get(pose, it["stand"])
                for r, line in rows.items():
                    f.sprite([line], X, y0 + r, pal=it["pal"])
        for name in ORDER:
            if name not in worn and name not in [n for n, _, _ in flying]:
                dx, dy = HOME[name]
                it = ITEMS[name]
                for r, line in it["stand"].items():
                    f.sprite([line], X + dx, Y + r + dy, pal=it["pal"])
        for name, dx, dy in flying:
            it = ITEMS[name]
            for r, line in it["stand"].items():
                f.sprite([line], X + round(dx), Y + r + round(dy), pal=it["pal"])
        for sx, sy in sparks:
            f.sprite(SPARK, sx - 1, sy - 1)
        frames.append(f)

    def hold(n, **kw):
        for _ in range(n):
            draw(**kw)

    # центр каждой вещи на теле — туда вспышки
    def anchor(name):
        rows = ITEMS[name]["stand"]
        ys = list(rows)
        return X + 4, Y + (min(ys) + max(ys)) // 2

    hold(10)
    for name in ORDER:
        hx, hy = HOME[name]
        STEPS = 10
        for i in range(1, STEPS + 1):
            k = ease(i / STEPS)
            lift = -2 * math.sin(math.pi * i / STEPS)   # летит дугой
            draw(flying=[(name, hx * (1 - k), hy * (1 - k) + lift)])
        worn.add(name)
        ax, ay = anchor(name)
        hold(2, sparks=[(ax - 4, ay), (ax + 4, ay)])
        hold(7)

    # радуется: машет руками вверх-вниз (прыжка нет — шляпа упирается в верх экрана)
    for rep in range(3):
        st["pose"] = "cheer"
        hold(5, sparks=[(X - 1, 1), (X + 9, 1)] if rep % 2 == 0 else [(X - 1, 5), (X + 9, 5)])
        st["pose"] = "stand"
        hold(4)
    hold(6)

    # одежда разлетается обратно на свои места
    worn.clear()
    STEPS = 8
    for i in range(0, STEPS + 1):
        k = ease(i / STEPS)
        lift = -2 * math.sin(math.pi * i / STEPS)
        draw(flying=[(n, HOME[n][0] * k, HOME[n][1] * k + lift) for n in ORDER])
    hold(6)

    gen.save("dress_up", frames, 90)


if __name__ == "__main__":
    build()
