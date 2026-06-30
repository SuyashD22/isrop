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
    <div className="flex flex-col space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-gray-700 flex items-center">
          <Layers size={16} className="mr-2 text-space-500" />
          Temporal Reference Stack
        </h4>
        <span className="text-xs font-medium text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
          {references.length} / {maxFiles}
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {/* Render existing references */}
        {references.map((ref, idx) => (
          <div key={idx} className="relative aspect-square rounded-lg overflow-hidden border border-gray-200 group">
            <img src={ref.preview} alt={`Reference ${idx + 1}`} className="w-full h-full object-cover" />
            <div className="absolute top-1 left-1 bg-black/60 text-white text-[10px] px-1.5 py-0.5 rounded font-mono">
              t-{idx + 1}
            </div>
            <button
              onClick={() => onRemove(idx)}
              className="absolute top-1 right-1 bg-red-500/80 hover:bg-red-600 text-white p-1 rounded-md opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <X size={12} />
            </button>
          </div>
        ))}

        {/* Upload slot (if under maxFiles) */}
        {references.length < maxFiles && (
          <div
            {...getRootProps()}
            className={`aspect-square rounded-lg border-2 border-dashed flex flex-col items-center justify-center p-2 cursor-pointer transition-colors ${
              isDragActive ? 'border-space-500 bg-space-50' : 'border-gray-300 hover:border-space-400 hover:bg-gray-50'
            }`}
          >
            <input {...getInputProps()} />
            <Plus size={20} className={isDragActive ? 'text-space-500' : 'text-gray-400'} />
            <span className="text-[10px] font-medium text-gray-500 mt-1 text-center">Add Clear Tile</span>
          </div>
        )}
        
        {/* Empty slots for visual structure */}
        {Array.from({ length: Math.max(0, maxFiles - references.length - 1) }).map((_, idx) => (
          <div key={`empty-${idx}`} className="aspect-square rounded-lg border-2 border-dashed border-gray-200 bg-gray-50/50 flex items-center justify-center">
             <span className="text-[10px] text-gray-300">Empty</span>
          </div>
        ))}
      </div>
      
      <p className="text-xs text-gray-500 leading-relaxed">
        Adding cloud-free tiles from previous dates over the same location provides the model with persistent spatial structure (roads, buildings, topography).
      </p>
    </div>
  );
}
