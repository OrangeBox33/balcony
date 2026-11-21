# Гирлянда на балконе

Матрица из адресной RGB-гирлянды на окне ~290×140 см: **28×14 = 392 диода**, шаг 10 см, змейкой.
Управляет ESP32 с **WLED 16.0.1**. Анимации — GIF, их играет эффект WLED «Image».

Пользователь пишет по-русски и хочет короткие пошаговые ответы. Железо у него уже работает
(данные 3,3 В через резистор — норм, не предлагать переделывать).

Git: публичный репозиторий. Не коммитить чужое (APK и анимации Surplife, иконки LaMetric) — см. `.gitignore`.

## Контроллеры

- `192.168.1.19` (wled-297124) — **основной, для балконной матрицы**. Пока на нём 20 диодов и лимит 250 мА
  (питание от ноутбука), бывает выключен.
- `192.168.1.10` (wled-0c2158) — **другой проект: гирлянда для телевизора**, 227 диодов. К балкону не относится, не трогать.
- Под GIF во флешке раздел LittleFS 960 КБ (0xF0000). Каждый файл занимает целые блоки по 4 КБ
  (в среднем теряется ~2 КБ на файл — проверено `mklittlefs -b 4096 -p 256 -s 983040`). Галерея считает это сама.
- Плейлист для контроллера — `animations/playlist.json`: `often` {имя: раз подряд}, `long` {имя: секунд}.
- Ничего не прошивать и не заливать на контроллеры без явного «да» пользователя.
- **При создании и правке анимаций не предлагать залить их на контроллер** и не спрашивать об этом —
  заливать будем отдельно, когда пользователь сам скажет.

## Новая анимация — рецепт

1. Файл `animations/scenes/<name>.py` с функцией `build()`, в конце `gen.save("<name>", frames, ms)`.
   Образцы: `scenes/surf.py`, `scenes/snail_kiss.py`, `scenes/campfire.py`, `scenes/heart_beat.py`.
   ```python
   import sys; from pathlib import Path
   sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
   import gen
   W, H = gen.W, gen.H
   def build():
       frames = []
       for t in range(N):
           f = gen.Frame()          # чёрный кадр 28×14
           f.set(x, y, (r, g, b)); f.add(...)            # точка / прибавить цвет
           f.sprite(rows, x, y, flip=False, pal={...})   # спрайт из строк, '.' — прозрачно
           f.text("СЛОВО", x, y, color, gen.FONT7)       # color может быть функцией (x, y)
           frames.append(f)
       gen.save("<name>", frames, 70)   # ms на кадр (или список ms)
   if __name__ == "__main__": build()
   ```
2. Запуск: `python3 animations/scenes/<name>.py` → `animations/wled/<name>.gif` (для контроллера)
   и `animations/preview/<name>.gif` (крупный превью-GIF).
3. **Проверить глазами:** `python3 animations/tools/sheet.py <name> [--every N --cols 8 --start K]`
   → `animations/tools/sheets/<name>.png` (кадры «как на диодах»). Прочитать PNG и поправить, пока не читается.
4. Добавить русское название в `TITLES` в `animations/tools/gallery.py`.
5. `python3 animations/tools/gallery.py` → `animations/gallery.html`, отправить пользователю (SendUserFile).

Пересобирать все сцены разом (`python3 animations/gen.py`) не нужно и нежелательно:
часть сцен с несеянным `random` — нарисуются иначе, чем пользователь уже одобрил.

## Правила картинки на диодах

- WLED применяет гамму 2,8: канал **ниже ~70 практически не светится**, тусклое делать ≥ ~90.
  Тёмные детали на ярком (спираль, контур) пропадают — делать их **светлее** фона, а не темнее.
- Чёрный = диод выключен. Чёрный силуэт работает только на цветном фоне.
- Большие яркие заливки = большой ток; луну/фон лучше чуть приглушать.
- Длина 4–15 с, кадр 50–100 мс. Петля по возможности без шва (периодичный шум/фазы по `t % N`).
- Текст: `FONT7` (5×7, вся кириллица, цифры, `!?.,:-`), `FONT5` (≈3×5, две строки по ~6 букв),
  `FONT3` (латиница/цифры 3×5). В ширину 28 влезает ~4 буквы FONT7 — длинное делать бегущей строкой.
- Пользователь не любит: медленные затянутые сцены, «кашу» из цветов, резкие смены фона/земли,
  обрезанные края (центрировать по реальному размеру фигуры).

## Устройство кода

- `animations/gen.py` — общая библиотека: `Frame`, `PAL` (буквы цветов для спрайтов),
  шрифты, `hsv`, `scale`, `led_preview`, `save`, свой GIF-кодировщик `write_gif`
  (без потерь: одинаковые кадры подряд склеиваются, кадр хранит только прямоугольник изменений
  с прозрачными неизменными пикселями — WLED рисует поверх прошлого кадра; палитра под число цветов,
  >256 → палитра на кадр; `delta=False` — старый режим «кадр целиком». На живом контроллере дельта-кадры
  ещё не проверены; слайдер Blur у эффекта Image держать 0). Готовые GIF пережимает `tools/repack.py`,
  сверяя попиксельно (`--full` — обратно в «кадр целиком», тоже без потерь).
  плюс 7 старых сцен (fight, boxer, samurai, tree, fireworks, santa, greeting).
- `animations/scenes/` — по сцене на файл.
- `animations/wled/` — **набор для контроллера** (что лежит здесь — то и в галерее).
- `animations/life/life.html`, `animations/snake/snake.html` — прототипы игр «Жизнь» и «Змейка» в браузере.
- `animations/lametric/` — каталог иконок LaMetric; `animations/surplife/` + `surplife/convert.py` —
  57 анимаций из приложения Surplife (в основной набор не входят).
- `web/` — сайт балкона (рисовалка + будущий пульт), копия kvadratNikitosa → nikitosfrolov.ru/balcony. См. `web/CLAUDE.md`.
- `.claude/launch.json` — http-серверы: `animations` (порт 8766) и `catalog` (8765) для браузерной панели.

## Прошивка

- `firmware/WLED/` — исходники WLED v16.0.1 (клон github.com/wled/WLED, в наш git не входит).
  Наш модуль — `firmware/balcony_games/balcony_games.cpp` (эффекты **Life Rounds** и **Snake Bot** — порт html-игр),
  конфиг сборки — `firmware/platformio_override.ini` (env `balcony`). В WLED они подключены **ссылками**:
  `WLED/usermods/balcony_games -> ../../balcony_games`, `WLED/platformio_override.ini -> ../platformio_override.ini`.
  Если после переноса модуль пропал из сборки — удалить `WLED/.pio/libdeps/balcony/balcony_games.pio-link`
  и `integrity.dat` (PlatformIO помнит старый путь). Проверка: `strings …/firmware.bin | grep "Life Rounds"`.
- Сборка: `cd firmware/WLED && ../.pio-venv/bin/pio run -e balcony` (PlatformIO в локальном venv).
  Готовый файл: `firmware/WLED_16.0.1_ESP32_balcony.bin`. Прошивка по OTA: `http://<ip>/update` — только с согласия.
- `firmware/sim/` — те же эффекты (`#include "../balcony_games/balcony_games.cpp"`), собранные под Mac с подменой WLED (`wled.h`), для прогона без контроллера.
  Компиляция (на этом Mac нужны явные пути libc++):
  `SDK=/Library/Developer/CommandLineTools/SDKs/MacOSX26.2.sdk; c++ -std=c++17 -O2 -I. -isysroot $SDK -nostdinc++ -isystem $SDK/usr/include/c++/v1 -o sim main.cpp`
  Запуск: `./sim life|snake secs=600 seed=1 [sx= ix= c1= c2= o1= o2=] [dump=file.raw from= to=]`.
- Для эффектов в WLED матрица должна быть настроена как 2D 28×14.
