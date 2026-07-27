import type { Book, Voice } from "@/types";

// Milestone 1 (UI shell) renders against this fixture data so every
// screen is visually complete before real upload / parsing / TTS
// endpoints exist. Swapped for React Query hooks in Milestone 2.

export const mockVoices: Voice[] = [
  {
    id: "v1",
    name: "Dad's voice",
    language: "English",
    sourceMinutes: 62,
    status: "ready",
    createdAt: "2026-06-02T10:00:00Z",
    isDefault: true,
  },
  {
    id: "v2",
    name: "Narrator (test take)",
    language: "English",
    sourceMinutes: 48,
    status: "training",
    createdAt: "2026-07-10T09:30:00Z",
    isDefault: false,
  },
];

export const mockBooks: Book[] = [
  {
    id: "b1",
    title: "Meditations",
    author: "Marcus Aurelius",
    coverUrl: null,
    format: "epub",
    status: "ready",
    currentChapterId: "b1c7",
    voiceId: null,
    addedAt: "2026-06-03T08:00:00Z",
    chapters: Array.from({ length: 12 }, (_, i) => ({
      id: `b1c${i + 1}`,
      index: i + 1,
      title: `Book ${i + 1}`,
      durationSeconds: i < 7 ? 1400 + i * 60 : null,
      audioStatus: i < 7 ? "cached" : "not_generated",
      progressSeconds: i === 6 ? 1892 : 0,
      generationSegmentsDone: 0,
      generationSegmentsTotal: null,
    })),
  },
  {
    id: "b2",
    title: "The Pragmatic Programmer",
    author: "David Thomas, Andrew Hunt",
    coverUrl: null,
    format: "pdf",
    status: "ready",
    currentChapterId: "b2c1",
    voiceId: null,
    addedAt: "2026-06-20T14:00:00Z",
    chapters: Array.from({ length: 9 }, (_, i) => ({
      id: `b2c${i + 1}`,
      index: i + 1,
      title: `Chapter ${i + 1}`,
      durationSeconds: i === 0 ? 2130 : null,
      audioStatus: i === 0 ? "cached" : "not_generated",
      progressSeconds: i === 0 ? 340 : 0,
      generationSegmentsDone: 0,
      generationSegmentsTotal: null,
    })),
  },
  {
    id: "b3",
    title: "Notes from a Nigerian Founder",
    author: "Unknown",
    coverUrl: null,
    format: "txt",
    status: "needs_voice",
    currentChapterId: null,
    voiceId: null,
    addedAt: "2026-07-12T11:00:00Z",
    chapters: Array.from({ length: 5 }, (_, i) => ({
      id: `b3c${i + 1}`,
      index: i + 1,
      title: `Section ${i + 1}`,
      durationSeconds: null,
      audioStatus: "not_generated",
      progressSeconds: 0,
      generationSegmentsDone: 0,
      generationSegmentsTotal: null,
    })),
  },
];

export function formatDuration(seconds: number | null): string {
  if (seconds === null) return "--:--";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) {
    return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  }
  return `${m}:${String(s).padStart(2, "0")}`;
}
