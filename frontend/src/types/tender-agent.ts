export interface CompanyProfile {
  id?: string;
  company_id: string;
  name: string;
  company_url: string;
  experience_years: number;
  turnover?: string;
  description?: string;
  interest_tags: string[];
  interested_states?: string[];
  tender_topics?: string[];
  website_scrape?: {
    status: string;
    pages: string[];
    extracted_text: string;
    last_error?: string | null;
  };
  uploaded_files?: Array<{
    file_hash: string;
    original_name: string;
    local_path: string;
    mime_type?: string;
    size_bytes?: number;
    uploaded_at: string;
    extract_status?: string;
    extracted_text_len?: number;
  }>;
  status?: {
    processing_status: string;
    files_processed: number;
    total_files: number;
    last_error?: string | null;
  };
  metadata?: Record<string, unknown>;
}

export interface MatchItem {
  tender: Tender;
  match: {
    score: number;
    reasons: string[];
  };
  action: "saved" | "applied" | "discarded" | null;
}

export interface Tender {
  id: string;
  bid_id: string;
  gem_url?: string;
  pdf_local_path?: string;
  portal?: string;
  scraped_info?: {
    department?: string;
    start_date?: string;
    end_date?: string;
    bid_type?: string;
    bid_value_range?: string;
    items?: string;
  };
  metadata?: {
    title?: string;
    department?: string;
    location?: string;
    summary?: string;
    domains?: string[];
    required_technologies?: string[];
    required_certifications?: string[];
    estimated_value?: string;
    eligibility_criteria?: Record<string, unknown>;
  };
}

export interface DashboardStats {
  company_id?: string;
  company_name: string;
  totals: {
    tenders_analyzed: number;
    best_tenders_found: number;
    tenders_saved: number;
    tenders_applied: number;
  };
  overview_range?: "7d" | "10d" | "6m" | "12m";
  overview?: {
    gathering: number;
    analyzed: number;
    saved: number;
    applied: number;
  };
  overview_last_7_days: {
    gathering: number;
    analyzed: number;
    saved: number;
    applied: number;
  };
}

export interface DashboardReport {
  range: string;
  labels: string[];
  series: {
    gathering: number[];
    analyze: number[];
    saved: number[];
  };
}

export interface ApiErrorShape {
  error?: {
    code?: string;
    message?: string;
    details?: Record<string, string>;
  };
}
