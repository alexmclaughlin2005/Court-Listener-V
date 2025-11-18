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

  async delete<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'DELETE',
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
   * Get AI-powered analysis of citation risk for an opinion
   *
   * Only available for cases with negative citation risk.
   * Requires ANTHROPIC_API_KEY to be configured on the backend.
   *
   * @param opinionId - The opinion to analyze
   * @param quick - If true, uses Claude Haiku 4.5 for fast analysis (~2-5s).
   *                If false, uses Claude Sonnet 4.5 for comprehensive analysis (~10-30s).
   */
  analyzeRisk(opinionId: number, quick: boolean = false): Promise<{
    opinion_id: number;
    case_name: string;
    risk_summary: {
      treatment_type: string;
      severity: string;
      confidence: number;
      negative_count: number;
      positive_count: number;
      neutral_count: number;
    };
    citing_cases_count: number;
    analysis: string | null;
    model: string | null;
    usage: {
      input_tokens: number;
      output_tokens: number;
    } | null;
    error: string | null;
  }> {
    const params = quick ? '?quick=true' : '';
    return apiClient.post(`/api/v1/ai-analysis/${opinionId}${params}`);
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

// Citation Quality API
export const citationQualityAPI = {
  /**
   * Analyze citation quality tree for an opinion
   *
   * Performs recursive citation analysis up to specified depth:
   * - Fetches all cited opinions (breadth-first traversal)
   * - Analyzes each citation with AI (Claude Haiku 4.5)
   * - Calculates overall risk assessment
   * - Saves complete tree to database
   *
   * @param opinionId - Root opinion to analyze
   * @param depth - Analysis depth (1-5 levels, default 4)
   * @param forceRefresh - If true, re-analyze even if cached
   */
  analyzeTree(opinionId: number, params?: {
    depth?: number;
    force_refresh?: boolean;
  }): Promise<{
    success: boolean;
    opinion_id: number;
    result: CitationQualityTree;
  }> {
    const queryParams = new URLSearchParams();
    if (params?.depth) queryParams.append('depth', params.depth.toString());
    if (params?.force_refresh) queryParams.append('force_refresh', 'true');
    return apiClient.post(`/api/v1/citation-quality/analyze/${opinionId}?${queryParams}`);
  },

  /**
   * Get cached citation analysis tree
   *
   * @param opinionId - Opinion ID
   * @param depth - Optional depth filter
   */
  getTree(opinionId: number, depth?: number): Promise<CitationQualityTree> {
    const queryParams = new URLSearchParams();
    if (depth) queryParams.append('depth', depth.toString());
    return apiClient.get(`/api/v1/citation-quality/tree/${opinionId}?${queryParams}`);
  },

  /**
   * Get individual citation quality analysis
   *
   * @param opinionId - Opinion ID
   */
  getAnalysis(opinionId: number): Promise<CitationQualityAnalysis> {
    return apiClient.get(`/api/v1/citation-quality/analysis/${opinionId}`);
  },

  /**
   * Get citation quality analysis statistics
   */
  getStats(): Promise<{
    total_analyses: number;
    by_quality: Record<string, number>;
    average_risk_score: number;
    total_trees_analyzed: number;
    average_execution_time_seconds: number;
    cache_hit_rate: number;
  }> {
    return apiClient.get('/api/v1/citation-quality/stats');
  },

  /**
   * Get high-risk opinions
   *
   * @param limit - Maximum number of results (default 20, max 100)
   */
  getHighRiskOpinions(limit: number = 20): Promise<{
    count: number;
    high_risk_opinions: CitationQualityAnalysis[];
  }> {
    const queryParams = new URLSearchParams();
    queryParams.append('limit', limit.toString());
    return apiClient.get(`/api/v1/citation-quality/high-risk?${queryParams}`);
  },

  /**
   * Delete cached citation analysis tree(s)
   *
   * @param opinionId - Opinion ID
   */
  deleteTree(opinionId: number): Promise<{
    success: boolean;
    deleted_count: number;
    message: string;
  }> {
    return apiClient.delete(`/api/v1/citation-quality/tree/${opinionId}`);
  },

  /**
   * Check citation quality analysis service status
   */
  getStatus(): Promise<{
    ai_available: boolean;
    ai_model: string | null;
    courtlistener_api_configured: boolean;
    service_status: 'operational' | 'degraded';
    message: string;
  }> {
    return apiClient.get('/api/v1/citation-quality/status');
  },
};

// Type definitions for Citation Quality
export interface CitationQualityAnalysis {
  id: number;
  cited_opinion_id: number;
  quality_assessment: 'GOOD' | 'QUESTIONABLE' | 'OVERRULED' | 'SUPERSEDED' | 'UNCERTAIN';
  confidence: number;
  ai_summary: string;
  ai_model: string;
  is_overruled: boolean;
  is_questioned: boolean;
  is_criticized: boolean;
  risk_score: number;
  analysis_version: number;
  analyzed_at: string;
  last_updated: string;
}

export interface CitationQualityTree {
  id: number;
  root_opinion_id: number;
  max_depth: number;
  current_depth: number;
  total_citations_analyzed: number;
  good_count: number;
  questionable_count: number;
  overruled_count: number;
  superseded_count: number;
  uncertain_count: number;
  overall_risk_score: number;
  overall_risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  risk_factors: string[];
  tree_data: {
    root_opinion_id: number;
    citations_by_depth: Record<number, Array<{
      opinion_id: number;
      quality_assessment: string;
      risk_score: number;
      summary: string;
    }>>;
  };
  high_risk_citations: Array<{
    opinion_id: number;
    depth: number;
    quality_assessment: string;
    risk_score: number;
    summary: string;
  }>;
  analysis_started_at: string;
  analysis_completed_at: string | null;
  execution_time_seconds: number;
  cache_hits: number;
  cache_misses: number;
  status: 'in_progress' | 'completed' | 'failed';
  error_message: string | null;
}

export default apiClient;
