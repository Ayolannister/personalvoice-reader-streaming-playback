"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Dropzone } from "@/components/ui/dropzone";
import { useUploadBook } from "@/hooks/use-books";

export default function UploadBookPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const { mutate, isPending, error } = useUploadBook();

  const handleSubmit = () => {
    if (!file) return;
    mutate(file, {
      onSuccess: (book) => router.push(`/books/${book.id}`),
    });
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 md:px-8">
      <h1 className="font-display text-2xl text-paper">Add a book</h1>
      <p className="mt-1 text-sm text-paper-muted">
        Upload an EPUB, PDF, or TXT file you have the legal right to read.
      </p>

      <div className="mt-6">
        <Dropzone accept=".epub,.pdf,.txt" hint="EPUB, PDF, or TXT" onFileSelected={setFile} />
      </div>

      {error && (
        <p className="mt-4 rounded-lg border border-danger-400/30 bg-danger-400/5 px-3 py-2 text-sm text-danger-400">
          {error instanceof Error ? error.message : "Something went wrong"}
        </p>
      )}

      <button
        disabled={!file || isPending}
        onClick={handleSubmit}
        className="mt-8 flex w-full items-center justify-center gap-2 rounded-full bg-lamp-400 py-3 text-sm font-medium text-ink disabled:cursor-not-allowed disabled:opacity-40"
      >
        {isPending && <Loader2 size={16} className="animate-spin" />}
        {isPending ? "Parsing your book" : "Add to library"}
      </button>
      <p className="mt-2 text-center text-xs text-paper-faint">
        Cover, author, and chapters are detected automatically once the book is parsed
      </p>
    </div>
  );
}
