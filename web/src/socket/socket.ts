import { setGrid, setPalette, setPixels } from '../redux/slice';
import { store } from '../redux/store';
import ReconnectingWebSocket from 'reconnecting-websocket';
import { SOCKET_URL } from './url';
import { EMessageTypes } from '../../shared/enums';

export const socket = new ReconnectingWebSocket(SOCKET_URL);

socket.addEventListener('message', (message) => {
	const { type, pixels, grid, palette } = JSON.parse(message.data);

	if (type === EMessageTypes.DRAW) {
		store.dispatch(setPixels(pixels));
	}

	if (type === EMessageTypes.GET_GRID) {
		store.dispatch(setGrid(grid));
	}

	if (type === EMessageTypes.GET_PALETTE) {
		store.dispatch(setPalette(palette));
	}
});
