// frontend/src/hooks/useFileUpload.ts
import { useState, useCallback } from 'react';
import { UploadedFile } from '@/lib/types';

export function useFileUpload(maxFiles: number = 1) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [error, setError] = useState<string | null>(null);

  const addFiles = useCallback((acceptedFiles: File[]) => {
    setError(null);
    
    const newFiles = acceptedFiles.map(file => ({
      file,
      preview: URL.createObjectURL(file),
      name: file.name
    }));

    setFiles(prev => {
      const combined = [...prev, ...newFiles];
      if (combined.length > maxFiles) {
        setError(`Maximum ${maxFiles} file(s) allowed. Excess files ignored.`);
        return combined.slice(0, maxFiles);
      }
      return combined;
    });
  }, [maxFiles]);

  const removeFile = useCallback((index: number) => {
    setFiles(prev => {
      const updated = [...prev];
      URL.revokeObjectURL(updated[index].preview);
      updated.splice(index, 1);
      return updated;
    });
    setError(null);
  }, []);

  const clear = useCallback(() => {
    files.forEach(f => URL.revokeObjectURL(f.preview));
    setFiles([]);
    setError(null);
  }, [files]);

  return { files, addFiles, removeFile, clear, error };
}
