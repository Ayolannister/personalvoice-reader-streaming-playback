import type { Book, Voice } from "@/types";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function fetchBooks(): Promise<Book[]> {
  const res = await fetch(`${API_BASE}/books`);
  if (!res.ok) throw new Error("Couldn't load your library");
  return withCoverUrls(await res.json());
}

export async function fetchBook(id: string): Promise<Book> {
  const res = await fetch(`${API_BASE}/books/${id}`);
  if (!res.ok) throw new Error("Couldn't load this book");
  return withCoverUrls([await res.json()])[0];
}

export async function uploadBook(file: File): Promise<Book> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/books`, { method: "POST", body: formData });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? "Upload failed");
  }
  return withCoverUrls([await res.json()])[0];
}

export async function updateChapterProgress(bookId: string, chapterId: string, positionSeconds: number) {
  const res = await fetch(`${API_BASE}/books/${bookId}/chapters/${chapterId}/progress`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ positionSeconds }),
  });
  if (!res.ok) throw new Error("Couldn't save your progress");
}

export async function fetchVoices(): Promise<Voice[]> {
  const res = await fetch(`${API_BASE}/voices`);
  if (!res.ok) throw new Error("Couldn't load your voices");
  return res.json();
}

export async function fetchVoice(id: string): Promise<Voice> {
  const res = await fetch(`${API_BASE}/voices/${id}`);
  if (!res.ok) throw new Error("Couldn't load this voice");
  return res.json();
}

export async function uploadVoice(params: { name: string; language: string; file: File }): Promise<Voice> {
  const formData = new FormData();
  formData.append("name", params.name);
  formData.append("language", params.language);
  formData.append("file", params.file);
  const res = await fetch(`${API_BASE}/voices`, { method: "POST", body: formData });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? "Upload failed");
  }
  return res.json();
}

export async function trainVoice(id: string): Promise<Voice> {
  const res = await fetch(`${API_BASE}/voices/${id}/train`, { method: "POST" });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? "Couldn't start training");
  }
  return res.json();
}

export async function assignBookVoice(bookId: string, voiceId: string): Promise<Book> {
  const res = await fetch(`${API_BASE}/books/${bookId}/voice`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ voiceId }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? "Couldn't set the voice for this book");
  }
  return withCoverUrls([await res.json()])[0];
}

export async function generateChapterAudio(bookId: string, chapterId: string, voiceId?: string) {
  const res = await fetch(`${API_BASE}/books/${bookId}/chapters/${chapterId}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ voiceId: voiceId ?? null }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? "Couldn't start generating this chapter");
  }
  return res.json();
}

export function chapterAudioUrl(bookId: string, chapterId: string): string {
  return `${API_BASE}/books/${bookId}/chapters/${chapterId}/audio`;
}

function withCoverUrls(books: Book[]): Book[] {
  return books.map((b) => ({
    ...b,
    coverUrl: b.coverUrl ? `${API_BASE}${b.coverUrl}` : null,
  }));
}
