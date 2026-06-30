import { useState } from 'react';
import { cn } from './Button';

interface TooltipProps {
  children: React.ReactNode;
  content: string;
  className?: string;
}

export function Tooltip({ children, content, className }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div 
      className={cn('relative inline-flex', className)}
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div className="absolute z-50 w-64 p-2.5 text-[12px] text-[rgba(226,232,244,0.9)] bg-[rgba(5,10,20,0.95)] border border-[rgba(0,212,255,0.2)] rounded shadow-[0_4px_20px_rgba(0,0,0,0.8)] -top-2 left-1/2 -translate-x-1/2 -translate-y-full before:content-[''] before:absolute before:top-full before:left-1/2 before:-translate-x-1/2 before:border-4 before:border-transparent before:border-t-[rgba(0,212,255,0.2)]">
          {content}
        </div>
      )}
    </div>
  );
}
