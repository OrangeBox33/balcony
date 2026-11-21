#!/usr/bin/env python3
"""Кот гонится за мышонком, тот юркает в норку, кот с размаху врезается в стену — «ТЫДЫЩ»."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
FLOOR_Y = H - 1          # строка пола
WALL_X = 23              # левый край стены
HOLE_X = WALL_X          # левый край норки

FLOOR = (120, 75, 40)
WALL = (165, 110, 60)
WALL_LIGHT = (210, 160, 100)
BASE = (235, 225, 205)
BLACK = (0, 0, 0)

CAT_C = (100, 125, 185)
CAT_PAL = {
    "c": CAT_C,
    "t": CAT_C,
    "W": (240, 240, 250),
    "Y": (190, 255, 60),    # глаз
    "n": (255, 110, 150),   # нос
    "o": (255, 255, 255),   # выпученный глаз
}
MOUSE_PAL = {
    "m": (175, 95, 35),
    "E": (255, 130, 160),
    "t": (230, 150, 150),
    "W": (255, 255, 255),
    "n": (255, 90, 130),
    "K": (0, 0, 0),
}

# кот смотрит вправо, низ спрайта стоит на полу; нос — в последнем столбце
CAT = {
    # галоп: лапы вытянуты вперёд и назад
    "run_a": [
        "...........c..c..",
        "tt.........cccc..",
        "..t........ccYcc.",
        "...cccccccccccWWn",
        "..cccccccccccWW..",
        "..ccWWWWWWWcc....",
        ".cc.........cc...",
        "WW............WW.",
    ],
    # галоп: лапы собраны под телом
    "run_b": [
        ".................",
        "...........c..c..",
        "t..........cccc..",
        ".tt........ccYcc.",
        "...tccccccccccWWn",
        "...cccccccccccWW.",
        "....ccWWWWWcc....",
        ".....WW...WW.....",
    ],
    # тормозит: откинулся назад, передние лапы упёрты вперёд, глаз выпучен
    "skid": [
        "..........c..c...",
        "t.........cccc...",
        ".t........cocc...",
        "..ccccccccccccWWn",
        "..cccccccccccWW..",
        "..ccWWWWWWcccc...",
        "...cc.......ccc..",
        "...WW.........WWW",
    ],
}

# расплющен об стену: морда вжата в стену справа, лапы растопырены
SPLAT = [
    ".c...",
    "..cc.",
    "W.ccW",
    ".Wcc.",
    "tccc.",
    "t.cc.",
    ".Wcc.",
    "W.ccW",
]
# сполз и осел
SLUMP = [
    "......c.c.",
    "......cccc",
    "t...cccccc",
    ".tcccccccc",
    "..WWccccWW",
]
# лежит блином у стены
FLAT = [
    "...........c.c",
    "tt.........coc",
    "..cccccccccccc",
    ".WW.WWcccc.WWW",
]

MOUSE = {
    "a": [
        "....EE.",
        "tt.mmmW",
        "..m.mmn",
    ],
    "b": [
        "....EE.",
        ".tmmmmW",
        "t..mmmn",
    ],
}
# мордочка из норки (смотрит влево); левый верх — (HOLE_X + dx, FLOOR_Y - 4)
MOUSE_PEEK = {
    "edge": [".EE", "EWm", "nmm", ".mm"],          # только высунул нос
    "out_a": [".EE..", "EEmm.", "mKmm.", "nmmmm"],  # голова снаружи
    "out_b": ["..EE.", ".EEm.", "mKmm.", "nmmmm"],  # ушки шевелятся
}

STAR_COLS = [(255, 230, 0), (255, 255, 255), (0, 220, 255)]


def draw_floor(f):
    for x in range(W):
        f.set(x, FLOOR_Y, FLOOR)


def draw_wall(f, flash=False):
    for y in range(FLOOR_Y):
        for x in range(WALL_X, W):
            c = WALL_LIGHT if x == WALL_X + 2 else WALL
            if y >= FLOOR_Y - 2:
                c = BASE
            if flash:
                c = tuple(min(255, v + 50) for v in c)
            f.set(x, y, c)
    f.set(HOLE_X + 1, FLOOR_Y - 4, BLACK)
    for y in (FLOOR_Y - 3, FLOOR_Y - 2, FLOOR_Y - 1):
        for x in range(HOLE_X, HOLE_X + 3):
            f.set(x, y, BLACK)


def rays(f, cx, cy, r0, r1, color):
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        for r in range(r0, r1 + 1):
            f.set(cx + round(math.cos(a) * r), cy + round(math.sin(a) * r * 0.8), color)


def shifted(f, dx, dy):
    g = gen.Frame()
    for y in range(H):
        for x in range(W):
            g.set(x + dx, y + dy, f.px[y][x])
    return g


def cat_sprite(f, rows, x):
    f.sprite(rows, round(x), FLOOR_Y - len(rows), pal=CAT_PAL)


def stars(f, t, cx, cy):
    for k in range(3):
        a = t * 0.6 + k * 2 * math.pi / 3
        x = cx + round(math.cos(a) * 3.2)
        y = cy + round(math.sin(a) * 1.3)
        c = STAR_COLS[k]
        f.set(x, y, c)
        if (t + k) % 2 == 0:
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                f.add(x + ddx, y + ddy, gen.scale(c, 0.55))


def outlined_text(f, word, x, y, color):
    """Текст с чёрной обводкой — чтобы читался поверх стены."""
    tmp = gen.Frame()
    tmp.text(word, x, y, color, gen.FONT5)
    lit = [(xx, yy) for yy in range(H) for xx in range(W) if tmp.px[yy][xx] != BLACK]
    for xx, yy in lit:
        for ddx in (-1, 0, 1):
            for ddy in (-1, 0, 1):
                f.set(xx + ddx, yy + ddy, BLACK)
    for xx, yy in lit:
        f.set(xx, yy, tmp.px[yy][xx])


def build():
    frames, ms = [], []

    def push(f, d=70):
        frames.append(f)
        ms.append(d)

    # ---------------- 1. погоня
    CW = len(CAT["run_a"][0])
    mx = -3.0
    nose = -9.0          # x носа кота
    dust = []             # [x, age]
    t = 0
    skid = 0
    while True:
        f = gen.Frame()
        draw_floor(f)
        if mx < W:
            f.sprite(MOUSE["a" if t % 2 == 0 else "b"], round(mx), FLOOR_Y - 3, pal=MOUSE_PAL)
            # штрихи за мышонком
            if mx > -3:
                f.set(round(mx) - 2 - t % 2, FLOOR_Y - 2, (110, 110, 120))
        draw_wall(f)
        cx = round(nose) - CW + 1
        if skid:
            pose = "skid"
        else:
            pose = "run_a" if (t // 2) % 2 == 0 else "run_b"
        # линии скорости позади кота
        for k, yy in enumerate((FLOOR_Y - 5, FLOOR_Y - 3)):
            off = (t + 2 * k) % 3
            for x in range(cx - 2 - off - 4, cx - 2 - off):
                f.set(x, yy, (190, 200, 230))
            f.set(cx - 9 - off, yy, (150, 160, 190))
        # пыль из-под задних лап
        if pose != "run_b":
            dust.append([cx + (3 if skid else 0), 0])
        for d in dust:
            a = d[1]
            if a < 4:
                v = 210 - a * 30
                f.set(d[0] - a, FLOOR_Y - 1 - a // 2, (v, v - 25, v - 70))
                if a >= 1:
                    f.set(d[0] - a - 1, FLOOR_Y - 1, (v - 30, v - 55, v - 95))
            d[1] += 1
        # искры из-под передних лап при торможении
        if skid:
            for k in range(3):
                f.set(round(nose) - 1 + k, FLOOR_Y - 1 - (k + t) % 2, (255, 200 - k * 50, 0))
        cat_sprite(f, CAT[pose], cx)
        push(f)
        t += 1
        mx += 1.5
        if skid:
            nose += 1.6
            skid += 1
        else:
            nose += 1.75
        if mx >= HOLE_X - 2 and not skid:
            skid = 1
        if nose >= WALL_X - 1:
            break

    # ---------------- 2. удар
    sx = WALL_X - len(SPLAT[0])
    sy = FLOOR_Y - len(SPLAT)
    shake = [(1, 0), (-1, 1), (1, -1), (-1, 0), (1, 1), (0, -1), (-1, 0), (1, 0), (0, 0)]
    word = "ТЫДЫЩ"
    tw = gen.text_width(word, gen.FONT5)
    for i in range(16):
        f = gen.Frame()
        draw_floor(f)
        draw_wall(f, flash=i == 0)
        if i < 3:
            # вспышка в точке удара: лучи расходятся, кот поверх
            rays(f, WALL_X - 1, sy + 3, 4 + i, 6 + i, (255, 255, 255) if i == 0 else (255, 210, 0))
        f.sprite(SPLAT, sx, sy, pal=CAT_PAL)
        if i >= 1:
            outlined_text(f, word, (W - tw) // 2, 0, (255, 255, 255) if i == 1 else (255, 220, 0))
        if i >= 3:
            stars(f, i, sx + 2, sy - 1)
        dx, dy = shake[i] if i < len(shake) else (0, 0)
        push(shifted(f, dx, dy), 60 if i < 9 else 80)

    # ---------------- 3. сползает по стене
    seq = []
    rows = list(SPLAT)
    for k in range(4):
        seq.append(list(rows))
        del rows[len(rows) // 2]
    BACK = 2              # улёгшись, кот отваливается от стены
    for i, rws in enumerate(seq + [SLUMP, SLUMP, FLAT]):
        f = gen.Frame()
        draw_floor(f)
        draw_wall(f)
        f.sprite(rws, WALL_X - gen.width(rws) - (BACK if rws is FLAT else 0), FLOOR_Y - len(rws), pal=CAT_PAL)
        push(f, 110)

    # ---------------- 4. лежит, звёздочки, мышонок выглядывает
    fx = WALL_X - gen.width(FLAT) - BACK
    N = 30
    for i in range(N):
        f = gen.Frame()
        draw_floor(f)
        draw_wall(f)
        f.sprite(FLAT, fx, FLOOR_Y - len(FLAT), pal=CAT_PAL)
        stars(f, i, fx + 9, FLOOR_Y - 6)
        if 6 <= i < 11:
            f.sprite(MOUSE_PEEK["edge"], HOLE_X, FLOOR_Y - 4, pal=MOUSE_PAL)
        elif i >= 11:
            peek = MOUSE_PEEK["out_a" if (i // 2) % 2 == 0 else "out_b"]
            f.sprite(peek, HOLE_X - 2, FLOOR_Y - 4, pal=MOUSE_PAL)
        push(f, 90)

    gen.save("cat_mouse_hole", frames, ms)
    print("кадров", len(frames), "сек", sum(ms) / 1000)


if __name__ == "__main__":
    build()
