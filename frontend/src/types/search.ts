export interface SearchResult {
  tender_id: string;
  bid_id: string;
  score: number;
  match_reasons: string[];
}

export interface SearchResponse {
  company_id: string;
  results: SearchResult[];
  total: number;
  generated_at: string;
  query?: string | null;
}
