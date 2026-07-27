"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ShieldCheck, Loader2 } from "lucide-react";
import { Dropzone } from "@/components/ui/dropzone";
import { useUploadVoice, useTrainVoice } from "@/hooks/use-voices";

export default function NewVoicePage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const upload = useUploadVoice();
  const train = useTrainVoice();

  const isBusy = upload.isPending || train.isPending;
  const error = upload.error ?? train.error;

  const handleSubmit = () => {
    if (!file || !name.trim()) return;
    upload.mutate(
      { name: name.trim(), language: "English", file },
      {
        onSuccess: (voice) => {
          train.mutate(voice.id, {
            onSuccess: () => router.push("/voices"),
          });
        },
      }
    );
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 md:px-8">
      <h1 className="font-display text-2xl text-paper">Add a voice</h1>
      <p className="mt-1 text-sm text-paper-muted">
        Upload a recording and PersonalVoice Reader will build a voice model from it.
      </p>

      <div className="mt-4 flex gap-3 rounded-card border border-ribbon-600/40 bg-ribbon-900/20 p-4">
        <ShieldCheck size={18} className="mt-0.5 shrink-0 text-ribbon-400" />
        <p className="text-xs leading-relaxed text-paper-muted">
          Only upload a voice recording from someone who has explicitly agreed to let you clone
          their voice for your personal use — including your own voice. This tool is for personal
          audiobooks only: it has no sharing, marketplace, or export features, and cloned voices
          never leave your device.
        </p>
      </div>

      <div className="mt-6">
        <label className="mb-2 block text-sm text-paper">Voice name</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Dad's voice"
          className="w-full rounded-lg border border-ink-hairline bg-ink-surface px-3 py-2.5 text-sm text-paper placeholder:text-paper-faint focus:border-lamp-400/50"
        />
      </div>

      <div className="mt-6">
        <label className="mb-2 block text-sm text-paper">Source recording</label>
        <Dropzone
          accept=".wav,.mp3,.flac"
          hint="WAV, MP3, or FLAC · 45–90 minutes recommended · English"
          onFileSelected={setFile}
        />
      </div>

      {error && (
        <p className="mt-4 rounded-lg border border-danger-400/30 bg-danger-400/5 px-3 py-2 text-sm text-danger-400">
          {error instanceof Error ? error.message : "Something went wrong"}
        </p>
      )}

      <button
        disabled={!file || !name.trim() || isBusy}
        onClick={handleSubmit}
        className="mt-8 flex w-full items-center justify-center gap-2 rounded-full bg-lamp-400 py-3 text-sm font-medium text-ink disabled:cursor-not-allowed disabled:opacity-40"
      >
        {isBusy && <Loader2 size={16} className="animate-spin" />}
        {upload.isPending ? "Uploading" : train.isPending ? "Starting training" : "Train voice"}
      </button>
      <p className="mt-2 text-center text-xs text-paper-faint">
        {!file || !name.trim() ? "Add a name and a recording to continue" : "Training runs in the background — you can leave this page"}
      </p>
    </div>
  );
}
