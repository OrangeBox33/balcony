import React, { FC } from 'react';
import { Grid } from '../../Grid';
import { Palette } from '../../Palette';
import { Toolbar } from '../../Toolbar';
import { DeviceType } from '../../../utils/types';
import { PALETTE2, PALETTE_COLUMNS_DESKTOP } from '../../../utils/constants';
import { StyledBoardColumn, StyledMainContainer, StyledTools } from './styled';

export const MainDesktop: FC = () => {
	return (
		<StyledMainContainer>
			<StyledBoardColumn>
				<Grid deviceType={DeviceType.DESKTOP} />
				<StyledTools>
					<Toolbar />
					<Palette colors={PALETTE2} columns={PALETTE_COLUMNS_DESKTOP} />
				</StyledTools>
			</StyledBoardColumn>
		</StyledMainContainer>
	);
};
