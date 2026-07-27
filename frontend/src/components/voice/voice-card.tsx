"use client";

import { Loader2, CircleCheck, CircleAlert, Mic, RotateCw } from "lucide-react";
import type { Voice } from "@/types";
import { cn } from "@/lib/utils";
import { useTrainVoice } from "@/hooks/use-voices";

const statusConfig: Record<Voice["status"], { label: string; icon: typeof Mic; className: string }> = {
  ready: { label: "Ready to use", icon: CircleCheck, className: "text-ribbon-400" },
  training: { label: "Training", icon: Loader2, className: "text-lamp-400" },
  untrained: { label: "Not trained yet", icon: Mic, className: "text-paper-faint" },
  failed: { label: "Training failed", icon: CircleAlert, className: "text-danger-400" },
};

export function VoiceCard({ voice }: { voice: Voice }) {
  const status = statusConfig[voice.status];
  const StatusIcon = status.icon;
  const retrain = useTrainVoice();

  return (
    <div className="rounded-card border border-ink-hairline bg-ink-surface p-4">
      <div className="flex items-center gap-4">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-ink-raised">
          <Mic size={18} className="text-paper-muted" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="truncate text-sm text-paper">{voice.name}</p>
            {voice.isDefault && (
              <span className="rounded-full border border-ink-hairline px-2 py-0.5 text-[10px] text-paper-muted">
                Default
              </span>
            )}
          </div>
          <p className="mt-0.5 text-xs text-paper-muted">
            {voice.language} · {voice.sourceMinutes} min of source audio
          </p>
        </div>

        <div className={cn("flex items-center gap-1.5 text-xs shrink-0", status.className)}>
          <StatusIcon size={14} className={voice.status === "training" ? "animate-spin" : ""} />
          {status.label}
        </div>

        {voice.status === "failed" && (
          <button
            onClick={() => retrain.mutate(voice.id)}
            disabled={retrain.isPending}
            aria-label="Retry training"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-paper-muted hover:bg-ink-raised hover:text-lamp-400 disabled:opacity-40"
          >
            <RotateCw size={14} className={retrain.isPending ? "animate-spin" : ""} />
          </button>
        )}
      </div>

      {voice.status === "failed" && voice.errorMessage && (
        <p className="mt-3 rounded-lg bg-danger-400/5 px-3 py-2 text-xs text-danger-400">
          {voice.errorMessage}
        </p>
      )}
    </div>
  );
}
