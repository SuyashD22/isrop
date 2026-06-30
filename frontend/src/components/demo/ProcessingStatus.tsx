import { UploadState } from '@/lib/types';
import { Progress } from '../ui/Progress';
import { CheckCircle2, Loader2, AlertCircle } from 'lucide-react';

interface Props {
  state: UploadState;
}

export function ProcessingStatus({ state }: Props) {
  if (state.status === 'idle') return null;

  return (
    <div 
      className="w-full rounded p-5 border"
      style={{
        background: "rgba(8,15,30,0.85)",
        borderColor: "rgba(0,212,255,0.12)",
      }}
    >
      <div className="flex items-center space-x-3 mb-4">
        {state.status === 'uploading' && <Loader2 className="animate-spin text-[#00D4FF]" size={20} />}
        {state.status === 'processing' && (
          <div className="relative flex items-center justify-center">
            <Loader2 className="animate-spin text-[#00D4FF] absolute" size={24} />
            <div className="w-2 h-2 bg-[#00D4FF] rounded-full animate-pulse"></div>
          </div>
        )}
        {state.status === 'done' && <CheckCircle2 className="text-[#00E5A0]" size={20} />}
        {state.status === 'error' && <AlertCircle className="text-[#ff5f56]" size={20} />}
        
        <div className="flex-1">
          <h4 className="text-[13px] font-semibold text-white tracking-wide">
            {state.status === 'uploading' && 'UPLOADING TILES...'}
            {state.status === 'processing' && 'RUNNING DIFFUSION INFERENCE...'}
            {state.status === 'done' && 'RECONSTRUCTION COMPLETE'}
            {state.status === 'error' && 'PROCESSING FAILED'}
          </h4>
          <p className="text-[11.5px] font-mono mt-0.5 text-[rgba(226,232,244,0.45)]">
            {state.status === 'processing' && 'This may take 10-30 seconds depending on the device.'}
            {state.error && <span className="text-[#ff5f56]">{state.error}</span>}
          </p>
        </div>
      </div>

      {(state.status === 'uploading' || state.status === 'processing') && (
        <Progress 
          value={state.status === 'uploading' ? state.progress * 0.5 : 50 + (state.progress * 0.5)} 
          className="h-1.5"
        />
      )}
    </div>
  );
}
