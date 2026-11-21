#!/usr/bin/env python3
"""Собирает animations/gallery.html — все GIF из animations/wled/ на макете матрицы."""
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
WLED = ROOT / "wled"
ALPHA = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_"

TITLES = {
    "fight": "Драка",
    "boxer": "Боксёр и груша",
    "samurai": "Самурай приседает",
    "tree": "Ёлка",
    "fireworks": "Салют",
    "santa": "Дед Мороз на санях",
    "greeting": "С Новым годом!",
    "pikachu_bulb": "Пикачу и лампочка",
    "day_night": "День и ночь",
    "cheburashka_smoke": "Чебурашка курит",
    "banana_slip": "Банановая кожура",
    "dress_up": "Одевание",
    "smiley_draw": "Смайлик",
    "fruit_morph": "Фрукты",
    "beach": "Пляж",
    "volcano": "Вулкан",
    "bird_poop": "Птичка и ружьё",
    "spiderman": "Спайдермен",
    "transformer": "Трансформер",
    "surf": "Серфер на волне",
    "newyear_2027": "2026 → 2027",
    "hohoho": "Хо-хо-хо",
    "hello_neighbor": "Привет, сосед!",
    "snow_text": "Снег идёт",
    "smile_text": "Улыбнись",
    "santa_letter": "Дед Мороз, я был хорошим",
    "warmth": "Тепла",
    "tangerines": "Мандарины есть?",
    "all_good": "Всё будет хорошо",
    "garland_lives": "Тут живёт гирлянда",
    "heart_beat": "Бьющееся сердце",
    "earth": "Земля вращается",
    "campfire": "Костёр с искрами",
    "ded_moroz_gifts": "Дед Мороз и конфетти",
    "armor_hero": "Бронированный герой",
    "witch": "Ведьма на метле",
    "snail_kiss": "Улитка шлёт поцелуй",
    "blocks": "Падающие блоки",
    "sand_worm": "Песчаный червь и танк",
    "dune_worm": "Червь и танк",
    "sonic_rings": "Ёж собирает кольца",
    "minecraft_lava": "Майнкрафт: копнул в лаву",
    "sponge_pineapple": "Губка из ананаса",
    "mouse_star": "Звёздный мышонок",
    "plumber_flag": "Водопроводчик: уровень пройден",
    "bat_hero": "Бэтмен и бэтмобиль",
    "steel_flat": "Стальной блин",
    "wizard_patronus": "Экспекто Патронум",
    "bald_choke": "Ах ты!..",
    "bear_balloon": "Я тучка, я тучка!",
    "cat_mouse_hole": "Кот и норка: тыдыщ!",
    "green_master": "Зелёный мастер",
    "claw_car": "Когти против машины",
    "night_yard": "Ночной двор: фонарь и снег",
    "crane_blocks": "Кран строит дом",
    "winter_forest": "Лес под луной",
    "aurora": "Северное сияние",
    "bullfinch": "Снегирь на ветке",
    "bunny_drift": "Зайчик за сугробом",
    "snowflake_grow": "Растущая снежинка",
    "tree_spiral": "Ёлка со спиральной гирляндой",
    "retro_bulbs": "Ретро-гирлянда",
    "xmas_ball": "Ёлочный шар",
    "gift_surprise": "Подарок с сюрпризом",
    "snow_globe": "Снежный шар",
    "ded_moroz_face": "Портрет Деда Мороза",
    "ded_moroz_window": "Дед Мороз у окна",
    "gift_sack": "Мешок с подарками",
    "candy_canes": "Леденцы-тросточки",
    "candy_snow": "Конфетный снегопад",
    "gingerbread": "Пряничный человечек",
    "fireplace": "Камин и носки",
    "cocoa": "Кружка какао",
    "snow_cabin": "Домик в снегу",
    "sparkler": "Бенгальский огонь",
    "winter_forest_v2": "Ночной лес и луна",
    "forest_bunny": "Зайчик выглядывает из-за ёлки",
    "aurora_v2": "Северное сияние над лесом",
    "bullfinch_v2": "Снегирь чирикает",
    "snowman": "Снеговик машет",
    "tree_lights": "Ёлка с огоньками и подарками",
    "tree_spiral_v2": "Ёлка: гирлянда по спирали",
    "xmas_balls": "Ёлочные шары качаются",
    "gift_pile": "Гора подарков",
    "gift_open": "Подарок открывается",
    "gift_sack_v2": "Мешок: кто выглядывает",
    "mittens": "Варежки на верёвочке",
    "ded_moroz_wave": "Дед Мороз машет",
    "sleigh_city": "Сани над городом",
    "snegurochka": "Снегурочка кружится",
    "gingerbread_man": "Пряничный человечек танцует",
    "candy_canes_v2": "Леденцы-тросточки со звёздами",
    "gingerbread_house": "Пряничный домик",
    "cocoa_window": "Какао у окна",
    "tangerine_peel": "Мандарин раскрывается",
}


def pack(path):
    im = Image.open(path)
    frames, durs = [], []
    for i in range(getattr(im, "n_frames", 1)):
        im.seek(i)
        frames.append([im.convert("RGB").getpixel((x, y)) for y in range(im.height) for x in range(im.width)])
        durs.append(max(int(im.info.get("duration") or 100), 20))
    colors = sorted({c for f in frames for c in f})
    k = 1 if len(colors) <= 64 else 2
    def code(i):
        return ALPHA[i] if k == 1 else ALPHA[i // 64] + ALPHA[i % 64]
    idx = {c: code(i) for i, c in enumerate(colors)}
    return {
        "w": im.width, "h": im.height, "k": k,
        "p": ["%02x%02x%02x" % c for c in colors],
        "f": ["".join(idx[c] for c in f) for f in frames],
        "d": durs,
        "kb": round(path.stat().st_size / 1024, 1),
        "bytes": path.stat().st_size,
    }


def main():
    # python3 tools/gallery.py [папка_с_gif] [выходной.html]
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else WLED
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "gallery.html"
    order = list(TITLES)
    files = sorted(src.glob("*.gif"), key=lambda p: (order.index(p.stem) if p.stem in order else 999, p.stem))
    items = []
    for p in files:
        d = pack(p)
        d["name"] = p.stem
        d["title"] = TITLES.get(p.stem, p.stem)
        items.append(d)
    data = json.dumps(items, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    tpl = (Path(__file__).parent / "gallery.src.html").read_text()
    # плейлист для контроллера: {"often": {имя: раз подряд}, "long": {имя: секунд}} — стартовый выбор в галерее
    pl = ROOT / "playlist.json"
    playlist = pl.read_text() if pl.exists() and src == WLED else "null"
    out.write_text(tpl.replace("/*DATA*/[]", data).replace("/*PLAYLIST*/null", playlist.strip()))
    print(f"{out}: {len(items)} анимаций, {out.stat().st_size / 1024:.0f} КБ", file=sys.stderr)


if __name__ == "__main__":
    main()
