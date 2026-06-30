import { UploadState } from '@/lib/types';
import { Progress } from '../ui/Progress';
import { CheckCircle2, Loader2, AlertCircle } from 'lucide-react';

interface Props {
  state: UploadState;
}

export function ProcessingStatus({ state }: Props) {
  if (state.status === 'idle') return null;

  return (
    <div className="w-full bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
      <div className="flex items-center space-x-3 mb-4">
        {state.status === 'uploading' && <Loader2 className="animate-spin text-space-500" size={20} />}
        {state.status === 'processing' && (
          <div className="relative flex items-center justify-center">
            <Loader2 className="animate-spin text-space-500 absolute" size={24} />
            <div className="w-2 h-2 bg-space-500 rounded-full animate-pulse"></div>
          </div>
        )}
        {state.status === 'done' && <CheckCircle2 className="text-green-500" size={20} />}
        {state.status === 'error' && <AlertCircle className="text-red-500" size={20} />}
        
        <div className="flex-1">
          <h4 className="text-sm font-semibold text-gray-800">
            {state.status === 'uploading' && 'Uploading tiles...'}
            {state.status === 'processing' && 'Running diffusion inference...'}
            {state.status === 'done' && 'Reconstruction complete'}
            {state.status === 'error' && 'Processing failed'}
          </h4>
          <p className="text-xs text-gray-500">
            {state.status === 'processing' && 'This may take 10-30 seconds depending on the device.'}
            {state.error && <span className="text-red-500">{state.error}</span>}
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
