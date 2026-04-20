"use client";

import { useState, useRef } from "react";
import { Upload, X } from "lucide-react";
import { ingestPDF } from "@/lib/api";

interface UploadModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: (name: string, taskId: string) => void;
}

export default function UploadModal({
  open,
  onClose,
  onSuccess,
}: UploadModalProps) {
  const [dragActive, setDragActive] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const newFiles = Array.from(e.dataTransfer.files).filter((f) =>
      f.type.includes("pdf")
    );
    if (newFiles.length > 0) {
      setFiles((prev) => [...prev, ...newFiles]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles((prev) => [...prev, ...Array.from(e.target.files!)]);
    }
  };

  const removeFile = (idx: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    setLoading(true);
    setError(null);

    try {
      const file = files[0]; // Upload first file for simplicity
      const response = await ingestPDF(file);
      onSuccess(file.name, response.task_id);
      setFiles([]);
      onClose();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Upload failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 z-40 bg-ink/40" onClick={onClose} />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-surface rounded-2xl shadow-lg w-full max-w-md p-7">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-medium text-ink">Add documents</h2>
            <button
              onClick={onClose}
              className="p-1 hover:bg-bg-subtle rounded transition-colors"
            >
              <X className="w-5 h-5 text-ink-muted" />
            </button>
          </div>

          {/* Drop zone */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
              dragActive
                ? "border-amber bg-amber-soft"
                : "border-rim bg-bg-subtle"
            }`}
          >
            <Upload
              className={`w-8 h-8 mx-auto mb-2 ${
                dragActive ? "text-amber" : "text-ink-muted"
              }`}
            />
            <p className="text-sm font-medium text-ink mb-1">
              Drag and drop files here
            </p>
            <p className="text-xs text-ink-subtle mb-3">or</p>
            <button
              onClick={() => inputRef.current?.click()}
              className="text-sm font-medium text-accent hover:text-accent-dark transition-colors"
            >
              Browse files
            </button>
            <input
              ref={inputRef}
              type="file"
              accept=".pdf"
              onChange={handleChange}
              className="hidden"
            />
            <p className="text-xs text-ink-subtle mt-3">PDF only</p>
          </div>

          {/* File list */}
          {files.length > 0 && (
            <div className="mt-4 space-y-2">
              {files.map((file, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-2 bg-bg-subtle rounded border border-rim"
                >
                  <span className="text-sm text-ink truncate">{file.name}</span>
                  <button
                    onClick={() => removeFile(idx)}
                    className="p-1 hover:bg-bg rounded transition-colors"
                  >
                    <X className="w-4 h-4 text-ink-muted" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="mt-4 p-3 bg-danger-soft text-danger text-sm rounded">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 mt-6">
            <button
              onClick={onClose}
              disabled={loading}
              className="flex-1 px-4 py-2 rounded-lg border border-rim text-ink hover:bg-bg-subtle transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleUpload}
              disabled={files.length === 0 || loading}
              className="flex-1 px-4 py-2 rounded-lg bg-amber text-white font-medium hover:bg-amber-dark transition-colors disabled:opacity-50"
            >
              {loading ? "Uploading..." : "Upload"}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
