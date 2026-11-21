#!/usr/bin/env python3
"""Бегущая строка «УЛЫБНИСЬ» сжимается в точку, из точки вырастает смайлик, улыбается и подмигивает."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
WORD = "УЛЫБНИСЬ"
TY = 3                      # верх текста
CX, CY = 13.5, 6.5          # центр экрана и смайлика
R = 7.1
YELLOW = (255, 190, 0)
RIM = (255, 120, 0)         # кромка круга чуть оранжевее
DARK = (0, 0, 0)

EYE_L = [(10, 3), (11, 3), (10, 4), (11, 4)]
EYE_R = [(16, 3), (17, 3), (16, 4), (17, 4)]
WINK_R = [(15, 4), (16, 4), (17, 4), (18, 4)]   # закрытый глаз — чёрточка
MOUTHS = [
    # ровный рот
    [(10, 9), (11, 9), (12, 9), (13, 9), (14, 9), (15, 9), (16, 9), (17, 9)],
    # чуть улыбается
    [(9, 8), (10, 9), (11, 9), (12, 9), (13, 9), (14, 9), (15, 9), (16, 9), (17, 9), (18, 8)],
    # улыбка
    [(8, 7), (9, 8), (10, 9), (11, 10), (12, 10), (13, 10), (14, 10), (15, 10), (16, 10),
     (17, 9), (18, 8), (19, 7)],
]


def word_color(i):
    # от оранжевого к жёлтому по буквам
    return gen.hsv(0.06 + 0.07 * i / (len(WORD) - 1), 1.0, 1.0)


def mix(a, b, k):
    return tuple(int(p + (q - p) * k) for p, q in zip(a, b))


def word_pixels():
    """Пиксели слова в координатах от его левого края: [(x, y, цвет)]."""
    out, x = [], 0
    for i, ch in enumerate(WORD):
        g = gen.FONT7[ch]
        for dy, row in enumerate(g):
            for dx, v in enumerate(row):
                if v == "#":
                    out.append((x + dx, TY + dy, word_color(i)))
        x += len(g[0]) + 1
    return out


def face(f, r, eyes=True, mouth=None, wink=False):
    for y in range(H):
        for x in range(W):
            d = math.hypot(x - CX, y - CY)
            if d <= r:
                f.set(x, y, RIM if d > r - 1.0 and r > 3 else YELLOW)
    if eyes:
        for x, y in EYE_L:
            f.set(x, y, DARK)
        if wink:
            for x, y in EYE_R:
                f.set(x, y, YELLOW)
            for x, y in WINK_R:
                f.set(x, y, DARK)
        else:
            for x, y in EYE_R:
                f.set(x, y, DARK)
    if mouth is not None:
        for x, y in MOUTHS[mouth]:
            f.set(x, y, DARK)


def faster(ms, k=1.5):
    """Ускорить в k раз. GIF хранит задержку в сотых долях секунды — округляем до 10 мс, не меньше 20."""
    return [max(20, round(int(d / 10) * 10 / k / 10) * 10) for d in ms]


def build():
    frames, ms = [], []

    def emit(f, t, n=1):
        for _ in range(n):
            frames.append(f)
            ms.append(t)

    emit(gen.Frame(), 80, 3)

    pix = word_pixels()
    ww = gen.text_width(WORD, gen.FONT7)
    end = W - 2 - ww                     # слово остановилось: последняя буква у правого края

    # бегущая строка: по пикселю за кадр
    for ox in range(W, end - 1, -1):
        f = gen.Frame()
        for x, y, c in pix:
            f.set(ox + x, y, c)
        emit(f, 70)
    emit(f, 90, 5)

    # слово сжимается к центру экрана
    steps = 14
    for k in range(1, steps + 1):
        u = k / steps
        s = (1 - u) ** 2                 # быстро сначала, медленно в конце
        f = gen.Frame()
        for x, y, c in pix:
            nx = round(CX + (end + x - CX) * s)
            ny = round(CY + (y - CY) * (1 - u))
            f.add(nx, ny, mix(c, (255, 255, 200), u))
        emit(f, 60)

    # яркая точка в центре
    for c in ((255, 255, 255), (255, 240, 150), (255, 255, 255)):
        f = gen.Frame()
        for x, y in ((13, 6), (14, 6), (13, 7), (14, 7)):
            f.set(x, y, c)
        emit(f, 70)

    # смайлик раскрывается с небольшим перелётом
    for r in (1.5, 2.5, 3.6, 4.8, 6.0, 7.2, 8.0, 7.6, R):
        f = gen.Frame()
        face(f, r, eyes=False)
        emit(f, 60)

    blank = gen.Frame()
    face(blank, R, eyes=False)
    emit(blank, 100, 3)

    f = gen.Frame()
    face(f, R, eyes=True)
    emit(f, 100, 4)
    for m in range(3):
        f = gen.Frame()
        face(f, R, mouth=m)
        emit(f, 100, 3 if m < 2 else 10)

    # подмигивает
    f = gen.Frame()
    face(f, R, mouth=2, wink=True)
    emit(f, 100, 5)
    f = gen.Frame()
    face(f, R, mouth=2)
    emit(f, 100, 16)

    # гаснет
    last = frames[-1]
    for k in (0.7, 0.45, 0.28):
        f = gen.Frame()
        f.px = [[gen.scale(c, k) for c in row] for row in last.px]
        emit(f, 80)
    emit(gen.Frame(), 100, 3)

    gen.save("smile_text", frames, faster(ms))   # вся сцена в 1,5 раза быстрее


if __name__ == "__main__":
    build()
