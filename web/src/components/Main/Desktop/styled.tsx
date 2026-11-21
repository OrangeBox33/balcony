import styled from 'styled-components';
import { BOARD_H, BOARD_W } from '../../../utils/constants';

// Воздух между сеткой и инструментами.
const TOOLS_GAP = 24;

export const StyledMainContainer = styled.div`
	/* на десктопе размер пикселя фиксирован, поэтому и сетка фиксированная */
	--board-w: ${BOARD_W}px;
	--board-h: ${BOARD_H}px;
	height: 100%;
	display: flex;
	justify-content: center;
	align-items: center;
	background-color: var(--bg-page);
`;

export const StyledBoardColumn = styled.div`
	display: flex;
	flex-direction: column;
	width: var(--board-w);
	gap: var(--gap);
`;

// Инструменты и палитра идут после сетки с дополнительным отступом.
export const StyledTools = styled.div`
	display: flex;
	flex-direction: column;
	gap: var(--gap);
	margin-top: ${TOOLS_GAP}px;
`;
