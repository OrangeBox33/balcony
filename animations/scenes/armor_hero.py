#!/usr/bin/env python3
"""Бронированный герой (красно-золотой): влетает головой вперёд, приземляется у центра,
стреляет лучом из ладони — рука от отдачи уходит назад-вверх, корпус качается, — и улетает."""
import math
import random
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 60
GROUND = 13

C = {
    "R": (200, 20, 10),     # красная броня: шлем, корпус, плечи, бёдра, ботинки
    "r": (140, 10, 5),      # тень красного: пояс
    "Y": (230, 160, 20),    # золото: маска, предплечья, кисти, голени
    "E": (180, 230, 255),   # глаза и реактор
}

# стройный силуэт (руки прижаты) — для полёта и поворотов
SLIM = [
    ".RRR.",
    ".RYE.",
    ".RYY.",
    "RRRRR",
    "RRERR",
    "YRRRY",
    "YrrrY",
    ".R.R.",
    ".Y.Y.",
    ".Y.Y.",
    "RR.RR",
]
# стоит: руки по бокам (правую руку рисуем отдельно — ей целиться)
STAND = [
    "..RRR..",
    "..RYE..",
    "..RYY..",
    ".RRRRR.",
    "R.RER..",
    "Y.RRR..",
    "Y.rrr..",
    "..R.R..",
    "..Y.Y..",
    "..Y.Y..",
    ".RR.RR.",
]


def sprite_img(rows):
    w = max(len(r) for r in rows)
    im = Image.new("RGBA", (w, len(rows)), (0, 0, 0, 0))
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != ".":
                im.putpixel((x, y), C[ch] + (255,))
    return im


SLIM_IMG = sprite_img(SLIM)


def paste_rotated(f, angle, cx, cy):
    """Стройный силуэт, повёрнутый на angle градусов (−90 — летит головой вправо), центр в (cx, cy)."""
    im = SLIM_IMG.rotate(angle, resample=Image.Resampling.NEAREST, expand=True)
    ox, oy = round(cx - im.width / 2), round(cy - im.height / 2)
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = im.getpixel((x, y))
            if a:
                f.set(ox + x, oy + y, (r, g, b))
    return im, ox, oy


def flame(t, k):
    """Выхлоп ботинок: мерцает; k — 0 у сопла (белый), дальше голубее."""
    flick = 0.75 + 0.25 * ((t * 7 + k * 3) % 5) / 4
    base = [(220, 245, 255), (120, 200, 255), (50, 130, 255)][min(k, 2)]
    return gen.scale(base, flick)


def jets_down(f, x_left, y_feet, t, length=3):
    for bx in (x_left, x_left + 3):
        for k in range(length):
            if k < length - 1 or t % 2:
                f.set(bx + (k % 2 == 1 and t % 3 == 0), y_feet + 1 + k, flame(t, k))
                f.set(bx + 1, y_feet + 1 + k, flame(t, k))


def jets(f, cx, cy, ang, t, length):
    """Пламя из ботинок стройного силуэта, повёрнутого на ang (как в paste_rotated).
    Направление и место считаются от тела — при развороте пламя поворачивается плавно, без скачков."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    n = int(length)
    for bx in (-2.0, -1.0, 1.0, 2.0):            # два ботинка по 2 точки (относительно центра силуэта)
        for k in range(n + 1):
            if k == n and (length - n < 0.5 or t % 2):   # кончик мерцает
                continue
            by = 6.0 + k                         # ниже подошв, по оси тела
            x = cx + bx * ca + by * sa
            y = cy - bx * sa + by * ca
            f.set(round(x - 0.5), round(y - 0.5), flame(t, min(k, 2)))


def jets_back(f, x_tail, cy, t, length=4):
    """Пламя назад (влево) от ботинок при горизонтальном полёте."""
    for dy in (-2, 1):
        for k in range(length):
            if k < length - 1 or t % 2:
                f.set(x_tail - 1 - k, round(cy) + dy, flame(t, k))
                f.set(x_tail - 1 - k, round(cy) + dy + 1, flame(t, k))


def ease_out(p):
    p = max(0.0, min(1.0, p))
    return 1 - (1 - p) ** 2


def ease_in(p):
    p = max(0.0, min(1.0, p))
    return p * p


def build():
    rnd = random.Random(5)
    stars = [(rnd.randrange(W), rnd.randrange(0, 10), rnd.randrange(6)) for _ in range(10)]
    frames = []

    def frame():
        f = gen.Frame()
        t = len(frames)
        for sx, sy, ph in stars:
            if (t // 4 + ph) % 6:
                f.set(sx, sy, (110, 110, 150))
        for x in range(W):
            f.set(x, GROUND, (70, 70, 95))
        return f, t

    X0 = 10                 # где стоит (левый край спрайта STAND)
    Y0 = GROUND - len(STAND)
    CX_STAND = X0 + 3.5     # центр стройного силуэта, когда он вертикально над точкой посадки

    # 1. влетает головой вперёд и тормозит
    N_IN = 22
    for i in range(N_IN):
        f, t = frame()
        cx = -8 + (CX_STAND + 8) * ease_out(i / (N_IN - 1))
        cy = 5.5
        paste_rotated(f, -90, cx, cy)
        jets(f, cx, cy, -90, t, 3.5 - 1.5 * max(0.0, (i - (N_IN - 8)) / 7))
        frames.append(f)

    # 2. разворачивается ногами вниз и опускается на землю
    N_TURN = 8
    for i in range(N_TURN):
        f, t = frame()
        p = i / (N_TURN - 1)
        ang = -90 * (1 - p)
        cy = 5.5 + (GROUND - 5.5 - len(SLIM) / 2) * ease_in(p)
        paste_rotated(f, ang, CX_STAND, cy)
        jets(f, CX_STAND, cy, ang, t, 2.0 - 0.8 * p)
        frames.append(f)

    # пыль при посадке
    def stand(f, dx=0, dy=0, arm=None, crouch=False):
        rows = STAND[:]
        if crouch:      # присел: ноги короче на строку
            rows = STAND[:7] + STAND[8:]
            dy += 1
        f.sprite([r.replace(".", ".") for r in rows], X0 + dx, Y0 + dy, pal=C)
        sx, sy = X0 + dx + 5, Y0 + dy + 4          # плечо правой руки
        if arm is None:
            arm = (90, 3)
        ang, ext = arm
        pts = []
        for k in range(1, ext + 1):
            pts.append((round(sx + k * math.cos(math.radians(ang)) * 0.95), round(sy + k * math.sin(math.radians(ang)))))
        for j, p in enumerate(pts):     # плечо красное, предплечье и кисть золотые
            f.set(p[0], p[1], C["R"] if j == 0 and len(pts) > 2 else C["Y"])
        return pts[-1]

    for i in range(4):
        f, t = frame()
        stand(f, crouch=i < 2)
        if i < 3:
            for dx in (-1, 0, 7, 8):
                f.set(X0 + dx - (i if dx < 0 else -i), GROUND - 1, (120, 110, 100))
        frames.append(f)
    for _ in range(5):
        f, t = frame()
        stand(f)
        frames.append(f)

    # 3. поднимает руку
    for ang in (60, 35, 15, 0):
        f, t = frame()
        stand(f, arm=(ang, 3))
        frames.append(f)

    # 4. заряд: ладонь разгорается
    for i in range(9):
        f, t = frame()
        palm = stand(f, arm=(0, 3))
        k = (i + 1) / 9
        f.set(palm[0], palm[1], gen.scale((150, 255, 255), 0.5 + 0.5 * k))
        if i >= 3:
            for d in ((1, 0), (0, -1), (0, 1)):
                f.add(palm[0] + d[0], palm[1] + d[1], gen.scale((0, 160, 255), 0.4 + 0.6 * k * (0.7 + 0.3 * (t % 2))))
        frames.append(f)

    # 5. выстрел: луч мгновенно до края, рука от отдачи уходит назад-вверх, корпус качается назад
    #    (отдача — по кадрам: смещение корпуса dx, рука: угол и длина)
    RECOIL = [(-1, (-25, 2)), (-1, (-20, 2)), (-1, (-12, 2)), (0, (-6, 3)), (0, (-2, 3)), (0, (0, 3))]
    beam_y = Y0 + 4
    beam_x0 = X0 + 5 + 3 + 1
    N_BEAM = 12
    for i in range(N_BEAM + 4):
        f, t = frame()
        dx, arm = RECOIL[i] if i < len(RECOIL) else (0, (0, 3))
        if i >= N_BEAM:
            arm = ((0, 30, 60, 90)[i - N_BEAM], 3)     # опускает руку
        palm = stand(f, dx=dx, arm=arm)
        if i < N_BEAM:
            fade = 1 - i / N_BEAM
            reach = W if i > 0 else (beam_x0 + W) // 2
            for x in range(beam_x0, reach):
                core = (255, 255, 255) if i < 6 else (170, 250, 255)
                f.set(x, beam_y, gen.scale(core, 0.55 + 0.45 * fade))
                if i < 7 and (x + t) % 5:
                    for yy in (beam_y - 1, beam_y + 1):
                        f.add(x, yy, gen.scale((0, 170, 255), 0.75 * fade))
            if i < 2:   # вспышка у ладони
                for ddx in (-1, 0, 1):
                    for ddy in (-1, 0, 1):
                        f.add(palm[0] + ddx + 1, palm[1] + ddy, (120, 220, 255))
            if 0 < i < 8:   # искры в точке попадания у края
                for _ in range(3):
                    f.set(W - 1 - rnd.randrange(3), beam_y + rnd.choice((-2, -1, 1, 2)), (255, 230, 150))
        frames.append(f)

    for _ in range(4):
        f, t = frame()
        stand(f)
        frames.append(f)

    # 6. присед, ботинки загораются — и улетает вправо, ложась горизонтально
    for i in range(4):
        f, t = frame()
        stand(f, crouch=True)
        if i >= 2:
            jets_down(f, X0 + 1, GROUND - 1, t, 1)
        frames.append(f)
    N_OUT = 16
    for i in range(N_OUT):
        f, t = frame()
        p = i / (N_OUT - 1)
        ang = -90 * min(1.0, p * 1.6)
        cx = CX_STAND + 26 * ease_in(p)
        cy = (GROUND - len(SLIM) / 2) - 5 * ease_out(min(1.0, p * 1.8))
        paste_rotated(f, ang, cx, cy)
        jets(f, cx, cy, ang, t, 1.5 + 2.0 * min(1.0, p * 2))
        frames.append(f)

    for _ in range(6):
        f, t = frame()
        frames.append(f)
    gen.save("armor_hero", frames, MS)


if __name__ == "__main__":
    build()
