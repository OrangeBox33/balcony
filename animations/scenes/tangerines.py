#!/usr/bin/env python3
"""«МАНДАРИНЫ ЕСТЬ?» бегущей строкой; «ЕСТЬ?» встаёт, мандарин вкатывается и выталкивает слово.
Потом справа подкатывается второй мандарин."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H

# «?» шириной 4, чтобы «ЕСТЬ?» влезло ровно в 28 столбцов
FONT = {**gen.FONT7, "?": [".##.", "#..#", "...#", "..#.", "..#.", "....", "..#."]}
TEXT = "МАНДАРИНЫ ЕСТЬ?"
WORD = "ЕСТЬ?"
TY = 4                      # строка текста: ряды 4..10

ORANGE = (255, 110, 0)
SHADE = (190, 30, 0)        # полоска-долька, по ней видно вращение
SHINE = (255, 200, 110)     # блик
LEAF = (0, 210, 0)
STEM = (0, 130, 20)
TEXT_C = (255, 190, 0)

R = 3.9                     # радиус: диаметр 8 px
CY = 7.0                    # центр по вертикали: ряды 3..10


def tangerine(f, cx, ang):
    """cx — центр (дробный), ang — угол черешка (0 = вправо, -pi/2 = вверх)."""
    x0 = round(cx - 3.5)
    ccx = x0 + 3.5
    for y in range(H):
        for x in range(x0 - 1, x0 + 9):
            dx, dy = x - ccx, y - CY + 0.5
            if math.hypot(dx, dy) > R:
                continue
            c = ORANGE
            # долька: полоса через центр, повёрнутая вместе с черешком
            a = math.atan2(dy, dx) - ang
            d = abs(math.hypot(dx, dy) * math.sin(a))
            if d < 0.6 and math.hypot(dx, dy) > 0.8:
                c = SHADE
            f.set(x, y, c)
    # блик всегда сверху слева
    f.set(x0 + 2, round(CY) - 3, SHINE)
    f.set(x0 + 1, round(CY) - 2, SHINE)
    # черешок на краю и листик, отогнутый по ходу вращения
    ca, sa = math.cos(ang), math.sin(ang)
    sx, sy = ccx - 0.5 + ca * 3.6, CY + sa * 3.6
    f.set(round(sx), round(sy), STEM)
    for k in (1.2, 2.2):
        lx = sx + ca * k * 0.7 - sa * k
        ly = sy + sa * k * 0.7 + ca * k
        f.set(round(lx), round(ly), LEAF)


def rolled(cx, stop):
    # угол такой, что в точке остановки листик смотрит вверх
    return -math.pi / 2 + (cx - stop) / R


def build():
    frames, ms = [], []
    tw = gen.text_width(TEXT, FONT)
    word_at = gen.text_width(TEXT[:-len(WORD)], FONT) + 1  # смещение «ЕСТЬ?» в строке

    def frame(tx=None, text=TEXT, mand=(), t=70):
        f = gen.Frame()
        if tx is not None:
            f.text(text, tx, TY, TEXT_C, FONT)
        for cx, stop in mand:
            tangerine(f, cx, rolled(cx, stop))
        frames.append(f)
        ms.append(t)

    # бегущая строка до момента, когда «ЕСТЬ?» встаёт на место
    for t in range(W + word_at + 1):
        frame(W - t, t=40)      # текст в 1,5 раза быстрее (было 60 мс)
    # вопрос висит, «?» мигает
    for i in range(14):
        frame(0, WORD if i % 6 < 4 else WORD[:-1], t=60)

    # первый мандарин вкатывается слева
    stop1 = 9.5
    cx = -5.0
    wx = 0.0
    v = 0.9
    while round(cx - 3.5) + 8 < 0:
        frame(0, WORD, [(cx, stop1)])
        cx += v
    # толкает слово
    while cx < 7.0:
        wx = round(cx - 3.5) + 8   # слово вплотную к правому краю мандарина
        frame(round(wx), WORD, [(cx, stop1)])
        cx += v
    # слово улетает по инерции, мандарин тормозит
    wv = 1.4
    while wx < W or cx < stop1:
        wx += wv
        wv += 0.15
        cx = min(stop1, cx + max(0.15, (stop1 - cx) * 0.35))
        frame(round(wx) if wx < W else None, WORD, [(cx, stop1)])
    for _ in range(8):
        frame(mand=[(stop1, stop1)], t=90)

    # второй — справа, лёгкий удар
    stop2 = 18.5
    hit = stop2 - 1          # точка касания
    c2 = W + 5.0
    while c2 > hit:
        c2 = max(hit, c2 - max(0.35, min(0.9, (c2 - hit) * 0.3)))
        frame(mand=[(stop1, stop1), (c2, stop2)])
    # стукнулись: первый откатился и вернулся, второй отскочил на место
    for d1, d2 in ((-1, -1), (-1, -0.5), (-1, 0), (-0.5, 0), (0, 0)):
        frame(mand=[(stop1 + d1, stop1), (stop2 + d2, stop2)], t=80)
    for _ in range(22):
        frame(mand=[(stop1, stop1), (stop2, stop2)], t=100)

    # гаснут к началу петли
    last = frames[-1]
    for k in (0.7, 0.45):
        f = gen.Frame()
        f.px = [[gen.scale(c, k) for c in row] for row in last.px]
        frames.append(f)
        ms.append(80)
    frame(t=200)

    gen.save("tangerines", frames, ms)


if __name__ == "__main__":
    build()
