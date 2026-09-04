"use client";

import { useEffect, useRef, useState } from "react";
import { AlertCircle, CheckCircle2, Loader2, Upload, X } from "lucide-react";
import {
  getIngestStatus,
  ingestPDF,
  type IngestTaskStatus,
} from "@/lib/api";

interface UploadModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

type ItemStatus = "pending" | "uploading" | IngestTaskStatus;

interface UploadItem {
  file: File;
  status: ItemStatus;
  progress: number;
  error: string | null;
}

const STAGE_LABEL: Record<ItemStatus, string> = {
  pending: "Waiting",
  uploading: "Uploading",
  queued: "Queued",
  parsing: "Parsing PDF",
  embedding: "Generating embeddings",
  done: "Done",
  failed: "Failed",
};

const POLL_INTERVAL_MS = 1000;

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export default function UploadModal({
  open,
  onClose,
  onSuccess,
}: UploadModalProps) {
  const [dragActive, setDragActive] = useState(false);
  const [items, setItems] = useState<UploadItem[]>([]);
  const [running, setRunning] = useState(false);
  const [rejectedCount, setRejectedCount] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const cancelledRef = useRef(false);

  useEffect(() => {
    cancelledRef.current = false;
    return () => {
      cancelledRef.current = true;
    };
  }, []);

  useEffect(() => {
    if (open) closeButtonRef.current?.focus();
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  const updateItem = (idx: number, patch: Partial<UploadItem>) => {
    if (cancelledRef.current) return;
    setItems((prev) =>
      prev.map((item, i) => (i === idx ? { ...item, ...patch } : item))
    );
  };

  const addFiles = (fileList: FileList | File[]) => {
    const incoming = Array.from(fileList);
    const pdfs = incoming.filter(
      (f) => f.type === "application/pdf" || f.name.toLowerCase().endsWith(".pdf")
    );
    setRejectedCount(incoming.length - pdfs.length);
    if (pdfs.length > 0) {
      setItems((prev) => [
        ...prev,
        ...pdfs.map((file) => ({
          file,
          status: "pending" as ItemStatus,
          progress: 0,
          error: null,
        })),
      ]);
    }
  };

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
    addFiles(e.dataTransfer.files);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) addFiles(e.target.files);
    e.target.value = "";
  };

  const removeItem = (idx: number) => {
    setItems((prev) => prev.filter((_, i) => i !== idx));
  };

  const uploadOne = async (idx: number, file: File) => {
    updateItem(idx, { status: "uploading", error: null });
    try {
      const { task_id } = await ingestPDF(file);
      updateItem(idx, { status: "queued" });

      while (true) {
        await sleep(POLL_INTERVAL_MS);
        if (cancelledRef.current) return;

        const record = await getIngestStatus(task_id);
        const progress =
          record.total_chunks > 0
            ? Math.round((record.chunks_indexed / record.total_chunks) * 100)
            : 0;
        updateItem(idx, { status: record.status, progress });

        if (record.status === "done") {
          onSuccess();
          return;
        }
        if (record.status === "failed") {
          updateItem(idx, {
            error: record.error ?? "Ingestion failed. Please try again.",
          });
          return;
        }
      }
    } catch (err) {
      updateItem(idx, {
        status: "failed",
        error: err instanceof Error ? err.message : "Upload failed.",
      });
    }
  };

  const handleUpload = async () => {
    setRunning(true);
    for (let idx = 0; idx < items.length; idx += 1) {
      if (cancelledRef.current) break;
      if (items[idx].status !== "pending") continue;
      await uploadOne(idx, items[idx].file);
    }
    if (!cancelledRef.current) setRunning(false);
  };

  const handleClose = () => {
    setItems([]);
    setRejectedCount(0);
    onClose();
  };

  if (!open) return null;

  const pendingCount = items.filter((i) => i.status === "pending").length;
  const allSettled =
    items.length > 0 &&
    items.every((i) => i.status === "done" || i.status === "failed");

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 z-40 bg-ink/40" onClick={handleClose} />

      {/* Modal */}
      <div
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="upload-modal-title"
      >
        <div className="bg-surface rounded-2xl shadow-[var(--shadow-raised)] w-full max-w-md p-7 animate-scale-in">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 id="upload-modal-title" className="text-lg font-serif font-bold text-ink">
              Add documents
            </h2>
            <button
              ref={closeButtonRef}
              onClick={handleClose}
              aria-label="Close dialog"
              className="p-1 hover:bg-bg-subtle rounded transition-colors focus:outline-none focus:ring-2 focus:ring-amber"
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
              className="text-sm font-medium text-amber hover:text-amber-dark transition-colors focus:outline-none focus:underline"
            >
              Browse files
            </button>
            <input
              ref={inputRef}
              type="file"
              accept=".pdf"
              multiple
              onChange={handleChange}
              className="hidden"
            />
            <p className="text-xs text-ink-subtle mt-3">PDF only</p>
          </div>

          {rejectedCount > 0 && (
            <p className="mt-2 text-xs text-danger">
              {rejectedCount} file{rejectedCount !== 1 ? "s" : ""} skipped
              &mdash; only PDF files are supported.
            </p>
          )}

          {/* File list */}
          {items.length > 0 && (
            <div className="mt-4 space-y-2 max-h-56 overflow-y-auto">
              {items.map((item, idx) => (
                <div
                  key={`${item.file.name}-${idx}`}
                  className="p-2 bg-bg-subtle rounded border border-rim"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm text-ink truncate flex-1">
                      {item.file.name}
                    </span>
                    {item.status === "pending" && !running && (
                      <button
                        onClick={() => removeItem(idx)}
                        aria-label={`Remove ${item.file.name}`}
                        className="p-1 hover:bg-bg rounded transition-colors flex-shrink-0"
                      >
                        <X className="w-4 h-4 text-ink-muted" />
                      </button>
                    )}
                    {item.status === "done" && (
                      <CheckCircle2 className="w-4 h-4 text-success flex-shrink-0" />
                    )}
                    {item.status === "failed" && (
                      <AlertCircle className="w-4 h-4 text-danger flex-shrink-0" />
                    )}
                    {item.status !== "pending" &&
                      item.status !== "done" &&
                      item.status !== "failed" && (
                        <Loader2 className="w-4 h-4 text-amber animate-spin flex-shrink-0" />
                      )}
                  </div>

                  {item.status !== "pending" && (
                    <div className="mt-2">
                      <div className="h-1.5 w-full rounded-full bg-rim overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-300 ${
                            item.status === "failed" ? "bg-danger" : "bg-amber"
                          }`}
                          style={{
                            width: `${
                              item.status === "done"
                                ? 100
                                : item.status === "failed"
                                  ? 100
                                  : Math.max(item.progress, 8)
                            }%`,
                          }}
                        />
                      </div>
                      <p
                        className={`mt-1 text-xs ${
                          item.status === "failed"
                            ? "text-danger"
                            : "text-ink-subtle"
                        }`}
                      >
                        {item.error ?? STAGE_LABEL[item.status]}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 mt-6">
            <button
              onClick={handleClose}
              className="flex-1 px-4 py-2 rounded-lg border border-rim text-ink hover:bg-bg-subtle transition-colors"
            >
              {allSettled ? "Done" : "Cancel"}
            </button>
            {!allSettled && (
              <button
                onClick={handleUpload}
                disabled={pendingCount === 0 || running}
                className="flex-1 px-4 py-2 rounded-lg bg-amber text-white font-medium shadow-[var(--shadow-card)] hover:bg-amber-dark hover:shadow-[var(--shadow-card-hover)] active:scale-[0.98] transition-all disabled:opacity-50 disabled:shadow-none disabled:active:scale-100 flex items-center justify-center gap-2"
              >
                {running && <Loader2 className="w-4 h-4 animate-spin" />}
                {running ? "Uploading…" : "Upload"}
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
