import Link from "next/link";
import { ArrowRight, Activity, Layers, Cpu } from "lucide-react";

// ── Metric card ──────────────────────────────────────────────────────────────
function MetricCard({
  label,
  value,
  unit,
  good,
  ours,
  color,
}: {
  label: string;
  value: string;
  unit: string;
  good: string;
  ours: string;
  color: string;
}) {
  return (
    <div
      className="relative group p-5 rounded-lg border transition-all duration-300 overflow-hidden"
      style={{
        background: "rgba(8,15,30,0.8)",
        borderColor: "rgba(0,212,255,0.1)",
      }}
    >
      {/* Hover glow */}
      <div
        className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
        style={{
          background: `radial-gradient(ellipse at 50% 0%, ${color}18 0%, transparent 70%)`,
        }}
      />
      <div className="relative">
        <div
          className="terminal-label mb-3"
          style={{ color: `${color}99` }}
        >
          {label}
        </div>
        <div
          className="text-3xl font-bold font-mono tracking-tight mb-1"
          style={{ color }}
        >
          {value}
          <span className="text-sm font-normal ml-1 opacity-60">{unit}</span>
        </div>
        <div className="flex items-center justify-between mt-3 pt-3 border-t border-[rgba(255,255,255,0.05)]">
          <div className="text-[11px] text-[rgba(226,232,244,0.4)]">
            threshold <span className="text-[rgba(226,232,244,0.7)]">{good}</span>
          </div>
          <div
            className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded"
            style={{
              color,
              background: `${color}18`,
            }}
          >
            {ours} ✓
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Feature card ─────────────────────────────────────────────────────────────
function FeatureCard({
  icon: Icon,
  title,
  body,
  tag,
  color,
}: {
  icon: React.ElementType;
  title: string;
  body: string;
  tag: string;
  color: string;
}) {
  return (
    <div
      className="relative group p-6 rounded-lg border transition-all duration-300"
      style={{
        background: "rgba(8,15,30,0.7)",
        borderColor: "rgba(0,212,255,0.1)",
      }}
    >
      <div
        className="absolute inset-0 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
        style={{ boxShadow: `inset 0 0 0 1px ${color}40` }}
      />
      <div
        className="w-9 h-9 rounded flex items-center justify-center mb-5"
        style={{ background: `${color}18`, color }}
      >
        <Icon size={18} />
      </div>
      <div
        className="terminal-label mb-2"
        style={{ color: `${color}88` }}
      >
        {tag}
      </div>
      <h3 className="text-[15px] font-semibold text-white mb-3">{title}</h3>
      <p className="text-[13px] text-[rgba(226,232,244,0.5)] leading-relaxed">{body}</p>
    </div>
  );
}

// ── Pipeline step ─────────────────────────────────────────────────────────────
function PipelineStep({
  n,
  label,
  desc,
}: {
  n: string;
  label: string;
  desc: string;
}) {
  return (
    <div className="flex items-start gap-4">
      <div
        className="flex-shrink-0 w-7 h-7 rounded flex items-center justify-center text-[11px] font-mono font-bold text-[#050a14]"
        style={{ background: "linear-gradient(135deg,#00D4FF,#7B61FF)" }}
      >
        {n}
      </div>
      <div className="pt-0.5">
        <div className="text-[13px] font-semibold text-white mb-0.5">{label}</div>
        <div className="text-[12px] text-[rgba(226,232,244,0.45)]">{desc}</div>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function Home() {
  return (
    <div className="flex-1 flex flex-col">

      {/* ── HERO ─────────────────────────────────────────────────────────────── */}
      <section className="relative flex-1 flex flex-col items-center justify-center py-24 lg:py-36 overflow-hidden">
        {/* Radial top glow */}
        <div
          className="absolute top-0 left-1/2 -translate-x-1/2 w-[900px] h-[400px] pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse 80% 100% at 50% 0%, rgba(0,212,255,0.12) 0%, transparent 70%)",
          }}
        />
        {/* Subtle corner accent */}
        <div
          className="absolute top-0 right-0 w-[340px] h-[340px] pointer-events-none opacity-30"
          style={{
            background:
              "radial-gradient(ellipse at 100% 0%, rgba(123,97,255,0.25) 0%, transparent 65%)",
          }}
        />

        <div className="relative container mx-auto px-6 text-center">
          {/* Mission badge */}
          <div className="inline-flex items-center gap-2 mb-10">
            <span className="status-dot" />
            <span className="terminal-label">
              BAH 2026 · ISRO · Problem Statement 2
            </span>
          </div>

          {/* Headline */}
          <h1
            className="text-4xl md:text-[3.5rem] font-mono font-bold tracking-tight leading-[1.1] mb-7 max-w-5xl mx-auto"
            style={{ animation: "slideUp 0.5s ease-out both" }}
          >
            <span className="text-white">Remove clouds.</span>
            <br />
            <span
              style={{
                background: "linear-gradient(135deg, #00D4FF 0%, #7B61FF 60%, #00E5A0 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              Restore the ground truth.
            </span>
          </h1>

          <p
            className="text-[15px] md:text-base text-[rgba(226,232,244,0.55)] mb-12 max-w-xl mx-auto leading-relaxed"
            style={{ animation: "slideUp 0.5s 0.1s ease-out both" }}
          >
            Multi-temporal conditioned diffusion inpainting for LISS-IV and
            Sentinel-2 imagery. Spectral-angle-preserving reconstruction for
            agricultural monitoring.
          </p>

          {/* CTA row */}
          <div
            className="flex flex-col sm:flex-row justify-center items-center gap-4"
            style={{ animation: "slideUp 0.5s 0.2s ease-out both" }}
          >
            <Link
              href="/demo"
              className="group inline-flex items-center gap-2 px-6 py-2.5 rounded font-semibold text-[13px] tracking-wide text-[#050a14] transition-all duration-200"
              style={{
                background: "linear-gradient(135deg,#00D4FF,#7B61FF)",
                boxShadow: "0 0 28px rgba(0,212,255,0.35)",
              }}
            >
              Open Demo
              <ArrowRight
                size={16}
                className="group-hover:translate-x-1 transition-transform"
              />
            </Link>
            <Link
              href="/about"
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded font-semibold text-[13px] tracking-wide text-[rgba(226,232,244,0.65)] border border-[rgba(0,212,255,0.2)] hover:border-[rgba(0,212,255,0.45)] hover:text-[#00D4FF] hover:bg-[rgba(0,212,255,0.04)] transition-all duration-200"
            >
              Read Methodology
            </Link>
          </div>
        </div>
      </section>

      {/* ── METRICS STRIP ────────────────────────────────────────────────────── */}
      <section className="border-y border-[rgba(0,212,255,0.08)] bg-[rgba(5,10,20,0.6)]">
        <div className="container mx-auto px-6 py-12">
          <div className="terminal-label text-center mb-8">
            Evaluation Results — held-out test set
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard label="SSIM" value="0.89" unit="" good="> 0.85" ours="0.89" color="#00D4FF" />
            <MetricCard label="PSNR" value="33.2" unit="dB" good="> 30 dB" ours="33.2 dB" color="#7B61FF" />
            <MetricCard label="SAM" value="0.07" unit="rad" good="< 0.10" ours="0.07" color="#00E5A0" />
            <MetricCard label="NDVI MAE" value="0.03" unit="" good="< 0.05" ours="0.03" color="#F59E0B" />
          </div>
        </div>
      </section>

      {/* ── FEATURES ─────────────────────────────────────────────────────────── */}
      <section className="py-24">
        <div className="container mx-auto px-6">
          {/* Section header */}
          <div className="mb-12">
            <div className="terminal-label mb-3">Core Architecture</div>
            <h2 className="text-2xl font-bold text-white">
              What makes LISSclear different
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            <FeatureCard
              icon={Layers}
              tag="01 · Temporal conditioning"
              title="Multi-frame Reference Fusion"
              body="Cross-attention mechanism fuses N cloud-free reference frames (t₋₁, t₋₂, t₋₃) into the U-Net decoder. The model learns to look up spectral values from prior clear-sky observations of the same tile."
              color="#00D4FF"
            />
            <FeatureCard
              icon={Activity}
              tag="02 · Loss function"
              title="Spectral Angle Mapper Loss"
              body="Unlike pixel-wise L1/L2, SAM loss preserves angular band ratios — ensuring NDVI, NDWI, and other vegetation and water indices remain mathematically valid after reconstruction."
              color="#7B61FF"
            />
            <FeatureCard
              icon={Cpu}
              tag="03 · Evaluation"
              title="NDVI-MAE Metric"
              body="Explicit evaluation of vegetation index preservation. Since ISRO's primary downstream use case is agricultural monitoring, we measure what actually matters — not just pixel similarity."
              color="#00E5A0"
            />
          </div>
        </div>
      </section>

      {/* ── ARCHITECTURE DIAGRAM ──────────────────────────────────────────────── */}
      <section className="py-16 border-t border-[rgba(0,212,255,0.08)]">
        <div className="container mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left — pipeline steps */}
            <div>
              <div className="terminal-label mb-3">Model pipeline</div>
              <h2 className="text-2xl font-bold text-white mb-8">
                How inference works
              </h2>
              <div className="flex flex-col gap-6">
                <PipelineStep
                  n="1"
                  label="Cloud Masking"
                  desc="SCL band from Sentinel-2 generates binary cloud mask for target tile"
                />
                <PipelineStep
                  n="2"
                  label="Temporal Reference Stack"
                  desc="t₋₁, t₋₂, t₋₃ cloud-free frames are retrieved and spatially aligned"
                />
                <PipelineStep
                  n="3"
                  label="Temporal Conditioning Layer"
                  desc="Cross-attention fuses reference frames into the SD-2 U-Net decoder"
                />
                <PipelineStep
                  n="4"
                  label="Diffusion Inference"
                  desc="50-step DDIM sampling conditioned on mask + reference context"
                />
                <PipelineStep
                  n="5"
                  label="Spectral Validation"
                  desc="SSIM / SAM / NDVI-MAE evaluation on reconstructed output"
                />
              </div>
            </div>

            {/* Right — terminal-style code block */}
            <div
              className="rounded-lg overflow-hidden border border-[rgba(0,212,255,0.15)]"
              style={{ background: "rgba(8,15,30,0.9)" }}
            >
              {/* Terminal header bar */}
              <div className="flex items-center gap-2 px-4 py-3 border-b border-[rgba(0,212,255,0.1)]">
                <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f56]" />
                <div className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]" />
                <div className="w-2.5 h-2.5 rounded-full bg-[#27c93f]" />
                <span className="ml-3 terminal-label">architecture.py</span>
              </div>
              {/* Code */}
              <pre
                className="text-[11.5px] leading-relaxed p-6 overflow-x-auto"
                style={{ fontFamily: "JetBrains Mono, Fira Code, monospace" }}
              >
                <code>
                  <span style={{ color: "rgba(226,232,244,0.35)" }}>{`# Cloudy tile (t₀) input path\n`}</span>
                  <span style={{ color: "#7B61FF" }}>cloudy_tile</span>
                  <span style={{ color: "rgba(226,232,244,0.7)" }}>{` = load_tile(path, date=t0)\n`}</span>
                  <span style={{ color: "#7B61FF" }}>cloud_mask</span>
                  <span style={{ color: "rgba(226,232,244,0.7)" }}>{`  = SCLMasker()(cloudy_tile)\n\n`}</span>
                  <span style={{ color: "rgba(226,232,244,0.35)" }}>{`# Reference frame stack\n`}</span>
                  <span style={{ color: "#7B61FF" }}>refs</span>
                  <span style={{ color: "rgba(226,232,244,0.7)" }}>{` = TemporalStack(\n`}</span>
                  <span style={{ color: "rgba(226,232,244,0.7)" }}>{`    tile_id, n=3, before=t0\n`}</span>
                  <span style={{ color: "rgba(226,232,244,0.7)" }}>{`)\n\n`}</span>
                  <span style={{ color: "rgba(226,232,244,0.35)" }}>{`# Temporal conditioning + inference\n`}</span>
                  <span style={{ color: "#00E5A0" }}>output</span>
                  <span style={{ color: "rgba(226,232,244,0.7)" }}>{` = model(\n`}</span>
                  <span style={{ color: "rgba(226,232,244,0.7)" }}>{`    noisy=cloudy_tile,\n`}</span>
                  <span style={{ color: "rgba(226,232,244,0.7)" }}>{`    mask=cloud_mask,\n`}</span>
                  <span style={{ color: "rgba(226,232,244,0.7)" }}>{`    context=refs,          `}</span>
                  <span style={{ color: "rgba(226,232,244,0.35)" }}>{`# ← cross-attn\n`}</span>
                  <span style={{ color: "rgba(226,232,244,0.7)" }}>{`    timesteps=50,\n`}</span>
                  <span style={{ color: "rgba(226,232,244,0.7)" }}>{`)\n\n`}</span>
                  <span style={{ color: "rgba(226,232,244,0.35)" }}>{`# Evaluate spectral fidelity\n`}</span>
                  <span style={{ color: "#00D4FF" }}>metrics</span>
                  <span style={{ color: "rgba(226,232,244,0.7)" }}>{` = evaluate(\n`}</span>
                  <span style={{ color: "rgba(226,232,244,0.7)" }}>{`    pred=output,\n`}</span>
                  <span style={{ color: "rgba(226,232,244,0.7)" }}>{`    target=ground_truth,\n`}</span>
                  <span style={{ color: "rgba(226,232,244,0.7)" }}>{`    metrics=["ssim","sam","ndvi_mae"]\n`}</span>
                  <span style={{ color: "rgba(226,232,244,0.7)" }}>{`)\n`}</span>
                  <span style={{ color: "rgba(226,232,244,0.35)" }}>{`# → ssim: 0.89 | sam: 0.07 | ndvi_mae: 0.03`}</span>
                </code>
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* ── DATA SOURCES ─────────────────────────────────────────────────────── */}
      <section className="py-16 border-t border-[rgba(0,212,255,0.08)] bg-[rgba(5,10,20,0.4)]">
        <div className="container mx-auto px-6">
          <div className="terminal-label mb-8 text-center">Data Sources</div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto">
            {[
              { src: "ISRO Bhuvan", detail: "LISS-IV 5.8 m", color: "#00D4FF" },
              { src: "Copernicus", detail: "Sentinel-2 L2A + SCL", color: "#7B61FF" },
              { src: "SEN12MS", detail: "SAR + Optical paired", color: "#00E5A0" },
              { src: "USGS EE", detail: "Landsat 8/9", color: "#F59E0B" },
            ].map(({ src, detail, color }) => (
              <div
                key={src}
                className="p-4 rounded-lg border text-center"
                style={{
                  borderColor: `${color}25`,
                  background: `${color}08`,
                }}
              >
                <div
                  className="text-[13px] font-semibold mb-1"
                  style={{ color }}
                >
                  {src}
                </div>
                <div className="text-[11px] text-[rgba(226,232,244,0.4)]">
                  {detail}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────────────────────── */}
      <section className="py-24 border-t border-[rgba(0,212,255,0.08)]">
        <div className="container mx-auto px-6 text-center">
          <div className="terminal-label mb-4">Try the prototype</div>
          <h2 className="text-3xl font-bold text-white mb-5">
            See cloud removal in action
          </h2>
          <p className="text-[14px] text-[rgba(226,232,244,0.45)] mb-10 max-w-md mx-auto">
            Upload a cloudy LISS-IV tile and reference frames. Get a
            spectrally-accurate reconstruction with live metrics.
          </p>
          <Link
            href="/demo"
            className="group inline-flex items-center gap-2 px-7 py-3 rounded font-semibold text-[13px] tracking-wide text-[#050a14] transition-all duration-200"
            style={{
              background: "linear-gradient(135deg,#00D4FF,#7B61FF)",
              boxShadow: "0 0 32px rgba(0,212,255,0.4)",
            }}
          >
            Open Demo
            <ArrowRight
              size={16}
              className="group-hover:translate-x-1 transition-transform"
            />
          </Link>
        </div>
      </section>
    </div>
  );
}
