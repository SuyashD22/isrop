import { ButtonHTMLAttributes, forwardRef } from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg' | 'icon';
  isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, children, ...props }, ref) => {

    const variants = {
      primary: [
        'text-[#050a14] font-semibold',
        'bg-gradient-to-r from-[#00D4FF] to-[#7B61FF]',
        'shadow-[0_0_24px_rgba(0,212,255,0.3)]',
        'hover:shadow-[0_0_40px_rgba(0,212,255,0.5)]',
        'hover:-translate-y-px',
      ].join(' '),
      secondary: [
        'bg-[rgba(0,212,255,0.08)] text-[#00D4FF]',
        'border border-[rgba(0,212,255,0.2)]',
        'hover:bg-[rgba(0,212,255,0.14)] hover:border-[rgba(0,212,255,0.4)]',
      ].join(' '),
      outline: [
        'border border-[rgba(0,212,255,0.2)] bg-transparent',
        'text-[rgba(226,232,244,0.65)]',
        'hover:border-[rgba(0,212,255,0.45)] hover:text-[#00D4FF] hover:bg-[rgba(0,212,255,0.04)]',
      ].join(' '),
      ghost: [
        'bg-transparent text-[rgba(226,232,244,0.55)]',
        'hover:bg-[rgba(0,212,255,0.06)] hover:text-[#00D4FF]',
      ].join(' '),
      danger: 'bg-red-600/80 border border-red-500/40 text-white hover:bg-red-600',
    };

    const sizes = {
      sm:   'h-8 px-3 text-xs rounded',
      md:   'h-9 px-4 py-2 text-sm rounded',
      lg:   'h-11 px-6 text-sm rounded',
      icon: 'h-9 w-9 p-2 rounded',
    };

    return (
      <button
        ref={ref}
        disabled={isLoading || props.disabled}
        className={cn(
          'inline-flex items-center justify-center font-medium transition-all duration-200',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00D4FF]/50',
          'disabled:opacity-40 disabled:pointer-events-none',
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {isLoading ? (
          <svg
            className="animate-spin -ml-1 mr-2 h-4 w-4 text-current"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        ) : null}
        {children}
      </button>
    );
  }
);
Button.displayName = 'Button';
