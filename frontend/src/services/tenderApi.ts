import api from "./api";
import { Tender, TenderListResponse } from "@/types/tender";

export interface TenderQueryParams {
  skip?: number;
  limit?: number;
  status?: string;
  domains?: string[];
  search?: string;
  expired?: boolean;
  sort_by?: string;
  sort_dir?: string;
}

export const fetchTenders = async (params: TenderQueryParams) => {
  const response = await api.get<TenderListResponse>("/tenders/", {
    params: {
      ...params,
      domains: params.domains?.join(","),
    },
  });
  return response.data;
};

export const fetchTender = async (id: string) => {
  const response = await api.get<Tender>(`/tenders/${id}`);
  return response.data;
};

export const reprocessTender = async (id: string) => {
  const response = await api.post(`/tenders/${id}/reprocess`);
  return response.data;
};

export const fetchTenderMatches = async (id: string, limit = 5) => {
  const response = await api.get(`/tenders/${id}/matches`, { params: { limit } });
  return response.data;
};
