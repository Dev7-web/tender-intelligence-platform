import api from "./api";
import { SearchResponse } from "@/types/search";

export interface SearchParams {
  query?: string;
  domains?: string[];
  certifications?: string[];
  limit?: number;
}

export const searchTenders = async (companyId: string, params: SearchParams) => {
  const response = await api.get<SearchResponse>(`/search/tenders/${companyId}`, {
    params: {
      query: params.query,
      domains: params.domains?.join(","),
      certifications: params.certifications?.join(","),
      limit: params.limit,
    },
  });
  return response.data;
};
