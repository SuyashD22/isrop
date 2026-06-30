// frontend/src/hooks/useCloudRemoval.ts
import { useState, useCallback } from 'react';
import { InferenceResult, UploadState } from '@/lib/types';
import { removeClouds } from '@/lib/api';

export function useCloudRemoval() {
  const [result, setResult] = useState<InferenceResult | null>(null);
  const [state, setState] = useState<UploadState>({ status: 'idle', progress: 0 });

  const executeInference = useCallback(async (
    cloudyFile: File,
    referenceFiles: File[] = [],
    sensor: string = 'sentinel2',
    cloudMaskMethod: string = 'auto',
    modelName: string = 'cr_net',
  ) => {
    setState({ status: 'uploading', progress: 0 });
    setResult(null);

    try {
      const res = await removeClouds({
        cloudyFile,
        referenceFiles,
        sensor,
        cloudMaskMethod,
        modelName,
        onUploadProgress: (progress) => {
          if (progress < 100) {
            setState({ status: 'uploading', progress });
          } else {
            setState({ status: 'processing', progress: 100 });
          }
        }
      });

      setResult(res);
      setState({ status: 'done', progress: 100 });
    } catch (err: any) {
      console.error('Inference error:', err);
      setState({ 
        status: 'error', 
        progress: 0, 
        error: err.response?.data?.message || err.message || 'An unexpected error occurred during inference.'
      });
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setState({ status: 'idle', progress: 0 });
  }, []);

  return { result, state, executeInference, reset };
}
