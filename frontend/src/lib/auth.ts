export interface AuthUser {
  id: string;
  email: string;
  name?: string;
  company_id?: string | null;
}

const TOKEN_KEY = "ta_token";
const USER_KEY = "ta_user";
const COMPANY_KEY = "ta_company_id";

export const getToken = () => localStorage.getItem(TOKEN_KEY);

export const setToken = (token: string) => {
  localStorage.setItem(TOKEN_KEY, token);
};

export const clearAuth = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(COMPANY_KEY);
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
