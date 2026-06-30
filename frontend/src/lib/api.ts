// frontend/src/lib/api.ts
import axios, { AxiosProgressEvent } from 'axios';
import { InferenceResult } from './types';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 300_000, // 5 minutes — inference can take a while
});

export interface RemoveCloudsOptions {
  cloudyFile: File;
  referenceFiles?: File[];
  sensor?: string;
  cloudMaskMethod?: string;
  modelName?: string;
  onUploadProgress?: (progress: number) => void;
}

/**
 * Upload files and run cloud removal inference.
 */
export async function removeClouds(
  options: RemoveCloudsOptions
): Promise<InferenceResult> {
  const {
    cloudyFile,
    referenceFiles = [],
    sensor = 'sentinel2',
    cloudMaskMethod = 'auto',
    modelName = 'cr_net',
    onUploadProgress,
  } = options;

  const form = new FormData();
  form.append('cloudy_tile', cloudyFile);
  referenceFiles.forEach((f) => form.append('reference_tiles', f));
  form.append('sensor', sensor);
  form.append('cloud_mask_method', cloudMaskMethod);
  form.append('model_name', modelName);

  const res = await apiClient.post<InferenceResult>('/api/remove-clouds', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (event: AxiosProgressEvent) => {
      if (onUploadProgress && event.total) {
        onUploadProgress(Math.round((event.loaded / event.total) * 100));
      }
    },
  });

  return res.data;
}

/**
 * Check API health status.
 */
export async function checkHealth(): Promise<{
  status: string;
  model_loaded: boolean;
  device: string;
  version: string;
}> {
  const res = await apiClient.get('/api/health');
  return res.data;
}

/**
 * Get metric info and thresholds.
 */
export async function getMetricInfo(): Promise<Record<string, unknown>> {
  const res = await apiClient.get('/api/metrics');
  return res.data;
}
