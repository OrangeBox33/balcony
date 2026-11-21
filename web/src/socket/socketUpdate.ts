import ReconnectingWebSocket from 'reconnecting-websocket';
import { SOCKET_URL } from './url';

export const socketUpdate = new ReconnectingWebSocket(SOCKET_URL);
