// frontend/src/lib/constants.ts

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const ACCEPTED_FILE_TYPES = {
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/tiff': ['.tif', '.tiff'],
  'application/octet-stream': ['.tif', '.tiff'],
};

export const MAX_FILE_SIZE_MB = 50;
export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
export const MAX_REFERENCE_FRAMES = 3;

export const SENSOR_OPTIONS = [
  { value: 'sentinel2', label: 'Sentinel-2 L2A (10m)', description: 'R, G, B, NIR bands — SCL cloud masking' },
  { value: 'liss4', label: 'LISS-IV MX (5.8m)', description: 'Green, Red, NIR bands — NDSI cloud masking' },
];

export const CLOUD_MASK_METHODS = [
  { value: 'auto', label: 'Auto (recommended)', description: 'Best available method' },
  { value: 'ndsi', label: 'NDSI', description: 'Spectral index — for LISS-IV' },
  { value: 'brightness', label: 'Brightness', description: 'Simple threshold — fastest' },
];

export const MODEL_OPTIONS = [
  { value: 'cr_net', label: 'CR-Net (Recommended)', description: 'Complex multi-modal architecture with attention' },
  { value: 'baseline_resnet', label: 'Baseline ResNet', description: '16-block ResNet architecture' },
  { value: 'sar_carl', label: 'SAR-Carl (HDF5)', description: '34-layer residual Keras model' },
];

export const APP_NAME = 'LISSclear';
export const APP_TAGLINE = 'Multi-temporal Cloud Removal for LISS-IV Satellite Imagery';
export const ISRO_URL = 'https://www.isro.gov.in';
export const BHUVAN_URL = 'https://bhuvan.nrsc.gov.in';
export const BAH_URL = 'https://isro.gov.in';

// Demo sample images (placeholder paths for development)
export const DEMO_SAMPLES = [
  {
    id: 'gangetic-plain',
    label: 'Gangetic Plain (UP)',
    description: 'Heavy monsoon cloud cover — agricultural zone',
    cloudCoverage: 0.65,
  },
  {
    id: 'deccan-plateau',
    label: 'Deccan Plateau (Maharashtra)',
    description: 'Mixed cloud/haze — Kharif crop monitoring',
    cloudCoverage: 0.42,
  },
  {
    id: 'coastal-orissa',
    label: 'Coastal Odisha',
    description: 'Dense cloud — cyclone aftermath',
    cloudCoverage: 0.81,
  },
];
