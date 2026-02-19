import api from "./api";

export const fetchDashboardStats = async () => {
  const response = await api.get("/dashboard/stats");
  return response.data;
};

export const fetchDashboardActivity = async (limit = 10) => {
  const response = await api.get("/dashboard/activity", { params: { limit } });
  return response.data;
};

export const fetchProcessingQueue = async (limit = 20) => {
  const response = await api.get("/dashboard/queue", { params: { limit } });
  return response.data;
};
