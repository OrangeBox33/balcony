#!/usr/bin/env python3
"""Жёлтая машина въезжает, встаёт и в три рывка («хоп-хоп-хоп») превращается в робота,
принимает геройскую позу, складывается обратно и уезжает вправо."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H

PAL = {
    "y": (255, 190, 0),    # жёлтый корпус
    "c": (0, 190, 255),    # стёкла
    "x": (150, 150, 165),  # металл, колёса
    "W": (255, 255, 255),  # фара, ступица
    "r": (255, 0, 0),      # стоп-сигнал
    "e": (0, 255, 255),    # глаза робота
}
ROAD = (100, 100, 110)
X0 = 7                     # где машина останавливается (ширина спрайтов 14)

CAR = [
    "....yyyyyy....",
    "...ycccyccy...",
    "yyyyyyyyyyyyyy",
    "ryyyyyyyyyyyyW",
    "yxxxyyyyyyxxxy",
    ".xxx......xxx.",
]
WHEELS = [(1, 4), (10, 4)]   # левый верхний угол колёс 3×2

STEP1 = [                    # машина встала на ноги
    "....yyyyyy....",
    "...ycccyccy...",
    "yyyyyyyyyyyyyy",
    "ryyyyyyyyyyyyW",
    "yxxxyyyyyyxxxy",
    "....xx..xx....",
    "....yy..yy....",
    "....yy..yy....",
    "...xxx..xxx...",
    "...yyy..yyy...",
]
STEP2 = [                    # корпус стал грудью, вышли руки
    "..yyy....yyy..",
    "..yyyyyyyyyy..",
    ".yyy.cccc.yyy.",
    ".yy..yyyy..yy.",
    ".yy..yyyy..yy.",
    ".xx..xxxx..xx.",
    ".....yyyy.....",
    "....yy..yy....",
    "....yy..yy....",
    "...xxx..xxx...",
    "...yyy..yyy...",
]
ROBOT = [                    # выскочила голова
    ".....y..y.....",
    ".....yyyy.....",
    ".....yeey.....",
    "..yyyyyyyyyy..",
    ".yyy.cccc.yyy.",
    ".yy..yyyy..yy.",
    ".yy..yyyy..yy.",
    ".xx..xxxx..xx.",
    ".....yyyy.....",
    "....yy..yy....",
    "....yy..yy....",
    "...xxx..xxx...",
    "...yyy..yyy...",
]
HERO = [                     # кулак вверх
    ".....y..y..xx.",
    ".....yyyy..yy.",
    ".....yeey..yy.",
    "..yyyyyyyyyy..",
    ".yyy.cccc.yy..",
    ".yy..yyyy.....",
    ".yy..yyyy.....",
    ".xx..xxxx.....",
    ".....yyyy.....",
    "....yy..yy....",
    "....yy..yy....",
    "...xxx..xxx...",
    "...yyy..yyy...",
]

# искры на суставах для каждого «хопа» (координаты относительно спрайта)
SPARKS = {
    "STEP1": [(4, 5), (9, 5)],
    "STEP2": [(1, 2), (12, 2)],
    "ROBOT": [(6, 2)],
}


def build():
    frames, ms = [], []

    def draw(spr, x, y=None, spin=0, sparks=(), speed=0, eyes=None, dur=80):
        f = gen.Frame()
        gen.floor(f, ROAD)
        if y is None:
            y = H - 1 - len(spr)
        # полосы скорости позади машины
        for k in range(speed):
            for ly, ln in ((y + 1, 3), (y + 3, 4)):
                for i in range(ln):
                    f.set(x - 2 - k * 5 - i, ly, (110, 110, 120))
        f.sprite(spr, x, y, pal=PAL)
        if spr is CAR:
            for wx, wy in WHEELS:
                # ступица крутится: белая точка бегает по ободу
                hub = [(1, 0), (2, 1), (1, 1), (0, 0)][spin % 4]
                f.set(x + wx + hub[0], y + wy + hub[1], PAL["W"])
        if eyes:
            for ex in (6, 7):
                f.set(x + ex, y + 2, eyes)
        for sx, sy in sparks:
            f.sprite(gen.SPARK, x + sx - 1, y + sy - 1)
        frames.append(f)
        ms.append(dur)

    # 1. въезд слева с торможением
    N_IN = 18
    for i in range(N_IN + 1):
        u = i / N_IN
        x = round(-15 + (X0 + 15) * (1 - (1 - u) ** 2))
        draw(CAR, x, spin=i, speed=2 if u < 0.6 else (1 if u < 0.85 else 0))
    for _ in range(5):
        draw(CAR, X0, dur=90)

    # 2. хоп-хоп-хоп: каждый шаг — подскок на 1 пиксель с искрами, потом пауза
    for name, spr in (("STEP1", STEP1), ("STEP2", STEP2), ("ROBOT", ROBOT)):
        y = H - 1 - len(spr)
        draw(spr, X0, y - 1, sparks=SPARKS[name], dur=90)
        draw(spr, X0, y, sparks=SPARKS[name][:1] if len(SPARKS[name]) > 1 else (), dur=80)
        eyes = (255, 255, 255) if spr is ROBOT else None
        for _ in range(5):
            draw(spr, X0, y, eyes=eyes, dur=90)
            eyes = None

    # 3. геройская поза, глаза вспыхивают
    for i in range(14):
        eyes = (255, 255, 255) if i in (0, 1, 7, 8) else None
        draw(HERO, X0, eyes=eyes, dur=100)
    for _ in range(4):
        draw(ROBOT, X0, dur=90)

    # 4. складывается обратно — быстрее
    for name, spr in (("STEP2", STEP2), ("STEP1", STEP1), ("CAR", CAR)):
        y = H - 1 - len(spr)
        sp = SPARKS.get(name, [(3, 2), (10, 2)])
        draw(spr, X0, y - 1, sparks=sp, dur=80)
        for _ in range(3):
            draw(spr, X0, y, dur=80)
    for _ in range(3):
        draw(CAR, X0, dur=90)

    # 5. газ — и уезжает вправо
    N_OUT = 14
    for i in range(1, N_OUT + 1):
        u = i / N_OUT
        x = round(X0 + (W + 1 - X0) * u ** 2)
        draw(CAR, x, spin=i, speed=0 if u < 0.25 else (1 if u < 0.5 else 2))
    draw(CAR, W + 5, dur=200)

    gen.save("transformer", frames, ms)


if __name__ == "__main__":
    build()
