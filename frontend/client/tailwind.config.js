/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#fef2f4',
          100: '#fde6ea',
          200: '#fbcdd6',
          300: '#f8a7b6',
          400: '#f4899e',
          500: '#f17992',
          600: '#e85d7a',
          700: '#d44463',
          800: '#b33551',
          900: '#8f2d43',
          950: '#5c1a2a',
        },
        surface: {
          50: '#f5f6f8',
          100: '#eceef2',
          200: '#d8dce4',
          300: '#b8bfcc',
          400: '#90a1b9',
          500: '#6b7a8d',
          600: '#566173',
          700: '#464b58',
          800: '#353a45',
          900: '#232833',
          950: '#1a1a1e',
        },
        accent: {
          pink: '#f17992',
          orange: '#ffb900',
          green: '#36d399',
          purple: '#845ef7',
          cyan: '#00a1d6',
          yellow: '#ffb900',
          blue: '#90a1b9',
        },
        bg: {
          light: '#f5f6f8',
          dark: '#1a1a1e',
        },
        card: {
          light: '#ffffff',
          dark: '#252529',
        },
        sidebar: {
          dark: '#1a1a1e',
        },
        header: {
          dark: '#1a1a1e',
        },
      },
      fontFamily: {
        sans: [
          '"Noto Sans SC"',
          '"Inter"',
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'sans-serif',
        ],
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
      },
      fontSize: {
        'hero': ['3.5rem', { lineHeight: '1.1', fontWeight: '700' }],
        'display': ['2rem', { lineHeight: '1.2', fontWeight: '700' }],
        'title': ['1.25rem', { lineHeight: '1.4', fontWeight: '600' }],
        'body': ['0.9375rem', { lineHeight: '1.6' }],
        'caption': ['0.8125rem', { lineHeight: '1.5' }],
        'micro': ['0.6875rem', { lineHeight: '1.4' }],
      },
      borderRadius: {
        'xl': '0.875rem',
        '2xl': '1rem',
        '3xl': '1.25rem',
      },
      boxShadow: {
        'card': '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        'card-hover': '0 10px 25px rgba(0,0,0,0.08), 0 4px 10px rgba(0,0,0,0.04)',
        'float': '0 20px 40px rgba(0,0,0,0.1)',
        'glow': '0 0 20px rgba(241,121,146,0.15)',
      },
      aspectRatio: {
        'poster': '2 / 3',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'skeleton': 'skeleton 1.5s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        skeleton: {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '0.8' },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'hero-pattern': 'linear-gradient(135deg, rgba(241,121,146,0.06) 0%, transparent 50%, rgba(0,161,214,0.04) 100%)',
      },
    },
  },
  plugins: [],
}
