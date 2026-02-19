import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchTender, fetchTenders, reprocessTender, TenderQueryParams } from "@/services/tenderApi";

export const useTenders = (params: TenderQueryParams) => {
  return useQuery({
    queryKey: ["tenders", params],
    queryFn: () => fetchTenders(params),
  });
};

export const useTender = (id?: string) => {
  return useQuery({
    queryKey: ["tenders", id],
    queryFn: () => fetchTender(id || ""),
    enabled: Boolean(id),
  });
};

export const useReprocessTender = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => reprocessTender(id),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["tenders"] });
    },
  });
};
