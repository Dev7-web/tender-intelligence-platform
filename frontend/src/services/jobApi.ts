import api from "./api";
import { Job, JobListResponse } from "@/types/job";

export interface JobQueryParams {
  skip?: number;
  limit?: number;
  job_type?: string;
  status?: string;
}

export const fetchJobs = async (params: JobQueryParams) => {
  const response = await api.get<JobListResponse>("/jobs/", { params });
  return response.data;
};

export const fetchJob = async (jobId: string) => {
  const response = await api.get<Job>(`/jobs/${jobId}`);
  return response.data;
};

export const triggerScrape = async () => {
  const response = await api.post("/jobs/scrape/trigger");
  return response.data;
};

export const triggerProcess = async () => {
  const response = await api.post("/jobs/process/trigger");
  return response.data;
};

export const fetchSchedulerStatus = async () => {
  const response = await api.get("/jobs/scheduler/status");
  return response.data as { running: boolean };
};
