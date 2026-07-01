export interface AuthUser {
  id: string;
  email: string;
  name?: string;
  username?: string;
  phone?: string;
  profession?: string;
  location?: string;
  about_me?: string;
  company_id?: string | null;
  is_admin?: boolean;
  is_active?: boolean;
  notification_preferences?: {
    tender_updates?: boolean;
    matching_tenders?: boolean;
    expiring_tenders?: boolean;
  };
}

const TOKEN_KEY = "ta_token";
const REFRESH_TOKEN_KEY = "ta_refresh_token";
const USER_KEY = "ta_user";
const COMPANY_KEY = "ta_company_id";

export const getToken = () => localStorage.getItem(TOKEN_KEY);

export const setToken = (token: string) => {
  localStorage.setItem(TOKEN_KEY, token);
};

// Refresh token issued by the central auth gateway (mirrors main-dashboard).
export const getRefreshToken = () => localStorage.getItem(REFRESH_TOKEN_KEY);

export const setRefreshToken = (token: string) => {
  localStorage.setItem(REFRESH_TOKEN_KEY, token);
};

export type AuthClearReason = "manual" | "session-expired" | "unknown";

export const clearAuth = (reason: AuthClearReason = "unknown") => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(COMPANY_KEY);

  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("ta:auth:cleared", { detail: { reason } }));
  }
};

export const getUser = (): AuthUser | null => {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
};

export const setUser = (user: AuthUser) => {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  if (user.company_id) {
    setCompanyId(user.company_id);
  }
};

export const getCompanyId = () => {
  return localStorage.getItem(COMPANY_KEY);
};

export const setCompanyId = (companyId: string) => {
  localStorage.setItem(COMPANY_KEY, companyId);
};
