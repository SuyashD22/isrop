import { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { cn } from '../ui/Button';

interface Props {
  cloudyImage: string; // Object URL or base64
  cloudMask: string;   // Base64
  coverage: number;
}

export function CloudOverlay({ cloudyImage, cloudMask, coverage }: Props) {
  const [showMask, setShowMask] = useState(false);

  return (
    <div className="flex flex-col space-y-3">
      <div className="relative w-full aspect-square rounded border border-[rgba(0,212,255,0.2)] shadow-sm group bg-[rgba(5,10,20,1)] overflow-hidden">
        {/* Base cloudy image */}
        <img 
          src={cloudyImage.startsWith('blob:') ? cloudyImage : `data:image/png;base64,${cloudyImage}`} 
          alt="Cloudy input" 
          className="w-full h-full object-cover transition-opacity duration-300"
          style={{ opacity: showMask ? 0.4 : 1 }}
        />
        
        {/* Cloud mask overlay (red/magenta glow) */}
        <img 
          src={`data:image/png;base64,${cloudMask}`} 
          alt="Cloud mask" 
          className={cn(
            "absolute inset-0 w-full h-full object-cover mix-blend-screen transition-opacity duration-300",
            showMask ? "opacity-100" : "opacity-0"
          )}
          style={{ filter: 'invert(20%) sepia(90%) saturate(6000%) hue-rotate(300deg) brightness(120%) contrast(150%)' }}
        />

        {/* Toggle button */}
        <button
          onClick={() => setShowMask(!showMask)}
          className="absolute bottom-2 right-2 bg-[rgba(5,10,20,0.8)] hover:bg-[rgba(0,212,255,0.15)] backdrop-blur-md text-[#00D4FF] p-2 rounded transition-colors border border-[rgba(0,212,255,0.2)] shadow-[0_0_15px_rgba(0,212,255,0.2)]"
          title="Toggle Cloud Mask Overlay"
        >
          {showMask ? <EyeOff size={16} /> : <Eye size={16} />}
        </button>
        
        {/* Coverage badge */}
        <div className="absolute top-2 left-2 bg-[rgba(5,10,20,0.85)] backdrop-blur-md text-[rgba(226,232,244,0.9)] px-2 py-1 rounded text-[10px] font-mono tracking-wider border border-[rgba(0,212,255,0.15)] shadow-[0_0_10px_rgba(0,0,0,0.5)]">
          {(coverage * 100).toFixed(1)}% COVERAGE
        </div>
      </div>
    </div>
  );
}
