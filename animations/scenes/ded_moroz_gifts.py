#!/usr/bin/env python3
"""Дед Мороз идёт с мешком, прибегают дети, он ставит мешок, лезет в него
и подбрасывает над детьми горсти конфетти."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
GROUND = 13
MS = 90
STOP_X = 3                  # где Дед Мороз останавливается

# Дед Мороз лицом вправо: шуба до пят, белая опушка, борода
DM = [
    "...rrw...",
    "..rrrr...",
    "..wwwww..",
    "...ssks..",
    "..wwwww..",
    ".rwwwwwr.",
    ".rrwwwrr.",
    ".rrrwrrr.",
    ".rrrwrrr.",
    ".rrrwrrr.",
    "rrrrwrrrr",
    "wwwwwwwww",
]
BOOTS = ["..nn.nn..", ".nn...nn."]      # шаг
DM_PAL = {"r": (230, 0, 20), "n": (120, 50, 10)}

SACK = [
    "..y..",
    ".ooo.",
    "ooooo",
    "ooooo",
    ".ooo.",
]
SACK_OPEN = [
    ".y.y.",
    ".ooo.",
    "ooooo",
    "ooooo",
    ".ooo.",
]
SACK_PAL = {"o": (30, 80, 255), "y": (255, 200, 0)}

# ребёнок лицом влево
KID = [
    "..w..",
    ".hhh.",
    "hhhhh",
    ".kss.",
    ".sss.",
    "scccs",
    ".ccc.",
]
KID_LEGS = [".b.b.", "b...b"]
KIDS = [  # (куда встанет, куртка, шапка, когда выбегает)
    (18, (0, 140, 255), (255, 30, 30), 18),
    (23, (0, 210, 60), (255, 210, 0), 23),
]

CONFETTI = [(255, 30, 30), (255, 220, 0), (0, 230, 60), (0, 120, 255), (255, 0, 200), (0, 230, 230), (255, 255, 255), (255, 120, 0)]


def ease(p):
    p = max(0.0, min(1.0, p))
    return 0.5 - 0.5 * math.cos(math.pi * p)


def draw_dm(f, x, step, arm):
    """arm: None — руки при себе, 'reach' — тянется в мешок, 'throw' — бросок вверх."""
    f.sprite(DM, x, 0, pal=DM_PAL)
    f.sprite([BOOTS[step % 2]], x, 12, pal=DM_PAL)
    red, skin = DM_PAL["r"], gen.PAL["s"]
    if arm == "reach":
        f.set(x + 8, 7, red)
        f.set(x + 9, 8, red)
        f.set(x + 10, 9, skin)
    elif arm == "throw":
        f.set(x + 8, 6, red)
        f.set(x + 9, 5, red)
        f.set(x + 10, 4, skin)
    else:
        f.set(x + 8, 8, skin)


def draw_kid(f, x, kid, step, cheer, y_off=0):
    _, coat, hat, _ = kid
    pal = {"c": coat, "h": hat, "b": (60, 60, 160)}
    y = 5 - y_off
    f.sprite(KID, x, y, pal=pal)
    f.sprite([KID_LEGS[step % 2]], x, y + 7, pal=pal)
    if cheer:   # руки вверх: ладошки по бокам головы
        for dx in (0, 4):
            f.set(x + dx, y + 5, coat)
            f.set(x + dx, y + 4, coat)
        f.set(x - 1, y + 3, gen.PAL["s"])
        f.set(x + 5, y + 3, gen.PAL["s"])


class Bit:
    def __init__(self, rnd, x, y, t0):
        self.x, self.y, self.t0 = x, y, t0
        self.vx = rnd.uniform(0.25, 1.05)
        self.vy = rnd.uniform(-1.05, -0.45)
        self.c = rnd.choice(CONFETTI)
        self.ph = rnd.uniform(0, 6.28)
        self.landed = None

    def step(self, t):
        if self.landed is not None:
            return
        self.vy = min(self.vy + 0.07, 0.35)              # медленно планирует вниз
        self.x += self.vx * 0.6 + 0.25 * math.sin(self.ph + t * 0.7)
        self.vx *= 0.97
        self.y += self.vy
        if self.y >= GROUND - 0.5:
            self.y = GROUND
            self.landed = t


def build():
    rnd = random.Random(11)
    snow = [[rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(0.08, 0.18)] for _ in range(9)]
    bits = []
    frames = []

    WALK = 28                       # идёт
    SACK_DOWN = WALK + 8            # снимает мешок
    THROWS = [SACK_DOWN + 4 + k * 16 for k in range(3)]   # три горсти
    END = THROWS[-1] + 30
    FADE = 8

    for t in range(END + FADE):
        f = gen.Frame()
        # снег на земле и в воздухе
        for x in range(W):
            f.set(x, GROUND, (200, 220, 255))
        for s in snow:
            s[1] += s[2]
            if s[1] >= GROUND:
                s[0], s[1] = rnd.uniform(0, W), 0
            f.set(int(s[0]), int(s[1]), (130, 150, 200))

        # Дед Мороз
        if t < WALK:
            x = round(-10 + (STOP_X + 10) * t / (WALK - 1))
            step = t // 2
        else:
            x, step = STOP_X, 0

        # мешок: на спине → на снегу справа от деда
        if t < WALK:
            sx, sy, open_ = x - 3, 4, False
        elif t < SACK_DOWN:
            p = ease((t - WALK) / (SACK_DOWN - WALK))
            sx = round((STOP_X - 3) + (STOP_X + 9 - (STOP_X - 3)) * p)
            sy = round(4 - 3 * math.sin(math.pi * p) + 4 * p)        # дугой через плечо
            open_ = False
        else:
            sx, sy, open_ = STOP_X + 9, 8, True

        arm = None
        for th in THROWS:
            if th - 6 <= t < th - 1:
                arm = "reach"
            elif th - 1 <= t < th + 3:
                arm = "throw"
        on_back = t < WALK
        if on_back:
            f.sprite(SACK, sx, sy, pal=SACK_PAL)
        draw_dm(f, x, step, arm)
        if not on_back:
            sprite = SACK_OPEN if open_ else SACK
            wiggle = 1 if arm == "reach" and t % 2 else 0
            f.sprite(sprite, sx + wiggle, sy, pal=SACK_PAL)
            if arm == "reach":                 # рука снова поверх мешка
                f.set(x + 10, 9, gen.PAL["s"])

        # дети выбегают справа и встают у мешка
        cheering = any(th <= t < th + 14 for th in THROWS)
        for i, kid in enumerate(KIDS):
            tx, _, _, start = kid
            if t < start:
                continue
            run = t - start
            kx = max(tx, W + 1 - run)
            moving = kx > tx
            hop = 1 if cheering and ((t + i * 2) // 3) % 2 == 0 else 0
            draw_kid(f, kx, kid, run if moving else 0, cheering and not moving, hop if not moving else 0)

        # конфетти
        for th in THROWS:
            if t == th:
                for _ in range(22):
                    bits.append(Bit(rnd, STOP_X + 11 + rnd.uniform(-0.5, 0.5), 3.5, t))
        for b in bits:
            b.step(t)
            if b.landed is not None and t - b.landed > 25:
                continue
            twinkle = 1.0 if b.landed is not None else (0.65 + 0.35 * math.sin(b.ph + t * 1.3))
            f.set(round(b.x), round(b.y), gen.scale(b.c, twinkle))

        # в конце — плавно гаснем, чтобы петля началась с пустой сцены
        if t >= END:
            k = 1 - (t - END + 1) / FADE
            for y in range(H):
                for xx in range(W):
                    f.px[y][xx] = gen.scale(f.px[y][xx], k)
        frames.append(f)
    gen.save("ded_moroz_gifts", frames, MS)


if __name__ == "__main__":
    build()
