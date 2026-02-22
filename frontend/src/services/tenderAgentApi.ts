import api from "@/lib/api";
import { AuthUser } from "@/lib/auth";
import { CompanyProfile, DashboardReport, DashboardStats, MatchItem, Tender } from "@/types/tender-agent";

type AuthResponse = { token: string; user: AuthUser };

export const authSignUp = async (payload: { email: string; password: string; name?: string }) => {
  const { data } = await api.post<AuthResponse>("/auth/signup", payload);
  return data;
};

export const authSignIn = async (payload: { email: string; password: string }) => {
  const { data } = await api.post<AuthResponse>("/auth/signin", payload);
  return data;
};

export const authGoogleStart = async () => {
  const { data } = await api.get<{ enabled: boolean; message: string; auth_url?: string }>("/auth/oauth/google/start");
  return data;
};

export const fetchMe = async () => {
  const { data } = await api.get<{ user: AuthUser }>("/auth/me");
  return data.user;
};

export const createCompany = async (payload: {
  name: string;
  company_url: string;
  experience_years: number;
}) => {
  const { data } = await api.post<{ company_id: string; status: string; company: CompanyProfile }>("/companies", payload);
  return data;
};

export const scrapeCompanyWebsite = async (companyId: string) => {
  const { data } = await api.post(`/companies/${companyId}/scrape-website`);
  return data;
};

export const uploadCompanyDocuments = async (
  companyId: string,
  files: File[],
  onProgress?: (percent: number) => void
) => {
  const form = new FormData();
  files.forEach((file) => form.append("files", file));
  const { data } = await api.post(`/companies/${companyId}/documents`, form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (event) => {
      if (!onProgress || !event.total) return;
      onProgress(Math.round((event.loaded / event.total) * 100));
    },
  });
  return data;
};

export const deleteCompanyDocument = async (companyId: string, fileHash: string) => {
  const { data } = await api.delete(`/companies/${companyId}/documents/${fileHash}`);
  return data;
};

export const setCompanyInterests = async (companyId: string, interestTags: string[]) => {
  const { data } = await api.post(`/companies/${companyId}/interests`, { interest_tags: interestTags });
  return data;
};

export const processCompanyProfile = async (companyId: string) => {
  const { data } = await api.post<{ status: string; job_id: string }>(`/companies/${companyId}/process`);
  return data;
};

export const fetchCompanyProfile = async (companyId: string) => {
  const { data } = await api.get<CompanyProfile>(`/companies/${companyId}`);
  return data;
};

export const fetchDashboardStats = async (companyId?: string, overviewRange = "7d") => {
  const { data } = await api.get<DashboardStats>("/dashboard/stats", {
    params: { company_id: companyId, overview_range: overviewRange },
  });
  return data;
};

export const fetchDashboardReport = async (range = "12m", companyId?: string) => {
  const { data } = await api.get<DashboardReport>("/dashboard/report", {
    params: { range, company_id: companyId },
  });
  return data;
};

export const triggerScrapeAnalyze = async () => {
  const { data } = await api.post("/jobs/scrape/trigger");
  return data;
};

export const fetchCompanyMatches = async (
  companyId: string,
  params: {
    q?: string;
    time_period?: string;
    sort?: string;
    min_score?: number;
    page?: number;
    limit?: number;
    state?: string;
    city?: string;
    certification?: string;
    portal?: string;
    procurement?: string;
    organisation?: string;
    amount_range?: string;
  }
) => {
  const { data } = await api.get<{ items: MatchItem[]; page: number; limit: number; total: number }>(
    `/companies/${companyId}/matches`,
    { params }
  );
  return data;
};

export const fetchTenderDetail = async (tenderId: string) => {
  const { data } = await api.get<Tender>(`/tenders/${tenderId}`);
  return data;
};

export const updateTenderAction = async (
  tenderId: string,
  payload: { company_id: string; action: "saved" | "applied" | "discarded" | null }
) => {
  const { data } = await api.post(`/tenders/${tenderId}/action`, payload);
  return data;
};

export const fetchMyList = async (companyId: string, tab: string, page = 1, limit = 10) => {
  const { data } = await api.get(`/companies/${companyId}/my-list`, {
    params: { tab, page, limit },
  });
  return data;
};

export const fetchAiSuggestions = async (tenderId: string) => {
  const { data } = await api.get<{ items: string[] }>(`/tenders/${tenderId}/ai/suggestions`);
  return data.items;
};

export const askTenderAi = async (
  tenderId: string,
  payload: { company_id: string; message: string; chat_id?: string }
) => {
  const { data } = await api.post<{ chat_id: string; reply: string }>(`/tenders/${tenderId}/ai/chat`, payload);
  return data;
};

export const shareTenderByEmail = async (
  tenderId: string,
  payload: { company_id: string; recipients: string[]; note?: string }
) => {
  const { data } = await api.post<{ sent: boolean; count: number }>(`/tenders/${tenderId}/share`, payload);
  return data;
};

export const downloadTenderUrl = (tenderId: string) => {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
  return `${baseUrl}/tenders/${tenderId}/download`;
};

const getFilenameFromContentDisposition = (value?: string) => {
  if (!value) return null;
  const utfMatch = /filename\*=UTF-8''([^;]+)/i.exec(value);
  if (utfMatch?.[1]) {
    try {
      return decodeURIComponent(utfMatch[1]);
    } catch {
      return utfMatch[1];
    }
  }
  const match = /filename="([^"]+)"/i.exec(value) || /filename=([^;]+)/i.exec(value);
  return match?.[1]?.trim().replace(/^"|"$/g, "") ?? null;
};

export const downloadTenderFile = async (tenderId: string) => {
  const response = await api.get(`/tenders/${tenderId}/download`, { responseType: "blob" });
  const contentType = response.headers?.["content-type"] || "application/pdf";
  const filename =
    getFilenameFromContentDisposition(response.headers?.["content-disposition"]) || `tender-${tenderId}.pdf`;
  const blob = new Blob([response.data], { type: contentType });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};
