/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // ISRO-inspired space palette
        space: {
          50:  '#f0f4ff',
          100: '#e0eaff',
          200: '#c0d4ff',
          300: '#91b4ff',
          400: '#5a8aff',
          500: '#2d5fff',
          600: '#1a3fff',
          700: '#122fcf',
          800: '#0d20a8',
          900: '#0a1882',
          950: '#060e52',
        },
        earth: {
          50:  '#f0faf4',
          100: '#dcf5e5',
          200: '#b8eacc',
          300: '#85d8a7',
          400: '#4abf7c',
          500: '#27a35c',
          600: '#1a8448',
          700: '#166a3b',
          800: '#145531',
          900: '#11462a',
        },
        cloud: {
          50:  '#f8fafc',
          100: '#f0f4f9',
          200: '#dde6f0',
          300: '#b8cfe1',
          400: '#8eb0ce',
          500: '#6694bc',
          600: '#4d7aa8',
          700: '#3d6188',
          800: '#2d4a69',
          900: '#1e334d',
        },
        amber: {
          400: '#fbbf24',
          500: '#f59e0b',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      backgroundImage: {
        'space-gradient': 'linear-gradient(135deg, #060e52 0%, #0d20a8 40%, #1a3fff 70%, #27a35c 100%)',
        'earth-gradient': 'linear-gradient(135deg, #11462a 0%, #27a35c 50%, #85d8a7 100%)',
        'glass': 'linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.04) 100%)',
        'hero-radial': 'radial-gradient(ellipse at 50% 0%, #1a3fff33 0%, transparent 70%)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'float': 'float 6s ease-in-out infinite',
        'scan': 'scan 3s linear infinite',
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% center' },
          '100%': { backgroundPosition: '200% center' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      boxShadow: {
        'glow-blue': '0 0 30px rgba(45, 95, 255, 0.4)',
        'glow-green': '0 0 30px rgba(39, 163, 92, 0.4)',
        'glass': '0 8px 32px rgba(0, 0, 0, 0.3)',
        'metric': '0 4px 20px rgba(0, 0, 0, 0.2)',
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
};
