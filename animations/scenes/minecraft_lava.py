#!/usr/bin/env python3
"""Майнкрафт, вид сбоку. Стив копает под себя: трава, земля, камень, ещё камень —
а под ним лава. Падает в неё, горит, мигает красным и исчезает облачком.
Затем экран плавно гаснет."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 65
B = 3                               # блок 3×3
SKY = 7                             # строки неба в мире
LAYERS = ["grass", "dirt", "stone", "stone"]
CAVE = SKY + B * len(LAYERS)        # строка воздуха над лавой
LAVA = CAVE + 1                     # поверхность лавы
WORLD_H = LAVA + 5
CAM_MAX = WORLD_H - H
COL = 12                            # шахта — колонки 12–14, по центру
POCKET = (6, 21)                    # карман лавы по x
HITS = {"grass": 3, "dirt": 3, "stone": 4}

SKY_C = (55, 145, 230)
CRACK = (255, 245, 215)             # трещины светлее блока — тёмные на диодах пропадают

STEVE = [
    "kkk",
    "kss",
    "ccc",
    "scc",
    "bbb",
    "b.b",
]
SPAL = {"k": (120, 75, 30), "s": (255, 150, 95), "c": (0, 200, 175), "b": (70, 40, 215)}
HURT = (255, 35, 25)
WOOD, IRON = (175, 110, 45), (235, 235, 250)
# кирка относительно левого верхнего угла Стива (смотрит вправо): (рукоять, головка)
PICK = {
    "up":   ([(3, 2), (3, 1), (3, 0)], [(2, -1), (3, -1), (4, -1)]),
    "mid":  ([(3, 3), (4, 3)], [(5, 2), (5, 3), (5, 4)]),
    "down": ([(3, 4), (3, 5)], [(2, 6), (3, 6), (4, 6)]),
}
CRACKS = [
    [],
    [(1, 1), (2, 0)],
    [(1, 1), (2, 0), (0, 2), (1, 2)],
    [(1, 1), (2, 0), (0, 2), (1, 2), (0, 0), (2, 1)],
]


def hsh(x, y, k=0):
    v = (x * 73856093) ^ (y * 19349663) ^ (k * 83492791)
    v = (v ^ (v >> 13)) * 1274126177
    return ((v >> 8) & 1023) / 1023


def kind_at(x, y):
    if y < SKY:
        return "sky"
    if y < CAVE:
        return LAYERS[(y - SKY) // B]
    if POCKET[0] <= x <= POCKET[1] and not (y == CAVE and x in POCKET):
        return "air" if y == CAVE else "lava"
    return "stone"


def lava_color(x, y, t):
    v = 0.5 + 0.5 * math.sin(x * 0.8 + y * 1.5 + t * 0.45 + hsh(x, y, 1) * 6.3)
    v = 0.6 * v + 0.4 * (0.5 + 0.5 * math.sin(x * 0.37 - t * 0.3 + y))
    if v > 0.8:
        return (255, 210, 50)
    if v > 0.55:
        return (255, 140, 10)
    return (235, 75, 0)


def block_color(x, y, kind, t):
    n = hsh(x, y)
    bx, by = x // B, (y - SKY) // B
    shade = (0.9, 1.0, 1.1)[int(hsh(bx, by, 5) * 2.999)]            # блоки чуть отличаются — видна сетка
    if kind == "grass":
        if (y - SKY) % B == 0:
            return (120, 230, 80) if n > 0.72 else (60, 185, 45)
        if (y - SKY) % B == 1 and n > 0.8:
            return (60, 185, 45)                     # трава свисает на землю
        kind = "dirt"
    if kind == "dirt":
        return gen.scale((200, 135, 70), shade) if n > 0.7 else gen.scale((150, 92, 42), shade)
    if kind == "stone":
        if (bx, by) == (2, 3) and n > 0.6:          # алмазная руда
            return (90, 240, 230)
        return gen.scale((165, 165, 175), shade) if n > 0.78 else gen.scale((120, 120, 130), shade)
    if kind == "lava":
        return lava_color(x, y, t)
    return (0, 0, 0)


def build():
    rnd = random.Random(11)
    fire_rnd = random.Random(5)
    frames = []
    dug = set()
    parts = []                      # [x, y, vx, vy, цвет, рождён, жизнь, гравитация]
    st = {"my": SKY - 6, "cam": 0.0, "crack": None, "t": 0}

    def crumbs(x, y, color_fn, n, up=1.0):
        for _ in range(n):
            parts.append([x + rnd.uniform(-1, 1), y, rnd.uniform(-0.8, 0.8), -rnd.uniform(0.5, 1.2) * up,
                          color_fn(), st["t"], rnd.randint(7, 11), 0.2])

    def puff(x, y, n, spread=1.5):
        for _ in range(n):
            parts.append([x + rnd.uniform(-spread, spread), y + rnd.uniform(-1, 1), rnd.uniform(-0.25, 0.25),
                          -rnd.uniform(0.2, 0.5), (205, 205, 215), st["t"], rnd.randint(9, 14), 0.0])

    def frame(pick=None, fire=0.0, hurt=False, steve=True, sink=0, dim=1.0, cam_target=None, ease=0.4):
        t = st["t"]
        for p in parts:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += p[7]
        if cam_target is None:
            cam_target = max(0, min(CAM_MAX, st["my"] - 2))
        st["cam"] += (cam_target - st["cam"]) * ease
        cam = round(st["cam"])
        f = gen.Frame()
        for sy in range(H):
            wy = sy + cam
            for x in range(W):
                k = kind_at(x, wy)
                if k == "sky":
                    c = SKY_C
                elif k in LAYERS and COL <= x < COL + B and (wy - SKY) // B in dug:
                    c = (0, 0, 0)
                else:
                    c = block_color(x, wy, k, t)
                f.set(x, sy, c)
        # квадратное солнце и облака
        for dx in range(2):
            for dy in range(2):
                f.set(23 + dx, 1 + dy - cam, (255, 225, 90))
        for cx, cy in ((3, 2), (4, 2), (5, 2), (6, 2), (4, 1), (5, 1), (15, 4), (16, 4), (17, 4), (16, 3)):
            f.set(cx, cy - cam, (215, 225, 245))
        # пузыри на лаве
        for bx, phase in ((8, 0), (18, 11), (11, 23), (20, 31)):
            q = (t + phase) % 36
            if q < 3:
                f.set(bx, LAVA - 1 - (q == 1) - cam, (255, 200, 40) if q < 2 else (255, 120, 0))
        if st["crack"]:
            row, stage = st["crack"]
            for dx, dy in CRACKS[stage]:
                f.set(COL + dx, SKY + row * B + dy - cam, CRACK)
        my = st["my"] - cam
        if steve:
            for dy, r in enumerate(STEVE):
                for dx, ch in enumerate(r):
                    if ch != ".":
                        f.set(COL + dx, my + sink + dy, HURT if hurt else SPAL[ch])
            if pick:
                handle, head = PICK[pick]
                for dx, dy in handle:
                    f.set(COL + dx, my + dy, WOOD)
                for dx, dy in head:
                    f.set(COL + dx, my + dy, IRON)
            # лава поверх утонувшей части
            for wy in range(LAVA, WORLD_H):
                for x in range(COL, COL + B + 1):
                    f.set(x, wy - cam, lava_color(x, wy, t))
            if fire > 0:
                top = my + sink
                for dx in range(-1, 4):
                    if fire_rnd.random() > fire:
                        continue
                    h = fire_rnd.randint(1, 3) if 0 <= dx <= 2 else fire_rnd.randint(0, 2)
                    y0 = top - h + (0 if 0 <= dx <= 2 else 3)
                    for yy in range(y0, LAVA - cam):
                        if 0 <= dx <= 2 and yy >= top and fire_rnd.random() < 0.6:
                            continue                         # тело местами видно сквозь огонь
                        c = (255, 245, 180) if yy == y0 else ((255, 200, 30) if yy < y0 + 2 else (255, 100, 0))
                        f.set(COL + dx, yy, c)
        for p in parts:
            age = t - p[5]
            if 0 <= age < p[6]:
                c = p[4]
                if p[7] == 0.0:                              # дым тает
                    c = gen.scale(c, 1 - 0.45 * age / p[6])
                f.set(round(p[0]), round(p[1]) - cam, c)
        if dim < 1.0:
            for y in range(H):
                for x in range(W):
                    r, g, b = f.px[y][x]
                    f.px[y][x] = tuple(int(v * dim) // 8 * 8 for v in (r, g, b))
        frames.append(f)
        st["t"] += 1

    # стоит, замахнулся
    for _ in range(4):
        frame(pick="up")

    for row, kind in enumerate(LAYERS):
        by = SKY + row * B
        hits = HITS[kind]
        for hit in range(1, hits + 1):
            frame(pick="up")
            frame(pick="mid")
            if hit < hits:
                st["crack"] = (row, min(3, hit))
                crumbs(COL + 2, by, lambda: block_color(COL + 1, by + 1, kind, 0), 1)
                frame(pick="down")
                frame(pick="down")
            else:
                st["crack"] = None
                dug.add(row)
                crumbs(COL + 1, by + 1, lambda: block_color(COL + rnd.randint(0, 2), by + rnd.randint(0, 2), kind, 0), 9)
                frame(pick="down")
        # проваливается на блок ниже (в лаву — дальше)
        drop = B if row < len(LAYERS) - 1 else B + 3
        for _ in range(drop):
            st["my"] += 1
            frame(pick="up")
        if row < len(LAYERS) - 1:
            frame(pick="up")

    # плюх: брызги лавы
    crumbs(COL + 1, LAVA - 1, lambda: (255, rnd.choice((120, 200)), 0), 8, up=1.3)
    # горит по колено в лаве, мигает красным (урон)
    for i in range(16):
        frame(fire=0.9, hurt=(i % 4) < 2, sink=(1 if i % 6 < 3 else 0))
        if i % 4 == 0:
            puff(COL + 1, st["my"] - 2 - (st["cam"] - round(st["cam"])), 1, 1)
    # тонет
    for i in range(9):
        frame(fire=0.75, hurt=(i % 4) < 2, sink=1 + i * 5 // 8)
    # исчез облачком
    puff(COL + 1, LAVA - 2, 10, 2.0)
    for _ in range(7):
        frame(steve=False)
    # затемнение: яркость на диодах ~ v^2.8, поэтому множитель L^(1/2.8) — гаснет равномерно на глаз
    n = 9
    for i in range(1, n + 1):
        frame(steve=False, dim=(1 - i / n) ** (1 / 2.8))
    gen.save("minecraft_lava", frames, MS)


if __name__ == "__main__":
    build()
