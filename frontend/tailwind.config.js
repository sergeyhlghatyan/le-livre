/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	darkMode: 'class',
	theme: {
		extend: {
			colors: {
				// Monochrome base - neutral grays only
				neutral: {
					50: '#FAFAFA',
					100: '#F5F5F5',
					200: '#E5E5E5',
					300: '#D4D4D4',
					400: '#A3A3A3',
					500: '#737373',
					600: '#525252',
					700: '#404040',
					800: '#262626',
					900: '#171717',
					950: '#0A0A0A'
				},
				// Single accent color - blue only
				primary: {
					DEFAULT: '#2563EB',
					hover: '#1D4ED8',
					light: '#DBEAFE'
				},
				// Minimal semantic colors
				success: '#16A34A',
				warning: '#CA8A04',
				error: '#DC2626'
			},
			fontFamily: {
				sans: ['Inter Variable', 'system-ui', 'sans-serif'],
				mono: ['JetBrains Mono', 'Consolas', 'Monaco', 'monospace']
			},
			fontSize: {
				xs: ['11px', { lineHeight: '16px' }],
				sm: ['13px', { lineHeight: '20px' }],
				base: ['15px', { lineHeight: '24px' }],
				lg: ['17px', { lineHeight: '28px' }],
				xl: ['20px', { lineHeight: '32px' }],
				'2xl': ['24px', { lineHeight: '36px' }]
			},
			spacing: {
				'18': '72px',
				'22': '88px'
			},
			maxWidth: {
				'chat': '720px',
				'document': '920px'
			},
			borderRadius: {
				DEFAULT: '6px',
				lg: '8px',
				xl: '12px',
				'2xl': '16px'
			},
			boxShadow: {
				'lift': '0 4px 12px rgba(0, 0, 0, 0.1)',
				'lift-lg': '0 8px 24px rgba(0, 0, 0, 0.15)'
			}
		}
	},
	plugins: []
};
