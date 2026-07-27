"use client";

import { UploadCloud } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

export function Dropzone({
  accept,
  hint,
  onFileSelected,
}: {
  accept: string;
  hint: string;
  onFileSelected?: (file: File) => void;
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  return (
    <label
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        const file = e.dataTransfer.files?.[0];
        if (file) {
          setFileName(file.name);
          onFileSelected?.(file);
        }
      }}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-card border-2 border-dashed px-6 py-10 text-center transition-colors",
        isDragging ? "border-lamp-400 bg-lamp-400/5" : "border-ink-hairline hover:border-ink-hairline/70"
      )}
    >
      <input
        type="file"
        accept={accept}
        className="sr-only"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) {
            setFileName(file.name);
            onFileSelected?.(file);
          }
        }}
      />
      <UploadCloud size={22} className="text-paper-faint" />
      {fileName ? (
        <p className="text-sm text-paper">{fileName}</p>
      ) : (
        <p className="text-sm text-paper-muted">Drag a file here, or click to browse</p>
      )}
      <p className="text-xs text-paper-faint">{hint}</p>
    </label>
  );
}
