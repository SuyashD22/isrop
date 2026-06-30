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
      <div className="relative w-full h-64 rounded border border-[rgba(0,212,255,0.2)] overflow-hidden group">
        <img 
          src={file.preview} 
          alt={file.name} 
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-[#050a14]/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center backdrop-blur-sm">
          <button
            onClick={(e) => { e.stopPropagation(); onClear(); }}
            className="flex items-center space-x-2 bg-[rgba(0,212,255,0.1)] hover:bg-[rgba(0,212,255,0.2)] text-[#00D4FF] px-4 py-2 rounded border border-[rgba(0,212,255,0.3)] transition-all"
          >
            <X size={18} />
            <span className="font-mono text-[11px] uppercase tracking-wider">Remove & Re-upload</span>
          </button>
        </div>
        <div className="absolute bottom-3 left-3 bg-[rgba(5,10,20,0.85)] border border-[rgba(0,212,255,0.15)] text-[rgba(226,232,244,0.8)] px-3 py-1.5 rounded text-[11px] font-mono flex items-center space-x-2 shadow-glow-cyan backdrop-blur-md">
          <FileImage size={14} className="text-[#00D4FF]" />
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
          "w-full h-64 border border-dashed rounded flex flex-col items-center justify-center p-6 cursor-pointer transition-all duration-200",
          isDragActive 
            ? "border-[#00D4FF] bg-[rgba(0,212,255,0.08)] shadow-[inset_0_0_20px_rgba(0,212,255,0.1)]" 
            : "border-[rgba(0,212,255,0.2)] hover:border-[rgba(0,212,255,0.4)] bg-[rgba(5,10,20,0.6)] hover:bg-[rgba(0,212,255,0.02)]",
          isDragReject ? "border-red-500/50 bg-red-500/10" : "",
          error ? "border-red-500/50" : ""
        )}
      >
        <input {...getInputProps()} />
        <div className={cn("p-4 rounded-full mb-4 transition-colors", isDragActive ? "text-[#00D4FF] bg-[rgba(0,212,255,0.1)]" : "text-[rgba(0,212,255,0.4)] bg-[rgba(0,212,255,0.04)]")}>
          <UploadCloud size={32} />
        </div>
        
        <p className="text-[13px] font-medium text-[rgba(226,232,244,0.8)] text-center mb-1">
          {isDragActive ? "Drop tile here..." : "Drag & drop a cloudy tile"}
        </p>
        <p className="text-[12px] text-[rgba(226,232,244,0.4)] text-center mb-4">
          or click to browse
        </p>
        
        <div className="flex items-center space-x-2 text-[10px] font-mono uppercase tracking-widest text-[rgba(0,212,255,0.5)]">
          <span>PNG, TIFF</span>
          <span>•</span>
          <span>Max {MAX_FILE_SIZE_MB}MB</span>
        </div>
      </div>
      
      {error && (
        <p className="text-[11px] text-[#ff5f56] mt-2 font-mono flex items-center before:content-[''] before:inline-block before:w-1 before:h-1 before:rounded-full before:bg-[#ff5f56] before:mr-2">
          {error}
        </p>
      )}
    </div>
  );
}
