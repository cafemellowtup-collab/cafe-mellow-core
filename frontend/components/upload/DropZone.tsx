'use client';

import { useState, useCallback } from 'react';
import { Upload, FileSpreadsheet, CheckCircle2, AlertCircle, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { uploadFile, UploadResponse } from '@/lib/api';
import { toast } from 'sonner';

interface QueuedFile {
  name: string;
  file_id?: string;
  status: 'uploading' | 'queued' | 'error';
  error?: string;
}

export function DropZone() {
  const [isDragging, setIsDragging] = useState(false);
  const [queuedFiles, setQueuedFiles] = useState<QueuedFile[]>([]);
  const [uploadComplete, setUploadComplete] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const validateFile = (file: File): boolean => {
    const validExtensions = ['.csv', '.xls', '.xlsx'];
    return validExtensions.some((ext) => file.name.toLowerCase().endsWith(ext));
  };

  const processFiles = async (files: File[]) => {
    const validFiles = files.filter(validateFile);
    const invalidCount = files.length - validFiles.length;

    if (invalidCount > 0) {
      toast.error(`${invalidCount} file(s) skipped`, {
        description: 'Only CSV and Excel files are supported',
      });
    }

    if (validFiles.length === 0) return;

    setUploadComplete(false);
    
    // Initialize all files as uploading
    const initialQueue: QueuedFile[] = validFiles.map((f) => ({
      name: f.name,
      status: 'uploading',
    }));
    setQueuedFiles(initialQueue);

    // Upload all files in parallel
    const uploadPromises = validFiles.map(async (file, index) => {
      try {
        const response: UploadResponse = await uploadFile(file);
        setQueuedFiles((prev) =>
          prev.map((f, i) =>
            i === index ? { ...f, status: 'queued', file_id: response.file_id } : f
          )
        );
        return { success: true, filename: file.name };
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Upload failed';
        setQueuedFiles((prev) =>
          prev.map((f, i) =>
            i === index ? { ...f, status: 'error', error: errorMsg } : f
          )
        );
        return { success: false, filename: file.name };
      }
    });

    const results = await Promise.all(uploadPromises);
    const successCount = results.filter((r) => r.success).length;

    setUploadComplete(true);

    if (successCount > 0) {
      toast.success(`${successCount} file(s) uploaded`, {
        description: 'Analysis running in background. Check Data tab for status.',
      });
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      processFiles(files);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      processFiles(Array.from(files));
    }
  };

  const resetUpload = () => {
    setQueuedFiles([]);
    setUploadComplete(false);
  };

  const isIdle = queuedFiles.length === 0;
  const hasErrors = queuedFiles.some((f) => f.status === 'error');

  return (
    <div className="w-full">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => {
          if (isIdle) {
            document.getElementById('file-input')?.click();
          }
        }}
        className={cn(
          'relative rounded-xl border-2 border-dashed transition-all duration-200',
          'flex flex-col items-center justify-center p-8',
          isIdle && 'cursor-pointer',
          isDragging
            ? 'border-slate-900 bg-slate-50'
            : uploadComplete && !hasErrors
            ? 'border-green-300 bg-green-50'
            : hasErrors
            ? 'border-amber-300 bg-amber-50'
            : 'border-slate-200 bg-slate-50/50 hover:border-slate-300 hover:bg-slate-50'
        )}
      >
        <input
          id="file-input"
          type="file"
          accept=".csv,.xls,.xlsx"
          multiple
          onChange={handleFileSelect}
          className="hidden"
        />

        {isIdle && (
          <>
            <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
              <Upload className="w-8 h-8 text-slate-400" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-1">
              Drag financial documents here
            </h3>
            <p className="text-sm text-slate-500 mb-4">
              Drop multiple files at once • CSV, Excel supported
            </p>
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="text-xs">CSV</Badge>
              <Badge variant="secondary" className="text-xs">Excel</Badge>
              <Badge variant="secondary" className="text-xs">Multi-file</Badge>
            </div>
          </>
        )}

        {!isIdle && (
          <div className="w-full">
            <div className="flex items-center gap-3 mb-4">
              {uploadComplete ? (
                <CheckCircle2 className="w-6 h-6 text-green-600" />
              ) : (
                <div className="w-6 h-6 rounded-full border-2 border-slate-300 border-t-slate-600 animate-spin" />
              )}
              <div>
                <h3 className="font-semibold text-slate-900">
                  {uploadComplete ? 'Upload Complete' : 'Uploading files...'}
                </h3>
                <p className="text-sm text-slate-500">
                  {uploadComplete
                    ? 'Analysis running in background'
                    : `${queuedFiles.filter((f) => f.status === 'uploading').length} remaining`}
                </p>
              </div>
            </div>

            <div className="space-y-2 max-h-48 overflow-y-auto">
              {queuedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-white rounded-lg border border-slate-100"
                >
                  <div className="flex items-center gap-3">
                    <FileSpreadsheet className="w-5 h-5 text-slate-400" />
                    <span className="text-sm font-medium text-slate-700 truncate max-w-[200px]">
                      {file.name}
                    </span>
                  </div>
                  {file.status === 'uploading' && (
                    <Badge variant="secondary" className="bg-slate-100">
                      <Clock className="w-3 h-3 mr-1" />
                      Uploading
                    </Badge>
                  )}
                  {file.status === 'queued' && (
                    <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100">
                      Queued
                    </Badge>
                  )}
                  {file.status === 'error' && (
                    <Badge variant="destructive">
                      <AlertCircle className="w-3 h-3 mr-1" />
                      Failed
                    </Badge>
                  )}
                </div>
              ))}
            </div>

            {uploadComplete && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  resetUpload();
                }}
                className="mt-4 text-sm text-slate-600 hover:text-slate-900 underline"
              >
                Upload more files
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
