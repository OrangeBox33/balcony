#!/usr/bin/env node
// Показывает, что сейчас на панели. Сервер отдаёт сетку сам, сразу после
// подключения.
//
//   ./tools/kvadrat-state.mjs            # цветное превью (для человека)
//   ./tools/kvadrat-state.mjs --art      # палитра + 14 строк символов (для модели)
//
// --art печатает сетку ровно в том формате, в котором её просят у модели
// (палитра + 14 строк по 28 символов), поэтому вывод можно вклеить в промпт.

import { DEFAULT_URL, fetchState, gridToArt, renderPreview } from './lib/kvadrat.mjs';

const USAGE = `
Использование:
  ./tools/kvadrat-state.mjs [опции]

Опции:
  --art           сетка символами + палитра (машиночитаемо, для промпта)
  --url URL       куда подключаться (по умолчанию ${DEFAULT_URL})
`;

const opts = {
	art: false,
	url: DEFAULT_URL,
};

const argv = process.argv.slice(2);

for (let i = 0; i < argv.length; i++) {
	const arg = argv[i];

	switch (arg) {
		case '-h':
		case '--help':
			console.log(USAGE.trim());
			process.exit(0);
		case '--art':
			opts.art = true;
			break;
		case '--url':
			opts.url = argv[++i];
			break;
		default:
			console.error(`Ошибка: неизвестная опция "${arg}"`);
			process.exit(1);
	}
}

try {
	const { grid } = await fetchState(opts);

	if (!grid) {
		console.log('Сервер не прислал сетку.');
	} else if (opts.art) {
		const { rows, legend } = gridToArt(grid);

		console.log(`PALETTE: ${legend.join(' ')}`);
		console.log('GRID:');
		console.log(rows.join('\n'));
	} else {
		console.log(renderPreview(grid));
	}
} catch (err) {
	console.error(`Ошибка: ${err.message}`);
	process.exit(1);
}
