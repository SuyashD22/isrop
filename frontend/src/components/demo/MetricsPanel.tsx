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

    return (
      <div className="flex flex-col p-4 rounded-xl bg-gray-50/80 border border-gray-100 shadow-sm relative overflow-hidden group">
        {/* Status accent line */}
        <div className={cn(
          "absolute top-0 left-0 w-full h-1",
          isGood ? "bg-green-500" : "bg-amber-400"
        )} />
        
        <div className="flex items-center justify-between mb-2 mt-1">
          <div className="flex items-center space-x-1.5">
            <span className="text-sm font-medium text-gray-600">{info.label}</span>
            <Tooltip content={info.description}>
              <Info size={14} className="text-gray-400 cursor-help hover:text-space-500 transition-colors" />
            </Tooltip>
          </div>
          <div className={cn(
            "text-[10px] font-bold px-1.5 py-0.5 rounded",
            isGood ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"
          )}>
            {isGood ? 'PASS' : 'WARN'}
          </div>
        </div>
        
        <div className="flex items-baseline space-x-1 mt-auto">
          <span className="text-2xl font-bold text-gray-900 tracking-tight">
            {info.format(value).replace(info.unit, '').trim()}
          </span>
          {info.unit && (
            <span className="text-xs font-semibold text-gray-500">{info.unit}</span>
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
