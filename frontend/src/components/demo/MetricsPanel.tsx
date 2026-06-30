import { Info } from 'lucide-react';
import { MetricsResult, METRIC_INFO, MetricKey } from '@/lib/types';
import { Tooltip } from '../ui/Tooltip';
import { cn } from '../ui/Button';

interface Props {
  metrics: MetricsResult;
}

export function MetricsPanel({ metrics }: Props) {
  
  const MetricCard = ({ metricKey, value }: { metricKey: MetricKey, value: number }) => {
    const info = METRIC_INFO[metricKey];
    
    // Check if metric meets benchmark threshold
    const isGood = info.higherIsBetter 
      ? value >= info.threshold 
      : value <= info.threshold;

    // Set colors based on the specific metric to match the landing page theme
    let color = "#00D4FF"; // default cyan
    if (metricKey === "psnr") color = "#7B61FF"; // purple
    if (metricKey === "sam") color = "#00E5A0"; // green
    if (metricKey === "ndvi_mae") color = "#F59E0B"; // amber

    return (
      <div 
        className="flex flex-col p-4 rounded bg-[rgba(8,15,30,0.85)] border transition-all duration-300 relative overflow-hidden group"
        style={{ borderColor: "rgba(0,212,255,0.12)" }}
      >
        {/* Glow effect on hover */}
        <div
          className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
          style={{
            background: `radial-gradient(ellipse at 50% 0%, ${color}15 0%, transparent 70%)`,
          }}
        />
        
        <div className="flex items-center justify-between mb-3 relative z-10">
          <div className="flex items-center space-x-1.5">
            <span className="terminal-label" style={{ color: `${color}99` }}>
              {info.label}
            </span>
            <Tooltip content={info.description}>
              <Info size={12} style={{ color: `${color}60` }} className="cursor-help hover:opacity-100 transition-opacity" />
            </Tooltip>
          </div>
          <div className={cn(
            "text-[10px] font-mono font-bold px-1.5 py-0.5 rounded uppercase tracking-wider",
            isGood 
              ? "bg-[rgba(0,229,160,0.1)] text-[#00E5A0] border border-[rgba(0,229,160,0.2)]" 
              : "bg-[rgba(245,158,11,0.1)] text-[#F59E0B] border border-[rgba(245,158,11,0.2)]"
          )}>
            {isGood ? 'PASS ✓' : 'WARN !'}
          </div>
        </div>
        
        <div className="flex items-baseline space-x-1 mt-auto relative z-10">
          <span 
            className="text-2xl font-bold font-mono tracking-tight"
            style={{ color }}
          >
            {info.format(value).replace(info.unit, '').trim()}
          </span>
          {info.unit && (
            <span className="text-[11px] font-mono text-[rgba(226,232,244,0.4)] ml-1">{info.unit}</span>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <MetricCard metricKey="ssim" value={metrics.ssim} />
      <MetricCard metricKey="psnr" value={metrics.psnr} />
      <MetricCard metricKey="sam" value={metrics.sam} />
      {metrics.ndvi_mae !== null && (
        <MetricCard metricKey="ndvi_mae" value={metrics.ndvi_mae} />
      )}
    </div>
  );
}
