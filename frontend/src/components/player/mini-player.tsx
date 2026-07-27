"use client";

import { useEffect, useRef, useState } from "react";
import { Play, Pause, RotateCcw, RotateCw, Moon, Loader2 } from "lucide-react";
import { usePlaybackStore } from "@/hooks/use-playback-store";
import { useBook, useUpdateProgress } from "@/hooks/use-books";
import { formatDuration } from "@/data/mock";
import { chapterAudioUrl } from "@/lib/api";
import { cn } from "@/lib/utils";

const SLEEP_PRESETS = [null, 15, 30, 45] as const;
const PROGRESS_SAVE_INTERVAL_MS = 5000;
// How close to the end of the currently-loaded audio counts as "caught
// up" — close enough that we should reload for more as soon as it's
// available, rather than waiting for the person to hit a hard stop.
const CAUGHT_UP_THRESHOLD_SECONDS = 3;

export function MiniPlayer() {
  const {
    bookId,
    chapterId,
    isPlaying,
    positionSeconds,
    durationSeconds,
    speed,
    sleepTimerMinutes,
    togglePlay,
    setPlaying,
    reportProgress,
    seek,
    seekRequest,
    setSleepTimer,
  } = usePlaybackStore();

  const { data: book } = useBook(bookId ?? "");
  const updateProgress = useUpdateProgress(bookId ?? "");

  const audioRef = useRef<HTMLAudioElement>(null);
  const lastSavedRef = useRef(0);
  const sleepTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // The duration of the file currently loaded into the <audio> element —
  // not the same as the chapter's latest known duration from polling,
  // which can be ahead of it while a checkpoint is publishing.
  const loadedDurationRef = useRef(0);
  const [isWaitingForMore, setIsWaitingForMore] = useState(false);

  const chapter = book?.chapters.find((c) => c.id === chapterId);
  const isStillExtending = chapter?.audioStatus === "partial";

  // Play/pause intent -> real element
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    if (isPlaying) {
      audio.play().catch(() => setPlaying(false));
    } else {
      audio.pause();
    }
  }, [isPlaying, chapterId, setPlaying]);

  // Speed intent -> real element
  useEffect(() => {
    if (audioRef.current) audioRef.current.playbackRate = speed;
  }, [speed]);

  // Seek requests -> real element
  useEffect(() => {
    if (audioRef.current && seekRequest) {
      audioRef.current.currentTime = seekRequest.seconds;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seekRequest?.nonce]);

  // Sleep timer: (re)schedules a pause whenever it changes or playback resumes
  useEffect(() => {
    if (sleepTimeoutRef.current) clearTimeout(sleepTimeoutRef.current);
    if (sleepTimerMinutes && isPlaying) {
      sleepTimeoutRef.current = setTimeout(() => setPlaying(false), sleepTimerMinutes * 60 * 1000);
    }
    return () => {
      if (sleepTimeoutRef.current) clearTimeout(sleepTimeoutRef.current);
    };
  }, [sleepTimerMinutes, isPlaying, setPlaying]);

  // A chapter still being generated ("partial") gets re-published with
  // more audio every few segments (see CHECKPOINT_EVERY in the backend).
  // useBook() polls while that's true, so chapter.durationSeconds grows
  // over time. When it grows past what's actually loaded in the <audio>
  // element AND playback has caught up to (or ended at) the old end,
  // reload the element and reseek to the same spot — picking up the new
  // audio without the person having to do anything.
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !chapter || !bookId || !chapterId) return;
    const latestKnownDuration = chapter.durationSeconds ?? 0;
    const caughtUp =
      audio.ended || loadedDurationRef.current - audio.currentTime <= CAUGHT_UP_THRESHOLD_SECONDS;

    if (latestKnownDuration > loadedDurationRef.current + 0.5 && caughtUp) {
      const resumeAt = audio.currentTime;
      const shouldResumePlaying = isPlaying;
      setIsWaitingForMore(false);

      audio.src = `${chapterAudioUrl(bookId, chapterId)}?t=${Date.now()}`; // cache-bust
      const onLoaded = () => {
        loadedDurationRef.current = audio.duration;
        audio.currentTime = resumeAt;
        if (shouldResumePlaying) audio.play().catch(() => setPlaying(false));
        audio.removeEventListener("loadedmetadata", onLoaded);
      };
      audio.addEventListener("loadedmetadata", onLoaded);
      audio.load();
    } else if (audio.ended && isStillExtending) {
      // Caught up but the next checkpoint hasn't published yet — show a
      // brief "catching up" state instead of looking like it just stopped.
      setIsWaitingForMore(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chapter?.durationSeconds, chapter?.audioStatus]);

  if (!bookId || !chapterId || !book || !chapter) return null;

  const pct = durationSeconds > 0 ? Math.min(100, (positionSeconds / durationSeconds) * 100) : 0;

  const handleTimeUpdate = () => {
    const audio = audioRef.current;
    if (!audio) return;
    reportProgress(audio.currentTime, audio.duration || durationSeconds);

    if (audio.currentTime - lastSavedRef.current > PROGRESS_SAVE_INTERVAL_MS / 1000) {
      lastSavedRef.current = audio.currentTime;
      updateProgress.mutate({ chapterId, positionSeconds: audio.currentTime });
    }
  };

  const handlePause = () => {
    setPlaying(false);
    if (audioRef.current) {
      updateProgress.mutate({ chapterId, positionSeconds: audioRef.current.currentTime });
    }
  };

  const handleEnded = () => {
    if (isStillExtending) {
      // Don't treat this as "finished" — the growth-detection effect
      // above will pick up and resume once the next checkpoint lands.
      setIsWaitingForMore(true);
      return;
    }
    setPlaying(false);
  };

  const handleProgressBarClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!durationSeconds) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const ratio = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
    seek(ratio * durationSeconds);
  };

  const skip = (delta: number) => {
    seek(Math.min(durationSeconds, Math.max(0, positionSeconds + delta)));
  };

  const cycleSleepTimer = () => {
    const currentIndex = SLEEP_PRESETS.indexOf(sleepTimerMinutes as (typeof SLEEP_PRESETS)[number]);
    const next = SLEEP_PRESETS[(currentIndex + 1) % SLEEP_PRESETS.length];
    setSleepTimer(next);
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 border-t border-ink-hairline bg-ink-surface shadow-docked">
      <audio
        ref={audioRef}
        src={chapterAudioUrl(bookId, chapterId)}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={(e) => {
          loadedDurationRef.current = e.currentTarget.duration;
          reportProgress(positionSeconds, e.currentTarget.duration);
        }}
        onEnded={handleEnded}
        onPause={handlePause}
        onPlay={() => setPlaying(true)}
      />

      {/* progress rail — the ribbon-tab motif compressed into a thin bar, clickable to seek */}
      <div className="h-1.5 w-full cursor-pointer bg-ink-hairline" onClick={handleProgressBarClick}>
        <div className="h-full bg-lamp-400 transition-[width]" style={{ width: `${pct}%` }} />
      </div>

      <div className="flex items-center gap-4 px-4 py-3 md:px-6">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className="relative h-11 w-11 shrink-0 overflow-hidden rounded-md bg-ink-raised">
            <div className="ribbon-tab absolute right-0 top-0 h-full w-2 bg-lamp-400" />
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm text-paper">{book.title}</p>
            <p className="truncate text-xs text-paper-muted">
              {chapter.title}
              {isWaitingForMore && " · catching up to generation…"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 md:gap-2">
          <button
            onClick={() => skip(-15)}
            aria-label="Back 15 seconds"
            className="hidden sm:flex h-9 w-9 items-center justify-center rounded-full text-paper-muted hover:bg-ink-raised hover:text-paper"
          >
            <RotateCcw size={18} />
          </button>
          <button
            onClick={togglePlay}
            aria-label={isPlaying ? "Pause" : "Play"}
            disabled={isWaitingForMore}
            className="flex h-10 w-10 items-center justify-center rounded-full bg-lamp-400 text-ink hover:bg-lamp-200 disabled:opacity-60"
          >
            {isWaitingForMore ? (
              <Loader2 size={18} className="animate-spin" />
            ) : isPlaying ? (
              <Pause size={18} fill="currentColor" />
            ) : (
              <Play size={18} fill="currentColor" className="ml-0.5" />
            )}
          </button>
          <button
            onClick={() => skip(15)}
            aria-label="Forward 15 seconds"
            className="hidden sm:flex h-9 w-9 items-center justify-center rounded-full text-paper-muted hover:bg-ink-raised hover:text-paper"
          >
            <RotateCw size={18} />
          </button>
        </div>

        <div className="hidden md:flex items-center gap-4 flex-1 justify-end">
          <span className="font-mono text-xs text-paper-muted">
            {formatDuration(positionSeconds)} / {formatDuration(durationSeconds)}
          </span>
          <span className="rounded-md border border-ink-hairline px-2 py-1 font-mono text-xs text-paper-muted">
            {speed.toFixed(2)}x
          </span>
          <button
            onClick={cycleSleepTimer}
            aria-label="Sleep timer"
            title={sleepTimerMinutes ? `Sleep in ${sleepTimerMinutes} min` : "Sleep timer off"}
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-full hover:bg-ink-raised",
              sleepTimerMinutes ? "text-lamp-400" : "text-paper-muted hover:text-paper"
            )}
          >
            <Moon size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
