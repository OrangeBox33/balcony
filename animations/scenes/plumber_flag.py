#!/usr/bin/env python3
"""Усатый водопроводчик: бьёт головой «?»-блок, ловит гриб, вырастает, прыгает по трубе
и платформе на флагшток, съезжает вместе с флагом — уровень пройден, салют."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 70
FEET = 11             # строка ботинок на земле
GROUND_Y = 12         # кирпичи: строки 12–13

C = {
    "r": (255, 10, 0),       # кепка, рубашка
    "W": (255, 255, 255),    # буква M, перчатки
    "s": (255, 140, 70),     # кожа
    "k": (120, 50, 5),       # усы, волосы
    "b": (0, 80, 255),       # комбинезон
    "n": (170, 75, 10),      # ботинки
}

# ---------------------------------------------------------------- водопроводчик (лицом вправо)

SMALL = {
    "stand": [
        ".rrr..",
        "rrWrrr",
        "kssKs.",
        "rbbbr.",
        "WbbbW.",
        ".n.n..",
    ],
    "run_a": [
        ".rrr..",
        "rrWrrr",
        "kssKs.",
        "rbbbrW",
        ".bbb..",
        "n...n.",
    ],
    "run_b": [
        ".rrr..",
        "rrWrrr",
        "kssKs.",
        "Wrbbr.",
        ".bbbW.",
        "..nn..",
    ],
    "jump": [
        ".rrr.W",
        "rrWrrr",
        "kssKsr",
        "rbbbr.",
        "Wbbb..",
        "n...n.",
    ],
}

BIG = {
    "stand": [
        "..rrr..",
        ".rrWrrr",
        ".ksssss",
        ".ssKKK.",
        "rrbrbr.",
        "WbbbbbW",
        ".bb.bb.",
        "nnn.nnn",
    ],
    "run_a": [
        "..rrr..",
        ".rrWrrr",
        ".ksssss",
        ".ssKKK.",
        "rrbrbrW",
        ".bbbbb.",
        "bb...bb",
        "nn....n",
    ],
    "run_b": [
        "..rrr..",
        ".rrWrrr",
        ".ksssss",
        ".ssKKK.",
        "Wrbrbr.",
        ".bbbbbW",
        "..bbb..",
        "..nnn..",
    ],
    "jump": [
        "..rrr.W",
        ".rrWrrr",
        ".ksssss",
        ".ssKKKr",
        "rrbrbr.",
        "Wbbbbb.",
        "bb..bb.",
        "n....nn",
    ],
    "pole": [            # держится за шест справа обеими руками
        "..rrr.W",
        ".rrWrrW",
        ".ksssss",
        ".ssKKK.",
        "rrbrbr.",
        ".bbbbb.",
        ".bb.bb.",
        ".nn.nn.",
    ],
}

PAL = {**C, "K": C["k"]}


def hero(f, size, pose, x, feet, flip=False):
    rows = (BIG if size == "big" else SMALL)[pose]
    f.sprite(rows, round(x), round(feet) - len(rows) + 1, flip=flip, pal=PAL)


# ---------------------------------------------------------------- мир

BRICK_A = (230, 95, 25)
BRICK_B = (180, 65, 10)
BLOCK_X, BLOCK_Y = 13, 0
PIPE_X = 44           # шляпка 5 шириной, ствол 3
PLAT_X, PLAT_Y, PLAT_W = 53, 9, 6
POLE_X = 70
CAM_END = POLE_X - 19
TOP_LEDGE = 8         # ноги на трубе и платформе


def draw_ground(f, cam):
    for sx in range(W):
        wx = sx + cam
        for sy, col, off in ((GROUND_Y, BRICK_A, 0), (GROUND_Y + 1, BRICK_B, 2)):
            if (wx + off) % 4 != 0:
                f.set(sx, sy, col)


def draw_clouds(f, cam):
    cloud = [".ww.", "wwww"]
    pal = {"w": (120, 130, 160)}
    for wx, y in ((3, 5), (25, 3), (46, 5), (66, 2), (88, 4)):
        f.sprite(cloud, wx - round(cam * 0.5), y, pal=pal)


def draw_block(f, cam, bump, used, t):
    x = BLOCK_X - cam
    y = BLOCK_Y - bump
    if used:
        rows = ["nnnn", "nNNn", "nnnn"]
        pal = {"n": (150, 70, 10), "N": (200, 110, 40)}
    else:
        q = (255, 255, 255) if t % 8 < 5 else (255, 200, 120)
        rows = ["oyyo", "yQQy", "oyyo"]
        pal = {"o": (255, 90, 0), "y": (255, 190, 0), "Q": q}
    f.sprite(rows, x, y, pal=pal)


MUSH = [".rr.", "rWrW", ".cc."]
MUSH_PAL = {"r": (255, 0, 0), "W": (255, 255, 255), "c": (255, 210, 150)}


def draw_pipe(f, cam):
    x = PIPE_X - cam
    f.sprite(["Lgggd", ".Lgd.", ".Lgd."], x, 9,
             pal={"g": (0, 200, 0), "L": (140, 255, 120), "d": (0, 120, 0)})


def draw_platform(f, cam):
    for i in range(PLAT_W):
        c = BRICK_A if (PLAT_X + i) % 3 else (255, 150, 60)
        f.set(PLAT_X + i - cam, PLAT_Y, c)


def draw_pole(f, cam, flag_y):
    x = POLE_X - cam
    for y in range(1, 11):
        f.set(x, y, (170, 190, 170))
    f.set(x, 0, (0, 230, 60))
    f.sprite(["xxx"], x - 1, 11, pal={"x": (150, 150, 160)})
    fy = round(flag_y)
    f.sprite(["ggg", "gg.", "g.."], x + 1, fy, pal={"g": (0, 220, 40)})
    f.set(x + 2, fy, (255, 255, 255))


# ---------------------------------------------------------------- сценарий

def jump_arc(x0, f0, x1, f1, n, peak):
    """Позиции (x, ноги) прыжка из (x0, f0) в (x1, f1) за n кадров; peak — высшая строка ног."""
    out = []
    for i in range(1, n + 1):
        u = i / n
        x = x0 + (x1 - x0) * u
        base = f0 + (f1 - f0) * u
        lift = min(f0, f1) - peak
        y = base - 4 * lift * u * (1 - u) - (0 if f0 == f1 else 0)
        out.append((x, y))
    return out


def build():
    frames = []
    st = dict(size="small", pose="stand", x=-6.0, feet=FEET, flip=False, cam=0.0,
              bump=0, used=False, mush=None, flag=1.0, fade=1.0, sparkle=None, hide=False,
              booms=[])
    t = [0]

    def shot():
        f = gen.Frame()
        cam = round(st["cam"])
        draw_clouds(f, st["cam"])
        draw_ground(f, cam)
        draw_block(f, cam, st["bump"], st["used"], t[0])
        draw_pipe(f, cam)
        draw_platform(f, cam)
        draw_pole(f, cam, st["flag"])
        if st["mush"]:
            mx, my = st["mush"]
            f.sprite(MUSH, round(mx) - cam, round(my), pal=MUSH_PAL)
        if not st["hide"]:
            hero(f, st["size"], st["pose"], st["x"] - cam, st["feet"], st["flip"])
        if st["sparkle"] is not None:
            sx, sy, a = st["sparkle"]
            for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                f.set(round(sx - cam + dx * a), round(sy + dy * a), (255, 255, 200))
        for (bx, by, age, hue) in st["booms"]:
            draw_boom(f, bx, by, age, hue)
        if st["fade"] < 1:
            for y in range(H):
                for x in range(W):
                    f.px[y][x] = gen.scale(f.px[y][x], st["fade"])
        frames.append(f)
        t[0] += 1

    def run_pose():
        return "run_a" if t[0] % 4 < 2 else "run_b"

    # 1. влетает маленьким, бежит под блок (с проявлением)
    st["x"] = -6.0
    while st["x"] < 12:
        st["x"] += 1
        st["pose"] = run_pose()
        st["fade"] = min(1.0, (t[0] + 1) / 4)
        shot()
    st["fade"] = 1.0

    # 2. прыжок под блок
    for i, dy in enumerate((2, 3, 3, 2, 1, 0, 0)):
        st["feet"] = FEET - dy
        st["pose"] = "jump" if dy else "stand"
        st["bump"] = 1 if i in (1, 2) else 0
        if i == 3:
            st["used"] = True
            st["mush"] = (BLOCK_X, 1)
        st["sparkle"] = (BLOCK_X + 1.5, 1, 1) if i == 1 else None
        shot()

    # 3. гриб выскакивает вправо, падает и катится влево; водопроводчик бежит навстречу
    mush_path = [(BLOCK_X + 2, 0), (BLOCK_X + 3, 0), (BLOCK_X + 4, 0), (BLOCK_X + 5, 1),
                 (BLOCK_X + 6, 2), (BLOCK_X + 7, 4), (BLOCK_X + 8, 6), (BLOCK_X + 9, 9)]
    i = 0
    mx, my = mush_path[0]
    while True:
        if i < len(mush_path):
            mx, my = mush_path[i]
        else:
            mx -= 1
        i += 1
        st["mush"] = (mx, my)
        if i > 3:
            st["x"] += 1
            st["pose"] = run_pose()
        else:
            st["pose"] = "stand"
        if st["x"] + 5 >= mx and my >= 7:
            break
        shot()
    st["mush"] = None

    # 4. растёт: мигает маленький/большой
    cx = st["x"] + 3
    seq = "sbsbsbbsbbbb"
    for k, c in enumerate(seq):
        st["size"] = "big" if c == "b" else "small"
        st["pose"] = "stand"
        st["x"] = cx - (3.5 if c == "b" else 3)
        st["sparkle"] = (cx, 6, 1 + k % 3) if k < 9 else None
        shot()
    st["sparkle"] = None
    st["x"] = round(st["x"])

    # 5. бежит большим, камера плавно догоняет
    def step_cam():
        target = min(CAM_END, max(0.0, st["x"] - 8))
        d = target - st["cam"]
        st["cam"] += max(0.0, min(d * 0.35, 1.6))

    def run_to(xe):
        while st["x"] < xe:
            st["x"] += 1
            st["pose"] = run_pose()
            step_cam()
            shot()

    def leap(xe, fe, n, peak):
        for (x, y) in jump_arc(st["x"], st["feet"], xe, fe, n, peak):
            st["x"], st["feet"] = x, y
            st["pose"] = "jump"
            step_cam()
            shot()
        st["x"], st["feet"] = xe, fe

    run_to(PIPE_X - 9)
    leap(PIPE_X - 1, TOP_LEDGE, 7, 6)          # на трубу
    st["pose"] = "stand"
    run_to(PIPE_X + 1)
    leap(PLAT_X, TOP_LEDGE, 7, 6)               # на платформу
    run_to(PLAT_X + 1)
    leap(POLE_X - 6, 6, 7, 5)                   # на флагшток
    # 6. съезжает вместе с флагом
    st["pose"] = "pole"
    flag0 = 1.0
    for k in range(3):
        step_cam()
        shot()
    n = 9
    for k in range(1, n + 1):
        st["feet"] = 6 + (FEET - 6) * k / n
        st["flag"] = flag0 + (8 - flag0) * k / n
        step_cam()
        shot()
    for k in range(3):
        shot()
    # перепрыгивает на другую сторону шеста
    st["flip"] = True
    st["x"] = POLE_X + 1
    st["pose"] = "pole"
    for k in range(3):
        st["flag"] -= 1
        shot()
    st["flip"] = False
    for k in range(3):
        st["pose"] = "stand"
        st["flag"] -= 1
        shot()
    # 7. уходит вправо, флаг поднимается, салют
    booms = [(13, 3, 0.0), (5, 3, 0.33), (9, 7, 0.6), (14, 6, 0.15)]
    starts = [0, 5, 10, 15]
    k = 0
    while k < 34:
        if st["x"] - CAM_END < W + 1:
            st["x"] += 1
            st["pose"] = run_pose()
        else:
            st["hide"] = True
        if k >= 0:
            st["flag"] = max(1.0, st["flag"] - 1)
        st["booms"] = [(bx, by, k - 8 - s0, hue) for (bx, by, hue), s0 in zip(booms, starts)
                       if 0 <= k - 8 - s0 < 8]
        if k >= 30:
            st["fade"] = (34 - k) / 5
        shot()
        k += 1
    gen.save("plumber_flag", frames, MS)


def draw_boom(f, x, y, age, hue):
    if age == 0:
        f.set(x, y, (255, 255, 255))
        return
    r = age * 0.8
    k = max(0.7, 1 - age / 14)
    c = gen.scale(gen.hsv(hue, 0.7, 1), k)
    for a in range(8):
        ang = a * math.pi / 4 + age * 0.1
        f.set(round(x + math.cos(ang) * r), round(y + math.sin(ang) * r * 0.8), c)
    if age < 4:
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            f.set(x + dx, y + dy, (255, 255, 200) if age < 2 else c)


if __name__ == "__main__":
    build()
