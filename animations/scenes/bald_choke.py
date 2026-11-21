#!/usr/bin/env python3
"""Лысый толстяк и колючий мальчишка: мальчик дразнится языком, папаша багровеет
снизу вверх, хватает его за шею и трясёт туда-сюда, потом роняет — у мальчика звёздочки."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 70
GROUND = 13

YEL = (255, 200, 0)
RED = (255, 40, 0)
PAL = {
    "Y": YEL,                 # кожа (у обоих)
    "h": (190, 150, 110),     # два волоска
    "S": (150, 110, 150),     # щетина
    "W": (255, 255, 255),
    "w": (215, 215, 230),     # рубашка
    "b": (0, 70, 255),
    "M": (170, 0, 0),         # рот
    "r": (255, 0, 0),         # футболка мальчика
    "B": (0, 90, 255),        # шорты
    "t": (255, 90, 160),      # язык
}

# толстяк лицом вправо; переднюю руку рисуем отдельно
MAN = [
    "...h.h....",
    "..YYYYY...",
    ".YYYYYYY..",
    ".YYYYWWY..",
    ".YYYYYYYY.",
    ".YYSSSSS..",
    "..YSSMSS..",
    "..wwwwww..",
    ".wwwwwwww.",
    "Ywwwwwwwww",
    "Y.wwwwwwww",
    "..bbbbbbb.",
    "..bbb.bbb.",
]
MAN_HEAD_ROWS = 7

# мальчик лицом влево (к толстяку): зубцы-волосы, глаза, нос
BOY_HEAD = [
    ".Y.Y.Y.",
    ".YYYYYY",
    ".WWYYYY",
    "YYYYYYY",
    "..MYYYY",
]
BOY_BODY = [".rrrr.", "YrrrrY", ".BBBB."]
LEGS_STAND = ".Y..Y."
LEGS_DANGLE = [[".Y..Y.", "Y....Y"], [".Y.Y..", ".Y.Y.."], ["..Y..Y", "..Y..Y"], [".Y..Y.", ".Y..Y."]]

MAN_X0 = 3
BOY_X0 = 17
BOY_Y0 = 4          # верх головы мальчика стоя

T_TEASE = 18        # дразнится
T_RED = 34          # толстяк краснеет
T_GRAB = 39         # рывок
T_SHAKE = 85        # трясёт
T_DROP = 93         # падение
N = 110             # головокружение и возврат


def lerp(a, b, k):
    k = max(0.0, min(1.0, k))
    return tuple(round(x + (y - x) * k) for x, y in zip(a, b))


def draw_man(f, x, y, red, angry, mouth_open):
    """red — доля головы, залитая красным снизу вверх (0..1)."""
    level = MAN_HEAD_ROWS - red * MAN_HEAD_ROWS   # строки ниже level — красные
    for dy, row in enumerate(MAN):
        for dx, ch in enumerate(row):
            if ch == ".":
                continue
            c = PAL[ch]
            if ch == "Y" and dy < MAN_HEAD_ROWS:
                c = lerp(YEL, RED, (dy + 1 - level))
            if ch == "M" and mouth_open:
                c = PAL["W"]
            f.set(x + dx, y + dy, c)
    if angry:
        # злые брови: светлая косая чёрточка над глазами
        f.set(x + 5, y + 2, (255, 230, 150))
        f.set(x + 6, y + 2, (255, 230, 150))
        f.set(x + 7, y + 3, YEL if red < 1 else RED)
        f.set(x + 5, y + 6, PAL["W"])
        f.set(x + 6, y + 6, PAL["W"])


def draw_boy(f, x, y, legs, eyes_pop=False, tongue=0, hands_up=None):
    f.sprite(BOY_HEAD, x, y, pal=PAL)
    if eyes_pop:
        f.set(x, y + 2, PAL["W"])
        f.set(x + 1, y + 1, PAL["W"])
    if tongue:
        f.set(x + 1, y + 4, PAL["t"])
        f.set(x + 1, y + 5, PAL["t"])
        if tongue > 1:
            f.set(x, y + 5, PAL["t"])
    f.sprite(BOY_BODY, x + 1, y + 5, pal=PAL)
    if hands_up is not None:
        # большие пальцы в уши, ладошки машут
        f.set(x + 1, y + 6, PAL["r"])
        f.set(x + 6, y + 6, PAL["r"])
        # ладошка у уха с шевелящимися пальцами
        f.set(x + 7, y + 2, YEL)
        f.set(x + 7, y + 1, YEL)
        f.set(x + 8, y + 1 + hands_up, YEL)
        f.set(x + 8, y + 3 - hands_up, YEL)
    for dy, row in enumerate(legs):
        for dx, ch in enumerate(row):
            if ch != ".":
                f.set(x + 1 + dx, y + 8 + dy, YEL)


def arm(f, x0, y0, x1, y1):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        px = round(x0 + (x1 - x0) * i / n)
        py = round(y0 + (y1 - y0) * i / n)
        f.set(px, py, YEL)


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        for x in range(W):
            f.set(x, GROUND, (70, 50, 110))

        mx, my = MAN_X0, 0
        bx, by = BOY_X0, BOY_Y0
        red, angry, mouth_open = 0.0, False, False
        boy = dict(legs=[LEGS_STAND])
        grab = False

        if t < T_RED:
            # мальчик дразнится: подпрыгивает, язык, ладошки у ушей
            by = BOY_Y0 - (1 if (t // 3) % 2 else 0)
            boy.update(tongue=1 + (t // 3) % 2, hands_up=(t // 2) % 2)
            if t >= T_TEASE:
                red = (t - T_TEASE) / (T_RED - T_TEASE)
                angry = red > 0.5
                if red > 0.6:
                    mx += t % 2      # дрожит от злости
        elif t < T_GRAB:
            # рывок вперёд
            k = (t - T_RED) / (T_GRAB - T_RED)
            red, angry, mouth_open = 1.0, True, True
            mx = MAN_X0 + round(3 * k)
            by = BOY_Y0 - round(2 * k)
            grab = k > 0.3
            boy.update(eyes_pop=True, legs=[LEGS_STAND])
        elif t < T_SHAKE:
            red, angry, mouth_open = 1.0, True, (t // 2) % 2 == 0
            ph = (t - T_GRAB) // 2
            sh = [-2, 2][ph % 2]
            mx = MAN_X0 + 3 + (1 if sh > 0 else 0)
            bx = BOY_X0 + 1 + sh
            by = BOY_Y0 - 2 - (ph % 2)
            grab = True
            boy.update(eyes_pop=True, tongue=2, legs=LEGS_DANGLE[ph % 4])
        elif t < T_DROP:
            k = (t - T_SHAKE) / (T_DROP - T_SHAKE)
            red = 1.0 - k
            angry = True
            mx = MAN_X0 + 3 - round(3 * k)
            fall = min(1.0, k * 2)
            by = BOY_Y0 - 2 + round(2 * fall)
            boy.update(eyes_pop=True, tongue=1)
        else:
            k = (t - T_DROP) / (N - T_DROP)
            by = BOY_Y0
            bx = BOY_X0
            boy.update(tongue=0)

        draw_man(f, mx, my, red, angry, mouth_open)
        draw_boy(f, bx, by, **boy)

        if grab:
            # руки толстяка на шее мальчика
            nx, ny = bx + 1, by + 5
            arm(f, mx + 8, my + 8, nx, ny)
            arm(f, mx + 9, my + 9, nx, ny + 1)
            f.set(nx + 5, ny, YEL)
        if T_GRAB <= t < T_SHAKE:
            # чёрточки тряски
            side = bx + 7
            if (t // 2) % 2:
                f.set(side, by + 3, PAL["W"])
                f.set(side, by + 7, PAL["W"])
        if T_TEASE <= t < T_SHAKE and (t // 3) % 2:
            # пар с макушки
            f.set(mx + 1, 1 - (t // 3) % 2, (200, 200, 230))
            f.set(mx + 8, 1, (200, 200, 230))
        if t >= T_DROP - 2:
            # звёздочки над мальчиком
            for s in range(3):
                a = 2 * math.pi * (t / 12 + s / 3)
                px = round(bx + 3.5 + 3.5 * math.cos(a))
                py = round(by - 2 + 0.8 * math.sin(a))
                f.set(px, py, (255, 230, 60) if math.sin(a) > -0.3 else (160, 140, 40))
        frames.append(f)
    gen.save("bald_choke", frames, MS)


if __name__ == "__main__":
    build()
