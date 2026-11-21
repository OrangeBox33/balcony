#!/usr/bin/env python3
"""Земля вращается среди мерцающих звёзд, вокруг ходит Луна (за планетой — прячется)."""
import math
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
CX, CY, RAD = 14.0, 7.0, 6.75      # планета во всю высоту
N = 120                             # кадров на оборот
MS = 70
TILT = math.radians(20)             # наклон оси
LIGHT = (-0.55, -0.35, 0.76)        # свет слева-сверху-спереди
SS = 3                              # сглаживание: 3×3 замера на диод

# Карта суши 48×24 (клетка 7,5°): для каждой полосы широт — отрезки столбцов с сушей.
# Столбец c — долгота −180 + 7,5·c, строка r — широта 90 − 7,5·r.
LAND = {
    2: [(2, 5), (8, 14), (17, 21), (26, 28), (32, 47)],
    3: [(1, 10), (13, 14), (18, 20), (21, 21), (25, 47)],
    4: [(3, 10), (13, 15), (23, 23), (24, 46)],
    5: [(7, 16), (23, 42)],
    6: [(7, 14), (23, 29), (30, 41), (42, 43)],
    7: [(8, 13), (22, 33), (34, 40), (41, 42)],
    8: [(9, 11), (12, 12), (22, 31), (33, 39)],
    9: [(10, 11), (12, 13), (22, 31), (33, 34), (36, 38)],
    10: [(11, 12), (22, 30), (34, 34), (37, 38), (40, 40)],
    11: [(13, 16), (24, 30), (37, 39)],
    12: [(13, 18), (25, 29), (38, 41), (43, 44)],
    13: [(14, 18), (25, 29), (30, 30), (41, 44)],
    14: [(14, 18), (25, 28), (30, 30), (40, 45)],
    15: [(15, 17), (25, 28), (39, 45)],
    16: [(15, 16), (26, 27), (40, 44), (47, 47)],
    17: [(15, 16), (43, 43), (47, 47)],
    18: [(15, 15)],
    19: [(15, 15)],
}

OCEAN = (0, 70, 230)
LAND_C = (30, 175, 40)
ICE = (235, 245, 255)


def surface(lat, lon):
    """Цвет поверхности в точке (градусы)."""
    if abs(lat) > 68:
        return ICE
    r = min(23, int((90 - lat) / 7.5))
    c = int(((lon + 180) % 360) / 7.5) % 48
    for a, b in LAND.get(r, []):
        if a <= c <= b:
            return LAND_C
    return OCEAN


def planet_pixel(x, y, rot):
    """Средний цвет диода по SS×SS замерам; None — если вне диска."""
    acc = [0.0, 0.0, 0.0]
    hits = 0
    lx, ly, lz = LIGHT
    ln = math.sqrt(lx * lx + ly * ly + lz * lz)
    for i in range(SS):
        for j in range(SS):
            nx = (x + (i + 0.5) / SS - CX) / RAD
            ny = (y + (j + 0.5) / SS - CY) / RAD
            d = nx * nx + ny * ny
            if d > 1:
                continue
            nz = math.sqrt(1 - d)
            # наклон оси: поворачиваем картинку в плоскости экрана
            tx = nx * math.cos(TILT) - ny * math.sin(TILT)
            ty = nx * math.sin(TILT) + ny * math.cos(TILT)
            lat = math.degrees(math.asin(max(-1, min(1, -ty))))
            lon = math.degrees(math.atan2(tx, nz)) + rot
            c = surface(lat, lon)
            light = max(0.0, (nx * lx + ny * ly + nz * lz) / ln)
            k = 0.45 + 0.75 * light               # ночная сторона тусклее, но видна
            for q in range(3):
                acc[q] += min(255, c[q] * k)
            hits += 1
    if hits < SS * SS * 0.35:
        return None
    return tuple(int(v / hits) for v in acc)


STARS = [(1, 1), (4, 9), (2, 12), (6, 3), (24, 2), (26, 8), (22, 12), (27, 13), (0, 6), (25, 5)]


def build():
    frames = []
    for t in range(N):
        f = gen.Frame()
        rot = -360 * t / N                        # вращение с запада на восток
        for k, (x, y) in enumerate(STARS):        # звёзды мерцают каждая в своём ритме
            v = 0.55 + 0.45 * math.sin(2 * math.pi * (t * (k % 3 + 1) / N * 4 + k * 0.37))
            f.set(x, y, gen.scale((255, 240, 200), max(v, 0.4)))
        # Луна: один оборот вокруг Земли за петлю, по наклонной орбите
        a = 2 * math.pi * t / N
        mx, my, mz = CX + 12.3 * math.cos(a), CY + 3.2 * math.sin(a), math.sin(a)
        x0, y0 = round(mx - 0.5), round(my - 0.5)
        moon = [(x0, y0), (x0 + 1, y0), (x0, y0 + 1), (x0 + 1, y0 + 1)]
        behind = mz < 0
        if behind:
            for x, y in moon:
                f.set(x, y, (200, 200, 190))
        for y in range(H):
            for x in range(W):
                c = planet_pixel(x, y, rot)
                if c:
                    f.set(x, y, c)
        if not behind:
            for x, y in moon:
                f.set(x, y, (230, 230, 215))
        frames.append(f)
    # общая палитра на всю анимацию: так GIF в разы меньше, разницы не видно
    imgs = [fr.image() for fr in frames]
    big = Image.new("RGB", (W, H * N))
    for i, im in enumerate(imgs):
        big.paste(im, (0, i * H))
    q = big.quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
    gen.save("earth", [q.crop((0, i * H, W, (i + 1) * H)) for i in range(N)], MS)


if __name__ == "__main__":
    build()
