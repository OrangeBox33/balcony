#!/usr/bin/env bash
#
# Деплой балкона на nikitosfrolov.ru/balcony одной командой (копия деплоя kvadrat).
#
#   ./deploy.sh              собрать клиент + сервер, залить, перезапустить pm2
#   ./deploy.sh --setup      однократная настройка сервера (pm2, автозапуск)
#   ./deploy.sh --logs       живые логи сервера (pm2 logs)
#   ./deploy.sh --status     что сейчас крутится на сервере
#   ./deploy.sh --restart    перезапустить, ничего не собирая и не заливая
#   ./deploy.sh --no-build   залить то, что уже собрано локально
#   ./deploy.sh --dry-run    показать, что бы залилось, но не заливать
#   ./deploy.sh --nginx      поставить/обновить location /balcony/ в nginx (nikitosfrolov.ru)
#
# Порты: 3600 — браузеры (только 127.0.0.1, снаружи через nginx), 82 — ESP напрямую.
#
# Раскладка на сервере (её ждёт server.js: статика — ../public от dist/server):
#   /root/dev/balcony/dist/
#     ├── server/            скомпилированный сервер (+ save.json и palette.json, их не трогаем)
#     ├── shared/            общий код
#     ├── public/            собранный клиент (vite)
#     ├── package.json       зависимости сервера
#     ├── package-lock.json
#     ├── ecosystem.config.cjs
#     └── node_modules/      ставится на сервере через npm, не заливается

set -euo pipefail

REMOTE="${BALCONY_REMOTE:-root@185.228.232.194}"
# Своя папка: rsync --delete со старым путём стёр бы kvadrat.
REMOTE_DIR="${BALCONY_REMOTE_DIR:-/root/dev/balcony/dist}"
APP_NAME="balcony"
PORT=3600
BASE_PATH="/balcony"
PUBLIC_URL="https://nikitosfrolov.ru${BASE_PATH}/"
# Сайт nikitosfrolov.ru подключает все *.conf из этой папки.
NGINX_SNIPPET="/etc/nginx/snippets/nikitosfrolov/balcony.conf"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAGE="$ROOT/.deploy"

BUILD=1
DRY_RUN=0
MODE="deploy"

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
ok() { printf '\033[1;32m    %s\033[0m\n' "$*"; }
die() {
	printf '\n\033[1;31mОшибка: %s\033[0m\n' "$*" >&2
	exit 1
}

remote() { ssh "$REMOTE" "$*"; }

while [ $# -gt 0 ]; do
	case "$1" in
		--setup) MODE="setup" ;;
		--logs) MODE="logs" ;;
		--status) MODE="status" ;;
		--restart) MODE="restart" ;;
		--no-build) BUILD=0 ;;
		--dry-run) DRY_RUN=1 ;;
		--nginx) MODE="nginx" ;;
		-h | --help)
			sed -n '2,24p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
			exit 0
			;;
		*) die "неизвестный аргумент: $1" ;;
	esac
	shift
done

# ── Nginx ──────────────────────────────────────────────────────────────────
# Кладём фрагмент в папку, которую подключает сайт. Если nginx -t не прошёл,
# возвращаем прежний фрагмент (или убираем новый, если прежнего не было).
if [ "$MODE" = "nginx" ]; then
	say "Nginx: location $BASE_PATH/"
	scp -q "$ROOT/deploy/nginx.balcony.conf" "$REMOTE:/tmp/balcony.conf"
	remote "set -e
		mkdir -p \$(dirname $NGINX_SNIPPET)
		[ -f $NGINX_SNIPPET ] && cp $NGINX_SNIPPET /tmp/balcony.conf.bak || rm -f /tmp/balcony.conf.bak
		mv /tmp/balcony.conf $NGINX_SNIPPET
		if nginx -t 2>/tmp/balcony-nginx-t.log; then
			systemctl reload nginx && echo '    nginx -t ок, конфиг перечитан'
		else
			cat /tmp/balcony-nginx-t.log
			if [ -f /tmp/balcony.conf.bak ]; then mv /tmp/balcony.conf.bak $NGINX_SNIPPET; else rm -f $NGINX_SNIPPET; fi
			echo '    nginx -t не прошёл — фрагмент откачен'
			exit 1
		fi"
	ok "$NGINX_SNIPPET"
	exit 0
fi

# ── Разовая настройка сервера ──────────────────────────────────────────────
if [ "$MODE" = "setup" ]; then
	say "Настраиваю сервер $REMOTE"

	remote 'command -v pm2 >/dev/null || npm install -g pm2'
	ok "pm2 на месте: $(remote 'pm2 -v' | tail -1)"

	say "Проверяю, свободны ли порты $PORT и 82"
	remote "ss -ltnp | grep -E ':($PORT|82) ' && echo 'ЗАНЯТО — разберись до деплоя' || echo свободны"
	say "Файрвол (порт 82 должен быть открыт наружу для ESP)"
	remote "command -v ufw >/dev/null && ufw status || echo 'ufw нет'"

	say "Включаю автозапуск pm2 после ребута сервера"
	remote 'pm2 startup systemd -u root --hp /root' | tail -3
	ok "готово"

	printf '\n\033[1;32mСервер готов. Теперь просто: ./deploy.sh\033[0m\n'
	exit 0
fi

if [ "$MODE" = "logs" ]; then
	say "Логи $APP_NAME (Ctrl+C чтобы выйти)"
	# -t: интерактивный tty, иначе Ctrl+C не дойдёт до pm2
	ssh -t "$REMOTE" "pm2 logs $APP_NAME --lines 100"
	exit 0
fi

if [ "$MODE" = "status" ]; then
	remote "pm2 list && pm2 info $APP_NAME | head -25"
	exit 0
fi

if [ "$MODE" = "restart" ]; then
	say "Перезапускаю $APP_NAME"
	remote "cd $REMOTE_DIR && pm2 startOrRestart ecosystem.config.cjs --update-env && pm2 list"
	exit 0
fi

# ── Сборка ─────────────────────────────────────────────────────────────────
if [ "$BUILD" = "1" ]; then
	say "Собираю клиент (vite)"
	(cd "$ROOT" && npm run build)

	say "Собираю сервер (tsc)"
	# Старый dist сносим: rootDir у сервера — корень репо, и от прежних
	# раскладок в dist могли остаться файлы, которых уже нет в исходниках.
	rm -rf "$ROOT/server/dist"
	(cd "$ROOT/server" && npm run build)
fi

[ -f "$ROOT/dist/index.html" ] || die "нет dist/index.html — клиент не собран (убери --no-build)"
[ -f "$ROOT/server/dist/server/server.js" ] || die "нет server/dist/server/server.js — сервер не собран"
[ -f "$ROOT/server/dist/shared/constants.js" ] || die "нет server/dist/shared/ — проверь include в server/tsconfig.json"

# ── Раскладываем в точности то, что должно лежать на сервере ───────────────
say "Готовлю посылку в $STAGE"

rm -rf "$STAGE"
mkdir -p "$STAGE"

cp -R "$ROOT/server/dist/server" "$STAGE/server"
cp -R "$ROOT/server/dist/shared" "$STAGE/shared"
cp -R "$ROOT/dist" "$STAGE/public" # собранный клиент -> dist/public на сервере
cp "$ROOT/deploy/ecosystem.config.cjs" "$STAGE/ecosystem.config.cjs"
cp "$ROOT/server/package-lock.json" "$STAGE/package-lock.json"

# package.json берём серверный, но правим start: на сервере файл лежит в корне
# dist, поэтому путь до входной точки не dist/server/server.js, а server/server.js.
node -e '
const fs = require("fs");
const pkg = JSON.parse(fs.readFileSync(process.argv[1], "utf-8"));
pkg.scripts = { start: "node server/server.js" };
fs.writeFileSync(process.argv[2], JSON.stringify(pkg, null, "\t") + "\n");
' "$ROOT/server/package.json" "$STAGE/package.json"

ok "$(find "$STAGE" -type f | wc -l | tr -d ' ') файлов"

# ── Заливаем ───────────────────────────────────────────────────────────────
RSYNC_OPTS=(
	-az --delete --human-readable --itemize-changes
	# node_modules живёт на сервере (ставится npm), save.json — состояние холста,
	# palette.json — подобранная палитра калибровки.
	# Все три исключены и из заливки, и из --delete.
	--exclude 'node_modules'
	--exclude 'save.json'
	--exclude 'palette.json'
	--exclude '.DS_Store'
)

if [ "$DRY_RUN" = "1" ]; then
	say "Пробный прогон (ничего не меняем) -> $REMOTE:$REMOTE_DIR"
	rsync "${RSYNC_OPTS[@]}" --dry-run "$STAGE/" "$REMOTE:$REMOTE_DIR/"
	exit 0
fi

say "Заливаю на $REMOTE:$REMOTE_DIR"
rsync "${RSYNC_OPTS[@]}" "$STAGE/" "$REMOTE:$REMOTE_DIR/"

# ── Зависимости и перезапуск ───────────────────────────────────────────────
say "Ставлю зависимости на сервере"
remote "cd $REMOTE_DIR && npm install --omit=dev --no-audit --no-fund" | tail -3

say "Перезапускаю $APP_NAME"
remote "cd $REMOTE_DIR && pm2 startOrRestart ecosystem.config.cjs --update-env >/dev/null && pm2 save >/dev/null && pm2 list"

say "Проверяю, что сервис отвечает"
sleep 1
remote "curl -sf http://127.0.0.1:$PORT$BASE_PATH/healthz" || die "healthz не ответил — смотри ./deploy.sh --logs"
ok "healthz: ok"

say "Последние строки лога"
remote "pm2 logs $APP_NAME --lines 15 --nostream"

printf '\n\033[1;32mГотово: %s\033[0m\n' "$PUBLIC_URL"
printf 'Логи: ./deploy.sh --logs\n'
