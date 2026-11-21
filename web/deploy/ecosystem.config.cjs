// Конфиг pm2 для сервера balcony (копия kvadrat). Лежит в корне задеплоенного dist на сервере.
// Расширение .cjs обязательно: у package.json рядом стоит "type": "module",
// и обычный .js pm2 не сможет загрузить через require.
module.exports = {
	apps: [
		{
			name: 'balcony',
			script: 'server/server.js',
			// Рабочая папка — корень dist. server.js всё равно считает пути от __dirname
			// (статика ../public, save.json рядом с собой), так что cwd на это не влияет.
			cwd: '/root/dev/balcony/dist',
			instances: 1,
			exec_mode: 'fork',
			autorestart: true,
			max_restarts: 50,
			// Если процесс падает сразу после старта — не молотить рестартами.
			min_uptime: '10s',
			restart_delay: 2000,
			max_memory_restart: '400M',
			// Время в логах сервер печатает сам, второй раз не надо.
			time: false,
			env: {
				NODE_ENV: 'production',
				// 3500 и 81 заняты kvadrat, 3005/3010/8090 — galaxy, rjd, textbin
				PORT: 3600,
				ESP_PORT: 82,
				BASE_PATH: '/balcony',
			},
		},
	],
};
