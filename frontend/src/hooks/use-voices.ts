import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchVoice, fetchVoices, trainVoice, uploadVoice } from "@/lib/api";
import type { Voice } from "@/types";

export function useVoices() {
  return useQuery({
    queryKey: ["voices"],
    queryFn: fetchVoices,
    // Poll while any voice is mid-training so the UI reflects real progress
    // without the user refreshing the page.
    refetchInterval: (query) => {
      const voices = query.state.data as Voice[] | undefined;
      return voices?.some((v) => v.status === "training") ? 2000 : false;
    },
  });
}

export function useVoice(id: string) {
  return useQuery({
    queryKey: ["voices", id],
    queryFn: () => fetchVoice(id),
    enabled: !!id,
    refetchInterval: (query) => {
      const voice = query.state.data as Voice | undefined;
      return voice?.status === "training" ? 2000 : false;
    },
  });
}

export function useUploadVoice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: uploadVoice,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["voices"] });
    },
  });
}

export function useTrainVoice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: trainVoice,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["voices"] });
    },
  });
}
