"use client";

import Image from "next/image";
import { useState } from "react";
import type { Book } from "@/types";
import { Play, Mic2 } from "lucide-react";
import { usePlaybackStore } from "@/hooks/use-playback-store";
import { useAssignVoice } from "@/hooks/use-books";
import { useVoices } from "@/hooks/use-voices";

function initials(title: string) {
  return title
    .split(" ")
    .filter((w) => w.length > 2 || w === w.toUpperCase())
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join("");
}

export function BookHero({ book }: { book: Book }) {
  const load = usePlaybackStore((s) => s.load);
  const { data: voices } = useVoices();
  const assignVoice = useAssignVoice(book.id);
  const [pendingVoiceId, setPendingVoiceId] = useState("");

  const currentChapter = book.chapters.find((c) => c.id === book.currentChapterId) ?? book.chapters[0];
  const canPlay = currentChapter?.audioStatus === "cached" || currentChapter?.audioStatus === "partial";
  const readyVoices = voices?.filter((v) => v.status === "ready") ?? [];
  const assignedVoice = voices?.find((v) => v.id === book.voiceId);

  return (
    <div className="mb-8 flex flex-col gap-6 sm:flex-row sm:items-end">
      <div className="relative aspect-[2/3] w-36 shrink-0 overflow-hidden rounded-card bg-gradient-to-br from-ink-raised to-ink-surface ring-1 ring-ink-hairline">
        {book.coverUrl ? (
          <Image src={book.coverUrl} alt="" fill sizes="144px" className="object-cover" />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="font-display text-3xl italic text-paper-faint">{initials(book.title)}</span>
          </div>
        )}
      </div>

      <div className="min-w-0 flex-1">
        <p className="text-xs uppercase tracking-wide text-paper-faint">{book.format}</p>
        <h1 className="mt-1 font-display text-2xl text-paper">{book.title}</h1>
        <p className="mt-1 text-sm text-paper-muted">{book.author}</p>
        <p className="mt-1 text-xs text-paper-faint">{book.chapters.length} chapters</p>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          {currentChapter && (
            <button
              onClick={() =>
                canPlay &&
                load(
                  book.id,
                  currentChapter.id,
                  currentChapter.durationSeconds ?? 0,
                  currentChapter.progressSeconds
                )
              }
              disabled={!canPlay}
              className="flex items-center gap-2 rounded-full bg-lamp-400 px-5 py-2.5 text-sm font-medium text-ink hover:bg-lamp-200 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Play size={16} fill="currentColor" />
              {currentChapter.progressSeconds > 0
                ? `Resume ${currentChapter.title}`
                : `Start ${currentChapter.title}`}
            </button>
          )}

          {!book.voiceId && readyVoices.length > 0 && (
            <div className="flex items-center gap-2">
              <select
                value={pendingVoiceId}
                onChange={(e) => setPendingVoiceId(e.target.value)}
                className="rounded-full border border-ink-hairline bg-ink-surface px-3 py-2 text-xs text-paper"
              >
                <option value="">Choose a voice…</option>
                {readyVoices.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name}
                  </option>
                ))}
              </select>
              <button
                onClick={() => pendingVoiceId && assignVoice.mutate(pendingVoiceId)}
                disabled={!pendingVoiceId || assignVoice.isPending}
                className="flex items-center gap-1.5 rounded-full border border-lamp-400/50 px-3 py-2 text-xs text-lamp-400 hover:bg-lamp-400/10 disabled:opacity-40"
              >
                <Mic2 size={13} />
                Set voice
              </button>
            </div>
          )}

          {!book.voiceId && readyVoices.length === 0 && (
            <p className="text-xs text-paper-faint">Train a voice first to generate audio for this book</p>
          )}

          {assignedVoice && (
            <span className="flex items-center gap-1.5 text-xs text-paper-muted">
              <Mic2 size={13} />
              Reading in {assignedVoice.name}
            </span>
          )}
        </div>

        {!canPlay && currentChapter && book.voiceId && (
          <p className="mt-2 text-xs text-paper-faint">Generate this chapter's audio below to start listening</p>
        )}
      </div>
    </div>
  );
}
