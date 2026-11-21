import React, { FC } from 'react';
import { Grid } from '../../Grid';
import { Toolbar } from '../../Toolbar';
import { DeviceType } from '../../../utils/types';
import { PALETTE2 } from '../../../utils/constants';
import { StyledBoardArea, StyledMainContainer, StyledMainPalette } from '../Mobile/styled';

// Телефон боком: поле 2:1 упирается в высоту, поэтому инструменты не сбоку, а снизу,
// и палитра в один ряд — так полю достаётся почти весь экран.
export const MainMobileRotate: FC = () => {
	return (
		<StyledMainContainer>
			<StyledBoardArea>
				<Grid deviceType={DeviceType.MOBILE_ROTATE} />
			</StyledBoardArea>
			<Toolbar />
			<StyledMainPalette colors={PALETTE2} columns={PALETTE2.length} />
		</StyledMainContainer>
	);
};
