"use client";

import { Play, Loader2, Sparkles } from "lucide-react";
import type { Book, Chapter } from "@/types";
import { formatDuration } from "@/data/mock";
import { usePlaybackStore } from "@/hooks/use-playback-store";
import { useGenerateChapter } from "@/hooks/use-books";
import { cn } from "@/lib/utils";

export function ChapterList({ book }: { book: Book }) {
  return (
    <div>
      <h2 className="mb-3 font-display text-lg text-paper">Chapters</h2>
      <ul className="divide-y divide-ink-hairline overflow-hidden rounded-card border border-ink-hairline">
        {book.chapters.map((chapter) => (
          <ChapterRow key={chapter.id} book={book} chapter={chapter} />
        ))}
      </ul>
    </div>
  );
}

function ChapterRow({ book, chapter }: { book: Book; chapter: Chapter }) {
  const load = usePlaybackStore((s) => s.load);
  const generate = useGenerateChapter(book.id);
  const isCurrent = book.currentChapterId === chapter.id;
  const hasProgress = chapter.progressSeconds > 0;

  return (
    <li
      className={cn(
        "flex items-center gap-3 px-4 py-3 hover:bg-ink-surface/60",
        isCurrent && "bg-ink-surface"
      )}
    >
      <span className="w-6 shrink-0 font-mono text-xs text-paper-faint">
        {String(chapter.index).padStart(2, "0")}
      </span>

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm text-paper">{chapter.title}</p>
        {hasProgress && chapter.durationSeconds && (
          <div className="mt-1.5 h-1 w-40 max-w-full overflow-hidden rounded-full bg-ink-hairline">
            <div
              className="h-full bg-ribbon-400"
              style={{ width: `${Math.min(100, (chapter.progressSeconds / chapter.durationSeconds) * 100)}%` }}
            />
          </div>
        )}
      </div>

      <span className="hidden sm:block font-mono text-xs text-paper-muted">
        {formatDuration(chapter.durationSeconds)}
      </span>

      {(chapter.audioStatus === "cached" || chapter.audioStatus === "partial") && (
        <div className="flex items-center gap-2">
          {chapter.audioStatus === "partial" && (
            <span
              className="flex items-center gap-1 text-[11px] text-lamp-400"
              title="Playable now — more of this chapter is still generating in the background"
            >
              <Loader2 size={11} className="animate-spin" />
              {chapter.generationSegmentsDone}/{chapter.generationSegmentsTotal}
            </span>
          )}
          <button
            onClick={() => load(book.id, chapter.id, chapter.durationSeconds ?? 0, chapter.progressSeconds)}
            aria-label={`Play ${chapter.title}`}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-paper-muted hover:bg-ink-raised hover:text-lamp-400"
          >
            <Play size={16} fill="currentColor" />
          </button>
        </div>
      )}

      {chapter.audioStatus === "generating" && (
        <span className="flex items-center gap-1.5 text-xs text-lamp-400" title="First segment still rendering — playback starts as soon as it's ready">
          <Loader2 size={14} className="animate-spin" />
          {chapter.generationSegmentsTotal
            ? `Generating ${chapter.generationSegmentsDone}/${chapter.generationSegmentsTotal}`
            : "Generating"}
        </span>
      )}

      {chapter.audioStatus === "not_generated" && (
        <button
          onClick={() => generate.mutate(chapter.id)}
          disabled={!book.voiceId || generate.isPending}
          className="flex items-center gap-1.5 rounded-full border border-ink-hairline px-3 py-1.5 text-xs text-paper-muted hover:border-lamp-400/50 hover:text-lamp-400 disabled:cursor-not-allowed disabled:opacity-40"
          title={
            book.voiceId
              ? "Generates audio for this chapter only — nothing is pre-rendered in bulk"
              : "Choose a voice for this book first"
          }
        >
          <Sparkles size={13} />
          Generate
        </button>
      )}
    </li>
  );
}
