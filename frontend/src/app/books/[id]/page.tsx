"use client";

import { useParams, notFound } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useBook } from "@/hooks/use-books";
import { ChapterList } from "@/components/book/chapter-list";
import { BookHero } from "@/components/book/book-hero";

export default function BookDetailsPage() {
  const params = useParams<{ id: string }>();
  const { data: book, isLoading, isError } = useBook(params.id);

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-24 justify-center text-paper-muted text-sm">
        <Loader2 size={16} className="animate-spin" />
        Loading book
      </div>
    );
  }

  if (isError || !book) {
    notFound();
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 md:px-8">
      <BookHero book={book} />
      <ChapterList book={book} />
    </div>
  );
}
