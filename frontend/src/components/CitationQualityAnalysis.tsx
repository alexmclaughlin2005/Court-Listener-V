/**
 * CitationQualityAnalysis - AI-powered recursive citation quality analysis
 *
 * Analyzes citations up to 4 levels deep to assess precedential reliability:
 * - Uses Claude Haiku 4.5 for fast, cost-effective analysis
 * - Identifies overruled, questioned, or criticized citations
 * - Provides depth-weighted risk assessment
 * - Displays results in expandable list format by depth level
 *
 * @version 1.0.0
 */
import React, { useState, useEffect } from 'react';
import { citationQualityAPI, CitationQualityTree } from '../lib/api';

interface CitationQualityAnalysisProps {
  opinionId: number;
  caseName: string;
  className?: string;
}

// Quality assessment badge colors
const qualityColors = {
  GOOD: 'bg-green-100 text-green-800 border-green-300',
  QUESTIONABLE: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  OVERRULED: 'bg-red-100 text-red-800 border-red-300',
  SUPERSEDED: 'bg-orange-100 text-orange-800 border-orange-300',
  UNCERTAIN: 'bg-gray-100 text-gray-800 border-gray-300',
};

const qualityIcons = {
  GOOD: '✓',
  QUESTIONABLE: '?',
  OVERRULED: '✕',
  SUPERSEDED: '⚠',
  UNCERTAIN: '~',
};

// Risk level colors
const riskLevelColors = {
  LOW: 'bg-green-50 border-green-200 text-green-900',
  MEDIUM: 'bg-yellow-50 border-yellow-200 text-yellow-900',
  HIGH: 'bg-red-50 border-red-200 text-red-900',
};

export const CitationQualityAnalysis: React.FC<CitationQualityAnalysisProps> = ({
  opinionId,
  caseName,
  className = ''
}) => {
  const [tree, setTree] = useState<CitationQualityTree | null>(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(true);
  const [expandedDepths, setExpandedDepths] = useState<Set<number>>(new Set([1]));
  const [selectedDepth, setSelectedDepth] = useState<number>(4);
  const [filterQuality, setFilterQuality] = useState<string | null>(null);

  // Check for cached analysis on mount
  useEffect(() => {
    const fetchCachedTree = async () => {
      try {
        setLoading(true);
        const cachedTree = await citationQualityAPI.getTree(opinionId);
        setTree(cachedTree);
        setError(null);
      } catch (err) {
        // No cached tree available - this is expected
        console.log('No cached citation quality analysis found');
      } finally {
        setLoading(false);
      }
    };

    fetchCachedTree();
  }, [opinionId]);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setError(null);
    setExpanded(true);

    try {
      const result = await citationQualityAPI.analyzeTree(opinionId, {
        depth: selectedDepth,
        force_refresh: false
      });

      if (result.success) {
        setTree(result.result);
        // Expand all depth levels by default
        setExpandedDepths(new Set([1, 2, 3, 4].slice(0, result.result.current_depth)));
      } else {
        setError('Analysis failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze citations');
      console.error('Citation quality analysis failed:', err);
    } finally {
      setAnalyzing(false);
    }
  };

  const toggleDepth = (depth: number) => {
    const newExpanded = new Set(expandedDepths);
    if (newExpanded.has(depth)) {
      newExpanded.delete(depth);
    } else {
      newExpanded.add(depth);
    }
    setExpandedDepths(newExpanded);
  };

  const getRiskScoreColor = (score: number): string => {
    if (score >= 60) return 'text-red-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-green-600';
  };

  // Filter citations by quality if filter is set
  const getFilteredCitations = (citations: any[]) => {
    if (!filterQuality) return citations;
    return citations.filter(c => c.quality_assessment === filterQuality);
  };

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-t-lg border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🔍</span>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Citation Quality Analysis</h3>
              <p className="text-sm text-gray-600">
                AI-powered recursive citation precedent assessment
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Depth selector */}
            {!tree && !analyzing && (
              <select
                value={selectedDepth}
                onChange={(e) => setSelectedDepth(Number(e.target.value))}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={1}>Depth: 1 level</option>
                <option value={2}>Depth: 2 levels</option>
                <option value={3}>Depth: 3 levels</option>
                <option value={4}>Depth: 4 levels</option>
                <option value={5}>Depth: 5 levels</option>
              </select>
            )}

            {/* Analyze button */}
            {!tree && !analyzing && (
              <button
                onClick={handleAnalyze}
                disabled={analyzing}
                className="px-4 py-2 rounded-lg font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                Analyze Citations
              </button>
            )}

            {/* Refresh button */}
            {tree && !analyzing && (
              <button
                onClick={handleAnalyze}
                className="px-4 py-2 rounded-lg font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors"
              >
                Refresh Analysis
              </button>
            )}

            {/* Expand/Collapse */}
            {tree && !analyzing && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="px-4 py-2 rounded-lg font-medium bg-gray-200 text-gray-700 hover:bg-gray-300 transition-colors"
              >
                {expanded ? 'Collapse' : 'Expand'}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-6 py-4">
        {/* Loading initial check */}
        {loading && !tree && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-3"></div>
            <p className="text-gray-600">Checking for cached analysis...</p>
          </div>
        )}

        {/* No analysis yet */}
        {!loading && !tree && !analyzing && !error && (
          <div className="text-center py-12">
            <span className="text-6xl mb-4 block">🔍</span>
            <h4 className="text-lg font-semibold text-gray-900 mb-2">
              No Citation Quality Analysis Available
            </h4>
            <p className="text-gray-600 mb-6 max-w-2xl mx-auto">
              Analyze the citations in <strong>{caseName}</strong> to assess precedential reliability.
              This AI-powered analysis will examine up to {selectedDepth} levels of citations to identify
              overruled, questioned, or criticized cases.
            </p>
            <button
              onClick={handleAnalyze}
              className="px-6 py-3 rounded-lg font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors inline-flex items-center gap-2"
            >
              <span>🤖</span>
              <span>Start Analysis</span>
            </button>
            <p className="text-sm text-gray-500 mt-4">
              Powered by Claude Haiku 4.5 • Analysis time: ~30-120 seconds
            </p>
          </div>
        )}

        {/* Analyzing state */}
        {analyzing && (
          <div className="py-12">
            <div className="flex flex-col items-center gap-4">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <div className="text-center">
                <p className="text-lg font-medium text-gray-900 mb-2">
                  Analyzing {selectedDepth}-level citation tree...
                </p>
                <p className="text-sm text-gray-600 mb-1">
                  This may take 30-120 seconds depending on the number of citations
                </p>
                <p className="text-xs text-gray-500">
                  Fetching citations → Analyzing with AI → Building tree structure
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Error state */}
        {error && !analyzing && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <p className="text-red-800 font-medium mb-2">Analysis Failed</p>
            <p className="text-sm text-red-700">{error}</p>
            <button
              onClick={handleAnalyze}
              className="mt-4 text-sm text-red-700 hover:text-red-900 underline"
            >
              Try again
            </button>
          </div>
        )}

        {/* Analysis results */}
        {tree && expanded && !analyzing && (
          <div className="space-y-6">
            {/* Overall Risk Assessment */}
            <div className={`rounded-lg border p-6 ${riskLevelColors[tree.overall_risk_level]}`}>
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h4 className="text-lg font-semibold mb-1">Overall Risk Assessment</h4>
                  <p className="text-sm opacity-75">
                    Analyzed {tree.total_citations_analyzed} citations across {tree.current_depth} levels
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-3xl font-bold">{tree.overall_risk_level}</div>
                  <div className="text-sm opacity-75">
                    Risk Score: {tree.overall_risk_score.toFixed(1)}/100
                  </div>
                </div>
              </div>

              {/* Risk Factors */}
              {tree.risk_factors && tree.risk_factors.length > 0 && (
                <div className="mt-4 pt-4 border-t border-current/20">
                  <p className="text-sm font-medium mb-2">Risk Factors:</p>
                  <ul className="space-y-1">
                    {tree.risk_factors.map((factor, idx) => (
                      <li key={idx} className="text-sm">• {factor}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-5 gap-4">
              <div className="bg-green-50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-green-700">{tree.good_count}</div>
                <div className="text-sm text-green-600">Good</div>
              </div>
              <div className="bg-yellow-50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-yellow-700">{tree.questionable_count}</div>
                <div className="text-sm text-yellow-600">Questionable</div>
              </div>
              <div className="bg-red-50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-red-700">{tree.overruled_count}</div>
                <div className="text-sm text-red-600">Overruled</div>
              </div>
              <div className="bg-orange-50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-orange-700">{tree.superseded_count}</div>
                <div className="text-sm text-orange-600">Superseded</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-gray-700">{tree.uncertain_count}</div>
                <div className="text-sm text-gray-600">Uncertain</div>
              </div>
            </div>

            {/* High Risk Citations Section */}
            {tree.high_risk_citations && tree.high_risk_citations.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                <h4 className="text-lg font-semibold text-red-900 mb-4 flex items-center gap-2">
                  <span>⚠️</span>
                  <span>High-Risk Citations ({tree.high_risk_citations.length})</span>
                </h4>
                <div className="space-y-3">
                  {tree.high_risk_citations.map((citation, idx) => (
                    <div key={idx} className="bg-white rounded-lg p-4 border border-red-200">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className={`inline-block px-2 py-1 text-xs font-medium rounded border ${qualityColors[citation.quality_assessment as keyof typeof qualityColors]}`}>
                            {qualityIcons[citation.quality_assessment as keyof typeof qualityIcons]} {citation.quality_assessment}
                          </span>
                          <span className="text-sm text-gray-600">
                            Depth {citation.depth}
                          </span>
                        </div>
                        <div className={`text-lg font-bold ${getRiskScoreColor(citation.risk_score)}`}>
                          {citation.risk_score}
                        </div>
                      </div>
                      <p className="text-sm text-gray-700 mt-2">{citation.summary}</p>
                      <a
                        href={`/cases/${citation.opinion_id}`}
                        className="text-sm text-blue-600 hover:text-blue-800 mt-2 inline-block"
                      >
                        View Case →
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Quality Filter */}
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700">Filter by quality:</span>
              <div className="flex gap-2">
                <button
                  onClick={() => setFilterQuality(null)}
                  className={`px-3 py-1 text-xs font-medium rounded border ${
                    filterQuality === null
                      ? 'bg-blue-100 text-blue-800 border-blue-300'
                      : 'bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200'
                  }`}
                >
                  All
                </button>
                {Object.keys(qualityColors).map((quality) => (
                  <button
                    key={quality}
                    onClick={() => setFilterQuality(quality)}
                    className={`px-3 py-1 text-xs font-medium rounded border ${
                      filterQuality === quality
                        ? qualityColors[quality as keyof typeof qualityColors]
                        : 'bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200'
                    }`}
                  >
                    {qualityIcons[quality as keyof typeof qualityIcons]} {quality}
                  </button>
                ))}
              </div>
            </div>

            {/* Citations by Depth */}
            <div className="space-y-4">
              <h4 className="text-lg font-semibold text-gray-900">Citations by Depth</h4>
              {Object.entries(tree.tree_data.citations_by_depth)
                .sort(([a], [b]) => Number(a) - Number(b))
                .map(([depth, citations]) => {
                  const depthNum = Number(depth);
                  const isExpanded = expandedDepths.has(depthNum);
                  const filteredCitations = getFilteredCitations(citations);

                  if (filteredCitations.length === 0 && filterQuality) {
                    return null;
                  }

                  return (
                    <div key={depth} className="border border-gray-200 rounded-lg">
                      {/* Depth Header */}
                      <button
                        onClick={() => toggleDepth(depthNum)}
                        className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">{isExpanded ? '▼' : '▶'}</span>
                          <div className="text-left">
                            <h5 className="text-base font-semibold text-gray-900">
                              Level {depth} Citations
                            </h5>
                            <p className="text-sm text-gray-600">
                              {filteredCitations.length} {filterQuality ? 'filtered ' : ''}citation{filteredCitations.length !== 1 ? 's' : ''}
                            </p>
                          </div>
                        </div>
                      </button>

                      {/* Citations List */}
                      {isExpanded && (
                        <div className="px-6 pb-4 space-y-3">
                          {filteredCitations.map((citation, idx) => (
                            <div key={idx} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                              <div className="flex items-start justify-between mb-2">
                                <span className={`inline-block px-2 py-1 text-xs font-medium rounded border ${qualityColors[citation.quality_assessment as keyof typeof qualityColors]}`}>
                                  {qualityIcons[citation.quality_assessment as keyof typeof qualityIcons]} {citation.quality_assessment}
                                </span>
                                <div className={`text-lg font-bold ${getRiskScoreColor(citation.risk_score)}`}>
                                  {citation.risk_score}
                                </div>
                              </div>
                              <p className="text-sm text-gray-700 mt-2">{citation.summary}</p>
                              <a
                                href={`/cases/${citation.opinion_id}`}
                                className="text-sm text-blue-600 hover:text-blue-800 mt-2 inline-block"
                              >
                                View Case →
                              </a>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
            </div>

            {/* Analysis Metadata */}
            <div className="mt-6 pt-4 border-t border-gray-200 text-xs text-gray-500">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p>Analysis completed: {new Date(tree.analysis_completed_at!).toLocaleString()}</p>
                  <p>Execution time: {tree.execution_time_seconds.toFixed(1)}s</p>
                </div>
                <div>
                  <p>Cache hits: {tree.cache_hits} | Cache misses: {tree.cache_misses}</p>
                  <p>Cache hit rate: {((tree.cache_hits / (tree.cache_hits + tree.cache_misses)) * 100).toFixed(1)}%</p>
                </div>
              </div>
              <p className="mt-3">
                This analysis was generated by Claude Haiku 4.5 based on full opinion text and citation context.
                Results are cached for performance and reused across different analysis trees. Use this as a research
                aid and verify findings independently.
              </p>
            </div>
          </div>
        )}

        {/* Collapsed state */}
        {tree && !expanded && !analyzing && (
          <div className="text-center py-8">
            <p className="text-gray-600 mb-4">
              Citation quality analysis complete: <strong>{tree.total_citations_analyzed}</strong> citations analyzed
            </p>
            <button
              onClick={() => setExpanded(true)}
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              Click "Expand" to view results
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default CitationQualityAnalysis;
