#!/usr/bin/env python3
"""Бегущая строка «ВСЁ БУДЕТ ХОРОШО» с радужной волной и лёгким покачиванием букв."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
TEXT = "ВСЁ БУДЕТ ХОРОШО"
FONT = gen.FONT7
Y0 = 4          # базовая строка: буквы 7 px, с качанием ±1 занимают 3..11 (точки Ё — тоже в кадре)


def build():
    tw = gen.text_width(TEXT, FONT)
    frames = []
    n = W + tw + 1
    for t in range(n):
        f = gen.Frame()
        x = W - t
        for i, ch in enumerate(TEXT):
            g = FONT[ch]
            # покачивание: волна бежит по буквам
            dy = round(math.sin(i * 0.9 - t * 0.25))
            for ry, row in enumerate(g):
                for rx, v in enumerate(row):
                    if v == "#":
                        px = x + rx
                        # радуга: оттенок зависит от столбца экрана и времени
                        f.set(px, Y0 + dy + ry, gen.hsv(px * 0.035 - t * 0.02))
            x += len(g[0]) + 1
        frames.append(f)
    # в 1,5 раза быстрее: было 70 мс на шаг, стало в среднем 46,7 (GIF хранит паузы с шагом 10 мс)
    gen.save("all_good", frames, [(50, 50, 40)[i % 3] for i in range(len(frames))])


if __name__ == "__main__":
    build()
