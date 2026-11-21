#!/usr/bin/env python3
"""«ТУТ ЖИВЁТ ГИРЛЯНДА»: буквы включаются по одной, как лампочки; потом вся матрица мигает,
и загорается «ДОБРЫЙ ВЕЧЕР»."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
F5, F7 = gen.FONT5, gen.FONT7
# «Й» с отдельной дужкой в свободном ряду над строкой (рисуется на 1 px выше)
J_HI = [".##.", "....", "#..#", "#.##", "##.#", "#..#"]

# цвета лампочек гирлянды
BULBS = [(255, 0, 0), (0, 220, 0), (255, 180, 0), (0, 80, 255)]
# включение лампочки: яркость по кадрам (мерцание, потом горит)
FLICK = [0.0, 0.6, 0.0, 0.0, 1.0, 0.3, 1.0]


def glyph(f, g, x, y, c):
    for dy, row in enumerate(g):
        for dx, v in enumerate(row):
            if v == "#":
                f.set(x + dx, y + dy, c)


def layout(text, font, x, y):
    """Список (глиф, x, y) по буквам; пробелы пропускаются."""
    out = []
    for ch in text:
        if ch == "Й" and font is F5:
            out.append((J_HI, x, y - 1))
        elif ch != " ":
            out.append((font[ch], x, y))
        x += len(font[ch][0]) + 1
    return out


def centered(text, font, y):
    return layout(text, font, (W - gen.text_width(text, font)) // 2, y)


def lit(k):
    """Яркость лампочки через k кадров после щелчка."""
    if k < 0:
        return 0.0
    return FLICK[k] if k < len(FLICK) else 1.0


def dim(c, k):
    # тусклые каналы на диодах пропадают — «полуяркость» держим не ниже ~100
    if k <= 0:
        return gen.BLACK
    if k >= 1:
        return c
    return tuple(int(v * max(k, 0.45)) for v in c)


def build():
    frames, ms = [], []

    def push(f, t):
        frames.append(f)
        ms.append(t)

    # 1) «ТУТ» / «ЖИВЁТ» двумя строками мелким шрифтом, буквы включаются по очереди
    letters = centered("ТУТ", F5, 1) + centered("ЖИВЁТ", F5, 8)
    STEP = 4
    n = len(letters) * STEP + len(FLICK) + 12
    for t in range(n):
        f = gen.Frame()
        for i, (g, x, y) in enumerate(letters):
            glyph(f, g, x, y, dim(BULBS[i % 4], lit(t - 3 - i * STEP)))
        push(f, 80)

    # 2) «ГИРЛЯНДА» бегущей строкой: каждая буква включается, когда целиком въехала
    word = "ГИРЛЯНДА"
    tw = gen.text_width(word, F7)
    on_at = {}
    for t in range(W + tw + 1):
        f = gen.Frame()
        for i, (g, x, y) in enumerate(layout(word, F7, W - t, 3)):
            if x + len(g[0]) <= W - 1 and i not in on_at:
                on_at[i] = t
            k = lit(t - on_at[i]) if i in on_at else 0.0
            # пока не включена — еле тлеет (видно, что буква есть)
            c = dim(BULBS[(i + 1) % 4], k) if k > 0 else (90, 40, 0)
            glyph(f, g, x, y, c)
        push(f, 40)      # бегущая строка в 1,5 раза быстрее (было 60 мс)

    # 3) вся матрица вспыхивает гирляндой, цвета сдвигаются при каждой вспышке
    for flash in range(3):
        f = gen.Frame()
        for y in range(H):
            for x in range(W):
                f.set(x, y, BULBS[(x + y + flash) % 4])
        push(f, 140)
        push(gen.Frame(), 120)

    # 4) «ДОБРЫЙ» / «ВЕЧЕР»: тёплые буквы, цвета медленно бегут как в гирлянде
    letters = centered("ДОБРЫЙ", F5, 1) + centered("ВЕЧЕР", F5, 8)
    for t in range(52):
        f = gen.Frame()
        shift = t // 6
        for i, (g, x, y) in enumerate(letters):
            k = lit(t - i)              # быстрая волна включения
            glyph(f, g, x, y, dim(BULBS[(i + shift) % 4], k))
        push(f, 80)

    # гаснет к началу петли
    last = frames[-1]
    for k in (0.6, 0.4):
        f = gen.Frame()
        f.px = [[gen.scale(c, k) for c in row] for row in last.px]
        push(f, 80)
    push(gen.Frame(), 300)

    gen.save("garland_lives", frames, ms)
    print(f"длительность {sum(ms) / 1000:.1f} с")


if __name__ == "__main__":
    build()
