#!/usr/bin/env python3
"""Письмо Деду Морозу: бегущая строка под снегом, пауза «...» и мигающее «ПОЧТИ»."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MSG = "ДЕД МОРОЗ, Я БЫЛ ХОРОШИМ"
TY = 4
ICE = (170, 225, 255)
WHITE = (255, 255, 255)
SNOW = (110, 140, 230)
RED = (255, 30, 0)
ORANGE = (255, 170, 0)

# узкая Т (3 px), чтобы «ПОЧТИ» влезло в 28 столбцов
FONT = {**gen.FONT7, "Т": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", ".#."]}


def text_color(x, y):
    # лёгкий перелив от белого к ледяному по строкам
    return WHITE if y - TY < 3 else ICE


def make_snow(n_frames, count=9, seed=5):
    """Снежинки, падающие по кругу: за весь ролик каждая делает целое число оборотов."""
    rnd = random.Random(seed)
    flakes = []
    for _ in range(count):
        cycles = rnd.choice((2, 3, 3, 4))
        flakes.append((rnd.uniform(0, W), rnd.uniform(0, 1), cycles, rnd.uniform(0, 6.28), rnd.choice((1, 2))))

    def draw(f, t):
        for x0, ph, cycles, wph, sw in flakes:
            u = (ph + cycles * t / n_frames) % 1
            y = round(u * (H + 2)) - 1
            x = round(x0 + sw * math.sin(2 * math.pi * 2 * t / n_frames + wph)) % W
            f.set(x, y, SNOW)
    return draw


def faster(ms, k=1.5):
    """Ускорить в k раз. GIF хранит задержку в сотых долях секунды — округляем до 10 мс, не меньше 20."""
    return [max(20, round(int(d / 10) * 10 / k / 10) * 10) for d in ms]


def build():
    msg_w = gen.text_width(MSG, FONT)
    ticker = list(range(W, -msg_w - 1, -1))
    n_dots, n_blink = 16, 30
    total = len(ticker) + n_dots + n_blink
    snow = make_snow(total)
    frames, ms = [], []
    t = 0

    def frame():
        return gen.Frame()

    def push(f, dur):
        # снег рисуем только вдали от букв, чтобы не мешал читать
        nonlocal t
        sf = gen.Frame()
        snow(sf, t)
        for y in range(H):
            for x in range(W):
                if sf.px[y][x] != gen.BLACK and not any(
                        f.px[yy][xx] != gen.BLACK
                        for yy in range(max(0, y - 1), min(H, y + 2))
                        for xx in range(max(0, x - 1), min(W, x + 2))):
                    f.px[y][x] = sf.px[y][x]
        frames.append(f)
        ms.append(dur)
        t += 1

    # бегущая строка, 1 px за кадр
    for ox in ticker:
        f = frame()
        f.text(MSG, ox, TY, text_color, FONT)
        push(f, 60)

    # многозначительное «...»
    for k in range(n_dots):
        f = frame()
        for i in range(min(3, k // 4)):
            f.set(11 + 3 * i, TY + 6, ICE)
        push(f, 90)

    # «ПОЧТИ» мигает: 4 вспышки и удержание
    pw = gen.text_width("ПОЧТИ", FONT)
    px = (W - pw + 1) // 2
    pattern = [1] * 5 + [0] * 2 + [1] * 4 + [0] * 2 + [1] * 4 + [0] * 2 + [1] * 11
    assert len(pattern) == n_blink, len(pattern)
    for k, on in enumerate(pattern):
        f = frame()
        if on:
            col = RED if (k // 2) % 2 else ORANGE
            f.text("ПОЧТИ", px, TY - 1, col, FONT)
        push(f, 100)

    gen.save("santa_letter", frames, faster(ms))   # вся сцена в 1,5 раза быстрее


if __name__ == "__main__":
    build()
