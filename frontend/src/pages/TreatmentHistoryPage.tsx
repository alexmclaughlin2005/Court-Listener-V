/**
 * TreatmentHistoryPage - Detailed citation risk history for a case
 *
 * Shows chronological timeline of all citation risks (parentheticals)
 * for a specific opinion, grouped and filterable by risk type.
 */
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { treatmentAPI, TreatmentHistory } from '../lib/api';
import TreatmentBadge from '../components/TreatmentBadge';

export default function TreatmentHistoryPage() {
  const { id } = useParams<{ id: string }>();
  const opinionId = parseInt(id || '0');

  const [history, setHistory] = useState<TreatmentHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('all'); // all, negative, positive, neutral

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await treatmentAPI.getHistory(opinionId, 200);
        setHistory(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load citation risk history');
        console.error('Error fetching citation risk history:', err);
      } finally {
        setLoading(false);
      }
    };

    if (opinionId) {
      fetchHistory();
    }
  }, [opinionId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading citation risk history...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !history) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <div className="mb-8">
            <Link to={`/case/${opinionId}`} className="text-blue-600 hover:text-blue-700">
              ← Back to Case
            </Link>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <p className="text-red-800">{error || 'Citation risk history not found'}</p>
          </div>
        </div>
      </div>
    );
  }

  // Filter history based on selected filter
  const filteredHistory = history.history.filter(item => {
    if (filter === 'all') return true;
    return item.severity.toLowerCase() === filter;
  });

  // Group by severity for stats
  const stats = {
    negative: history.history.filter(h => h.severity === 'NEGATIVE').length,
    positive: history.history.filter(h => h.severity === 'POSITIVE').length,
    neutral: history.history.filter(h => h.severity === 'NEUTRAL').length,
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Navigation */}
        <div className="mb-8">
          <Link to={`/case/${opinionId}`} className="text-blue-600 hover:text-blue-700">
            ← Back to Case
          </Link>
        </div>

        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Citation Risk History
          </h1>
          <p className="text-gray-600">
            Showing {filteredHistory.length} of {history.total_treatments} citation risks for Opinion {opinionId}
          </p>

          {/* Stats Summary */}
          <div className="grid grid-cols-3 gap-4 mt-6">
            <div className="bg-red-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-red-700">{stats.negative}</div>
              <div className="text-sm text-red-600">Negative</div>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-green-700">{stats.positive}</div>
              <div className="text-sm text-green-600">Positive</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-gray-700">{stats.neutral}</div>
              <div className="text-sm text-gray-600">Neutral</div>
            </div>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="bg-white rounded-lg shadow-md mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex">
              <button
                onClick={() => setFilter('all')}
                className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
                  filter === 'all'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                All ({history.total_treatments})
              </button>
              <button
                onClick={() => setFilter('negative')}
                className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
                  filter === 'negative'
                    ? 'border-red-600 text-red-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Negative ({stats.negative})
              </button>
              <button
                onClick={() => setFilter('positive')}
                className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
                  filter === 'positive'
                    ? 'border-green-600 text-green-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Positive ({stats.positive})
              </button>
              <button
                onClick={() => setFilter('neutral')}
                className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
                  filter === 'neutral'
                    ? 'border-gray-600 text-gray-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Neutral ({stats.neutral})
              </button>
            </nav>
          </div>
        </div>

        {/* Treatment Timeline */}
        <div className="space-y-4">
          {filteredHistory.length === 0 ? (
            <div className="bg-white rounded-lg shadow-md p-8 text-center text-gray-500">
              No {filter !== 'all' ? filter : ''} citation risks found
            </div>
          ) : (
            filteredHistory.map((item, index) => (
              <div
                key={item.parenthetical_id || index}
                className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
              >
                {/* Header with badge and date */}
                <div className="flex items-start justify-between mb-4">
                  <TreatmentBadge
                    treatment={{
                      type: item.treatment_type,
                      severity: item.severity,
                      confidence: item.confidence
                    }}
                    size="md"
                    showConfidence={true}
                    showIcon={true}
                  />
                  {item.date_filed && (
                    <span className="text-sm text-gray-500">
                      {new Date(item.date_filed).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      })}
                    </span>
                  )}
                </div>

                {/* Citing Case Info */}
                {item.describing_case_name && (
                  <div className="mb-3">
                    <Link
                      to={`/case/${item.describing_opinion_id}`}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      {item.describing_case_name}
                    </Link>
                  </div>
                )}

                {/* Parenthetical Text */}
                <div className="bg-gray-50 rounded-lg p-4 mb-3">
                  <p className="text-gray-700 italic">"{item.text}"</p>
                </div>

                {/* Keywords */}
                {item.keywords && item.keywords.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {item.keywords.map((keyword, i) => (
                      <span
                        key={i}
                        className={`inline-block px-2 py-1 text-xs rounded ${
                          item.severity === 'NEGATIVE'
                            ? 'bg-red-100 text-red-700'
                            : item.severity === 'POSITIVE'
                            ? 'bg-green-100 text-green-700'
                            : 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {keyword}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Load More Notice */}
        {history.total_treatments > 200 && (
          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
            <p className="text-blue-800">
              Showing the most recent 200 citation risks.
              Total citation risks available: {history.total_treatments}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
