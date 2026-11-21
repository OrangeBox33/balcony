import ReconnectingWebSocket from 'reconnecting-websocket';
import { SOCKET_URL } from './url';

export const socketWifi = new ReconnectingWebSocket(SOCKET_URL);
