import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  CompanyQueryParams,
  deleteCompany,
  fetchCompanies,
  fetchCompany,
  uploadCompany,
} from "@/services/companyApi";

export const useCompanies = (params: CompanyQueryParams) => {
  return useQuery({
    queryKey: ["companies", params],
    queryFn: () => fetchCompanies(params),
  });
};

export const useCompany = (companyId?: string) => {
  return useQuery({
    queryKey: ["companies", companyId],
    queryFn: () => fetchCompany(companyId || ""),
    enabled: Boolean(companyId),
  });
};

export const useUploadCompany = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ files, companyName }: { files: File[]; companyName?: string }) =>
      uploadCompany(files, companyName),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["companies"] });
    },
  });
};

export const useDeleteCompany = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (companyId: string) => deleteCompany(companyId),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["companies"] });
    },
  });
};
