"use client";

import Link from "next/link";
import { Plus, Loader2 } from "lucide-react";
import { useVoices } from "@/hooks/use-voices";
import { VoiceCard } from "@/components/voice/voice-card";

export default function VoicesPage() {
  const { data: voices, isLoading, isError, error } = useVoices();

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 md:px-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl text-paper">Voices</h1>
          <p className="mt-1 text-sm text-paper-muted">
            Clone a voice from someone who's given you permission, then use it to read your books.
          </p>
        </div>
        <Link
          href="/voices/new"
          className="flex shrink-0 items-center gap-1.5 rounded-full bg-lamp-400 px-4 py-2 text-sm font-medium text-ink hover:bg-lamp-200"
        >
          <Plus size={16} />
          Add voice
        </Link>
      </div>

      {isLoading && (
        <div className="flex items-center gap-2 py-16 justify-center text-paper-muted text-sm">
          <Loader2 size={16} className="animate-spin" />
          Loading your voices
        </div>
      )}

      {isError && (
        <div className="rounded-card border border-danger-400/30 bg-danger-400/5 px-4 py-8 text-center text-sm text-danger-400">
          {error instanceof Error ? error.message : "Couldn't reach the backend"}
        </div>
      )}

      {voices && voices.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-card border border-dashed border-ink-hairline py-16 text-center">
          <p className="font-display text-lg text-paper">No voices yet</p>
          <p className="mt-1 max-w-sm text-sm text-paper-muted">
            Add a recording from someone who's agreed to let you clone their voice.
          </p>
        </div>
      )}

      {voices && voices.length > 0 && (
        <div className="flex flex-col gap-3">
          {voices.map((voice) => (
            <VoiceCard key={voice.id} voice={voice} />
          ))}
        </div>
      )}
    </div>
  );
}
