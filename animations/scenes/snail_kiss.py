#!/usr/bin/env python3
"""Улитка ползёт «гармошкой», посередине останавливается, делает «чмок» —
из губ вылетают сердечки, — и ползёт дальше."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
MS = 80
GROUND = 13

# лицом вправо; колонки 0–7 — раковина (подтягивается), 8–14 — голова и передняя часть ноги
SHELL = [
    "........",
    "........",
    "..SSSS..",
    ".SDDDDS.",
    "SDSSSSDS",
    "SDSDDSDS",
    "SDSSDDS.",
    "bbbbbbbb",
]
HEAD = [
    "...w.w.",
    "...b.b.",
    "...bbb.",
    "...bbb.",
    "..bbbl.",
    ".bbbb..",
    "bbbb...",
    "bbb....",
]
PAL = {
    "S": (240, 130, 30),
    "D": (255, 225, 140),     # спираль светлее раковины — тёмная на диодах пропадает
    "b": (120, 220, 90),
    "w": (255, 255, 255),
    "l": (255, 60, 140),
}
HEART_S = [".r.r.", "rrrrr", ".rrr.", "..r.."]
HEART_XS = ["r.r", "rrr", ".r."]


def draw_snail(f, x, stretch, t, pucker=False, eyes_closed=False):
    f.sprite(SHELL, x, GROUND - 8, pal=PAL)
    hx = x + 8 + stretch
    rows = HEAD[:]
    # рожки покачиваются
    if (t // 4) % 2:
        rows = [".. w.w.".replace(" ", "."), "...b.b."] + rows[2:]
    if eyes_closed:
        rows = [r.replace("w", "b") for r in rows]
    f.sprite(rows, hx, GROUND - 8, pal=PAL)
    if stretch:     # нога тянется — закрываем щель между раковиной и головой
        f.set(x + 8, GROUND - 1, PAL["b"])
    if pucker:      # губки трубочкой
        f.set(hx + 6, GROUND - 4, PAL["l"])
        f.set(hx + 5, GROUND - 5, PAL["l"])
        f.set(hx + 5, GROUND - 3, PAL["l"])
    return hx + 6, GROUND - 4      # где губы


def scenery(f, t):
    for x in range(W):
        f.set(x, GROUND, (40, 95, 70))
    for gx in (2, 9, 17, 24):                       # травинки
        f.set(gx, GROUND - 1, (30, 140, 50))
    f.set(25, GROUND - 2, (255, 220, 0))           # цветок
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        f.set(25 + dx, GROUND - 2 + dy, (255, 90, 170))
    f.set(25, GROUND - 1, (30, 140, 50))


def build():
    frames = []
    STOP = 7                       # раковина у этой колонки — улитка посередине
    t = 0

    def crawl(x_from, x_to):
        nonlocal t
        x = x_from
        while x < x_to:
            for stretch in (0, 1):
                f = gen.Frame()
                scenery(f, t)
                draw_snail(f, x, stretch, t)
                frames.append(f)
                t += 1
            x += 1                  # голова ушла вперёд — раковина подтянулась

    crawl(-15, STOP)

    # остановилась: моргнула, губки трубочкой — «чмок» — сердечки улетают
    hearts = []
    for i in range(36):
        f = gen.Frame()
        scenery(f, t)
        pucker = 4 <= i < 12
        lx, ly = draw_snail(f, STOP, 0, t, pucker=pucker, eyes_closed=i in (2, 3) or 8 <= i < 12)
        if i == 10:
            hearts.append((lx + 1, ly - 1, t, HEART_S))
        if i == 16:
            hearts.append((lx + 1, ly - 1, t, HEART_XS))
        for hx, hy, born, shape in hearts:
            age = t - born
            if age > 22:
                continue
            sx = hx + age * 0.35 + math.sin(age * 0.6) * 0.8
            sy = hy - 2 - age * 0.38
            k = 1 if age < 12 else 1 - (age - 12) / 12
            spr = HEART_XS if age < 3 else shape
            f.sprite(spr, round(sx - len(spr[0]) / 2), round(sy), pal={"r": gen.scale((255, 30, 90), k)})
        frames.append(f)
        t += 1

    crawl(STOP, W + 1)
    for _ in range(4):
        f = gen.Frame()
        scenery(f, t)
        frames.append(f)
        t += 1
    gen.save("snail_kiss", frames, MS)


if __name__ == "__main__":
    build()
