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
    <div className="relative rounded-xl overflow-hidden shadow-glass border border-gray-200/50 group">
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
        className="w-full h-full bg-gray-900"
      />
      
      {/* Labels */}
      <div className="absolute top-4 left-4 bg-black/60 backdrop-blur-md text-white text-xs font-semibold px-3 py-1.5 rounded-full pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity shadow-sm">
        Input
      </div>
      <div className="absolute top-4 right-4 bg-space-600/80 backdrop-blur-md text-white text-xs font-semibold px-3 py-1.5 rounded-full pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity shadow-glow-blue">
        Reconstructed
      </div>
    </div>
  );
}
