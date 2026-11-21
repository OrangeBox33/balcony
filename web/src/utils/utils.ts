import { DEFAULT_COLOR, DEFAULT_X, DEFAULT_Y } from './constants';
import { Ids } from './types';

export const createGrid = (size: number) => {
	const grid: string[] = [];
	for (let i = 0; i < size; i++) {
		grid[i] = DEFAULT_COLOR;
	}

	return grid;
};

export const createArr = (size: number) => {
	const arr: number[] = [];
	for (let i = 0; i < size; i++) {
		arr.push(i);
	}

	return arr;
};

export const sleep = async (timer: number) => {
	return new Promise((resolve) => setTimeout(resolve, timer));
};

// Окрестность 3×3 вокруг пикселя для кисти, без выхода за края поля.
export const needPaintPixels = (id: number): Ids => {
	const x = id % DEFAULT_X;
	const y = Math.floor(id / DEFAULT_X);
	const arr = [id];

	for (let dy = -1; dy <= 1; dy++) {
		for (let dx = -1; dx <= 1; dx++) {
			const nx = x + dx;
			const ny = y + dy;

			if ((dx || dy) && nx >= 0 && nx < DEFAULT_X && ny >= 0 && ny < DEFAULT_Y) {
				arr.push(ny * DEFAULT_X + nx);
			}
		}
	}

	return arr;
};
