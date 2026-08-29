const withAlpha = (variable) => `rgb(var(${variable}) / <alpha-value>)`;

export default {
  darkMode: ['class', '[data-theme="dark"]'],
  content: [
  './index.html',
  './src/**/*.{js,ts,jsx,tsx}'
],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"IBM Plex Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      colors: {
        white: withAlpha('--fg-invert'),
        canvas: withAlpha('--canvas'),
        panel: withAlpha('--panel'),
        panelDeep: withAlpha('--panel-deep'),
        topbar: withAlpha('--topbar'),
        rail: withAlpha('--rail'),
        inset: withAlpha('--inset'),
        ink: withAlpha('--ink'),
        line: {
          DEFAULT: withAlpha('--line'),
          soft: withAlpha('--line-soft'),
          strong: withAlpha('--line-strong'),
        },
        lineStrong: withAlpha('--line-strong'),
        muted: withAlpha('--muted'),
        subtle: withAlpha('--subtle'),
        faint: withAlpha('--faint'),
        bright: withAlpha('--bright'),
        ok: withAlpha('--ok'),
        slate: {
          100: withAlpha('--slate-100'),
          200: withAlpha('--slate-200'),
          300: withAlpha('--slate-300'),
          400: withAlpha('--slate-400'),
          500: withAlpha('--slate-500'),
          600: withAlpha('--slate-600'),
          700: '#334155',
          800: withAlpha('--slate-800'),
          900: '#0F172A',
        },
        accent: {
          DEFAULT: '#0EA5E9',
          soft: withAlpha('--accent-soft'),
          pale: withAlpha('--accent-pale'),
          ice: withAlpha('--accent-ice'),
          deep: '#0369A1',
        },
        sky: {
          soft: withAlpha('--accent-pale'),
          bright: withAlpha('--accent-soft'),
          pale: '#BAE6FD',
          deep: '#075985',
          400: '#38BDF8',
          500: '#0EA5E9',
          700: '#0369A1',
        },
      },
      keyframes: {
        flight: {
          '0%': { left: '0%', opacity: '0' },
          '10%': { opacity: '1' },
          '90%': { opacity: '1' },
          '100%': { left: '100%', opacity: '0' },
        }
      },
      animation: {
        flight: 'flight 20s linear infinite',
      }
    },
  },
  plugins: [],
};
