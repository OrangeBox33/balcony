#!/usr/bin/env python3
"""Старый гном-мудрец тренируется со светящимся мечом: зажигает клинок,
рубит со шлейфом, прыгает с ударом в воздухе, крутит сальто и гасит меч."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 60
GROUND = 13

# лицом вправо, рука с мечом — точка (5, 6)
GNOME = [
    "..h...",
    "..hh..",
    ".hhhh.",
    "hhhhhh",
    ".sssns",
    ".BBBB.",
    "rrBBr.",
    ".rBBr.",
    ".r..r.",
    ".f..f.",
]
PAL = {
    "h": (60, 90, 255),       # колпак
    "s": (255, 150, 90),
    "n": (255, 90, 80),       # нос
    "B": (235, 235, 235),     # борода
    "r": (170, 90, 30),       # ряса
    "f": (120, 120, 130),
}
HAND = (5.5, 6)
CX, CY = 3, 5                 # центр вращения в спрайте
BLADE = (90, 255, 140)
CORE = (170, 255, 200)


def rot(dx, dy, th):
    c, s = math.cos(th), math.sin(th)
    return dx * c - dy * s, dx * s + dy * c


def draw(f, x, y, th, blade_a, blade_len, trail):
    """x, y — экранная позиция центра (CX, CY); th — поворот тела; blade_a — угол меча (рад, 0 = вправо)."""
    # тело: обратная выборка, чтобы при повороте не было дыр
    for py in range(H):
        for px in range(W):
            sx, sy = rot(px - x, py - y, -th)
            ix, iy = round(sx + CX), round(sy + CY)
            if 0 <= iy < len(GNOME) and 0 <= ix < 6:
                ch = GNOME[iy][ix]
                if ch != ".":
                    f.set(px, py, PAL[ch])
    hx, hy = rot(HAND[0] - CX, HAND[1] - CY, th)
    hx += x
    hy += y
    # шлейф: прошлые положения клинка, гаснущие
    for i, (a, k) in enumerate(trail):
        for r in range(2, int(blade_len) + 1):
            f.add(round(hx + r * math.cos(a)), round(hy + r * math.sin(a)), gen.scale(BLADE, k))
    if blade_len > 0:
        f.set(round(hx), round(hy), (200, 200, 210))   # рукоять
        for r in range(1, int(blade_len) + 1):
            f.set(round(hx + r * math.cos(blade_a)), round(hy + r * math.sin(blade_a)),
                  CORE if r < blade_len - 1 else BLADE)


def scenery(f):
    for x in range(W):
        f.set(x, GROUND + 0, (60, 45, 90)) if False else None
    for x in range(W):
        f.set(x, H - 1, (70, 50, 110))


def build():
    # ключевые состояния по кадрам: (x, y, th, blade_a, blade_len)
    st = []
    UP = -math.pi / 2
    gy = GROUND - 1 - (9 - CY)        # центр, когда ноги на земле
    x0 = 6
    # 1) стоит, лёгкое покачивание, зажигает меч (вертикально вверх)
    for t in range(14):
        st.append((x0, gy + (1 if t % 6 < 3 else 0) * 0, 0, UP, min(7, max(0, t - 4) * 1.0)))
    # 2) три маха на земле с шагом вперёд
    swings = [(UP, 0.5), (0.5, -2.3), (-2.3, 0.3)]
    x = x0
    for a0, a1 in swings:
        for k in range(7):
            p = min(1, k / 3)
            p = p * p * (3 - 2 * p)
            dip = 1 if 2 <= k <= 3 else 0
            st.append((x, gy + dip, 0, a0 + (a1 - a0) * p, 7))
        x += 2
    # 3) прыжок вперёд, в воздухе меч крутится полным кругом (удар в воздухе)
    N = 14
    for k in range(N + 1):
        p = k / N
        st.append((x + 6 * p, gy - 3 * 4 * p * (1 - p), 0, 0.3 + 2 * math.pi * p, 7))
    x += 6
    for k in range(4):                 # приземление, присед
        st.append((x, gy + (1 if k < 2 else 0), 0, 0.3 + 0.2 * k, 7))
    # 4) сальто назад через голову обратно к началу
    N = 18
    xs = x
    for k in range(N + 1):
        p = k / N
        st.append((xs + (x0 - xs) * p, gy - 3 * 4 * p * (1 - p), -2 * math.pi * p, UP - 2 * math.pi * p, 7))
    # 5) приземлился, поза, меч гаснет
    for k in range(14):
        st.append((x0, gy + (1 if k < 2 else 0), 0, UP, max(0, 7 - max(0, k - 5))))

    frames = []
    hist = []
    for i, (x, y, th, a, ln) in enumerate(st):
        f = gen.Frame()
        scenery(f)
        trail = []
        for j, ha in enumerate(reversed(hist[-4:])):
            if abs(ha - a) > 0.15 and ln > 0:
                trail.append((ha, 0.95 - 0.18 * j))
        draw(f, round(x), round(y), th, a, ln, trail)
        hist.append(a)
        frames.append(f)
    gen.save("sage_saber", frames, MS)


if __name__ == "__main__":
    build()
