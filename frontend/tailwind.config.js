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
        // Mission-control dark palette
        bg: {
          base:  '#050a14',
          panel: '#080f1e',
          card:  '#0c1628',
          hover: '#0f1d35',
        },
        cyan: {
          DEFAULT: '#00D4FF',
          dim:     'rgba(0,212,255,0.12)',
          glow:    'rgba(0,212,255,0.4)',
          400:     '#22d3ee',
          300:     '#67e8f9',
          200:     '#a5f3fc',
        },
        violet: {
          DEFAULT: '#7B61FF',
          dim:     'rgba(123,97,255,0.12)',
        },
        emerald: {
          DEFAULT: '#00E5A0',
          dim:     'rgba(0,229,160,0.1)',
        },
        amber: {
          DEFAULT: '#F59E0B',
          dim:     'rgba(245,158,11,0.1)',
        },
        // Legacy compat
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
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      backgroundImage: {
        'space-gradient':  'linear-gradient(135deg, #060e52 0%, #0d20a8 40%, #1a3fff 70%, #27a35c 100%)',
        'earth-gradient':  'linear-gradient(135deg, #11462a 0%, #27a35c 50%, #85d8a7 100%)',
        'hero-radial':     'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(0,212,255,0.18) 0%, transparent 70%)',
        'cyan-gradient':   'linear-gradient(135deg, #00D4FF 0%, #7B61FF 100%)',
        'green-gradient':  'linear-gradient(135deg, #00E5A0 0%, #00D4FF 100%)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4,0,0.6,1) infinite',
        'shimmer':    'shimmer 2.5s linear infinite',
        'float':      'float 6s ease-in-out infinite',
        'scan':       'scan 3s linear infinite',
        'fade-in':    'fadeIn 0.5s ease-out both',
        'slide-up':   'slideUp 0.5s ease-out both',
        'sweep-right':'sweep-right 1.2s ease-out forwards',
      },
      boxShadow: {
        'glow-cyan':   '0 0 28px rgba(0,212,255,0.35)',
        'glow-green':  '0 0 28px rgba(0,229,160,0.35)',
        'glow-purple': '0 0 28px rgba(123,97,255,0.35)',
        'glow-blue':   '0 0 30px rgba(45,95,255,0.4)',
        'metric':      '0 4px 20px rgba(0,0,0,0.5)',
        'glass':       '0 8px 32px rgba(0,0,0,0.6), inset 0 0 0 1px rgba(0,212,255,0.08)',
        'card-hover':  '0 0 40px rgba(0,212,255,0.12), 0 0 0 1px rgba(0,212,255,0.25)',
      },
      backdropBlur: { xs: '2px' },
    },
  },
  plugins: [],
};
