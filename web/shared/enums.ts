// Типы WebSocket-сообщений между браузером и сервером.
// Значения — это те самые строки, что летят в JSON (type: '...').
export enum EMessageTypes {
	GET_GRID = 'getGrid',
	DRAW = 'draw',
	WIFI = 'wifi',
	OTA = 'ota',
	// Калибровка палитры: браузер шлёт подобранную пару цветов,
	// сервер копит их в своей палитре и рассылает её обратно.
	SAVE_COLOR = 'saveColor',
	GET_PALETTE = 'getPalette',
	// Запись рисования: проиграть её на панелях / начать заново.
	// В квадрате это были «магические» сообщения чата 42 и 228; чата здесь нет.
	PLAY_HISTORY = 'playHistory',
	RESET_HISTORY = 'resetHistory',
}
