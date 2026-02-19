export interface TenderScrapedInfo {
  items?: string;
  quantity?: number;
  department?: string;
  department_address?: string;
  start_date?: string;
  end_date?: string;
  bid_type?: string;
  bid_value_range?: string;
}

export interface TenderMetadata {
  title?: string;
  department?: string;
  sector?: string;
  domains?: string[];
  required_certifications?: string[];
  required_technologies?: string[];
  summary?: string;
}

export interface TenderStatus {
  scrape_status?: string;
  pdf_downloaded?: boolean;
  llm_processed?: boolean;
  embedding_generated?: boolean;
  last_error?: string | null;
}

export interface Tender {
  id?: string;
  _id?: string;
  bid_id: string;
  ra_no?: string | null;
  gem_url?: string | null;
  pdf_url?: string | null;
  pdf_local_path?: string | null;
  scraped_info?: TenderScrapedInfo;
  metadata?: TenderMetadata;
  status?: TenderStatus;
  scraped_at?: string;
  created_at?: string;
  updated_at?: string;
  expired?: boolean;
}

export interface TenderListResponse {
  items: Tender[];
  total: number;
  skip: number;
  limit: number;
}
