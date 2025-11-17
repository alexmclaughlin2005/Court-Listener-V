import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { citationAPI, CitationAnalytics } from '../lib/api'

export default function CitationAnalyticsPage() {
  const { opinionId } = useParams<{ opinionId: string }>()
  const [analytics, setAnalytics] = useState<CitationAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchAnalytics = async () => {
      if (!opinionId) return

      setLoading(true)
      setError(null)

      try {
        const data = await citationAPI.getAnalytics(parseInt(opinionId))
        setAnalytics(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load citation analytics')
      } finally {
        setLoading(false)
      }
    }

    fetchAnalytics()
  }, [opinionId])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading citation analytics...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error || !analytics) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <div className="mb-8">
            <Link to="/search" className="text-blue-600 hover:text-blue-700">
              ← Back to Search
            </Link>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <p className="text-red-800">{error || 'Analytics not found'}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8 flex justify-between items-center">
          <Link to="/search" className="text-blue-600 hover:text-blue-700">
            ← Back to Search
          </Link>
          <Link
            to={`/citations/network/${opinionId}`}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            View Citation Network
          </Link>
        </div>

        <h1 className="text-3xl font-bold text-gray-900 mb-8">Citation Analytics</h1>

        {/* Summary Cards */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-700 mb-2">Outbound Citations</h2>
            <p className="text-4xl font-bold text-orange-600">{analytics.outbound_citations}</p>
            <p className="text-sm text-gray-600 mt-2">Cases cited by this opinion</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-700 mb-2">Inbound Citations</h2>
            <p className="text-4xl font-bold text-green-600">{analytics.inbound_citations}</p>
            <p className="text-sm text-gray-600 mt-2">Cases that cite this opinion</p>
          </div>
        </div>

        {/* Citation Timeline */}
        {analytics.citation_timeline.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Citation Timeline</h2>
            <p className="text-sm text-gray-600 mb-6">
              How often this case has been cited over time
            </p>

            <div className="space-y-2">
              {analytics.citation_timeline.map((item) => {
                const maxCount = Math.max(...analytics.citation_timeline.map(i => i.count))
                const width = (item.count / maxCount) * 100

                return (
                  <div key={item.year} className="flex items-center gap-4">
                    <span className="text-sm font-medium text-gray-700 w-16">{item.year}</span>
                    <div className="flex-1">
                      <div
                        className="h-8 bg-blue-500 rounded flex items-center justify-end pr-2 text-white text-sm font-medium"
                        style={{ width: `${width}%`, minWidth: '40px' }}
                      >
                        {item.count}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Top Citing Courts */}
        {analytics.top_citing_courts.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Top Citing Courts</h2>
            <p className="text-sm text-gray-600 mb-6">
              Which courts cite this case most frequently
            </p>

            <div className="space-y-3">
              {analytics.top_citing_courts.map((court, index) => {
                const maxCount = analytics.top_citing_courts[0].count
                const width = (court.count / maxCount) * 100

                return (
                  <div key={court.court} className="flex items-center gap-4">
                    <span className="text-sm font-medium text-gray-700 w-8">#{index + 1}</span>
                    <span className="text-sm text-gray-900 w-48 truncate">{court.court}</span>
                    <div className="flex-1">
                      <div
                        className="h-6 bg-green-500 rounded flex items-center justify-end pr-2 text-white text-xs font-medium"
                        style={{ width: `${width}%`, minWidth: '40px' }}
                      >
                        {court.count}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Related Cases */}
        {analytics.related_cases.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Related Cases</h2>
            <p className="text-sm text-gray-600 mb-6">
              Cases frequently co-cited with this opinion
            </p>

            <div className="space-y-3">
              {analytics.related_cases.map((relatedCase) => (
                <div
                  key={relatedCase.opinion_id}
                  className="flex justify-between items-start p-4 border rounded hover:bg-gray-50"
                >
                  <div className="flex-1">
                    <Link
                      to={`/case/${relatedCase.cluster_id}`}
                      className="font-medium text-blue-600 hover:text-blue-700"
                    >
                      {relatedCase.case_name_short || relatedCase.case_name}
                    </Link>
                    <div className="flex gap-4 text-sm text-gray-600 mt-1">
                      <span>{relatedCase.court_name}</span>
                      {relatedCase.date_filed && (
                        <span>{new Date(relatedCase.date_filed).getFullYear()}</span>
                      )}
                      <span>{relatedCase.citation_count} citations</span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Link
                      to={`/citations/network/${relatedCase.opinion_id}`}
                      className="text-blue-600 hover:text-blue-700 text-sm"
                    >
                      Network →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {analytics.citation_timeline.length === 0 &&
          analytics.top_citing_courts.length === 0 &&
          analytics.related_cases.length === 0 && (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <p className="text-gray-500 text-lg">
                No citation data available for this opinion yet.
              </p>
            </div>
          )}
      </div>
    </div>
  )
}
