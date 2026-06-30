import { Layers, Plus, X } from 'lucide-react';
import { UploadedFile } from '@/lib/types';
import { useDropzone } from 'react-dropzone';
import { ACCEPTED_FILE_TYPES, MAX_FILE_SIZE_BYTES } from '@/lib/constants';

interface Props {
  references: UploadedFile[];
  onAdd: (files: File[]) => void;
  onRemove: (index: number) => void;
  maxFiles?: number;
}

export function ReferenceStack({ references, onAdd, onRemove, maxFiles = 3 }: Props) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: onAdd,
    accept: ACCEPTED_FILE_TYPES,
    maxSize: MAX_FILE_SIZE_BYTES,
    multiple: true,
  });

  return (
    <div className="flex flex-col space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-[13px] font-semibold text-white flex items-center">
          <Layers size={16} className="mr-2 text-[#00D4FF]" />
          Temporal Reference Stack
        </h4>
        <span className="text-[10px] font-mono text-[rgba(226,232,244,0.6)] bg-[rgba(0,212,255,0.1)] border border-[rgba(0,212,255,0.2)] px-2 py-0.5 rounded">
          {references.length} / {maxFiles}
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {/* Render existing references */}
        {references.map((ref, idx) => (
          <div key={idx} className="relative aspect-square rounded overflow-hidden border border-[rgba(0,212,255,0.2)] group">
            <img src={ref.preview} alt={`Reference ${idx + 1}`} className="w-full h-full object-cover" />
            <div className="absolute top-1 left-1 bg-[rgba(5,10,20,0.85)] border border-[rgba(0,212,255,0.15)] text-[#00D4FF] text-[10px] px-1.5 py-0.5 rounded font-mono backdrop-blur-md">
              t-{idx + 1}
            </div>
            <button
              onClick={() => onRemove(idx)}
              className="absolute top-1 right-1 bg-[#ff5f56]/90 hover:bg-[#ff5f56] text-white p-1 rounded opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <X size={12} />
            </button>
          </div>
        ))}

        {/* Upload slot (if under maxFiles) */}
        {references.length < maxFiles && (
          <div
            {...getRootProps()}
            className={`aspect-square rounded border border-dashed flex flex-col items-center justify-center p-2 cursor-pointer transition-colors ${
              isDragActive 
                ? 'border-[#00D4FF] bg-[rgba(0,212,255,0.08)]' 
                : 'border-[rgba(0,212,255,0.2)] hover:border-[rgba(0,212,255,0.4)] bg-[rgba(5,10,20,0.6)] hover:bg-[rgba(0,212,255,0.04)]'
            }`}
          >
            <input {...getInputProps()} />
            <Plus size={20} className={isDragActive ? 'text-[#00D4FF]' : 'text-[rgba(0,212,255,0.4)]'} />
            <span className="text-[10px] font-mono text-[rgba(226,232,244,0.4)] mt-1 text-center uppercase tracking-wider">
              Add Frame
            </span>
          </div>
        )}
        
        {/* Empty slots for visual structure */}
        {Array.from({ length: Math.max(0, maxFiles - references.length - 1) }).map((_, idx) => (
          <div key={`empty-${idx}`} className="aspect-square rounded border border-dashed border-[rgba(0,212,255,0.1)] bg-[rgba(5,10,20,0.4)] flex items-center justify-center">
             <span className="text-[10px] font-mono text-[rgba(226,232,244,0.2)] uppercase tracking-wider">Empty</span>
          </div>
        ))}
      </div>
      
      <p className="text-[12px] text-[rgba(226,232,244,0.45)] leading-relaxed">
        Adding cloud-free tiles from previous dates provides the model with persistent spatial structure (roads, topography).
      </p>
    </div>
  );
}
