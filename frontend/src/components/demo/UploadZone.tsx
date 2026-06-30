import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, FileImage, X } from 'lucide-react';
import { ACCEPTED_FILE_TYPES, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB } from '@/lib/constants';
import { UploadedFile } from '@/lib/types';
import { cn } from '../ui/Button';

interface Props {
  onDrop: (files: File[]) => void;
  file: UploadedFile | null;
  onClear: () => void;
  error?: string | null;
}

export function UploadZone({ onDrop, file, onClear, error }: Props) {
  const handleDrop = useCallback((acceptedFiles: File[]) => {
    onDrop(acceptedFiles);
  }, [onDrop]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop: handleDrop,
    accept: ACCEPTED_FILE_TYPES,
    maxSize: MAX_FILE_SIZE_BYTES,
    multiple: false,
  });

  if (file) {
    return (
      <div className="relative w-full h-64 rounded-xl overflow-hidden border border-gray-200 group">
        <img 
          src={file.preview} 
          alt={file.name} 
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
          <button
            onClick={(e) => { e.stopPropagation(); onClear(); }}
            className="flex items-center space-x-2 bg-white/10 hover:bg-white/20 backdrop-blur-md text-white px-4 py-2 rounded-lg border border-white/30 transition-all"
          >
            <X size={18} />
            <span className="font-medium text-sm">Remove & Re-upload</span>
          </button>
        </div>
        <div className="absolute bottom-3 left-3 bg-black/60 backdrop-blur-sm text-white px-3 py-1.5 rounded-md text-xs font-mono flex items-center space-x-2">
          <FileImage size={14} />
          <span className="truncate max-w-[200px]">{file.name}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={cn(
          "w-full h-64 border-2 border-dashed rounded-xl flex flex-col items-center justify-center p-6 cursor-pointer transition-all duration-200",
          isDragActive ? "border-space-500 bg-space-50" : "border-gray-300 hover:border-space-400 hover:bg-gray-50",
          isDragReject ? "border-red-500 bg-red-50" : "",
          error ? "border-red-400" : ""
        )}
      >
        <input {...getInputProps()} />
        <div className={cn("p-4 rounded-full mb-4", isDragActive ? "bg-space-100 text-space-600" : "bg-gray-100 text-gray-500")}>
          <UploadCloud size={32} />
        </div>
        
        <p className="text-sm font-medium text-gray-700 text-center mb-1">
          {isDragActive ? "Drop tile here..." : "Drag & drop a cloudy tile"}
        </p>
        <p className="text-xs text-gray-500 text-center mb-4">
          or click to browse
        </p>
        
        <div className="flex items-center space-x-2 text-[11px] font-medium text-gray-400">
          <span>PNG, TIFF</span>
          <span>•</span>
          <span>Max {MAX_FILE_SIZE_MB}MB</span>
        </div>
      </div>
      
      {error && (
        <p className="text-xs text-red-500 mt-2 font-medium flex items-center before:content-[''] before:inline-block before:w-1 before:h-1 before:rounded-full before:bg-red-500 before:mr-2">
          {error}
        </p>
      )}
    </div>
  );
}
