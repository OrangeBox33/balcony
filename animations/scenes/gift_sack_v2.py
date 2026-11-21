#!/usr/bin/env python3
"""Мешок с подарками: большой красный мешок, перевязанный верёвкой. Из горловины по очереди
выглядывают и прячутся подарок, конфета и мандарин. Мешок слегка шевелится. Петля без шва."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 60
SLOT = 50                    # кадров на одного «выглядывающего»
N = SLOT * 3                 # 150 кадров = 9 с

SACK_X = 5                   # мешок 18 столбцов: x 5..22, центр 13.5
# r — мешок, f — раскрытый край горловины (чуть светлее), y — верёвка, h — блик
NECK = [                     # ряды 3..5: края горловины разошлись, сама горловина, верёвка
    "....ff......ff....",
    "....ffffffffff....",
    "......yyyyyy......",
]
BODY = [                     # ряды 6..13; узел верёвки — два свисающих конца
    ".....rrryyrrr.....",
    "...rrrryrryrrrr...",
    "..rrhrrkrrrrkrrr..",
    ".rrhrrrkrrrrrkrrr.",
    ".rhrrrrrrrrrrrrrr.",
    ".rhrrrrrrrrrrrrrr.",
    ".rrrrrrrrrrrrrrrr.",
    "..rrrrrrrrrrrrrr..",
]
NECK_Y, BODY_Y = 3, 6
SACK_PAL = {
    "r": (200, 15, 15),
    "f": (240, 40, 35),
    "h": (255, 110, 90),
    "k": (240, 50, 40),      # складки ткани — светлее мешка, иначе пропадут
    "y": (235, 170, 70),
}

ITEMS = [
    # подарок: синяя коробка с золотой лентой и бантиком
    ([".y.y.",
      "BByBB",
      "yyyyy",
      "BByBB",
      "BByBB"], {"B": (20, 70, 255), "y": (255, 200, 40)}),
    # конфета в фантике: розовая с белой полоской, «хвостики» жёлтые
    (["y.....y",
      "yymWmyy",
      "y.mmm.y"], {"y": (255, 190, 0), "m": (255, 30, 140), "W": (255, 255, 255)}),
    # мандарин с листиком
    ([".gG..",
      ".ooo.",
      "oWooo",
      "ooooo",
      ".ooo."], {"o": (255, 110, 0), "W": (255, 200, 110), "g": (0, 210, 0), "G": (0, 130, 20)}),
]

TWINK = [(2, 1), (25, 1), (5, 4), (22, 4), (1, 7), (26, 7)]


def ease(a):
    a = min(max(a, 0.0), 1.0)
    return a * a * (3 - 2 * a)


def top_shift(t):
    """Горловина мягко покачивается: −1, 0, +1 (6 раз за петлю)."""
    return round(0.8 * math.sin(2 * math.pi * t * 6 / N))


HIDDEN = BODY_Y              # верх предмета здесь — его целиком закрывает мешок
UP, LOOK, DOWN = 4, 14, 38   # когда вылезает, когда оглядывается, когда прячется (кадр в слоте)


def item_state(p, top):
    """По кадру внутри слота: верх предмета (y) и сдвиг вбок, чтобы «оглядывался»."""
    if p < UP:
        return HIDDEN, 0
    if p < LOOK:                                 # вылезает
        return round(HIDDEN - (HIDDEN - top) * ease((p - UP) / (LOOK - UP))), 0
    if p < DOWN:                                 # оглядывается: влево-вправо, разок приседает
        q = (p - LOOK) * 16 // (DOWN - LOOK)
        dx = [0, 0, -1, -1, -1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0][q]
        dy = 1 if q in (12, 13) else 0
        return top + dy, dx
    if p < DOWN + 8:                             # прячется
        return round(top + (HIDDEN - top) * ease((p - DOWN) / 8)), 0
    return HIDDEN, 0


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        for i, (x, y) in enumerate(TWINK):
            k = 0.5 + 0.5 * math.sin(2 * math.pi * (t * 2 / N + i / len(TWINK)))
            if k > 0.4:
                f.set(x, y, gen.scale((255, 220, 150), 0.4 + 0.5 * k))

        sh = top_shift(t)
        slot, p = divmod(t, SLOT)
        rows, pal = ITEMS[slot]
        iy, idx = item_state(p, 1 if len(rows) < 5 else 0)
        iw = gen.width(rows)
        f.sprite(rows, round(13.5 - iw / 2) + idx + sh, iy, pal=pal)

        # тело мешка: когда предмет толкается наружу, бока чуть раздуваются
        puff = 1 if UP <= p < UP + 6 else 0
        for dy, row in enumerate(BODY):
            for dx, ch in enumerate(row):
                if ch != ".":
                    f.set(SACK_X + dx, BODY_Y + dy, SACK_PAL[ch])
            if puff and 4 <= dy <= 6:
                l, r = row.index("r"), row.rindex("r")
                f.set(SACK_X + l - 1, BODY_Y + dy, SACK_PAL["r"])
                f.set(SACK_X + r + 1, BODY_Y + dy, SACK_PAL["r"])
        f.sprite(NECK, SACK_X + sh, NECK_Y, pal=SACK_PAL)
        frames.append(f)
    gen.save("gift_sack_v2", frames, MS)


if __name__ == "__main__":
    build()
