/**
 * API client configuration and typed endpoints
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Type definitions
export interface Court {
  id: string;
  name: string;
  full_name: string;
}

export interface CaseResult {
  id: number;
  case_name: string;
  case_name_short: string;
  date_filed: string | null;
  citation_count: number;
  precedential_status: string;
  slug: string;
  opinion_count: number;
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

export interface CitationNode {
  opinion_id: number;
  cluster_id: number;
  case_name: string;
  case_name_short: string;
  date_filed: string | null;
  citation_count: number;
  court_id: string | null;
  court_name: string | null;
  node_type?: 'center' | 'cited' | 'citing';
}

export interface CitationEdge {
  source: number;
  target: number;
  type: 'inbound' | 'outbound';
  depth: number;
}

export interface CitationNetwork {
  center_opinion_id: number;
  nodes: CitationNode[];
  edges: CitationEdge[];
  node_count: number;
  edge_count: number;
}

export interface CitationAnalytics {
  opinion_id: number;
  outbound_citations: number;
  inbound_citations: number;
  citation_timeline: Array<{ year: number; count: number }>;
  top_citing_courts: Array<{ court: string; count: number }>;
  related_cases: CitationNode[];
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

// Citation API
export const citationAPI = {
  /**
   * Get citation network for visualization
   */
  getNetwork(opinionId: number, params?: {
    depth?: number;
    max_nodes?: number;
  }): Promise<CitationNetwork> {
    const queryParams = new URLSearchParams();
    if (params?.depth) queryParams.append('depth', params.depth.toString());
    if (params?.max_nodes) queryParams.append('max_nodes', params.max_nodes.toString());
    return apiClient.get<CitationNetwork>(`/api/v1/citations/network/${opinionId}?${queryParams}`);
  },

  /**
   * Get citation analytics for an opinion
   */
  getAnalytics(opinionId: number): Promise<CitationAnalytics> {
    return apiClient.get<CitationAnalytics>(`/api/v1/citations/analytics/${opinionId}`);
  },

  /**
   * Get inbound citations (cases that cite this opinion)
   */
  getInbound(opinionId: number, params?: {
    depth?: number;
    limit?: number;
    sort?: 'date' | 'relevance' | 'citation_count';
  }): Promise<{ opinion_id: number; depth: number; total_citing_cases: number; citations: CitationNode[] }> {
    const queryParams = new URLSearchParams();
    if (params?.depth) queryParams.append('depth', params.depth.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.sort) queryParams.append('sort', params.sort);
    return apiClient.get(`/api/v1/citations/inbound/${opinionId}?${queryParams}`);
  },

  /**
   * Get outbound citations (cases this opinion cites)
   */
  getOutbound(opinionId: number, params?: {
    depth?: number;
    limit?: number;
  }): Promise<{ opinion_id: number; depth: number; total_citations: number; citations: CitationNode[] }> {
    const queryParams = new URLSearchParams();
    if (params?.depth) queryParams.append('depth', params.depth.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    return apiClient.get(`/api/v1/citations/outbound/${opinionId}?${queryParams}`);
  },
};

export default apiClient;
