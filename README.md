# Гирлянда на балконе

Матрица из адресной RGB-гирлянды на окне ~290×140 см: **28×14 = 392 диода**, шаг 10 см, змейкой.
Управляет ESP32 с [WLED](https://github.com/wled/WLED) 16.0.1. Анимации — GIF, их играет эффект WLED «Image».

## Что где

| Папка | Что это |
|---|---|
| `animations/` | Генератор анимаций на Python: `gen.py` (библиотека: кадр 28×14, шрифты, свой GIF-кодировщик), `scenes/` — по сцене на файл, `wled/` — готовые GIF для контроллера, `playlist.json` — плейлист |
| `animations/tools/` | `sheet.py` — кадры «как на диодах» в PNG, `gallery.py` — HTML-галерея набора, `repack.py` — пережатие GIF без потерь |
| `animations/life/`, `animations/snake/` | Прототипы игр «Жизнь» и «Змейка» в браузере |
| `firmware/balcony_games/` | Модуль для WLED: эффекты **Life Rounds** и **Snake Bot** (порт игр из браузера) |
| `firmware/sim/` | Те же эффекты под Mac с подменой WLED — прогон без контроллера |
| `web/` | Сайт балкона: рисовалка 28×14 в реальном времени (React + Node, WebSocket). Будет и пульт выбора анимаций |

## Анимации

```bash
python3 animations/scenes/campfire.py      # -> animations/wled/campfire.gif и animations/preview/campfire.gif
python3 animations/tools/sheet.py campfire # -> animations/tools/sheets/campfire.png
python3 animations/tools/gallery.py        # -> animations/gallery.html
```

Нужен Python 3 и Pillow.

## Прошивка

Исходники WLED в репозиторий не входят. Чтобы собрать:

```bash
cd firmware
git clone --depth 1 --branch v16.0.1 https://github.com/wled/WLED.git
ln -s ../../balcony_games WLED/usermods/balcony_games
ln -s ../platformio_override.ini WLED/platformio_override.ini
cd WLED && pio run -e balcony
```

Готовая сборка: `firmware/WLED_16.0.1_ESP32_balcony.bin` (ESP32, 4 МБ). Для эффектов матрицу в WLED
нужно настроить как 2D 28×14.

## Сайт

См. [`web/CLAUDE.md`](web/CLAUDE.md). Сделан из проекта «Квадрат Никитоса» (панель 16×16).
