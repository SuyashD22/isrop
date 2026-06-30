import { forwardRef } from 'react';
import { cn } from './Button';

interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number;
  max?: number;
}

export const Progress = forwardRef<HTMLDivElement, ProgressProps>(
  ({ className, value, max = 100, ...props }, ref) => {
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

    return (
      <div
        ref={ref}
        className={cn('relative h-1.5 w-full overflow-hidden rounded bg-[rgba(0,212,255,0.08)] shadow-[inset_0_0_5px_rgba(0,212,255,0.1)]', className)}
        {...props}
      >
        <div
          className="h-full w-full flex-1 bg-gradient-to-r from-[#00D4FF] to-[#7B61FF] transition-all duration-300 ease-in-out shadow-[0_0_10px_rgba(0,212,255,0.8)]"
          style={{ transform: `translateX(-${100 - percentage}%)` }}
        />
      </div>
    );
  }
);
Progress.displayName = 'Progress';
