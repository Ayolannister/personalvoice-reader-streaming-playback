import Link from "next/link";
import Image from "next/image";
import type { Book } from "@/types";

function initials(title: string) {
  return title
    .split(" ")
    .filter((w) => w.length > 2 || w === w.toUpperCase())
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join("");
}

export function BookCoverCard({ book }: { book: Book }) {
  const currentChapter = book.chapters.find((c) => c.id === book.currentChapterId);
  const chapterProgressPct =
    currentChapter?.durationSeconds && currentChapter.durationSeconds > 0
      ? Math.min(100, (currentChapter.progressSeconds / currentChapter.durationSeconds) * 100)
      : 0;

  return (
    <Link href={`/books/${book.id}`} className="group block">
      <div className="relative aspect-[2/3] w-full overflow-hidden rounded-card bg-gradient-to-br from-ink-raised to-ink-surface ring-1 ring-ink-hairline transition-shadow group-hover:ring-lamp-400/40">
        {book.coverUrl ? (
          <Image
            src={book.coverUrl}
            alt=""
            fill
            sizes="(max-width: 768px) 45vw, 200px"
            className="object-cover"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="font-display text-3xl italic text-paper-faint">{initials(book.title)}</span>
          </div>
        )}

        {/* signature ribbon: only shows when there's a resume point, marking where you stopped */}
        {currentChapter && currentChapter.progressSeconds > 0 && (
          <div
            className="ribbon-tab absolute right-3 top-0 h-10 w-5 bg-lamp-400"
            style={{ opacity: 0.55 + (chapterProgressPct / 100) * 0.45 }}
            aria-hidden="true"
          />
        )}

        {book.status === "needs_voice" && (
          <div className="absolute bottom-2 left-2 rounded-md bg-ink/80 px-2 py-1 text-[10px] text-lamp-200 backdrop-blur-sm">
            Needs a trained voice
          </div>
        )}
      </div>

      <div className="mt-2.5 px-0.5">
        <p className="truncate text-sm text-paper">{book.title}</p>
        <p className="truncate text-xs text-paper-muted">{book.author}</p>
      </div>
    </Link>
  );
}
