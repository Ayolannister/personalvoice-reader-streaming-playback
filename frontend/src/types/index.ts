export type BookFormat = "epub" | "pdf" | "txt";

export type BookStatus = "ready" | "processing" | "needs_voice";

export interface Chapter {
  id: string;
  index: number;
  title: string;
  durationSeconds: number | null; // null until generated
  audioStatus: "not_generated" | "generating" | "partial" | "cached";
  progressSeconds: number; // resume position within this chapter
  generationSegmentsDone: number;
  generationSegmentsTotal: number | null;
}

export interface Book {
  id: string;
  title: string;
  author: string;
  coverUrl: string | null;
  format: BookFormat;
  status: BookStatus;
  chapters: Chapter[];
  currentChapterId: string | null; // resume pointer
  voiceId: string | null;
  addedAt: string;
}

export type VoiceTrainingStatus = "untrained" | "training" | "ready" | "failed";

export interface Voice {
  id: string;
  name: string;
  language: string;
  sourceMinutes: number;
  status: VoiceTrainingStatus;
  errorMessage?: string | null;
  createdAt: string;
  isDefault: boolean;
}

export interface PlaybackState {
  bookId: string | null;
  chapterId: string | null;
  isPlaying: boolean;
  positionSeconds: number;
  durationSeconds: number;
  speed: number; // 0.75 - 3.0
  sleepTimerMinutes: number | null;
}
