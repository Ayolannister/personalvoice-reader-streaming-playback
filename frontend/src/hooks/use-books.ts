import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  assignBookVoice,
  fetchBook,
  fetchBooks,
  generateChapterAudio,
  updateChapterProgress,
  uploadBook,
} from "@/lib/api";
import type { Book } from "@/types";

export function useBooks() {
  return useQuery({ queryKey: ["books"], queryFn: fetchBooks });
}

export function useBook(id: string) {
  return useQuery({
    queryKey: ["books", id],
    queryFn: () => fetchBook(id),
    enabled: !!id,
    // Poll while any chapter is generating or partial (playable but
    // still extending) so progress and duration keep updating live.
    refetchInterval: (query) => {
      const book = query.state.data as Book | undefined;
      return book?.chapters.some((c) => c.audioStatus === "generating" || c.audioStatus === "partial")
        ? 2000
        : false;
    },
  });
}

export function useUploadBook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: uploadBook,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["books"] });
    },
  });
}

export function useUpdateProgress(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ chapterId, positionSeconds }: { chapterId: string; positionSeconds: number }) =>
      updateChapterProgress(bookId, chapterId, positionSeconds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["books", bookId] });
    },
  });
}

export function useAssignVoice(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (voiceId: string) => assignBookVoice(bookId, voiceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["books", bookId] });
    },
  });
}

export function useGenerateChapter(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (chapterId: string) => generateChapterAudio(bookId, chapterId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["books", bookId] });
    },
  });
}
