/**
 * AIRiskAnalysis - AI-powered citation risk analysis component
 *
 * Auto-triggers quick analysis using Claude Haiku 4.5 on mount for instant preview.
 * Provides "Deep Analysis" button to get comprehensive analysis with Claude Sonnet 4.5.
 *
 * - Quick Analysis (Haiku 4.5): Automatic, 2-5s, concise summary with quality assessment
 * - Deep Analysis (Sonnet 4.5): Manual, 10-30s, comprehensive insights with overturn determination
 *
 * @version 2.0.0
 */
import React, { useState, useEffect } from 'react';
import { aiAnalysisAPI } from '../lib/api';

interface AIRiskAnalysisProps {
  opinionId: number;
  caseName: string;
  severity: string;  // NEGATIVE, POSITIVE, NEUTRAL, UNKNOWN
  className?: string;
}

export const AIRiskAnalysis: React.FC<AIRiskAnalysisProps> = ({
  opinionId,
  caseName,
  severity,
  className = ''
}) => {
  const [quickAnalysis, setQuickAnalysis] = useState<string | null>(null);
  const [deepAnalysis, setDeepAnalysis] = useState<string | null>(null);
  const [loadingQuick, setLoadingQuick] = useState(false);
  const [loadingDeep, setLoadingDeep] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [model, setModel] = useState<string>('');

  // Only show for cases with negative citation risk
  if (severity !== 'NEGATIVE') {
    return null;
  }

  // Auto-trigger quick analysis on mount
  useEffect(() => {
    const runQuickAnalysis = async () => {
      setLoadingQuick(true);
      setError(null);
      setExpanded(true);

      try {
        const result = await aiAnalysisAPI.analyzeRisk(opinionId, true);

        if (result.error) {
          console.error('Quick analysis failed:', result.error);
          setLoadingQuick(false);
          return;
        }

        setQuickAnalysis(result.analysis);
        setModel(result.model || '');
        setLoadingQuick(false);
      } catch (err) {
        console.error('Quick analysis failed:', err);
        setLoadingQuick(false);
      }
    };

    runQuickAnalysis();
  }, [opinionId]);

  const handleDeepAnalysis = async () => {
    setLoadingDeep(true);
    setError(null);
    setExpanded(true);

    try {
      const result = await aiAnalysisAPI.analyzeRisk(opinionId, false);

      if (result.error) {
        setError(result.error);
        setLoadingDeep(false);
        return;
      }

      setDeepAnalysis(result.analysis);
      setModel(result.model || '');
      setLoadingDeep(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze');
      setLoadingDeep(false);
    }
  };

  // Determine which analysis to display
  const currentAnalysis = deepAnalysis || quickAnalysis;
  const isLoading = loadingQuick || loadingDeep;

  return (
    <div className={`bg-white rounded-lg border border-red-200 ${className}`}>
      {/* Header with buttons */}
      <div className="px-6 py-4 bg-red-50 rounded-t-lg border-b border-red-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🤖</span>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">AI Risk Analysis</h3>
              <p className="text-sm text-gray-600">
                {model ? `Powered by ${model}` : 'Powered by Claude AI'}
                {quickAnalysis && !deepAnalysis && ' - Quick Preview'}
                {deepAnalysis && ' - Comprehensive Analysis'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Deep Analysis button - only show if we have quick analysis and not loading */}
            {quickAnalysis && !deepAnalysis && !isLoading && (
              <button
                onClick={handleDeepAnalysis}
                className="px-4 py-2 rounded-lg font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors"
              >
                Get Deep Analysis
              </button>
            )}

            {/* Expand/Collapse button */}
            {currentAnalysis && !isLoading && (
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
        {/* Loading state */}
        {isLoading && (
          <div className="flex items-center gap-3 py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <div>
              <p className="text-gray-900 font-medium">
                {loadingQuick ? 'Running quick analysis...' : 'Running deep analysis...'}
              </p>
              <p className="text-sm text-gray-600">
                {loadingQuick ? 'This will take 2-5 seconds' : 'This may take 10-30 seconds'}
              </p>
            </div>
          </div>
        )}

        {/* Error state */}
        {error && !isLoading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800 font-medium">Error</p>
            <p className="text-sm text-red-700 mt-1">{error}</p>
            <button
              onClick={handleDeepAnalysis}
              className="mt-3 text-sm text-red-700 hover:text-red-900 underline"
            >
              Try again
            </button>
          </div>
        )}

        {/* Analysis result */}
        {currentAnalysis && !isLoading && expanded && (
          <div className="prose prose-sm max-w-none">
            <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
              {currentAnalysis}
            </div>

            <div className="mt-6 pt-4 border-t border-gray-200 text-xs text-gray-500">
              <p>
                This analysis was generated by {model} based on the opinion text
                and negative citations. It should be used as a research aid and verified
                independently.
              </p>
              {quickAnalysis && !deepAnalysis && (
                <p className="mt-2 text-blue-600">
                  This is a quick preview. Click "Get Deep Analysis" for comprehensive insights.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Collapsed state */}
        {currentAnalysis && !isLoading && !expanded && (
          <div className="text-sm text-gray-600">
            <p>
              {deepAnalysis ? 'Comprehensive' : 'Quick'} AI analysis available. Click "Expand" to view.
            </p>
          </div>
        )}

        {/* Initial loading state (no analysis yet, but loading quick analysis) */}
        {!currentAnalysis && isLoading && !error && (
          <div className="text-sm text-gray-600">
            <p className="mb-3">
              Generating quick AI analysis of why <strong>{caseName}</strong> is at citation risk...
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIRiskAnalysis;
