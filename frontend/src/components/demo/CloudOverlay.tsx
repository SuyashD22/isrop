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
      <div className="relative w-full aspect-square rounded-xl overflow-hidden border border-gray-200 shadow-sm group bg-gray-900">
        {/* Base cloudy image */}
        <img 
          src={cloudyImage.startsWith('blob:') ? cloudyImage : `data:image/png;base64,${cloudyImage}`} 
          alt="Cloudy input" 
          className="w-full h-full object-cover transition-opacity duration-300"
          style={{ opacity: showMask ? 0.4 : 1 }}
        />
        
        {/* Cloud mask overlay (red) */}
        <img 
          src={`data:image/png;base64,${cloudMask}`} 
          alt="Cloud mask" 
          className={cn(
            "absolute inset-0 w-full h-full object-cover mix-blend-screen transition-opacity duration-300",
            showMask ? "opacity-100" : "opacity-0"
          )}
          style={{ filter: 'invert(20%) sepia(90%) saturate(6000%) hue-rotate(350deg) brightness(100%) contrast(150%)' }}
        />

        {/* Toggle button */}
        <button
          onClick={() => setShowMask(!showMask)}
          className="absolute bottom-3 right-3 bg-black/60 hover:bg-black/80 backdrop-blur-md text-white p-2 rounded-lg transition-colors border border-white/20 shadow-lg"
          title="Toggle Cloud Mask Overlay"
        >
          {showMask ? <EyeOff size={18} /> : <Eye size={18} />}
        </button>
        
        {/* Coverage badge */}
        <div className="absolute top-3 left-3 bg-black/60 backdrop-blur-md text-white px-2.5 py-1 rounded-md text-[11px] font-mono font-medium border border-white/10">
          {(coverage * 100).toFixed(1)}% Coverage
        </div>
      </div>
    </div>
  );
}
