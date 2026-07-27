"use client";

import { Play } from "lucide-react";
import type { Book } from "@/types";
import { formatDuration } from "@/data/mock";
import { usePlaybackStore } from "@/hooks/use-playback-store";

export function ContinueListening({ books }: { books: Book[] }) {
  const load = usePlaybackStore((s) => s.load);

  const inProgress = books.filter((b) => {
    const ch = b.chapters.find((c) => c.id === b.currentChapterId);
    return ch && ch.progressSeconds > 0;
  });

  if (inProgress.length === 0) return null;

  return (
    <section className="mb-10">
      <h2 className="mb-3 font-display text-lg text-paper">Continue listening</h2>
      <div className="flex gap-3 overflow-x-auto scrollbar-thin pb-2">
        {inProgress.map((book) => {
          const chapter = book.chapters.find((c) => c.id === book.currentChapterId)!;
          return (
            <button
              key={book.id}
              onClick={() =>
                load(book.id, chapter.id, chapter.durationSeconds ?? 0, chapter.progressSeconds)
              }
              className="flex w-72 shrink-0 items-center gap-3 rounded-card border border-ink-hairline bg-ink-surface p-3 text-left hover:border-lamp-400/40"
            >
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-lamp-400 text-ink">
                <Play size={16} fill="currentColor" className="ml-0.5" />
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm text-paper">{book.title}</p>
                <p className="truncate text-xs text-paper-muted">
                  {chapter.title} · {formatDuration(chapter.progressSeconds)} of{" "}
                  {formatDuration(chapter.durationSeconds)}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}
