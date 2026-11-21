#!/usr/bin/env python3
"""
Пиксельные анимации для LED-матрицы на WLED (эффект «Image»).

    python3 animations/gen.py                       — сгенерировать все анимации
    python3 animations/gen.py convert in.gif out    — подогнать любой GIF под матрицу

animations/wled/*.gif     — файлы для заливки в WLED
animations/preview/*.gif  — как это будет выглядеть на диодах (крупно)
"""
import colorsys
import math
import random
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

W, H = 28, 14  # 28 столбцов × 14 строк = 392 диода

HERE = Path(__file__).resolve().parent
OUT = HERE / "wled"
PREVIEW = HERE / "preview"

# WLED применяет гамма-коррекцию, поэтому каналы ниже ~60 на диодах почти гаснут.
PAL = {
    "s": (255, 120, 60),   # кожа
    "k": (130, 60, 10),    # волосы
    "r": (255, 0, 0),
    "R": (170, 30, 0),
    "b": (0, 70, 255),
    "g": (0, 210, 0),
    "G": (0, 120, 20),
    "y": (255, 180, 0),
    "o": (255, 90, 0),
    "w": (200, 200, 220),
    "W": (255, 255, 255),
    "x": (110, 110, 120),
    "n": (150, 60, 5),
    "p": (150, 0, 220),
    "m": (255, 70, 140),
    "c": (0, 200, 220),
}

BLACK = (0, 0, 0)


# ---------------------------------------------------------------- холст

class Frame:
    def __init__(self):
        self.px = [[BLACK] * W for _ in range(H)]

    def set(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            self.px[y][x] = c

    def add(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            o = self.px[y][x]
            self.px[y][x] = tuple(min(255, a + b) for a, b in zip(o, c))

    def sprite(self, rows, x, y, flip=False, pal=None):
        p = {**PAL, **(pal or {})}
        w = max(len(r) for r in rows)
        for dy, row in enumerate(rows):
            row = row.ljust(w, ".")
            if flip:
                row = row[::-1]
            for dx, ch in enumerate(row):
                if ch != ".":
                    self.set(x + dx, y + dy, p[ch])

    def text(self, s, x, y, color, font):
        for ch in s:
            g = font[ch]
            for dy, row in enumerate(g):
                for dx, v in enumerate(row):
                    if v == "#":
                        c = color(x + dx, y + dy) if callable(color) else color
                        self.set(x + dx, y + dy, c)
            x += len(g[0]) + 1
        return x

    def image(self):
        img = Image.new("RGB", (W, H))
        img.putdata([c for row in self.px for c in row])
        return img


def width(rows):
    return max(len(r) for r in rows)


def text_width(s, font):
    return sum(len(font[c][0]) + 1 for c in s) - 1


def scale(c, k):
    return tuple(int(v * k) for v in c)


def hsv(h, s=1.0, v=1.0):
    return tuple(int(255 * c) for c in colorsys.hsv_to_rgb(h % 1, s, v))


# ---------------------------------------------------------------- шрифты

FONT3 = {
    "0": ["###", "#.#", "#.#", "#.#", "###"],
    "1": [".#.", "##.", ".#.", ".#.", "###"],
    "2": ["##.", "..#", ".#.", "#..", "###"],
    "3": ["##.", "..#", ".#.", "..#", "##."],
    "4": ["#.#", "#.#", "###", "..#", "..#"],
    "5": ["###", "#..", "##.", "..#", "##."],
    "6": [".##", "#..", "###", "#.#", "###"],
    "7": ["###", "..#", ".#.", ".#.", ".#."],
    "8": ["###", "#.#", "###", "#.#", "###"],
    "9": ["###", "#.#", "###", "..#", "##."],
    "F": ["###", "#..", "##.", "#..", "#.."],
    "I": ["###", ".#.", ".#.", ".#.", "###"],
    "G": [".##", "#..", "#.#", "#.#", ".##"],
    "H": ["#.#", "#.#", "###", "#.#", "#.#"],
    "T": ["###", ".#.", ".#.", ".#.", ".#."],
    "K": ["#.#", "##.", "#..", "##.", "#.#"],
    "O": [".#.", "#.#", "#.#", "#.#", ".#."],
    "!": ["#", "#", "#", ".", "#"],
    ".": [".", ".", ".", ".", "#"],
}

FONT7 = {
    "А": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "Б": ["#####", "#....", "#....", "####.", "#...#", "#...#", "####."],
    "В": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "Г": ["#####", "#....", "#....", "#....", "#....", "#....", "#...."],
    "Д": [".###.", ".#.#.", ".#.#.", ".#.#.", ".#.#.", "#####", "#...#"],
    "Е": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "Ё": [".#.#.", "#####", "#....", "####.", "#....", "#....", "#####"],
    "Ж": ["#.#.#", "#.#.#", "#.#.#", ".###.", "#.#.#", "#.#.#", "#.#.#"],
    "З": [".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."],
    "И": ["#...#", "#...#", "#..##", "#.#.#", "##..#", "#...#", "#...#"],
    "Й": [".#.#.", "..#..", "#...#", "#..##", "#.#.#", "##..#", "#...#"],
    "К": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "Л": ["..###", ".#..#", ".#..#", ".#..#", ".#..#", ".#..#", "#...#"],
    "М": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "Н": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "О": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "П": ["#####", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#"],
    "Р": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "С": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "Т": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "У": ["#...#", "#...#", "#...#", ".####", "....#", "#...#", ".###."],
    "Ф": ["..#..", ".###.", "#.#.#", "#.#.#", "#.#.#", ".###.", "..#.."],
    "Х": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Ц": ["#..#.", "#..#.", "#..#.", "#..#.", "#..#.", "#####", "....#"],
    "Ч": ["#...#", "#...#", "#...#", ".####", "....#", "....#", "....#"],
    "Ш": ["#.#.#", "#.#.#", "#.#.#", "#.#.#", "#.#.#", "#.#.#", "#####"],
    "Щ": ["#.#.#.", "#.#.#.", "#.#.#.", "#.#.#.", "#.#.#.", "######", ".....#"],
    "Ъ": ["##...", ".#...", ".#...", ".###.", ".#..#", ".#..#", ".###."],
    "Ы": ["#...#", "#...#", "#...#", "##..#", "#.#.#", "#.#.#", "##..#"],
    "Ь": ["#....", "#....", "#....", "####.", "#...#", "#...#", "####."],
    "Э": [".###.", "#...#", "....#", ".####", "....#", "#...#", ".###."],
    "Ю": ["#..#.", "#.#.#", "#.#.#", "###.#", "#.#.#", "#.#.#", "#..#."],
    "Я": [".####", "#...#", "#...#", ".####", "..#.#", ".#..#", "#...#"],
    "0": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": ["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."],
    "!": ["#", "#", "#", "#", "#", ".", "#"],
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    ".": [".", ".", ".", ".", ".", ".", "#"],
    ",": ["..", "..", "..", "..", "..", ".#", "#."],
    ":": [".", ".", "#", ".", "#", ".", "."],
    "-": ["...", "...", "...", "###", "...", "...", "..."],
    " ": ["..", "..", "..", "..", "..", "..", ".."],
}

# 3×5 (широкие буквы шире): влезает 2 строки по ~6–7 букв
FONT5 = {
    "А": [".#.", "#.#", "###", "#.#", "#.#"],
    "Б": ["###", "#..", "##.", "#.#", "##."],
    "В": ["##.", "#.#", "##.", "#.#", "##."],
    "Г": ["###", "#..", "#..", "#..", "#.."],
    "Д": [".###", ".#.#", ".#.#", "####", "#..#"],
    "Е": ["###", "#..", "##.", "#..", "###"],
    "Ё": ["#.#", "###", "##.", "#..", "###"],
    "Ж": ["#.#.#", "#.#.#", ".###.", "#.#.#", "#.#.#"],
    "З": ["##.", "..#", ".#.", "..#", "##."],
    "И": ["#..#", "#..#", "#.##", "##.#", "#..#"],
    "Й": [".##.", "#..#", "#.##", "##.#", "#..#"],
    "К": ["#.#", "#.#", "##.", "#.#", "#.#"],
    "Л": [".##", "#.#", "#.#", "#.#", "#.#"],
    "М": ["#...#", "##.##", "#.#.#", "#...#", "#...#"],
    "Н": ["#.#", "#.#", "###", "#.#", "#.#"],
    "О": [".#.", "#.#", "#.#", "#.#", ".#."],
    "П": ["###", "#.#", "#.#", "#.#", "#.#"],
    "Р": ["##.", "#.#", "##.", "#..", "#.."],
    "С": [".##", "#..", "#..", "#..", ".##"],
    "Т": ["###", ".#.", ".#.", ".#.", ".#."],
    "У": ["#.#", "#.#", ".##", "..#", "##."],
    "Ф": ["..#..", "#####", "#.#.#", "#####", "..#.."],
    "Х": ["#.#", "#.#", ".#.", "#.#", "#.#"],
    "Ц": ["#.#.", "#.#.", "#.#.", "####", "...#"],
    "Ч": ["#.#", "#.#", "###", "..#", "..#"],
    "Ш": ["#.#.#", "#.#.#", "#.#.#", "#.#.#", "#####"],
    "Щ": ["#.#.#.", "#.#.#.", "#.#.#.", "######", ".....#"],
    "Ъ": ["##..", ".#..", ".##.", ".#.#", ".##."],
    "Ы": ["#...#", "#...#", "##..#", "#.#.#", "##..#"],
    "Ь": ["#..", "#..", "##.", "#.#", "##."],
    "Э": ["##.", "..#", ".##", "..#", "##."],
    "Ю": ["#..#.", "#.#.#", "###.#", "#.#.#", "#..#."],
    "Я": [".##", "#.#", ".##", "#.#", "#.#"],
    **{d: FONT3[d] for d in "0123456789"},
    "!": ["#", "#", "#", ".", "#"],
    "?": ["##.", "..#", ".#.", "...", ".#."],
    ".": [".", ".", ".", ".", "#"],
    ",": ["..", "..", "..", ".#", "#."],
    ":": [".", "#", ".", "#", "."],
    "-": ["..", "..", "##", "..", ".."],
    " ": ["..", "..", "..", "..", ".."],
}


# ---------------------------------------------------------------- спрайты бойца (лицом вправо)

FIGHTER = {
    "idle": [
        "..kkk...",
        "..sss...",
        "..sssrr.",
        "...s.rr.",
        ".sssss..",
        ".ssss...",
        "..sss...",
        "..bbb...",
        ".bb.bb..",
        ".b...b..",
        ".b...b..",
        "xx...xx.",
    ],
    "punch": [
        "..kkk.....",
        "..sss.....",
        "..sss...rr",
        "...sssssrr",
        ".ssss.....",
        ".ssss.....",
        "..sss.....",
        "..bbb.....",
        ".bb..bb...",
        ".b....b...",
        "b.....b...",
        "x.....xx..",
    ],
    "kick": [
        "..kkk.....",
        "..sss.....",
        "..sssrr...",
        "...s.rr...",
        ".sssss....",
        ".ssss.....",
        "..sssbbbbx",
        "..bbbbbbbx",
        "..b.......",
        "..b.......",
        ".b........",
        "xx........",
    ],
    "hit": [
        "kkk.....",
        "sss.....",
        "sss..rr.",
        ".s...rr.",
        ".sssss..",
        ".ssss...",
        "..sss...",
        "..bbb...",
        ".bb.bb..",
        ".b...b..",
        ".b...b..",
        "xx...xx.",
    ],
    "down": [
        "......rr.....",
        "kssssssbbbbbx",
        "kss.......bbx",
    ],
}

FIGHTER_B = {"r": (0, 210, 0), "b": (255, 110, 0), "k": (150, 150, 160)}

SPARK = [".W.", "WyW", ".W."]
SPARK_BIG = ["y.W.y", ".WWW.", "WWyWW", ".WWW.", "y.W.y"]


def floor(f, color=(70, 70, 80)):
    for x in range(W):
        f.set(x, H - 1, color)


# ---------------------------------------------------------------- 1. драка

def fight():
    frames = []
    A = {"pose": "idle", "x": 1}
    B = {"pose": "idle", "x": 26}  # для B это правый край (он зеркальный)

    def draw(spark=None, big=False, text=None):
        f = Frame()
        floor(f)
        t = len(frames)
        up = (t // 3) % 2  # пружинистая стойка
        for P, flip in ((A, False), (B, True)):
            rows = FIGHTER[P["pose"]]
            if P["pose"] == "down":
                y = H - 1 - len(rows)
            else:
                y = 1 - (up if P["pose"] == "idle" else 0)
            if flip:
                f.sprite(rows, P["x"] - width(rows) + 1, y, flip=True, pal=FIGHTER_B)
            else:
                f.sprite(rows, P["x"], y)
        if spark:
            s = SPARK_BIG if big else SPARK
            f.sprite(s, spark[0] - width(s) // 2, spark[1] - len(s) // 2)
        if text:
            text(f)
        frames.append(f)

    def hold(n, **kw):
        for _ in range(n):
            draw(**kw)

    # FIGHT!
    for i in range(14):
        f = Frame()
        if i % 4 != 3:
            word = "FIGHT!"
            f.text(word, (W - text_width(word, FONT3)) // 2, 4, (255, 40, 0), FONT3)
        frames.append(f)

    # сходятся
    while A["x"] < 7:
        hold(2)
        A["x"] += 1
        B["x"] -= 1
    hold(4)

    def a_attack(pose, dy):
        A["pose"] = pose
        B["pose"] = "hit"
        hold(2, spark=(B["x"] - 4, dy))
        A["pose"] = "idle"
        B["x"] += 1
        hold(2)
        B["pose"] = "idle"
        hold(3)
        B["x"] -= 1
        hold(2)

    def b_attack(pose, dy):
        B["pose"] = pose
        A["pose"] = "hit"
        hold(2, spark=(A["x"] + 4, dy))
        B["pose"] = "idle"
        A["x"] -= 1
        hold(2)
        A["pose"] = "idle"
        hold(3)
        A["x"] += 1
        hold(2)

    a_attack("punch", 3)
    b_attack("kick", 8)
    a_attack("punch", 3)
    b_attack("punch", 3)
    a_attack("kick", 8)

    # добивание
    A["pose"] = "punch"
    B["pose"] = "hit"
    hold(3, spark=(B["x"] - 4, 3), big=True)
    A["pose"] = "idle"
    B["x"] += 2
    hold(2)
    B["pose"] = "down"
    B["x"] += 3

    def ko(f):
        f.text("K.O.", W - text_width("K.O.", FONT3) - 1, 1, (255, 200, 0), FONT3)

    for i in range(20):
        draw(text=ko if i % 4 < 3 else None)

    save("fight", frames, 90)


# ---------------------------------------------------------------- 2. боксёр и груша

def boxer():
    frames = []
    bx = 18          # левый край груши
    st = {"pose": "idle", "swing": 0.0, "v": 0.0, "hits": 0}
    X = bx - 11      # позиция боксёра: перчатка в ударе касается груши

    def draw(spark=None):
        f = Frame()
        floor(f)
        t = len(frames)
        up = (t // 3) % 2
        y = 1 - (up if st["pose"] == "idle" else 0)
        f.sprite(FIGHTER[st["pose"]], X, y)
        # цепь
        for yy in (0, 1):
            f.set(bx + 1, yy, PAL["x"])
            f.set(bx + 2, yy, PAL["x"])
        # груша, низ отклоняется сильнее верха
        for yy in range(2, 11):
            k = (yy - 2) / 8
            off = round(st["swing"] * k)
            for xx in range(4):
                c = (200, 0, 0) if yy not in (3, 9) else (230, 230, 230)
                f.set(bx + xx + off, yy, c)
        # счётчик ударов
        f.text(f"{st['hits']:02d}", 0, 0, (0, 160, 255), FONT3)
        if spark:
            f.sprite(SPARK, spark[0] - 1, spark[1] - 1)
        frames.append(f)
        # физика груши: затухающий маятник
        st["v"] += -0.35 * st["swing"] - 0.15 * st["v"]
        st["swing"] += st["v"]

    def idle(n):
        st["pose"] = "idle"
        for _ in range(n):
            draw()

    def hit(pose, sy, power):
        st["pose"] = pose
        st["hits"] += 1
        st["v"] += power
        draw(spark=(bx, sy))
        draw()

    idle(6)
    for seq in (["punch"], ["punch", "punch"], ["kick"], ["punch", "punch", "punch"], ["kick", "punch"]):
        for p in seq:
            hit(p, 4 if p == "punch" else 8, 1.2 if p == "punch" else 2.0)
            idle(2)
        idle(8)
    idle(6)
    save("boxer", frames, 90)


# ---------------------------------------------------------------- 3. самурай приседает

SAMURAI = {
    "stand": [
        "...k....",
        "..kkk...",
        "..sss...",
        "..sss...",
        ".bbbbb..",
        ".bbbbb..",
        ".bbbbb..",
        "xrrrrrnn",
        "..ppp...",
        "..ppp...",
        "..p.p...",
        ".nn.nn..",
    ],
    "half": [
        "...k.....",
        "..kkk....",
        "..sss....",
        "..sss....",
        ".bbbbbss.",
        ".bbbbb...",
        "xrrrrrnn.",
        ".ppppp...",
        ".p...p...",
        "nn..nn...",
    ],
    "squat": [
        "....k.....",
        "...kkk....",
        "...sss....",
        "...sss....",
        "..bbbbbsss",
        "xrrrrrnn..",
        "pppppp....",
        "nn...nn...",
    ],
}


def samurai():
    frames = []
    rnd = random.Random(3)
    petals = [(rnd.randint(0, W - 1), rnd.randint(0, H - 1)) for _ in range(6)]
    count = 0
    seq = []
    for _ in range(8):
        seq += ["stand"] * 4 + ["half"] * 2 + ["squat"] * 4 + ["half"] * 2 + ["+"]
    seq += ["stand"] * 10
    for pose in seq:
        if pose == "+":
            count += 1
            continue
        f = Frame()
        t = len(frames)
        # солнце
        for yy in range(H):
            for xx in range(W):
                if (xx - 21) ** 2 + (yy - 5) ** 2 <= 14:
                    f.set(xx, yy, (190, 25, 0))
        # лепестки сакуры
        for px, py in petals:
            f.set((px - t // 3) % W, (py + t // 2) % (H - 1), (255, 90, 150))
        floor(f, (90, 50, 20))
        rows = SAMURAI[pose]
        f.sprite(rows, 7, H - 1 - len(rows))
        f.text(str(count), 1, 1, (255, 200, 0), FONT3)
        frames.append(f)
    save("samurai", frames, 100)


# ---------------------------------------------------------------- 4. ёлочка

def tree():
    # 168 кадров — общий период всего: снег (14 рядов за 28 и 56 кадров), мигание (24), звезда (8)
    N = 168
    rnd = random.Random(5)
    cx = 13
    halfw = {2: 0, 3: 1, 4: 2, 5: 1, 6: 2, 7: 3, 8: 2, 9: 4, 10: 5, 11: 6}
    cells = [(x, y) for y, hw in halfw.items() for x in range(cx - hw, cx + hw + 1)]
    lights = rnd.sample([c for c in cells if c[1] > 2], 14)
    lcolors = [(255, 0, 0), (255, 180, 0), (0, 80, 255), (255, 0, 200), (0, 220, 220)]
    flakes = [(rnd.randint(0, W - 1), rnd.randint(0, H - 1), rnd.choice([2, 4])) for _ in range(12)]
    snowman = [".xxx.", "xxxxx", ".www.", ".wwwo", ".rrr.", "wwwww", "wwwww", ".www."]
    gift1 = ["ryr", "yyy", "ryr"]
    gift2 = ["bbyb", "yyyy", "bbyb"]

    frames = []
    for t in range(N):
        f = Frame()
        for fx, fy, sp in flakes:
            f.set(fx, (fy + t // sp) % H, (150, 150, 180))
        for x in range(W):
            f.set(x, H - 1, (150, 150, 180))
        for (x, y) in cells:
            f.set(x, y, (0, 140, 20))
        f.set(cx, 12, PAL["n"])
        f.set(cx + 1, 12, PAL["n"])
        for i, (x, y) in enumerate(lights):
            phase = (t // 3 + i * 2) % 8
            if phase < 6:
                f.set(x, y, lcolors[(i + t // 12) % len(lcolors)])
        star = (255, 200, 0) if (t // 4) % 2 else (255, 255, 160)
        f.set(cx, 0, star)
        for x in (cx - 1, cx, cx + 1):
            f.set(x, 1, star)
        f.sprite(snowman, 21, 5)
        f.sprite(gift1, 3, 10)
        f.sprite(gift2, 7, 10)
        frames.append(f)
    save("tree", frames, 110)


# ---------------------------------------------------------------- 5. салют

def fireworks():
    """Салют по нарастающей: начало как раньше (редкие кольца), потом залпы чаще, крупнее
    и пышнее (пионы, двойные, золотые ивы), в финале — всё небо взрывается разом, затем тишина."""
    rnd = random.Random(11)
    RISE, LIFE = 8, 16
    # 1) начало — те же 4 кольца, что были
    rings = []
    for i in range(8):
        sh = {
            "t0": i * 12 + rnd.randint(0, 5),
            "x": rnd.randint(4, W - 5),
            "top": rnd.randint(2, 5),
            "color": hsv(rnd.random()),
            "n": rnd.choice([10, 14, 18]),
            "v": rnd.uniform(0.45, 0.7),
        }
        if i < 4:
            rings.append(sh)

    # 2) и 3) — разгон и финал: частицы с сопротивлением воздуха и гравитацией
    COLORS = [(255, 40, 40), (40, 255, 80), (60, 120, 255), (255, 220, 40), (230, 60, 255),
              (40, 230, 255), (255, 120, 20), (255, 80, 160)]
    shells = []

    def shell(t0, kind, big, rise=8):
        x = rnd.randint(3, W - 4)
        top = rnd.randint(2, 6) if big < 1.2 else rnd.randint(3, 6)
        shells.append({"t0": t0, "x": x, "top": top, "kind": kind, "big": big, "rise": rise,
                       "c1": rnd.choice(COLORS), "c2": rnd.choice(COLORS), "seed": rnd.random()})

    t = 50
    while t < 112:                      # разгон: залпы чаще и крупнее
        p = (t - 50) / 62
        shell(t, rnd.choice(["peony", "double", "peony", "willow"]), 0.9 + 0.4 * p)
        if rnd.random() < 0.25 + 0.5 * p:
            shell(t + rnd.randint(1, 3), rnd.choice(["peony", "ring2"]), 0.9 + 0.3 * p)
        t += max(4, round(9 - 5 * p)) + rnd.randint(0, 2)
    t = 114
    while t < 144:                      # финал: небо целиком
        for _ in range(rnd.randint(2, 3)):
            shell(t + rnd.randint(0, 2), rnd.choice(["peony", "double", "crackle", "willow"]), 1.5, rise=6)
        t += 3
    shell(146, "crackle", 2.0, rise=6)  # последний, самый большой — со вспышкой
    shell(147, "double", 1.8, rise=6)

    parts = []                          # [x, y, vx, vy, рождён, живёт, цвет, тип]

    def burst(sh, t):
        r = random.Random(sh["seed"])
        kind, big = sh["kind"], sh["big"]
        n = int((26 if kind != "willow" else 20) * big)
        for k in range(n):
            a = 2 * math.pi * (k + r.random() * 0.6) / n
            if kind == "ring2":
                sp = 0.95 * big
            else:
                sp = big * (0.55 + 0.45 * r.random() ** 0.5)
            c = sh["c1"]
            if kind == "double" and k % 2:
                c, sp = sh["c2"], sp * 0.55
            if kind == "willow":
                c = (255, 190, 60)
            life = r.randint(14, 20) if kind == "willow" else r.randint(10, 15)
            parts.append([sh["x"], sh["top"], math.cos(a) * sp * 1.3, math.sin(a) * sp, t, life, c, kind])

    frames = []
    N = 172
    flash = {146: 150, 147: 95, 148: 55}
    for t in range(N):
        f = Frame()
        if t in flash:
            v = flash[t]
            for y in range(H):
                for x in range(W):
                    f.set(x, y, (v, v, int(v * 0.8)))
        # старые кольца
        for s in rings:
            dt = t - s["t0"]
            x, top = s["x"], s["top"]
            if 0 <= dt < RISE:
                y = (H - 1) - (H - 1 - top) * dt / RISE
                f.add(x, round(y), (255, 190, 100))
                f.add(x, round(y) + 1, (110, 60, 20))
            elif RISE <= dt < RISE + LIFE:
                k = dt - RISE
                fade = (1 - k / LIFE) ** 1.4
                if k == 0:
                    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                        f.add(x + dx, top + dy, (255, 255, 255))
                    continue
                for q in range(s["n"]):
                    a = 2 * math.pi * q / s["n"]
                    px = x + math.cos(a) * s["v"] * k * 1.4
                    py = top + math.sin(a) * s["v"] * k + 0.035 * k * k
                    f.add(round(px), round(py), scale(s["color"], fade))
        # новые: ракета летит, потом взрыв
        for s in shells:
            dt = t - s["t0"]
            if 0 <= dt < s["rise"]:
                y = (H - 1) - (H - 1 - s["top"]) * dt / s["rise"]
                f.add(s["x"], round(y), (255, 200, 110))
                f.add(s["x"], round(y) + 1, (140, 70, 20))
            elif dt == s["rise"]:
                burst(s, t)
                rr = 1 + int(s["big"])
                for dx in range(-rr, rr + 1):
                    for dy in range(-rr, rr + 1):
                        if dx * dx + dy * dy <= rr * rr:
                            f.add(s["x"] + dx, s["top"] + dy, (255, 255, 230))
        for pt in parts:
            age = t - pt[4]
            if age <= 0 or age >= pt[5]:
                continue
            x0, y0 = pt[0], pt[1]
            drag = 0.86 if pt[7] != "willow" else 0.8
            pt[0] += pt[2]
            pt[1] += pt[3]
            pt[2] *= drag
            pt[3] = pt[3] * drag + (0.045 if pt[7] != "willow" else 0.06)
            left = 1 - age / pt[5]
            if age < 2:
                c = (255, 255, 235)                       # раскалённое начало
            elif pt[7] == "crackle" and left < 0.5:
                c = (255, 255, 255) if (age * 7 + int(pt[2] * 100)) % 3 == 0 else None
            else:
                c = scale(pt[6], 0.45 + 0.55 * left)      # не гаснет ниже порога диодов
                if left < 0.3 and (age + int(x0 * 3)) % 2:
                    c = None                              # под конец мерцает
            if c:
                f.add(round(pt[0]), round(pt[1]), c)
                if age < pt[5] * 0.6:                     # короткий хвост
                    f.add(round(x0), round(y0), scale(c, 0.45))
        frames.append(f)
    save("fireworks", frames, 60)


# ---------------------------------------------------------------- 6. Дед Мороз на санях

def santa():
    sleigh = [
        "..wrr.....",
        "...rrr....",
        "...ss.....",
        ".nnww.....",
        ".nnrrrr...",
        "rrrrrrrrry",
        ".rrrrrrry.",
        "yyyyyyyyy.",
    ]
    deer = [
        [
            "......n.n.",
            ".......n..",
            ".......nnr",
            ".nnnnnnn..",
            "nnnnnnn...",
            ".n.n..n.n.",
        ],
        [
            "......n.n.",
            ".......n..",
            ".......nnr",
            ".nnnnnnn..",
            "nnnnnnn...",
            "n...nn...n",
        ],
    ]
    house = ["..www..", ".wwwww.", "wwwwwww", ".RyRyR.", ".RRnRR."]
    rnd = random.Random(2)
    stars = [(rnd.randint(0, W - 1), rnd.randint(0, 7), rnd.randint(0, 5)) for _ in range(10)]
    span = 22 + W
    N = span + 16
    frames = []
    trail = []
    for t in range(N):
        f = Frame()
        for sx, sy, ph in stars:
            if (t // 4 + ph) % 6:
                f.set(sx, sy, (120, 120, 150))
        for yy in range(1, 4):
            for xx in range(1, 4):
                if (xx - 2) ** 2 + (yy - 2) ** 2 <= 1:
                    f.set(xx, yy, (230, 230, 160))
        for hx in (1, 11, 20):
            f.sprite(house, hx, H - 5)
        if t < span:
            x = t - 22
            y = 1 + round(math.sin(t / 3))
            trail.append((x - 1, y + 6, t))
            for tx, ty, tt in trail:
                age = t - tt
                if age < 8 and rnd.random() < 0.7:
                    f.add(tx - age // 2, ty + rnd.choice([-1, 0, 1]), scale((255, 200, 60), 1 - age / 8))
            f.sprite(sleigh, x, y)
            f.set(x + 10, y + 5, PAL["y"])
            f.set(x + 11, y + 5, PAL["y"])
            f.sprite(deer[(t // 2) % 2], x + 12, y + 1)
        frames.append(f)
    save("santa", frames, 80)


# ---------------------------------------------------------------- 7. «С НОВЫМ ГОДОМ!»

def greeting():
    msg = "С НОВЫМ ГОДОМ!"
    tw = text_width(msg, FONT7)
    rnd = random.Random(9)
    stars = [(rnd.randint(0, W - 1), rnd.choice([0, 1, 12, 13]), rnd.randint(0, 7)) for _ in range(10)]
    frames = []
    for t in range(tw + W):
        f = Frame()
        for sx, sy, ph in stars:
            if (t // 2 + ph) % 8 < 3:
                f.set(sx, sy, (200, 200, 255))
        f.text(msg, W - t, 3, lambda x, y: hsv((x + t) / 30), FONT7)
        frames.append(f)
    save("greeting", frames, 70)


# ---------------------------------------------------------------- сохранение и превью

def gamma_view(c):
    # как цвет будет выглядеть после гамма-коррекции WLED (тусклое гаснет)
    return tuple(round(((round(255 * (v / 255) ** 2.8)) / 255) ** (1 / 2.8) * 255) for v in c)


def led_preview(img, s=18):
    out = Image.new("RGB", (img.width * s, img.height * s), (6, 6, 8))
    d = ImageDraw.Draw(out)
    r = s * 0.36
    for y in range(img.height):
        for x in range(img.width):
            c = gamma_view(img.getpixel((x, y)))
            if max(c) < 10:
                c = (26, 26, 30)
            cx, cy = x * s + s / 2, y * s + s / 2
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
    return out


def save_gif(imgs, path, ms):
    """GIF через Pillow — только для превью (там картинки крупные и цветов много)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=ms, loop=0, disposal=1, optimize=False)


def _lzw(indices, min_bits):
    clear, eoi = 1 << min_bits, (1 << min_bits) + 1
    out = bytearray()
    acc = nacc = 0

    def emit(code, size):
        nonlocal acc, nacc
        acc |= code << nacc
        nacc += size
        while nacc >= 8:
            out.append(acc & 255)
            acc >>= 8
            nacc -= 8

    size = min_bits + 1
    table, nxt = {}, eoi + 1
    emit(clear, size)
    w = indices[0]
    for k in indices[1:]:
        if (w, k) in table:
            w = table[(w, k)]
            continue
        emit(w, size)
        if nxt < 4095:
            table[(w, k)] = nxt
            nxt += 1
            if nxt > (1 << size) and size < 12:
                size += 1
        else:
            emit(clear, size)
            table, nxt, size = {}, eoi + 1, min_bits + 1
        w = k
    emit(w, size)
    emit(eoi, size)
    if nacc:
        out.append(acc & 255)
    return bytes(out)


def write_gif(imgs, path, ms, delta=True):
    """
    GIF для WLED, без потерь.
    - Одинаковые кадры подряд склеиваются в один с суммарной паузой.
    - delta: кадр хранит только прямоугольник, где что-то поменялось; внутри него неизменные
      пиксели — прозрачные (из двух вариантов берётся тот, что короче). WLED рисует кадр
      поверх прошлого: его картинка лежит в памяти сегмента, а на ленту уходит целиком.
    - Палитра одна на файл ровно под число цветов; если цветов больше 256 — своя у каждого кадра
      (кадр с >256 цветами сводится квантованием).
    delta=False — старый режим «каждый кадр целиком».
    """
    w, h = imgs[0].size
    pix = [list(im.convert("RGB").getdata()) for im in imgs]
    durs = ms if isinstance(ms, (list, tuple)) else [ms] * len(imgs)

    # склейка одинаковых кадров подряд (паузу считаем в сотых, как она и пишется в файл)
    frames, cs = [], []
    for f, d in zip(pix, durs):
        c = int(d / 10)
        if frames and f == frames[-1] and cs[-1] + c <= 65535:
            cs[-1] += c
        else:
            frames.append(f)
            cs.append(c)
    delta = delta and len(frames) > 1

    def bits_for(n):
        bits = 2
        while (1 << bits) < n:
            bits += 1
        return bits

    def table(colors, bits):
        return b"".join(bytes(c) for c in colors) + b"\0" * 3 * ((1 << bits) - len(colors))

    def quant(f):
        im = Image.new("RGB", (w, h))
        im.putdata(f)
        return list(im.quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB").getdata())

    all_colors = sorted({c for f in frames for c in f})
    shared = len(all_colors) + (1 if delta else 0) <= 256
    b = bytearray(b"GIF89a")
    if shared:
        gbits = bits_for(len(all_colors) + (1 if delta else 0))
        gidx = {c: i for i, c in enumerate(all_colors)}
        TR = len(all_colors)                                 # индекс «прозрачного»
        b += struct.pack("<HHBBB", w, h, 0xF0 | (gbits - 1), 0, 0) + table(all_colors, gbits)
    else:
        b += struct.pack("<HHBBB", w, h, 0x70, 0, 0)
    b += b"\x21\xFF\x0BNETSCAPE2.0\x03\x01\x00\x00\x00"      # бесконечный повтор

    prev = None
    for f, c in zip(frames, cs):
        if not shared and len(set(f)) > 256:
            f = quant(f)                                     # даже один кадр не влезает в 256 цветов
        if delta and prev is not None:
            ch = [i for i in range(w * h) if f[i] != prev[i]] or [0]
            x0, x1 = min(i % w for i in ch), max(i % w for i in ch)
            y0, y1 = min(i // w for i in ch), max(i // w for i in ch)
        else:
            x0, y0, x1, y1 = 0, 0, w - 1, h - 1
        box = [y * w + x for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)]

        # варианты: прямоугольник как есть / неизменные пиксели прозрачные
        variants = []
        for transparent in ((False, True) if delta and prev is not None else (False,)):
            if shared:
                ind = [TR if transparent and f[i] == prev[i] else gidx[f[i]] for i in box]
                bits, local, tr = gbits, b"", TR
            else:
                cols = sorted({f[i] for i in box if not (transparent and f[i] == prev[i])})
                if len(cols) + transparent > 256:
                    continue
                m = {col: k for k, col in enumerate(cols)}
                tr = len(cols)
                ind = [tr if transparent and f[i] == prev[i] else m[f[i]] for i in box]
                bits = bits_for(len(cols) + transparent)
                local = table(cols, bits)
            data = _lzw(ind, bits)
            variants.append((len(data) + len(local), transparent, bits, local, tr, data))
        _, transparent, bits, local, tr, data = min(variants, key=lambda v: v[0])

        # GCE: disposal 1 (кадр остаётся под следующим), флаг прозрачности и её индекс
        b += struct.pack("<BBBBHBB", 0x21, 0xF9, 4, 0x04 | int(transparent), c, tr if transparent else 0, 0)
        flags = (0x80 | (bits - 1)) if local else 0
        b += struct.pack("<BHHHHB", 0x2C, x0, y0, x1 - x0 + 1, y1 - y0 + 1, flags) + local
        b.append(bits)
        for i in range(0, len(data), 255):
            b.append(len(data[i:i + 255]))
            b += data[i:i + 255]
        b.append(0)
        prev = f
    b.append(0x3B)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(b))


def save(name, frames, ms):
    imgs = [f.image() for f in frames] if isinstance(frames[0], Frame) else frames
    write_gif(imgs, OUT / f"{name}.gif", ms)
    save_gif([led_preview(i) for i in imgs], PREVIEW / f"{name}.gif", ms)
    print(f"{name:10s} {len(imgs):4d} кадров  {(OUT / f'{name}.gif').stat().st_size / 1024:5.1f} КБ")


def convert(src, name):
    im = Image.open(src)
    imgs, durs = [], []
    for i in range(getattr(im, "n_frames", 1)):
        im.seek(i)
        fr = ImageOps.contain(im.convert("RGB"), (W, H), Image.Resampling.BOX)
        canvas = Image.new("RGB", (W, H))
        canvas.paste(fr, ((W - fr.width) // 2, (H - fr.height) // 2))
        imgs.append(canvas)
        durs.append(im.info.get("duration", 100))
    save(name, imgs, durs)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "convert":
        convert(sys.argv[2], sys.argv[3])
    else:
        for fn in (fight, boxer, samurai, tree, fireworks, santa, greeting):
            fn()
        # сцены из animations/scenes/*.py, у каждой функция build()
        import importlib.util
        for p in sorted((HERE / "scenes").glob("*.py")):
            spec = importlib.util.spec_from_file_location(p.stem, p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.build()
