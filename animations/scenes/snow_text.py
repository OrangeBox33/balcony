#!/usr/bin/env python3
"""«СНЕГ» засыпает снегом до макушки, слово встряхивается — снег осыпается; потом то же с «ИДЁТ»."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
F = gen.FONT7
TY = 5                                   # верх букв: над ними 5 строк под сугробы
SNOW = (255, 255, 255)
FLAKE = (200, 220, 255)                  # летящая снежинка чуть голубее лежащего снега


def text_color(x, y):
    """Холодный градиент: сверху почти белый, снизу синий."""
    k = max(0.0, (y - TY) / 6)
    return (int(60 - 60 * k), int(170 - 90 * k), 255)


def draw_word(f, word, dx=0, color=text_color):
    """У Ё точки подняты на строку выше — в шрифте они прилипают к букве и не видны."""
    x = (W - gen.text_width(word, F)) // 2 + dx
    for ch in word:
        if ch == "Ё":
            f.text("Е", x, TY, color, F)
            for ddx in (1, 3):
                f.set(x + ddx, TY - 2, color(x + ddx, TY - 2) if callable(color) else color)
        else:
            f.text(ch, x, TY, color, F)
        x += len(F[ch][0]) + 1


def word_cells(word):
    f = gen.Frame()
    draw_word(f, word, 0, (1, 1, 1))
    return {(x, y) for y in range(H) for x in range(W) if f.px[y][x] != gen.BLACK}


def scene(word, rnd, frames, ms, cap):
    solid = word_cells(word)
    snow = set()                         # лежащий снег
    flakes = []                          # летящие: [x, y(float), скорость]

    def blocked(x, y):
        return y >= H or (x, y) in solid or (x, y) in snow or not (0 <= x < W)

    def buried():
        # засыпано, когда над каждым столбцом букв лежит снег
        tops = {}
        for x, y in solid:
            tops[x] = min(tops.get(x, H), y)
        return all((x, y - 1) in snow for x, y in tops.items())

    # 1. падает снег, копится на буквах и на земле
    t = 0
    spawning = True
    while spawning or flakes:
        # снег идёт, пока слово не засыпано (но не дольше cap кадров)
        spawning = spawning and t < cap and not buried()
        rate = 1.0 + 2.2 * min(1.0, t / 30)
        if spawning:
            n = int(rate) + (rnd.random() < rate % 1)
            for _ in range(n):
                flakes.append([rnd.randrange(W), -1.0, rnd.uniform(0.45, 0.8)])
        still = []
        for fl in flakes:
            x, y, v = fl
            ny = y + v
            # проверяем каждую целую строку, через которую пролетаем
            cy = int(y) if y >= 0 else -1
            stop = False
            while cy < int(ny):
                if blocked(x, cy + 1):
                    stop = True
                    break
                cy += 1
            if stop:
                # иногда скатывается по склону, как настоящий снег
                for side in rnd.sample((-1, 1), 2):
                    if rnd.random() < 0.35 and not blocked(x + side, cy + 1) and not blocked(x + side, cy):
                        x += side
                        break
                else:
                    if cy >= 0:
                        snow.add((x, cy))
                    continue
                fl[0], fl[1] = x, float(cy)
                still.append(fl)
                continue
            fl[1] = ny
            # лёгкий снос ветром
            if rnd.random() < 0.08:
                nx = x + rnd.choice((-1, 1))
                if not blocked(nx, int(ny)):
                    fl[0] = nx
            still.append(fl)
        flakes = still
        f = gen.Frame()
        draw_word(f, word)
        for x, y in snow:
            f.set(x, y, SNOW)
        for x, y, _ in flakes:
            if y >= 0:
                f.set(x, int(y), FLAKE)
        frames.append(f)
        ms.append(60)
        t += 1

    # пауза — слово под снегом
    for _ in range(6):
        f = gen.Frame()
        draw_word(f, word)
        for x, y in snow:
            f.set(x, y, SNOW)
        frames.append(f)
        ms.append(80)

    # 2. встряхивается: сначала дрожит, снег подскакивает и осыпается вниз за край
    parts = []
    for x, y in snow:
        parts.append([float(x), float(y), rnd.uniform(-0.35, 0.35),
                      rnd.uniform(-0.9, -0.2), rnd.randint(0, 6) + (H - y) // 3])
    shake = [1, -1, 1, -1, 1, -1, 1, 0, -1, 1, 0, 0]
    k = 0
    while parts or k < len(shake):
        dx = shake[k] if k < len(shake) else 0
        f = gen.Frame()
        draw_word(f, word, dx)
        alive = []
        for p in parts:
            if p[4] > 0:
                p[4] -= 1                # ещё держится, дрожит вместе со словом
                f.set(round(p[0]) + dx, round(p[1]), SNOW)
                alive.append(p)
                continue
            p[3] += 0.22
            p[0] += p[2]
            p[1] += p[3]
            if p[1] < H + 1:
                f.set(round(p[0]), round(p[1]), SNOW)
                alive.append(p)
        parts = alive
        frames.append(f)
        ms.append(60)
        k += 1

    # чистое слово
    for _ in range(5):
        f = gen.Frame()
        draw_word(f, word)
        frames.append(f)
        ms.append(80)


def build():
    rnd = random.Random(7)
    frames, ms = [], []
    scene("СНЕГ", rnd, frames, ms, 70)
    scene("ИДЁТ", rnd, frames, ms, 70)
    gen.save("snow_text", frames, ms)


if __name__ == "__main__":
    build()
