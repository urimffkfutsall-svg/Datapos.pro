/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
        '4xl': '2rem',
        '5xl': '2.5rem'
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Manrope', 'system-ui', 'sans-serif']
      },
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: { DEFAULT: 'hsl(var(--card))', foreground: 'hsl(var(--card-foreground))' },
        popover: { DEFAULT: 'hsl(var(--popover))', foreground: 'hsl(var(--popover-foreground))' },
        primary: { DEFAULT: 'hsl(var(--primary))', foreground: 'hsl(var(--primary-foreground))' },
        secondary: { DEFAULT: 'hsl(var(--secondary))', foreground: 'hsl(var(--secondary-foreground))' },
        muted: { DEFAULT: 'hsl(var(--muted))', foreground: 'hsl(var(--muted-foreground))' },
        accent: { DEFAULT: 'hsl(var(--accent))', foreground: 'hsl(var(--accent-foreground))' },
        destructive: { DEFAULT: 'hsl(var(--destructive))', foreground: 'hsl(var(--destructive-foreground))' },
        border: 'hsl(var(--border))',
        ring: 'hsl(var(--ring))',
        chart: {
          '2': 'hsl(var(--chart-2))',
          '3': 'hsl(var(--chart-3))',
          '4': 'hsl(var(--chart-4))',
          '5': 'hsl(var(--chart-5))'
        },
        brand: {
          50:  '#e6f7f6',
          100: '#c2ebe8',
          200: '#8dd9d4',
          300: '#5cc7c0',
          400: '#33b5ac',
          500: '#00a79d',
          600: '#008f86',
          700: '#007a73',
          800: '#005f59',
          900: '#003e3a'
        }
      },
      boxShadow: {
        'soft':       '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.02)',
        'soft-md':    '0 4px 16px -2px rgba(0,0,0,0.05), 0 2px 6px -2px rgba(0,0,0,0.04)',
        'soft-lg':    '0 12px 32px -8px rgba(0,0,0,0.08), 0 4px 12px -4px rgba(0,0,0,0.05)',
        'soft-xl':    '0 24px 48px -12px rgba(0,0,0,0.12), 0 8px 16px -8px rgba(0,0,0,0.06)',
        'glow':       '0 0 0 1px rgba(0,167,157,0.15), 0 8px 24px -8px rgba(0,167,157,0.3)',
        'glow-lg':    '0 0 0 1px rgba(0,167,157,0.2), 0 16px 40px -12px rgba(0,167,157,0.35)',
        'inner-soft': 'inset 0 1px 2px rgba(0,0,0,0.04)'
      },
      keyframes: {
        'accordion-down': { from: { height: '0' }, to: { height: 'var(--radix-accordion-content-height)' } },
        'accordion-up':   { from: { height: 'var(--radix-accordion-content-height)' }, to: { height: '0' } },
        'fade-in':        { from: { opacity: '0', transform: 'translateY(8px)' },  to: { opacity: '1', transform: 'translateY(0)' } },
        'fade-in-up':     { from: { opacity: '0', transform: 'translateY(16px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        'scale-in':       { from: { opacity: '0', transform: 'scale(0.96)' },      to: { opacity: '1', transform: 'scale(1)' } },
        'shimmer':        { '0%': { backgroundPosition: '-1000px 0' }, '100%': { backgroundPosition: '1000px 0' } },
        'pulse-soft':     { '0%, 100%': { opacity: '1' }, '50%': { opacity: '0.6' } }
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up':   'accordion-up 0.2s ease-out',
        'fade-in':        'fade-in 0.4s ease-out',
        'fade-in-up':     'fade-in-up 0.5s ease-out',
        'scale-in':       'scale-in 0.3s ease-out',
        'shimmer':        'shimmer 2s linear infinite',
        'pulse-soft':     'pulse-soft 2s ease-in-out infinite'
      },
      backdropBlur: { 'xs': '2px' }
    }
  },
  plugins: [require("tailwindcss-animate")]
};