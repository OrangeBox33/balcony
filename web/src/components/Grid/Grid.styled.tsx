import styled from 'styled-components';
import { BOARD_H, BOARD_W, DEFAULT_X, DEFAULT_Y, PIXEL_GAP } from '../../utils/constants';

/**
 * Размер сетки приходит из раскладки переменными --board-w / --board-h: на десктопе
 * это фиксированные BOARD_W×BOARD_H px, на телефоне — вписанный в свободное место
 * прямоугольник X:Y (FLUID_BOARD_VARS). Ячейки в 1fr и подстраиваются сами.
 */
export const StyledGrid = styled.div`
	flex: none;
	/* фолбэк для браузеров без cq-единиц */
	width: ${BOARD_W}px;
	height: ${BOARD_H}px;
	width: var(--board-w, ${BOARD_W}px);
	height: var(--board-h, ${BOARD_H}px);
	display: grid;
	grid-template-columns: repeat(${DEFAULT_X}, 1fr);
	grid-template-rows: repeat(${DEFAULT_Y}, 1fr);
	gap: ${PIXEL_GAP}px;
	touch-action: none;
`;
