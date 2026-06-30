// frontend/src/lib/types.ts

export interface MetricsResult {
  psnr: number;
  ssim: number;
  sam: number;
  ndvi_mae: number | null;
  cloud_coverage: number;
}

export interface InferenceResult {
  output_image: string;        // base64 PNG
  cloud_mask: string;          // base64 PNG
  metrics: MetricsResult;
  processing_time_ms: number;
  model_version: string;
  model_name?: string;
  tile_id?: string | null;
}

export interface UploadState {
  status: 'idle' | 'uploading' | 'processing' | 'done' | 'error';
  progress: number;
  error?: string;
}

export interface UploadedFile {
  file: File;
  preview: string;  // object URL for display
  name: string;
}

export type MetricKey = 'ssim' | 'psnr' | 'sam' | 'ndvi_mae';

export interface MetricInfo {
  label: string;
  unit: string;
  description: string;
  threshold: number;
  higherIsBetter: boolean;
  format: (v: number) => string;
}

export const METRIC_INFO: Record<MetricKey, MetricInfo> = {
  ssim: {
    label: 'SSIM',
    unit: '',
    description: 'Structural Similarity Index — measures structural fidelity',
    threshold: 0.85,
    higherIsBetter: true,
    format: (v) => v.toFixed(3),
  },
  psnr: {
    label: 'PSNR',
    unit: 'dB',
    description: 'Peak Signal-to-Noise Ratio — measures reconstruction accuracy',
    threshold: 30,
    higherIsBetter: true,
    format: (v) => `${v.toFixed(1)} dB`,
  },
  sam: {
    label: 'SAM',
    unit: 'rad',
    description: 'Spectral Angle Mapper — preserves band ratios for NDVI/NDWI',
    threshold: 0.10,
    higherIsBetter: false,
    format: (v) => v.toFixed(3),
  },
  ndvi_mae: {
    label: 'NDVI MAE',
    unit: '',
    description: 'Vegetation Index preservation — critical for agriculture monitoring',
    threshold: 0.05,
    higherIsBetter: false,
    format: (v) => v.toFixed(4),
  },
};
