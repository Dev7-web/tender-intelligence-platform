export interface JobError {
  bid_id?: string;
  error: string;
  timestamp?: string;
}

export interface Job {
  id?: string;
  _id?: string;
  job_id: string;
  job_type?: string;
  status?: string;
  started_at?: string;
  completed_at?: string;
  stats?: Record<string, number>;
  errors?: JobError[];
}

export interface JobListResponse {
  items: Job[];
  total: number;
  skip: number;
  limit: number;
}
