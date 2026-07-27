"use client";

import { useBooks } from "@/hooks/use-books";
import { BookCoverCard } from "@/components/book/book-cover-card";
import { ContinueListening } from "@/components/book/continue-listening";
import { Search, Loader2 } from "lucide-react";

export default function LibraryPage() {
  const { data: books, isLoading, isError, error } = useBooks();

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 md:px-8">
      <div className="mb-8 flex items-center justify-between gap-4">
        <h1 className="font-display text-2xl text-paper">Your library</h1>
        <div className="relative w-full max-w-xs">
          <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-paper-faint" />
          <input
            type="search"
            placeholder="Search your books"
            className="w-full rounded-lg border border-ink-hairline bg-ink-surface py-2 pl-9 pr-3 text-sm text-paper placeholder:text-paper-faint focus:border-lamp-400/50"
          />
        </div>
      </div>

      {isLoading && (
        <div className="flex items-center gap-2 py-16 justify-center text-paper-muted text-sm">
          <Loader2 size={16} className="animate-spin" />
          Loading your library
        </div>
      )}

      {isError && (
        <div className="rounded-card border border-danger-400/30 bg-danger-400/5 px-4 py-8 text-center text-sm text-danger-400">
          {error instanceof Error ? error.message : "Couldn't reach the backend"}
          <p className="mt-1 text-xs text-paper-muted">
            Is the FastAPI server running at localhost:8000?
          </p>
        </div>
      )}

      {books && (
        <>
          <ContinueListening books={books} />

          <section>
            <h2 className="mb-3 font-display text-lg text-paper">All books</h2>
            {books.length === 0 ? (
              <EmptyLibrary />
            ) : (
              <div className="grid grid-cols-2 gap-x-4 gap-y-6 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
                {books.map((book) => (
                  <BookCoverCard key={book.id} book={book} />
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}

function EmptyLibrary() {
  return (
    <div className="flex flex-col items-center justify-center rounded-card border border-dashed border-ink-hairline py-16 text-center">
      <p className="font-display text-lg text-paper">Start your library</p>
      <p className="mt-1 max-w-sm text-sm text-paper-muted">
        Add an EPUB, PDF, or TXT you have the right to read, and pick a voice to hear it in.
      </p>
    </div>
  );
}
