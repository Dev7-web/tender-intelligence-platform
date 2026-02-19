export interface UploadedFile {
  file_hash: string;
  original_name: string;
  local_path: string;
  uploaded_at: string;
}

export interface CompanyMetadata {
  company_name?: string;
  industries?: string[];
  capabilities?: string[];
  certifications?: string[];
  technologies?: string[];
  domains?: string[];
  past_clients?: string[];
  government_experience?: boolean;
  years_in_business?: number;
  employee_count?: string;
  annual_turnover?: string;
  locations?: string[];
  registrations?: string[];
  summary?: string;
}

export interface CompanyStatus {
  processing_status?: string;
  files_processed?: number;
  total_files?: number;
  last_error?: string | null;
}

export interface Company {
  id?: string;
  _id?: string;
  company_id: string;
  name?: string | null;
  uploaded_files?: UploadedFile[];
  metadata?: CompanyMetadata;
  status?: CompanyStatus;
  created_at?: string;
  updated_at?: string;
}

export interface CompanyListResponse {
  items: Company[];
  total: number;
  skip: number;
  limit: number;
}
