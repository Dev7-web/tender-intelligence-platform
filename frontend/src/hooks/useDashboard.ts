import { useQuery } from "@tanstack/react-query";

import { fetchDashboardActivity, fetchDashboardStats, fetchProcessingQueue } from "@/services/dashboardApi";

export const useDashboard = () => {
  const stats = useQuery({
    queryKey: ["dashboard", "stats"],
    queryFn: fetchDashboardStats,
    refetchInterval: 30000,
  });

  const activity = useQuery({
    queryKey: ["dashboard", "activity"],
    queryFn: () => fetchDashboardActivity(10),
    refetchInterval: 30000,
  });

  const queue = useQuery({
    queryKey: ["dashboard", "queue"],
    queryFn: () => fetchProcessingQueue(20),
    refetchInterval: 30000,
  });

  return { stats, activity, queue };
};
