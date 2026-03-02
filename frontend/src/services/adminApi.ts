import axios from "axios";

const BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
const ADMIN_KEY = import.meta.env.VITE_ADMIN_API_KEY || "tender-admin-secret";

const client = axios.create({
  baseURL: BASE,
  headers: { "x-admin-key": ADMIN_KEY },
});

export type AdminStats = {
  total_users: number;
  active_users: number;
  applied_tenders: number;
  discarded_tenders: number;
};

export type TenderStats = {
  period: string;
  labels: string[];
  applied: number[];
  discarded: number[];
};

export type AdminUser = {
  id: string;
  email: string;
  name?: string;
  auth_provider?: string;
  is_verified?: boolean;
  is_active?: boolean;
  company_id?: string;
  created_at?: string;
  last_login_at?: string;
  tender_stats?: {
    applied: number;
    saved: number;
    discarded: number;
    won: number;
  };
};

export type UsersResponse = {
  total: number;
  users: AdminUser[];
};

export const fetchAdminStats = (): Promise<AdminStats> =>
  client.get("/admin/stats").then((r) => r.data);

export const fetchTenderStats = (period: string): Promise<TenderStats> =>
  client.get("/admin/tender-stats", { params: { period } }).then((r) => r.data);

export const fetchUsers = (skip: number, limit: number, search: string): Promise<UsersResponse> =>
  client.get("/admin/users", { params: { skip, limit, search } }).then((r) => r.data);

export const fetchUser = (userId: string): Promise<AdminUser> =>
  client.get(`/admin/users/${userId}`).then((r) => r.data);

export const toggleUserStatus = (userId: string): Promise<{ is_active: boolean }> =>
  client.put(`/admin/users/${userId}/inactivate`).then((r) => r.data);

export const deleteUser = (userId: string): Promise<{ deleted: boolean }> =>
  client.delete(`/admin/users/${userId}`).then((r) => r.data);
