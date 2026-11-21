#!/usr/bin/env python3
"""Падающие блоки: фигуры падают и складываются, полные ряды вспыхивают и исчезают;
потом игра идёт вразнобой, стопка дорастает до верха — проигрыш, стакан заливается серым и очищается."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen  # noqa: E402

W, H = gen.W, gen.H
BW, BH = 8, 14              # стакан
BX = 10                     # левая колонка стакана на экране
MS = 45
WALL = (90, 90, 120)
GRAY = (120, 120, 130)

SHAPES = {   # клетки (x, y) в повороте 0
    "I": [(0, 1), (1, 1), (2, 1), (3, 1)],
    "O": [(1, 0), (2, 0), (1, 1), (2, 1)],
    "T": [(1, 0), (0, 1), (1, 1), (2, 1)],
    "S": [(1, 0), (2, 0), (0, 1), (1, 1)],
    "Z": [(0, 0), (1, 0), (1, 1), (2, 1)],
    "J": [(0, 0), (0, 1), (1, 1), (2, 1)],
    "L": [(2, 0), (0, 1), (1, 1), (2, 1)],
}
COLORS = {
    "I": (0, 220, 255), "O": (255, 210, 0), "T": (180, 0, 255), "S": (0, 220, 60),
    "Z": (255, 30, 30), "J": (30, 80, 255), "L": (255, 120, 0),
}


def rotations(kind):
    cells = SHAPES[kind]
    out = []
    for r in range(1 if kind == "O" else 4):
        c = cells
        for _ in range(r):
            c = [(-y, x) for x, y in c]          # поворот на 90°
        mx, my = min(x for x, _ in c), min(y for _, y in c)
        norm = sorted((x - mx, y - my) for x, y in c)
        if norm not in out:
            out.append(norm)
    return out


ROT = {k: rotations(k) for k in SHAPES}


def fits(board, cells, px, py):
    for x, y in cells:
        bx, by = px + x, py + y
        if bx < 0 or bx >= BW or by >= BH:
            return False
        if by >= 0 and board[by][bx]:
            return False
    return True


def drop_y(board, cells, px):
    y = -2
    if not fits(board, cells, px, y):
        return None
    while fits(board, cells, px, y + 1):
        y += 1
    return y


def place(board, cells, px, py, kind):
    b = [row[:] for row in board]
    for x, y in cells:
        if py + y < 0:
            return None                    # не влезла — проигрыш
        b[py + y][px + x] = kind
    full = [y for y in range(BH) if all(b[y])]
    return b, full


def clear(board, full):
    rest = [row for y, row in enumerate(board) if y not in full]
    return [[None] * BW for _ in full] + rest


def score(board, lines):
    heights = []
    holes = 0
    for x in range(BW):
        h = 0
        seen = False
        for y in range(BH):
            if board[y][x]:
                if not seen:
                    h = BH - y
                    seen = True
            elif seen:
                holes += 1
        heights.append(h)
    bump = sum(abs(a - b) for a, b in zip(heights, heights[1:]))
    return 0.76 * lines - 0.51 * sum(heights) - 0.36 * holes - 0.18 * bump


def options(board, kind):
    res = []
    for r, cells in enumerate(ROT[kind]):
        w = max(x for x, _ in cells) + 1
        for px in range(BW - w + 1):
            py = drop_y(board, cells, px)
            if py is None:
                continue
            res.append((r, px, py))
    return res


def simulate(seed, good):
    """Партия: первые good фигур — лучший ход, дальше — случайный. Список ходов до проигрыша."""
    rnd = random.Random(seed)
    board = [[None] * BW for _ in range(BH)]
    bag = []
    queue = []
    moves = []

    def next_kind():
        if not bag:
            bag.extend(rnd.sample(list(SHAPES), 7))
        return bag.pop()

    queue = [next_kind(), next_kind()]
    for n in range(80):
        kind = queue.pop(0)
        queue.append(next_kind())
        opts = options(board, kind)
        spawn = ROT[kind][0]
        if not opts or not fits(board, spawn, 3, 0):
            moves.append(("over", kind, queue[0]))
            return moves
        if n < good:
            best = max(opts, key=lambda o: (lambda pr: -1e9 if pr is None else score(clear(pr[0], pr[1]), len(pr[1])))(place(board, ROT[kind][o[0]], o[1], o[2], kind)))
        else:
            # «сдаёт»: ход из середины рейтинга — дыры копятся, но стопка растёт по всей ширине
            ranked = sorted(opts, key=lambda o: (lambda pr: -1e9 if pr is None else score(clear(pr[0], pr[1]), len(pr[1])))(place(board, ROT[kind][o[0]], o[1], o[2], kind)), reverse=True)
            best = rnd.choice(ranked[len(ranked) // 4: max(len(ranked) // 4 + 1, len(ranked) * 3 // 5)])
        r, px, py = best
        pr = place(board, ROT[kind][r], px, py, kind)
        if pr is None:
            moves.append(("over", kind, queue[0]))
            return moves
        b, full = pr
        moves.append(("move", kind, r, px, py, [row[:] for row in board], full, queue[0]))
        board = clear(b, full) if full else b
        last_board[0] = board
    return moves


last_board = [None]


def filled_rows(board):
    """Сколько рядов снизу заметно заполнены (больше половины клеток)."""
    n = 0
    for y in range(BH - 1, -1, -1):
        if sum(1 for c in board[y] if c) > BW // 2:
            n += 1
        else:
            break
    return n


def pick_game():
    """Ищем партию: несколько снесённых линий (есть «двойная»), проигрыш на 20–27 фигуре."""
    for seed in range(3000):
        moves = simulate(seed, good=12)
        if moves[-1][0] != "over":
            continue
        lines = [len(m[6]) for m in moves if m[0] == "move" and m[6]]
        if 22 <= len(moves) <= 34 and sum(lines) >= 4 and max(lines, default=0) >= 2 \
                and filled_rows(last_board[0]) >= 10:
            return moves
    raise RuntimeError("не нашли подходящую партию")


# ------------------------------------------------------------ отрисовка

def draw_static(f, board, lines, nxt):
    for y in range(H):
        f.set(BX - 1, y, WALL)
        f.set(BX + BW, y, WALL)
    for y in range(BH):
        for x in range(BW):
            k = board[y][x]
            if k:
                f.set(BX + x, y, GRAY if k == "#" else COLORS[k])
    f.text(str(lines), 1, 1, (200, 200, 220), gen.FONT3)
    if nxt:
        for x, y in ROT[nxt][0]:
            f.set(BX + BW + 3 + x, 2 + y, COLORS[nxt])


def build():
    moves = pick_game()
    frames = []
    lines = 0
    board = [[None] * BW for _ in range(BH)]

    def frame(board, piece=None, flash=(), nxt=None):
        f = gen.Frame()
        draw_static(f, board, lines, nxt)
        if piece:
            kind, cells, px, py = piece
            for x, y in cells:
                if py + y >= 0:
                    f.set(BX + px + x, py + y, COLORS[kind])
        for y in flash:
            for x in range(BW):
                f.set(BX + x, y, (255, 255, 255))
        frames.append(f)

    for m in moves:
        if m[0] == "over":
            break
        _, kind, r, px, py, before, full, nxt = m
        cells = ROT[kind][r]
        # появляется наверху, поворачивается, сдвигается к цели — и падает
        cx, cr, cy = 3, 0, -1
        while cr != r or cx != px:
            if cr != r:
                cr += 1
            elif cx != px:
                cx += 1 if px > cx else -1
            cy = min(cy + 1, py) if cy < 0 else cy
            frame(before, (kind, ROT[kind][cr], cx, cy), nxt=nxt)
        while cy < py:
            cy += 1
            frame(before, (kind, cells, cx, cy), nxt=nxt)
        after = [row[:] for row in before]
        for x, y in cells:
            after[py + y][px + x] = kind
        if full:
            for i in range(4):                       # полные ряды мигают
                frame(after, flash=full if i % 2 == 0 else (), nxt=nxt)
            lines += len(full)
            board = clear(after, full)
            frame(board, nxt=nxt)
        else:
            board = after

    # проигрыш: стопка заливается серым снизу вверх, затем стакан пустеет
    for _ in range(4):
        frame(board)
    for y in range(BH - 1, -1, -1):
        board = [row[:] for row in board]
        board[y] = ["#"] * BW
        frame(board)
    for _ in range(6):
        frame(board)
    for y in range(BH):
        board = [row[:] for row in board]
        board[y] = [None] * BW
        frame(board)
    lines = 0
    for _ in range(4):
        frame(board)
    gen.save("blocks", frames, MS)


if __name__ == "__main__":
    build()
