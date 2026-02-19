import api from "./api";
import { Company, CompanyListResponse } from "@/types/company";

export interface CompanyQueryParams {
  skip?: number;
  limit?: number;
  status?: string;
  search?: string;
}

export const fetchCompanies = async (params: CompanyQueryParams) => {
  const response = await api.get<CompanyListResponse>("/companies/", { params });
  return response.data;
};

export const fetchCompany = async (companyId: string) => {
  const response = await api.get<Company>(`/companies/${companyId}`);
  return response.data;
};

export const uploadCompany = async (files: File[], companyName?: string) => {
  const form = new FormData();
  files.forEach((file) => form.append("files", file));
  if (companyName) {
    form.append("company_name", companyName);
  }
  const response = await api.post<Company>("/companies/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};

export const deleteCompany = async (companyId: string) => {
  const response = await api.delete(`/companies/${companyId}`);
  return response.data;
};

export const fetchCompanySearchHistory = async (companyId: string, limit = 20) => {
  const response = await api.get(`/companies/${companyId}/search-history`, { params: { limit } });
  return response.data;
};
