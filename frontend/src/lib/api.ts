/**
 * API client configuration and typed endpoints
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Type definitions
export interface Court {
  id: string;
  name: string;
}

export interface CaseResult {
  id: number;
  case_name: string;
  case_name_short: string;
  date_filed: string | null;
  citation_count: number;
  precedential_status: string;
  slug: string;
  court: Court;
}

export interface SearchResponse {
  query: string;
  results: CaseResult[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface Opinion {
  id: number;
  type: string;
  plain_text: string;
  html: string;
  extracted_by_ocr: boolean;
}

export interface Docket {
  id: number;
  docket_number: string;
  date_filed: string | null;
}

export interface CaseDetail {
  id: number;
  case_name: string;
  case_name_short: string;
  case_name_full: string | null;
  slug: string;
  date_filed: string | null;
  date_filed_is_approximate: boolean;
  citation_count: number;
  precedential_status: string;
  judges: string;
  docket: Docket | null;
  court: {
    id: string;
    short_name: string;
    full_name: string;
  } | null;
  opinions: Opinion[];
}

// Base API client
const apiClient = {
  baseURL: API_URL,

  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_URL}${endpoint}`);
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `API Error: ${response.statusText}`);
    }
    return response.json();
  },

  async post<T>(endpoint: string, data?: any): Promise<T> {
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `API Error: ${response.statusText}`);
    }
    return response.json();
  },
};

// Search API
export const searchAPI = {
  /**
   * Search cases by query with optional filters
   */
  searchCases(params: {
    q: string;
    court?: string;
    date_from?: string;
    date_to?: string;
    sort?: 'relevance' | 'date' | 'citations';
    limit?: number;
    offset?: number;
  }): Promise<SearchResponse> {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, value.toString());
      }
    });
    return apiClient.get<SearchResponse>(`/api/v1/search/cases?${queryParams}`);
  },

  /**
   * Get detailed information about a specific case
   */
  getCaseDetail(caseId: number): Promise<CaseDetail> {
    return apiClient.get<CaseDetail>(`/api/v1/search/cases/${caseId}`);
  },
};

export default apiClient;
