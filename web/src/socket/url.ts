// Адрес WebSocket сервера балкона — от текущей страницы: в проде это
// wss://nikitosfrolov.ru/balcony/ws, в dev vite проксирует /balcony/ws на локальный сервер.
const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';

export const SOCKET_URL = `${proto}://${window.location.host}${import.meta.env.BASE_URL}ws`;
