#!/usr/bin/env python3
"""Портрет Деда Мороза: моргает, улыбается, помпон качается. На нос садится снежинка —
он косится на неё, морщит нос, чихает (шапка и борода подпрыгивают) и смеётся. Петля."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 80
SX = -1                      # сдвиг лица: с помпоном справа фигура по центру

HAT = (220, 0, 25)
HAT_TIP = (170, 0, 20)
FUR = (255, 255, 255)
SKIN = (255, 175, 125)
CHEEK = (255, 95, 115)
NOSE = (255, 75, 55)
EYE = (0, 0, 0)
LID = (120, 45, 20)          # закрытый глаз — тёмная чёрточка на коже
BEARD = (215, 215, 228)
MOUSTACHE = (140, 190, 255)
MOUTH = (190, 0, 35)
TONGUE = (255, 90, 110)
FLAKE = (150, 235, 255)
SPRAY = (130, 200, 255)


def px(f, x, y, c):
    f.set(x + SX, y, c)


def draw(f, st):
    hd, bd = st.get("hat", 0), st.get("beard", 0)
    # кожа: лоб (виден, если шапка подпрыгнула) и лицо
    for y in range(4, 9):
        for x in range(8, 20):
            px(f, x, y, SKIN)
    # щёки
    ch = st.get("cheek", 0)
    for x in (8, 9, 18, 19):
        px(f, x, 7 - ch, CHEEK)
    # глаза
    eyes = st.get("eyes", "open")
    for ex, side in ((10, -1), (17, 1)):
        if eyes == "open":
            px(f, ex, 6, EYE)
        elif eyes == "cross":                     # косится на нос
            px(f, ex - side, 6, EYE)
        elif eyes == "closed":
            for d in (-1, 0, 1):
                px(f, ex + d, 6, LID)
        elif eyes == "squeeze":                   # зажмурился: > <
            px(f, ex + side, 5, LID)
            px(f, ex, 6, LID)
            px(f, ex - side, 6, LID)
            px(f, ex + side, 7, LID)
        elif eyes == "laugh":                     # дуги ^ ^
            px(f, ex - 1, 6, EYE)
            px(f, ex, 5, EYE)
            px(f, ex + 1, 6, EYE)
    # нос
    ny = 7 - (1 if st.get("nose_up") else 0)
    for x in (13, 14):
        px(f, x, ny, NOSE)
        px(f, x, ny + 1, NOSE)
    # борода
    rows = {8: [(6, 9), (18, 21)], 9: [(6, 21)], 10: [(6, 21)], 11: [(6, 21)], 12: [(7, 20)], 13: [(9, 18)]}
    for y in range(5, 8):                         # бакенбарды
        for x in (6, 7, 20, 21):
            px(f, x, y, BEARD)
    for y, spans in rows.items():
        for a, b in spans:
            for x in range(a, b + 1):
                px(f, x, y + bd, BEARD)
    # рот (в бороде, двигается с ней)
    m = st.get("mouth", "smile")
    my = 10 + bd
    if m == "smile":
        for x, y in ((12, 0), (13, 1), (14, 1), (15, 0)):
            px(f, x, my + y, MOUTH)
    elif m == "laugh":
        for x in range(12, 16):
            px(f, x, my, MOUTH)
        px(f, 13, my + 1, TONGUE)
        px(f, 14, my + 1, TONGUE)
        px(f, 12, my + 1, MOUTH)
        px(f, 15, my + 1, MOUTH)
    elif m == "o":
        for x in (13, 14):
            px(f, x, my, MOUTH)
            px(f, x, my + 1, MOUTH)
    elif m == "flat":
        px(f, 13, my, MOUTH)
        px(f, 14, my, MOUTH)
    # усы — голубоватые, поверх бороды, крыльями от носа
    for x in list(range(10, 13)) + list(range(15, 18)):
        px(f, x, 9, MOUSTACHE)
    for x in list(range(8, 11)) + list(range(17, 20)):
        px(f, x, 10, MOUSTACHE)
    px(f, 7, 11, MOUSTACHE)
    px(f, 20, 11, MOUSTACHE)
    # шапка
    hat_rows = {0: (10, 18), 1: (8, 20), 2: (7, 21)}
    for y, (a, b) in hat_rows.items():
        for x in range(a, b + 1):
            px(f, x, y + hd, HAT)
    for x, y in ((19, 0), (20, 0), (21, 1), (22, 1)):
        px(f, x, y + hd, HAT_TIP)
    for y in (3, 4):
        for x in range(6, 22):
            px(f, x, y + hd, FUR)
    # помпон
    pc = 24 + st.get("pom", 0)
    for dx, dy in ((0, -1), (-1, 0), (0, 0), (1, 0), (0, 1), (-1, -1), (1, 1), (1, -1), (-1, 1)):
        if abs(dx) + abs(dy) == 2 and (dx, dy) != (-1, -1):
            continue
        px(f, pc + dx, 2 + dy + hd, FUR)


def build():
    N = 86
    # ключевые моменты
    BLINK = (6, 7, 74, 75)
    FALL0, LAND = 10, 24
    WR1, WR2, SNEEZE = (30, 33), (36, 41), 42
    LAUGH = (49, 68)

    frames = []
    for t in range(N):
        st = {"eyes": "open", "mouth": "smile"}
        if t in BLINK:
            st["eyes"] = "closed"
        if FALL0 <= t < LAND:                      # смотрит на падающую снежинку
            st["mouth"] = "flat" if t > FALL0 + 6 else "smile"
        if LAND <= t < SNEEZE:
            st["eyes"] = "cross"
            st["mouth"] = "flat"
        for a, b in (WR1, WR2):
            if a <= t < b:                         # а… а…
                st.update(eyes="squeeze", mouth="o", nose_up=True, cheek=1)
        if SNEEZE <= t < SNEEZE + 4:               # ЧХИ!
            st.update(eyes="squeeze", mouth="o", nose_up=(t == SNEEZE))
            st["hat"] = [-1, 0, -1, 0][t - SNEEZE]
            st["beard"] = [-1, 1, -1, 0][t - SNEEZE]
        if SNEEZE + 4 <= t < LAUGH[0]:
            st.update(eyes="closed", mouth="smile")
        if LAUGH[0] <= t < LAUGH[1]:               # хо-хо-хо
            k = (t - LAUGH[0]) // 3
            st.update(eyes="laugh", cheek=1, mouth="laugh" if k % 2 == 0 else "smile")
            st["beard"] = -1 if k % 2 == 0 and (t - LAUGH[0]) % 3 == 0 else 0
        # помпон: ровное покачивание + сильный мах после чиха
        sw = 0.8 * math.sin(2 * math.pi * t / N * 4)
        a = t - SNEEZE
        if a >= 0:
            sw += 2.2 * math.exp(-a / 9) * math.sin(a * 0.9)
        st["pom"] = max(-1, min(1, round(sw)))

        f = gen.Frame()
        draw(f, st)

        # снежинка: падает зигзагом справа сверху, садится на нос, при чихе улетает
        if FALL0 <= t < LAND:
            p = (t - FALL0) / (LAND - FALL0)
            x = 25 - 12 * p + 0.8 * math.sin(p * 9)
            y = -1 + 8 * p
            fx, fy = round(x), round(y)
            f.set(fx + SX, fy, FLAKE)
            if fy <= 2 and fx >= 22:               # в темноте — крестиком
                for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    f.add(fx + SX + ddx, fy + ddy, gen.scale(FLAKE, 0.5))
        elif LAND <= t < SNEEZE:
            ny = 6 if any(a <= t < b for a, b in (WR1, WR2)) else 7
            f.set(13 + SX, ny, FLAKE)
        elif SNEEZE <= t < SNEEZE + 7:             # сдуло вверх-влево
            a = t - SNEEZE
            fx, fy = 13 - 2 * a, 6 - 1.4 * a
            f.set(round(fx) + SX, round(fy), FLAKE)
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                f.add(round(fx) + SX + ddx, round(fy) + ddy, gen.scale(FLAKE, 0.5))
        # брызги чиха — в стороны, в темноту
        if SNEEZE <= t < SNEEZE + 6:
            a = t - SNEEZE
            k = 1 - a / 6
            for side in (-1, 1):
                for dy, sp in ((-1, 1.3), (1, 1.0), (0, 1.6)):
                    x = 13.5 + side * (8 + sp * a)
                    f.set(round(x) + SX, 8 + dy + round(dy * a * 0.4), gen.scale(SPRAY, k))
        frames.append(f)
    gen.save("ded_moroz_face", frames, MS)


if __name__ == "__main__":
    build()
