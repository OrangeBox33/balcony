import styled from 'styled-components';
import { Palette } from '../../Palette';
import { FLUID_BOARD_VARS } from '../../../utils/constants';

export const StyledMainContainer = styled.div`
	height: 100%;
	padding: var(--pad);
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: var(--gap);
	background-color: var(--bg-page);
	overflow: hidden;
`;

/**
 * Единственный растяжимый блок экрана: инструменты и палитра стоят flex: none
 * и всегда получают свою высоту целиком, а сетке достаётся остаток. Поэтому
 * «сетка + вся палитра на одном экране» выполняется на любом телефоне сама,
 * без вычитания window.screen.height, как было раньше.
 *
 * container-type: size даёт сетке единицы cqw/cqh — размер именно этого
 * блока, а не всего окна, так что сетка держит пропорцию X:Y и вписывается в него.
 */
export const StyledBoardArea = styled.div`
	flex: 1;
	min-height: 0;
	width: 100%;
	container-type: size;
	display: grid;
	place-items: center;
	/* Переменную объявляем на детях, а не на самом контейнере: cq-единицы
	   обязаны считаться относительно ЭТОГО блока, а элемент не может быть
	   контейнером для самого себя. */
	> * {
		${FLUID_BOARD_VARS}
	}
`;

// Палитра держит свою высоту: сжимается только сетка.
export const StyledMainPalette = styled(Palette)`
	flex: none;
`;
