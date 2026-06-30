import { ReactCompareSlider, ReactCompareSliderImage } from 'react-compare-slider';

interface Props {
  cloudyImage: string;
  cleanImage: string;
  isBase64?: boolean;
}

export function CompareSlider({ cloudyImage, cleanImage }: Props) {
  // If it's a raw base64 string (no data: prefix and not a blob URL), prepend the data URI
  const getSrc = (src: string) => {
    if (src.startsWith('blob:') || src.startsWith('http') || src.startsWith('data:')) {
      return src;
    }
    return `data:image/png;base64,${src}`;
  };

  return (
    <div className="relative rounded overflow-hidden group bg-[rgba(5,10,20,1)]">
      <ReactCompareSlider
        boundsPadding={0}
        itemOne={
          <ReactCompareSliderImage 
            src={getSrc(cloudyImage)} 
            alt="Cloudy input tile" 
            style={{ filter: 'brightness(1.05) contrast(1.02)', objectFit: 'cover', width: '100%', height: '100%' }}
          />
        }
        itemTwo={
          <ReactCompareSliderImage 
            src={getSrc(cleanImage)} 
            alt="Cloud-removed output" 
            style={{ filter: 'brightness(1.05) contrast(1.02)', objectFit: 'cover', width: '100%', height: '100%' }}
          />
        }
        style={{ width: '100%', height: '400px' }}
        position={50}
        className="w-full h-full bg-[#050a14]"
      />
      
      {/* Labels */}
      <div className="absolute top-4 left-4 bg-[rgba(5,10,20,0.85)] border border-[rgba(0,212,255,0.15)] text-[rgba(226,232,244,0.9)] backdrop-blur-md text-[10px] font-mono tracking-widest uppercase px-3 py-1.5 rounded pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity shadow-[0_0_15px_rgba(0,0,0,0.5)]">
        Target Tile
      </div>
      <div className="absolute top-4 right-4 bg-gradient-to-r from-[#00D4FF]/90 to-[#7B61FF]/90 border border-[rgba(0,212,255,0.4)] backdrop-blur-md text-[#050a14] text-[10px] font-mono font-bold tracking-widest uppercase px-3 py-1.5 rounded pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity shadow-[0_0_20px_rgba(0,212,255,0.4)]">
        Reconstructed
      </div>
    </div>
  );
}
