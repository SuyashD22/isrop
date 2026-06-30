"use client";

import { useState } from 'react';
import { UploadZone } from '@/components/demo/UploadZone';
import { ReferenceStack } from '@/components/demo/ReferenceStack';
import { CompareSlider } from '@/components/demo/CompareSlider';
import { MetricsPanel } from '@/components/demo/MetricsPanel';
import { CloudOverlay } from '@/components/demo/CloudOverlay';
import { ProcessingStatus } from '@/components/demo/ProcessingStatus';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { useFileUpload } from '@/hooks/useFileUpload';
import { useCloudRemoval } from '@/hooks/useCloudRemoval';
import { SENSOR_OPTIONS, CLOUD_MASK_METHODS, MODEL_OPTIONS } from '@/lib/constants';

export default function DemoPage() {
  const [sensor, setSensor] = useState(SENSOR_OPTIONS[0].value);
  const [maskMethod, setMaskMethod] = useState(CLOUD_MASK_METHODS[0].value);
  const [model, setModel] = useState(MODEL_OPTIONS[0].value);
  
  const { 
    files: cloudyFiles, 
    addFiles: addCloudyFile, 
    clear: clearCloudy,
    error: cloudyError
  } = useFileUpload(1);
  
  const { 
    files: refFiles, 
    addFiles: addRefFiles, 
    removeFile: removeRefFile,
  } = useFileUpload(3);

  const { result, state, executeInference, reset } = useCloudRemoval();

  const handleProcess = () => {
    if (cloudyFiles.length > 0) {
      executeInference(
        cloudyFiles[0].file,
        refFiles.map(f => f.file),
        sensor,
        maskMethod,
        model
      );
    }
  };

  const handleReset = () => {
    clearCloudy();
    // refFiles are kept intentionally to allow trying another cloudy image with same refs
    reset();
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight mb-2">
          Cloud Removal Inference
        </h1>
        <p className="text-gray-600 max-w-3xl">
          Upload a cloudy LISS-IV or Sentinel-2 tile and watch the multi-temporal diffusion model reconstruct the missing data.
        </p>
      </div>

      <div className="grid lg:grid-cols-12 gap-8">
        {/* Left Column: Controls & Inputs */}
        <div className="lg:col-span-5 space-y-6">
          <Card className="border-gray-200">
            <CardContent className="pt-6">
              
              {/* Target File */}
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-800 mb-3">1. Target Tile (Cloudy)</h3>
                <UploadZone 
                  onDrop={addCloudyFile}
                  file={cloudyFiles[0] || null}
                  onClear={() => { clearCloudy(); reset(); }}
                  error={cloudyError}
                />
              </div>

              {/* Reference Files */}
              <div className="mb-6 pt-6 border-t border-gray-100">
                <h3 className="text-sm font-semibold text-gray-800 mb-3">2. Context (Optional but recommended)</h3>
                <ReferenceStack 
                  references={refFiles}
                  onAdd={addRefFiles}
                  onRemove={removeRefFile}
                />
              </div>

              {/* Parameters */}
              <div className="mb-6 pt-6 border-t border-gray-100">
                <h3 className="text-sm font-semibold text-gray-800 mb-3">3. Parameters</h3>
                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-medium text-gray-600 block mb-1">Sensor Configuration</label>
                    <select 
                      className="w-full text-sm rounded-lg border-gray-300 shadow-sm focus:border-space-500 focus:ring-space-500 bg-white"
                      value={sensor}
                      onChange={(e) => setSensor(e.target.value)}
                      disabled={state.status === 'uploading' || state.status === 'processing'}
                    >
                      {SENSOR_OPTIONS.map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-600 block mb-1">Model Selection</label>
                    <select 
                      className="w-full text-sm rounded-lg border-gray-300 shadow-sm focus:border-space-500 focus:ring-space-500 bg-white"
                      value={model}
                      onChange={(e) => setModel(e.target.value)}
                      disabled={state.status === 'uploading' || state.status === 'processing'}
                    >
                      {MODEL_OPTIONS.map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-600 block mb-1">Cloud Masking Strategy</label>
                    <select 
                      className="w-full text-sm rounded-lg border-gray-300 shadow-sm focus:border-space-500 focus:ring-space-500 bg-white"
                      value={maskMethod}
                      onChange={(e) => setMaskMethod(e.target.value)}
                      disabled={state.status === 'uploading' || state.status === 'processing'}
                    >
                      {CLOUD_MASK_METHODS.map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-2">
                <Button 
                  className="w-full py-6 text-base"
                  onClick={handleProcess}
                  disabled={cloudyFiles.length === 0 || state.status === 'uploading' || state.status === 'processing'}
                  isLoading={state.status === 'uploading' || state.status === 'processing'}
                >
                  {state.status === 'uploading' || state.status === 'processing' 
                    ? 'Processing...' 
                    : 'Remove Clouds'}
                </Button>
              </div>

            </CardContent>
          </Card>
        </div>

        {/* Right Column: Output & Visualization */}
        <div className="lg:col-span-7 flex flex-col space-y-6">
          <ProcessingStatus state={state} />

          {result ? (
            <div className="space-y-6 animate-fade-in">
              <div className="glass-panel p-1 border-gray-200">
                <CompareSlider 
                  cloudyImage={cloudyFiles[0].preview} 
                  cleanImage={result.output_image} 
                  isBase64={true}
                />
              </div>
              
              <MetricsPanel metrics={result.metrics} />

              <Card className="border-gray-200">
                <CardContent className="pt-6">
                  <h3 className="text-sm font-semibold text-gray-800 mb-4">Analysis Layers</h3>
                  <div className="grid sm:grid-cols-2 gap-6">
                    <CloudOverlay 
                      cloudyImage={cloudyFiles[0].preview}
                      cloudMask={result.cloud_mask}
                      coverage={result.metrics.cloud_coverage}
                    />
                    <div className="bg-gray-50 rounded-xl p-4 flex flex-col justify-center text-sm text-gray-600 border border-gray-100">
                      <p className="mb-2"><strong>Time taken:</strong> {result.processing_time_ms}ms</p>
                      <p className="mb-2"><strong>Cloud mask:</strong> Auto-generated</p>
                      <p className="mb-4"><strong>Model:</strong> {result.model_name || `LISSclear v${result.model_version}`}</p>
                      
                      <Button variant="outline" size="sm" onClick={handleReset} className="w-full mt-auto">
                        Process Another Tile
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <div className="flex-1 min-h-[500px] border-2 border-dashed border-gray-200 rounded-2xl flex flex-col items-center justify-center text-gray-400 bg-gray-50/50">
              <svg className="w-16 h-16 mb-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <p className="text-sm font-medium">Reconstruction output will appear here</p>
              <p className="text-xs mt-1">Upload a tile and click Process to begin</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
