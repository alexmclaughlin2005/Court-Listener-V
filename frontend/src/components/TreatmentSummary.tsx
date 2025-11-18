/**
 * TreatmentSummary - Detailed citation risk analysis panel
 *
 * Displays comprehensive citation risk information including:
 * - Overall citation risk status
 * - Breakdown by risk type
 * - Significant citation risk examples with links
 * - Confidence indicators
 */
import React, { useEffect, useState } from 'react';
import { TreatmentSummary as TreatmentSummaryType, treatmentAPI } from '../lib/api';
import TreatmentBadge from './TreatmentBadge';
import AIRiskAnalysis from './AIRiskAnalysis';

interface TreatmentSummaryProps {
  opinionId: number;
  caseName?: string;
  showHistory?: boolean;
  className?: string;
}

export const TreatmentSummary: React.FC<TreatmentSummaryProps> = ({
  opinionId,
  caseName,
  showHistory = false,
  className = ''
}) => {
  const [treatment, setTreatment] = useState<TreatmentSummaryType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTreatment = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await treatmentAPI.getTreatment(opinionId);
        setTreatment(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load citation risk data');
        console.error('Error fetching citation risk:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTreatment();
  }, [opinionId]);

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="text-red-600">
          <p className="font-semibold">Error loading citation risk data</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      </div>
    );
  }

  if (!treatment) {
    return null;
  }

  const hasTreatments = treatment.summary.total && treatment.summary.total > 0;

  return (
    <div className={`bg-white rounded-lg shadow-md ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Citation Risk</h3>
      </div>

      {/* Content */}
      <div className="p-6">
        {!hasTreatments ? (
          <div className="text-gray-600 text-center py-8">
            <p>No citation risk information available for this case.</p>
            <p className="text-sm mt-2">
              This case has not been cited in a way that indicates specific citation risk.
            </p>
          </div>
        ) : (
          <>
            {/* Overall Status */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-gray-700">Overall Status</h4>
                {treatment.from_cache && (
                  <span className="text-xs text-gray-500">Cached</span>
                )}
              </div>
              <TreatmentBadge
                treatment={treatment}
                size="lg"
                showConfidence={true}
                showIcon={true}
              />
            </div>

            {/* Treatment Breakdown */}
            <div className="mb-6">
              <h4 className="text-sm font-medium text-gray-700 mb-3">Citation Risk Breakdown</h4>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-red-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-red-700">
                    {treatment.summary.negative}
                  </div>
                  <div className="text-sm text-red-600">Negative</div>
                </div>
                <div className="bg-green-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-green-700">
                    {treatment.summary.positive}
                  </div>
                  <div className="text-sm text-green-600">Positive</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-gray-700">
                    {treatment.summary.neutral}
                  </div>
                  <div className="text-sm text-gray-600">Neutral</div>
                </div>
              </div>
            </div>

            {/* AI Risk Analysis */}
            <AIRiskAnalysis
              opinionId={opinionId}
              caseName={caseName || `Opinion ${opinionId}`}
              severity={treatment.severity}
              className="mb-6"
            />

            {/* Significant Treatments */}
            {treatment.significant_treatments && treatment.significant_treatments.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-3">
                  Significant Citation Risks
                </h4>
                <div className="space-y-3">
                  {treatment.significant_treatments.map((sig, index) => (
                    <div
                      key={index}
                      className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <TreatmentBadge
                          treatment={{
                            type: sig.type,
                            severity: sig.severity,
                            confidence: sig.confidence
                          }}
                          size="sm"
                          showConfidence={true}
                        />
                        <a
                          href={`/cases/${sig.describing_opinion_id}`}
                          className="text-sm text-blue-600 hover:text-blue-800"
                        >
                          View Case →
                        </a>
                      </div>
                      <p className="text-sm text-gray-700 mt-2 italic">
                        "{sig.excerpt}"
                      </p>
                      {sig.keywords && sig.keywords.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {sig.keywords.map((keyword, i) => (
                            <span
                              key={i}
                              className="inline-block px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded"
                            >
                              {keyword}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* View Full History Link */}
            {showHistory && (
              <div className="mt-6 pt-4 border-t border-gray-200">
                <a
                  href={`/cases/${opinionId}/treatment-history`}
                  className="text-blue-600 hover:text-blue-800 font-medium text-sm"
                >
                  View Full Citation Risk History →
                </a>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default TreatmentSummary;
