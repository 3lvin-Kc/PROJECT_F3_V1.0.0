import type { Config } from "tailwindcss";

export default {
	darkMode: ["class"],
	content: [
		"./pages/**/*.{ts,tsx}",
		"./components/**/*.{ts,tsx}",
		"./app/**/*.{ts,tsx}",
		"./src/**/*.{ts,tsx}",
	],
	prefix: "",
	theme: {
		container: {
			center: true,
			padding: {
				DEFAULT: '1rem',
				sm: '1.5rem',
				lg: '2rem',
				xl: '2.5rem',
				'2xl': '3rem'
			},
			screens: {
				'2xl': '1400px'
			}
		},
		extend: {
			colors: {
				border: 'hsl(var(--border))',
				input: 'hsl(var(--input))',
				ring: 'hsl(var(--ring))',
				background: 'hsl(var(--background))',
				foreground: 'hsl(var(--foreground))',
				primary: {
					DEFAULT: 'hsl(var(--primary))',
					foreground: 'hsl(var(--primary-foreground))'
				},
				secondary: {
					DEFAULT: 'hsl(var(--secondary))',
					foreground: 'hsl(var(--secondary-foreground))'
				},
				destructive: {
					DEFAULT: 'hsl(var(--destructive))',
					foreground: 'hsl(var(--destructive-foreground))'
				},
				muted: {
					DEFAULT: 'hsl(var(--muted))',
					foreground: 'hsl(var(--muted-foreground))'
				},
				accent: {
					DEFAULT: 'hsl(var(--accent))',
					foreground: 'hsl(var(--accent-foreground))'
				},
				popover: {
					DEFAULT: 'hsl(var(--popover))',
					foreground: 'hsl(var(--popover-foreground))'
				},
				card: {
					DEFAULT: 'hsl(var(--card))',
					foreground: 'hsl(var(--card-foreground))'
				},
				sidebar: {
					DEFAULT: 'hsl(var(--sidebar))',
					foreground: 'hsl(var(--sidebar-foreground))',
					accent: 'hsl(var(--sidebar-accent))',
					'accent-foreground': 'hsl(var(--sidebar-accent-foreground))'
				},
				// Premium Theme Extensions
				hero: {
					DEFAULT: 'hsl(var(--hero))',
					foreground: 'hsl(var(--hero-foreground))',
					muted: 'hsl(var(--hero-muted))'
				},
				editor: {
					DEFAULT: 'hsl(var(--editor))',
					foreground: 'hsl(var(--editor-foreground))',
					border: 'hsl(var(--editor-border))',
					panel: 'hsl(var(--editor-panel))'
				},
				thinking: {
					DEFAULT: 'hsl(var(--thinking))',
					foreground: 'hsl(var(--thinking-foreground))',
					accent: 'hsl(var(--thinking-accent))'
				},
				surface: {
					DEFAULT: 'hsl(var(--surface))',
					hover: 'hsl(var(--surface-hover))',
					active: 'hsl(var(--surface-active))'
				}
			},
			backgroundImage: {
				'gradient-hero': 'var(--gradient-hero)',
				'gradient-thinking': 'var(--gradient-thinking)',
				'gradient-primary': 'var(--gradient-primary)',
				'gradient-glass': 'var(--gradient-glass)',
				'gradient-surface': 'var(--gradient-surface)',
				'noise': "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E\")"
			},
			borderRadius: {
				lg: 'var(--radius)',
				md: 'calc(var(--radius) - 2px)',
				sm: 'calc(var(--radius) - 4px)'
			},
			spacing: {
				'0.5': '0.125rem',  // 2px
				'1.5': '0.375rem',  // 6px
				'2.5': '0.625rem',  // 10px
				'3.5': '0.875rem',  // 14px
				'4.5': '1.125rem',  // 18px
				'5.5': '1.375rem',  // 22px
				'6.5': '1.625rem',  // 26px
				'7.5': '1.875rem',  // 30px
				'8.5': '2.125rem',  // 34px
				'9.5': '2.375rem',  // 38px
				'18': '4.5rem',     // 72px
				'22': '5.5rem',     // 88px
				'26': '6.5rem',     // 104px
				'30': '7.5rem',     // 120px
				'34': '8.5rem',     // 136px
				'38': '9.5rem',     // 152px
			},
			boxShadow: {
				'elevation-1': 'var(--elevation-1)',
				'elevation-2': 'var(--elevation-2)',
				'elevation-3': 'var(--elevation-3)',
				'elevation-4': 'var(--elevation-4)',
				'elevation-5': 'var(--elevation-5)',
				'glass': 'var(--glass-shadow)',
				'premium': '0 32px 64px -12px rgba(0, 0, 0, 0.25)',
				'glow': '0 0 20px hsl(var(--primary) / 0.3)',
				'glow-lg': '0 0 40px hsl(var(--primary) / 0.4)',
			},
			keyframes: {
				'accordion-down': {
					from: { height: '0' },
					to: { height: 'var(--radix-accordion-content-height)' }
				},
				'accordion-up': {
					from: { height: 'var(--radix-accordion-content-height)' },
					to: { height: '0' }
				},
				'fade-in': {
					'0%': { opacity: '0', transform: 'translateY(10px)' },
					'100%': { opacity: '1', transform: 'translateY(0)' }
				},
				'slide-up': {
					'0%': { opacity: '0', transform: 'translateY(20px)' },
					'100%': { opacity: '1', transform: 'translateY(0)' }
				},
				'pulse-glow': {
					'0%, 100%': { opacity: '1', boxShadow: '0 0 20px hsl(var(--primary))' },
					'50%': { opacity: '0.8', boxShadow: '0 0 40px hsl(var(--primary))' }
				},
				'thinking-pulse': {
					'0%, 100%': { opacity: '0.5', transform: 'scale(1)' },
					'50%': { opacity: '1', transform: 'scale(1.05)' }
				},
				'code-typing': {
					'0%': { width: '0' },
					'100%': { width: '100%' }
				},
				'spring-in': {
					'0%': { opacity: '0', transform: 'scale(0.9) translateY(20px)' },
					'100%': { opacity: '1', transform: 'scale(1) translateY(0)' }
				},
				'bounce-in': {
					'0%': { opacity: '0', transform: 'scale(0.3)' },
					'50%': { opacity: '1', transform: 'scale(1.05)' },
					'70%': { transform: 'scale(0.9)' },
					'100%': { opacity: '1', transform: 'scale(1)' }
				},
				'slide-in-right': {
					'0%': { opacity: '0', transform: 'translateX(50px)' },
					'100%': { opacity: '1', transform: 'translateX(0)' }
				},
				'slide-in-left': {
					'0%': { opacity: '0', transform: 'translateX(-50px)' },
					'100%': { opacity: '1', transform: 'translateX(0)' }
				},
				'float': {
					'0%, 100%': { transform: 'translateY(0px)' },
					'50%': { transform: 'translateY(-10px)' }
				},
				'shimmer': {
					'0%': { transform: 'translateX(-100%)' },
					'100%': { transform: 'translateX(100%)' }
				},
				'gradient-x': {
					'0%, 100%': { 'background-size': '200% 200%', 'background-position': 'left center' },
					'50%': { 'background-size': '200% 200%', 'background-position': 'right center' }
				},
				'gradient-y': {
					'0%, 100%': { 'background-size': '200% 200%', 'background-position': 'center top' },
					'50%': { 'background-size': '200% 200%', 'background-position': 'center bottom' }
				},
				'skeleton': {
					'0%': { opacity: '1' },
					'50%': { opacity: '0.4' },
					'100%': { opacity: '1' }
				},
				'progress': {
					'0%': { transform: 'translateX(-100%)' },
					'100%': { transform: 'translateX(100%)' }
				},
				'breathe': {
					'0%, 100%': { transform: 'scale(1)', opacity: '0.8' },
					'50%': { transform: 'scale(1.1)', opacity: '1' }
				},
				'glow': {
					'0%, 100%': { boxShadow: '0 0 20px hsl(var(--primary) / 0.3)' },
					'50%': { boxShadow: '0 0 40px hsl(var(--primary) / 0.6)' }
				}
			},
			animation: {
				'accordion-down': 'accordion-down 0.2s ease-out',
				'accordion-up': 'accordion-up 0.2s ease-out',
				'fade-in': 'fade-in 0.6s var(--spring-smooth)',
				'slide-up': 'slide-up 0.4s var(--spring-smooth)',
				'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
				'thinking-pulse': 'thinking-pulse 1.5s ease-in-out infinite',
				'code-typing': 'code-typing 2s ease-in-out',
				'spring-in': 'spring-in 0.6s var(--spring-bounce)',
				'bounce-in': 'bounce-in 0.8s var(--spring-bounce)',
				'slide-in-right': 'slide-in-right 0.5s var(--spring-smooth)',
				'slide-in-left': 'slide-in-left 0.5s var(--spring-smooth)',
				'float': 'float 3s ease-in-out infinite',
				'shimmer': 'shimmer 2s linear infinite',
				'gradient-x': 'gradient-x 3s ease infinite',
				'gradient-y': 'gradient-y 3s ease infinite',
				'skeleton': 'skeleton 2s ease-in-out infinite',
				'progress': 'progress 2s linear infinite',
				'breathe': 'breathe 2s ease-in-out infinite',
				'glow': 'glow 2s ease-in-out infinite',
				'stagger-1': 'spring-in 0.6s var(--spring-bounce) 0.1s both',
				'stagger-2': 'spring-in 0.6s var(--spring-bounce) 0.2s both',
				'stagger-3': 'spring-in 0.6s var(--spring-bounce) 0.3s both',
				'stagger-4': 'spring-in 0.6s var(--spring-bounce) 0.4s both'
			},
			fontFamily: {
				'sans': ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
				'mono': ['JetBrains Mono', 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', 'monospace']
			},
			fontSize: {
				'xs': ['0.75rem', { lineHeight: '1rem', letterSpacing: '0.01em' }],
				'sm': ['0.875rem', { lineHeight: '1.25rem', letterSpacing: '0.005em' }],
				'base': ['1rem', { lineHeight: '1.5rem', letterSpacing: '0em' }],
				'lg': ['1.125rem', { lineHeight: '1.75rem', letterSpacing: '-0.005em' }],
				'xl': ['1.25rem', { lineHeight: '1.75rem', letterSpacing: '-0.01em' }],
				'2xl': ['1.5rem', { lineHeight: '2rem', letterSpacing: '-0.015em' }],
				'3xl': ['1.875rem', { lineHeight: '2.25rem', letterSpacing: '-0.02em' }],
				'4xl': ['2.25rem', { lineHeight: '2.5rem', letterSpacing: '-0.025em' }],
				'5xl': ['3rem', { lineHeight: '1.1', letterSpacing: '-0.03em' }],
				'6xl': ['3.75rem', { lineHeight: '1.05', letterSpacing: '-0.035em' }],
				'7xl': ['4.5rem', { lineHeight: '1', letterSpacing: '-0.04em' }],
				'8xl': ['6rem', { lineHeight: '1', letterSpacing: '-0.045em' }],
				'9xl': ['8rem', { lineHeight: '1', letterSpacing: '-0.05em' }]
			},
			fontWeight: {
				'light': '300',
				'normal': '400',
				'medium': '500',
				'semibold': '600',
				'bold': '700',
				'extrabold': '800',
				'black': '900'
			},
			letterSpacing: {
				'tighter': '-0.05em',
				'tight': '-0.025em',
				'normal': '0em',
				'wide': '0.025em',
				'wider': '0.05em',
				'widest': '0.1em'
			},
			lineHeight: {
				'none': '1',
				'tight': '1.25',
				'snug': '1.375',
				'normal': '1.5',
				'relaxed': '1.625',
				'loose': '2'
			},
			backdropBlur: {
				'xs': '2px',
				'sm': '4px',
				'md': '8px',
				'lg': '16px',
				'xl': '20px',
				'2xl': '24px',
				'3xl': '40px'
			},
			transitionDuration: {
				'150': '150ms',
				'250': '250ms',
				'350': '350ms'
			},
			transitionTimingFunction: {
				'spring': 'var(--spring-smooth)',
				'spring-bounce': 'var(--spring-bounce)',
				'spring-snappy': 'var(--spring-snappy)'
			}
		}
	},
	plugins: [
		require("tailwindcss-animate"),
		function({ addUtilities }: any) {
			const newUtilities = {
				'.text-balance': {
					'text-wrap': 'balance'
				},
				'.text-pretty': {
					'text-wrap': 'pretty'
				},
				'.scrollbar-hide': {
					'-ms-overflow-style': 'none',
					'scrollbar-width': 'none',
					'&::-webkit-scrollbar': {
						'display': 'none'
					}
				},
				'.glass': {
					'background': 'rgba(var(--glass-bg))',
					'border': '1px solid rgba(var(--glass-border))',
					'box-shadow': 'var(--glass-shadow)',
					'backdrop-filter': 'blur(20px)',
					'-webkit-backdrop-filter': 'blur(20px)'
				},
				'.glass-subtle': {
					'background': 'rgba(var(--glass-bg))',
					'border': '1px solid rgba(var(--glass-border))',
					'backdrop-filter': 'blur(10px)',
					'-webkit-backdrop-filter': 'blur(10px)'
				}
			}
			addUtilities(newUtilities)
		}
	],
} satisfies Config;
