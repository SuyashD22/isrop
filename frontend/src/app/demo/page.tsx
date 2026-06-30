"use client";

import { useState } from 'react';
import { UploadZone } from '@/components/demo/UploadZone';
import { ReferenceStack } from '@/components/demo/ReferenceStack';
import { CompareSlider } from '@/components/demo/CompareSlider';
import { MetricsPanel } from '@/components/demo/MetricsPanel';
import { CloudOverlay } from '@/components/demo/CloudOverlay';
import { ProcessingStatus } from '@/components/demo/ProcessingStatus';
import { Button } from '@/components/ui/Button';
import { useFileUpload } from '@/hooks/useFileUpload';
import { useCloudRemoval } from '@/hooks/useCloudRemoval';
import { SENSOR_OPTIONS, CLOUD_MASK_METHODS, MODEL_OPTIONS } from '@/lib/constants';

// ── Dark select styles applied globally via inline style ──────────────────────
const selectClass = [
  'w-full text-[12.5px] rounded px-3 py-2 font-mono',
  'bg-[rgba(5,10,20,0.9)] text-[rgba(226,232,244,0.8)]',
  'border border-[rgba(0,212,255,0.15)]',
  'focus:outline-none focus:border-[rgba(0,212,255,0.45)]',
  'disabled:opacity-40 transition-colors',
].join(' ');

export default function DemoPage() {
  const [sensor, setSensor] = useState(SENSOR_OPTIONS[0].value);
  const [maskMethod, setMaskMethod] = useState(CLOUD_MASK_METHODS[0].value);
  const [model, setModel] = useState(MODEL_OPTIONS[0].value);

  const {
    files: cloudyFiles,
    addFiles: addCloudyFile,
    clear: clearCloudy,
    error: cloudyError,
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
    reset();
  };

  const isRunning = state.status === 'uploading' || state.status === 'processing';

  return (
    <div className="container mx-auto px-6 py-10 max-w-6xl">

      {/* Header */}
      <div className="mb-8">
        <div className="terminal-label mb-2">Inference Console</div>
        <h1 className="text-3xl font-bold text-white tracking-tight mb-2">
          Cloud Removal
        </h1>
        <p className="text-[13.5px] text-[rgba(226,232,244,0.45)] max-w-2xl">
          Upload a cloudy LISS-IV or Sentinel-2 tile and watch the multi-temporal
          diffusion model reconstruct missing spectral data.
        </p>
      </div>

      <div className="grid lg:grid-cols-12 gap-6">

        {/* ── Left: Controls ─────────────────────────────────────────────── */}
        <div className="lg:col-span-5 flex flex-col gap-4">

          {/* Upload card */}
          <div
            className="rounded-lg border p-5"
            style={{ background: "rgba(8,15,30,0.85)", borderColor: "rgba(0,212,255,0.12)" }}
          >
            {/* Target tile */}
            <div className="mb-5">
              <div className="terminal-label mb-2.5">01 · Target Tile (Cloudy)</div>
              <UploadZone
                onDrop={addCloudyFile}
                file={cloudyFiles[0] || null}
                onClear={() => { clearCloudy(); reset(); }}
                error={cloudyError}
              />
            </div>

            {/* Reference stack */}
            <div
              className="mb-5 pt-5 border-t"
              style={{ borderColor: "rgba(0,212,255,0.08)" }}
            >
              <div className="terminal-label mb-2.5">02 · Reference Frames (Optional)</div>
              <ReferenceStack
                references={refFiles}
                onAdd={addRefFiles}
                onRemove={removeRefFile}
              />
            </div>

            {/* Parameters */}
            <div
              className="mb-5 pt-5 border-t"
              style={{ borderColor: "rgba(0,212,255,0.08)" }}
            >
              <div className="terminal-label mb-3">03 · Parameters</div>
              <div className="space-y-3">
                <div>
                  <label className="text-[11px] font-mono text-[rgba(226,232,244,0.4)] block mb-1.5 uppercase tracking-widest">
                    Sensor
                  </label>
                  <select
                    className={selectClass}
                    value={sensor}
                    onChange={e => setSensor(e.target.value)}
                    disabled={isRunning}
                  >
                    {SENSOR_OPTIONS.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-[11px] font-mono text-[rgba(226,232,244,0.4)] block mb-1.5 uppercase tracking-widest">
                    Model
                  </label>
                  <select
                    className={selectClass}
                    value={model}
                    onChange={e => setModel(e.target.value)}
                    disabled={isRunning}
                  >
                    {MODEL_OPTIONS.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-[11px] font-mono text-[rgba(226,232,244,0.4)] block mb-1.5 uppercase tracking-widest">
                    Cloud Mask Strategy
                  </label>
                  <select
                    className={selectClass}
                    value={maskMethod}
                    onChange={e => setMaskMethod(e.target.value)}
                    disabled={isRunning}
                  >
                    {CLOUD_MASK_METHODS.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Run button */}
            <Button
              className="w-full h-10"
              onClick={handleProcess}
              disabled={cloudyFiles.length === 0 || isRunning}
              isLoading={isRunning}
            >
              {isRunning ? 'Processing…' : 'Run Cloud Removal'}
            </Button>
          </div>
        </div>

        {/* ── Right: Output ──────────────────────────────────────────────── */}
        <div className="lg:col-span-7 flex flex-col gap-4">
          <ProcessingStatus state={state} />

          {result ? (
            <div className="space-y-4" style={{ animation: "fadeIn 0.4s ease-out both" }}>
              {/* Compare slider */}
              <div
                className="rounded-lg border overflow-hidden"
                style={{ borderColor: "rgba(0,212,255,0.15)" }}
              >
                <CompareSlider
                  cloudyImage={cloudyFiles[0].preview}
                  cleanImage={result.output_image}
                  isBase64={true}
                />
              </div>

              {/* Metrics */}
              <MetricsPanel metrics={result.metrics} />

              {/* Analysis + reset */}
              <div
                className="rounded-lg border p-5"
                style={{ background: "rgba(8,15,30,0.85)", borderColor: "rgba(0,212,255,0.12)" }}
              >
                <div className="terminal-label mb-4">Analysis Layers</div>
                <div className="grid sm:grid-cols-2 gap-5">
                  <CloudOverlay
                    cloudyImage={cloudyFiles[0].preview}
                    cloudMask={result.cloud_mask}
                    coverage={result.metrics.cloud_coverage}
                  />
                  <div
                    className="rounded p-4 flex flex-col justify-between text-[12.5px] text-[rgba(226,232,244,0.55)]"
                    style={{
                      background: "rgba(5,10,20,0.7)",
                      border: "1px solid rgba(0,212,255,0.08)",
                    }}
                  >
                    <div className="space-y-2 mb-4 font-mono">
                      <div className="flex justify-between">
                        <span className="text-[rgba(226,232,244,0.35)]">Time</span>
                        <span className="text-[#00D4FF]">{result.processing_time_ms} ms</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[rgba(226,232,244,0.35)]">Mask</span>
                        <span className="text-[rgba(226,232,244,0.7)]">Auto-generated</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[rgba(226,232,244,0.35)]">Model</span>
                        <span className="text-[rgba(226,232,244,0.7)]">
                          {result.model_name || `LISSclear v${result.model_version}`}
                        </span>
                      </div>
                    </div>
                    <Button variant="outline" size="sm" onClick={handleReset} className="w-full">
                      Process Another Tile
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* Empty state */
            <div
              className="flex-1 min-h-[520px] rounded-lg flex flex-col items-center justify-center"
              style={{
                border: "1px dashed rgba(0,212,255,0.15)",
                background: "rgba(8,15,30,0.4)",
              }}
            >
              <div
                className="w-16 h-16 rounded-lg flex items-center justify-center mb-5"
                style={{ background: "rgba(0,212,255,0.06)", border: "1px solid rgba(0,212,255,0.15)" }}
              >
                <svg className="w-7 h-7 text-[rgba(0,212,255,0.4)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <div className="terminal-label mb-1">Awaiting input</div>
              <p className="text-[12px] text-[rgba(226,232,244,0.3)] mt-1">
                Upload a tile and click Run Cloud Removal
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
