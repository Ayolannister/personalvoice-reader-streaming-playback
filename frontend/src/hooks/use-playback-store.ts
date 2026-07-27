import { create } from "zustand";
import type { PlaybackState } from "@/types";

interface PlaybackStore extends PlaybackState {
  seekRequest: { seconds: number; nonce: number } | null;
  load: (bookId: string, chapterId: string, durationSeconds: number, startAt?: number) => void;
  togglePlay: () => void;
  setPlaying: (isPlaying: boolean) => void;
  reportProgress: (positionSeconds: number, durationSeconds?: number) => void;
  seek: (seconds: number) => void;
  setSpeed: (speed: number) => void;
  setSleepTimer: (minutes: number | null) => void;
  stop: () => void;
}

// bookId/chapterId/speed/sleepTimer are the "what should be playing"
// intent; positionSeconds/durationSeconds are updated FROM the real
// <audio> element (owned by MiniPlayer) via reportProgress, not the
// other way around. seek() is a request the audio element fulfills —
// the nonce lets the same seconds value seek twice in a row.
export const usePlaybackStore = create<PlaybackStore>((set) => ({
  bookId: null,
  chapterId: null,
  isPlaying: false,
  positionSeconds: 0,
  durationSeconds: 0,
  speed: 1.0,
  sleepTimerMinutes: null,
  seekRequest: null,
  load: (bookId, chapterId, durationSeconds, startAt = 0) =>
    set({
      bookId,
      chapterId,
      durationSeconds,
      positionSeconds: startAt,
      isPlaying: true,
      seekRequest: { seconds: startAt, nonce: Date.now() },
    }),
  togglePlay: () => set((s) => ({ isPlaying: !s.isPlaying })),
  setPlaying: (isPlaying) => set({ isPlaying }),
  reportProgress: (positionSeconds, durationSeconds) =>
    set((s) => ({ positionSeconds, durationSeconds: durationSeconds ?? s.durationSeconds })),
  seek: (seconds) => set({ seekRequest: { seconds, nonce: Date.now() } }),
  setSpeed: (speed) => set({ speed }),
  setSleepTimer: (minutes) => set({ sleepTimerMinutes: minutes }),
  stop: () => set({ bookId: null, chapterId: null, isPlaying: false, positionSeconds: 0 }),
}));
