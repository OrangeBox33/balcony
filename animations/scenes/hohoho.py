#!/usr/bin/env python3
"""«ХО-ХО-ХО»: три слога прыгают как мячики по очереди, на каждом ударе о пол меняют цвет."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
F = gen.FONT5
SYL_W = gen.text_width("ХО", F)          # 7
DASH = 1                                 # тире в 1 пиксель — иначе фраза не влезает в 28
XS = [0, 10, 20]                         # левый край каждого слога; тире в столбцах 8 и 18
FLOOR = 6                                # верх букв, когда слог стоит на полу (строки 6..10)
COLORS = [(255, 0, 0), (255, 255, 255), (0, 220, 0)]
DASH_C = (255, 190, 0)
G = 0.32                                 # гравитация, пикс/кадр²


def vy_for(h):
    """Начальная скорость вверх, чтобы подпрыгнуть на h пикселей."""
    return -math.sqrt(2 * G * h)


class Ball:
    def __init__(self, i, x, t0, hops):
        self.i, self.x, self.t0 = i, x, t0
        self.y, self.vy = -6.0, 0.0
        self.hops = list(hops)       # высоты прыжков по порядку; потом лежит
        self.n = len(hops)
        self.hits = -1               # до первого удара — без цвета (белый)

    def step(self, t):
        if t < self.t0:
            return None
        if self.y >= FLOOR and self.vy == 0:
            return None
        self.vy += G
        self.y += self.vy
        if self.y >= FLOOR:
            self.y = FLOOR
            self.hits += 1
            if self.hops:
                self.vy = vy_for(self.hops.pop(0))
            else:
                self.vy = 0
            return "hit"
        return None

    def color(self):
        # сдвиг подобран так, что в конце слоги стоят красный-белый-зелёный
        return COLORS[(self.hits - self.n + self.i) % 3] if self.hits >= 0 else (255, 200, 0)


def build():
    frames, ms = [], []
    # слоги вылетают по очереди; потом прыгают «волной» и затихают
    wave = [6, 6, 6, 6, 6, 6, 6, 4, 2, 1]
    balls = [Ball(i, XS[i], i * 7, wave) for i in range(3)]
    dust = []                        # искорки от удара: x, y, vx, vy, жизнь, цвет
    t = 0
    calm = 0
    while calm < 22:
        f = gen.Frame()
        # тире появляются, когда соседние слоги уже на месте
        for i, bx in enumerate((8, 18)):
            if balls[i].hits >= 0 and balls[i + 1].hits >= 0:
                f.set(bx, FLOOR + 2, DASH_C)
        for b in balls:
            if b.step(t) == "hit":
                c = b.color()
                for dx, vx in ((0, -0.7), (SYL_W - 1, 0.7), (1, -0.4), (SYL_W - 2, 0.4)):
                    dust.append([b.x + dx, FLOOR + 5, vx, -0.5, 5, c])
            if t < b.t0:
                continue
            y = round(b.y)
            c = b.color()
            f.text("ХО", b.x, y, c, F)
        for d in dust:
            d[0] += d[2]
            d[1] += d[3]
            d[3] += 0.15
            d[4] -= 1
            f.add(round(d[0]), round(d[1]), gen.scale(d[5], 0.5 + d[4] / 10))
        dust = [d for d in dust if d[4] > 0]
        # пол — светлая снежная полоска
        for x in range(W):
            f.set(x, FLOOR + 6, (90, 110, 160))
        if all(b.vy == 0 and b.hits >= 0 for b in balls):
            calm += 1
        frames.append(f)
        ms.append(60)
        t += 1

    # финал: вся фраза мигает радугой из трёх цветов
    for k in range(18):
        f = gen.Frame()
        for i, b in enumerate(balls):
            f.text("ХО", b.x, FLOOR, COLORS[(i + k // 3) % 3], F)
        for bx in (8, 18):
            f.set(bx, FLOOR + 2, DASH_C)
        for x in range(W):
            f.set(x, FLOOR + 6, (90, 110, 160))
        frames.append(f)
        ms.append(80)

    gen.save("hohoho", frames, ms)


if __name__ == "__main__":
    build()
