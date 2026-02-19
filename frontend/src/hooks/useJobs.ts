import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchJob,
  fetchJobs,
  fetchSchedulerStatus,
  JobQueryParams,
  triggerProcess,
  triggerScrape,
} from "@/services/jobApi";

export const useJobs = (params: JobQueryParams) => {
  return useQuery({
    queryKey: ["jobs", params],
    queryFn: () => fetchJobs(params),
    refetchInterval: 30000,
  });
};

export const useJob = (jobId?: string) => {
  return useQuery({
    queryKey: ["jobs", jobId],
    queryFn: () => fetchJob(jobId || ""),
    enabled: Boolean(jobId),
  });
};

export const useTriggerScrape = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: triggerScrape,
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
};

export const useTriggerProcess = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: triggerProcess,
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
};

export const useSchedulerStatus = () => {
  return useQuery({
    queryKey: ["jobs", "scheduler"],
    queryFn: fetchSchedulerStatus,
    refetchInterval: 30000,
  });
};
