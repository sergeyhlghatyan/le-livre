import { browser } from '$app/environment';

type Theme = 'light' | 'dark';

class ThemeStore {
	theme = $state<Theme>('light');

	constructor() {
		if (browser) {
			// Load theme from localStorage or system preference
			const stored = localStorage.getItem('theme') as Theme | null;
			const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

			this.theme = stored ?? (systemPrefersDark ? 'dark' : 'light');
			this.apply();
		}
	}

	toggle() {
		this.theme = this.theme === 'light' ? 'dark' : 'light';
		this.apply();
	}

	set(theme: Theme) {
		this.theme = theme;
		this.apply();
	}

	private apply() {
		if (browser) {
			// Update DOM
			if (this.theme === 'dark') {
				document.documentElement.classList.add('dark');
				// Set true black background for OLED
				document.documentElement.style.backgroundColor = '#0A0A0A';
			} else {
				document.documentElement.classList.remove('dark');
				document.documentElement.style.backgroundColor = '#FAFAFA';
			}

			// Persist to localStorage
			localStorage.setItem('theme', this.theme);
		}
	}
}

export const theme = new ThemeStore();
