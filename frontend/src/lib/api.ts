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
  html_with_citations?: string;
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

export type TreatmentType =
  | 'OVERRULED' | 'REVERSED' | 'VACATED' | 'ABROGATED' | 'SUPERSEDED'
  | 'AFFIRMED' | 'FOLLOWED'
  | 'DISTINGUISHED' | 'QUESTIONED' | 'CRITICIZED' | 'CITED'
  | 'UNKNOWN';

export type Severity = 'NEGATIVE' | 'POSITIVE' | 'NEUTRAL' | 'UNKNOWN';

export interface Treatment {
  type: TreatmentType;
  severity: Severity;
  confidence: number;
}

export interface TreatmentSummary {
  opinion_id: number;
  treatment_type: TreatmentType;
  severity: Severity;
  confidence: number;
  summary: {
    negative: number;
    positive: number;
    neutral: number;
    total?: number;
  };
  significant_treatments?: SignificantTreatment[];
  from_cache?: boolean;
  last_updated?: string;
}

export interface SignificantTreatment {
  type: TreatmentType;
  severity: Severity;
  confidence: number;
  described_opinion_id: number;
  describing_opinion_id: number;
  excerpt: string;
  keywords: string[];
}

export interface TreatmentHistory {
  opinion_id: number;
  total_treatments: number;
  history: Array<{
    parenthetical_id: number;
    treatment_type: TreatmentType;
    severity: Severity;
    confidence: number;
    text: string;
    describing_opinion_id: number;
    describing_case_name: string;
    date_filed: string | null;
    keywords: string[];
  }>;
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
  treatment?: Treatment | null;
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

  /**
   * Fetch opinion text from CourtListener API (automatically caches in database)
   */
  fetchOpinionText(opinionId: number): Promise<{
    opinion_id: number;
    plain_text: string | null;
    html: string | null;
    html_with_citations: string | null;
    source: string;
    cached: boolean;
  }> {
    return apiClient.get(`/api/v1/opinions/${opinionId}/text`);
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
    include_treatment_analysis?: boolean;
  }): Promise<{
    opinion_id: number;
    depth: number;
    total_citations: number;
    citations: CitationNode[];
    treatment_analysis?: {
      negative_treatment_count: number;
      risk_score: number;
      risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
      warnings: Array<{
        opinion_id: number;
        case_name: string;
        treatment_type: string;
        confidence: number;
        depth: number;
      }>;
    };
  }> {
    const queryParams = new URLSearchParams();
    if (params?.depth) queryParams.append('depth', params.depth.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.include_treatment_analysis) queryParams.append('include_treatment_analysis', 'true');
    return apiClient.get(`/api/v1/citations/outbound/${opinionId}?${queryParams}`);
  },

  /**
   * Check if an opinion has citations and needs syncing
   */
  checkCitationStatus(opinionId: number): Promise<{
    opinion_id: number;
    has_citations: boolean;
    citation_count: number;
    needs_sync: boolean;
  }> {
    return apiClient.get(`/api/v1/citation-sync/check/${opinionId}`);
  },

  /**
   * Sync citations from CourtListener API for an opinion
   */
  syncCitations(opinionId: number): Promise<{
    opinion_id: number;
    status: string;
    existing_citations: number;
    new_citations: number;
    api_citations_found?: number;
    local_matches?: number;
    message: string;
  }> {
    return apiClient.post(`/api/v1/citation-sync/sync/${opinionId}`);
  },

  /**
   * Get deep citation analysis with treatment tracking (4+ layers deep)
   */
  getDeepAnalysis(opinionId: number, params?: {
    depth?: number; // 1-5 levels, default 4
  }): Promise<{
    opinion_id: number;
    analysis_depth: number;
    total_cases_analyzed: number;
    negative_treatment_count: number;
    risk_assessment: {
      score: number;
      level: 'LOW' | 'MEDIUM' | 'HIGH';
      description: string;
    };
    treatment_warnings: Array<{
      opinion_id: number;
      case_name: string;
      treatment_type: string;
      confidence: number;
      depth: number;
      citation_chain: number[];
    }>;
    warnings_by_type: Record<string, Array<{
      opinion_id: number;
      case_name: string;
      treatment_type: string;
      confidence: number;
      depth: number;
      citation_chain: number[];
    }>>;
    problematic_citation_chains: Array<{
      start_case: any;
      problem_case: any;
      chain_length: number;
      chain_ids: number[];
    }>;
    citation_tree: any;
    all_cases: Record<number, any>;
  }> {
    const queryParams = new URLSearchParams();
    if (params?.depth) queryParams.append('depth', params.depth.toString());
    return apiClient.get(`/api/v1/citations/deep-analysis/${opinionId}?${queryParams}`);
  },
};

// Citation Risk API
export const treatmentAPI = {
  /**
   * Get citation risk analysis for an opinion
   */
  getTreatment(opinionId: number, useCache: boolean = true): Promise<TreatmentSummary> {
    const queryParams = new URLSearchParams();
    queryParams.append('use_cache', useCache.toString());
    return apiClient.get<TreatmentSummary>(`/api/v1/treatment/${opinionId}?${queryParams}`);
  },

  /**
   * Get citation risk history for an opinion
   */
  getHistory(opinionId: number, limit: number = 50): Promise<TreatmentHistory> {
    const queryParams = new URLSearchParams();
    queryParams.append('limit', limit.toString());
    return apiClient.get<TreatmentHistory>(`/api/v1/treatment/${opinionId}/history?${queryParams}`);
  },

  /**
   * Force fresh citation risk analysis (bypass cache)
   */
  analyzeTreatment(opinionId: number): Promise<TreatmentSummary> {
    return apiClient.post<TreatmentSummary>(`/api/v1/treatment/analyze/${opinionId}`);
  },

  /**
   * Batch analyze multiple opinions
   */
  batchAnalyze(opinionIds: number[], useCache: boolean = true): Promise<{
    total: number;
    results: TreatmentSummary[];
  }> {
    const queryParams = new URLSearchParams();
    queryParams.append('use_cache', useCache.toString());
    return apiClient.post(`/api/v1/treatment/batch?${queryParams}`, opinionIds);
  },

  /**
   * Get citation risk statistics
   */
  getStats(): Promise<{
    total_analyzed: number;
    total_parentheticals: number;
    by_severity: {
      negative: number;
      positive: number;
      neutral: number;
    };
  }> {
    return apiClient.get('/api/v1/treatment/stats/summary');
  },
};

// AI Analysis API
export const aiAnalysisAPI = {
  /**
   * Get AI-powered analysis of citation risk for an opinion (streaming)
   *
   * Only available for cases with negative citation risk.
   * Requires ANTHROPIC_API_KEY to be configured on the backend.
   *
   * @param opinionId - The opinion to analyze
   * @param quick - If true, uses Claude 3.5 Haiku for fast analysis (~2-5s).
   *                If false, uses Claude Sonnet 4.5 for comprehensive analysis (~10-30s).
   * @param onChunk - Callback function called for each streamed chunk
   * @param onComplete - Callback function called when streaming completes
   * @param onError - Callback function called if an error occurs
   */
  async analyzeRiskStreaming(
    opinionId: number,
    quick: boolean = false,
    onChunk: (chunk: string) => void,
    onComplete: (metadata: { model: string; usage: { input_tokens: number; output_tokens: number } }) => void,
    onError: (error: string) => void
  ): Promise<void> {
    const params = quick ? '?quick=true' : '';
    const url = `${API_URL}/api/v1/ai-analysis/${opinionId}${params}`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          console.log('[SSE] Stream done');
          break;
        }

        console.log('[SSE] Received chunk, size:', value.length, 'bytes');

        // Decode chunk and add to buffer
        buffer += decoder.decode(value, { stream: true });

        // Split by lines but keep incomplete lines in buffer
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep last incomplete line in buffer

        console.log('[SSE] Parsed', lines.length, 'lines from buffer');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === 'text') {
                console.log('[SSE] Text chunk:', data.content.substring(0, 20));
                onChunk(data.content);
              } else if (data.type === 'metadata') {
                onComplete({ model: data.model, usage: data.usage });
              } else if (data.type === 'error') {
                onError(data.error);
              } else if (data.type === 'done') {
                // Stream complete
                console.log('[SSE] Done signal received');
                return;
              }
            } catch (e) {
              // Skip malformed JSON
              console.warn('Failed to parse SSE data:', line);
            }
          }
        }
      }
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Failed to analyze');
    }
  },

  /**
   * Check if AI analysis is available
   */
  getStatus(): Promise<{
    available: boolean;
    model: string | null;
    message: string;
  }> {
    return apiClient.get('/api/v1/ai-analysis/status');
  },
};

export default apiClient;
