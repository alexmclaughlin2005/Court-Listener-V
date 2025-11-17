import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { searchAPI, CaseDetail } from '../lib/api'
import TreatmentSummary from '../components/TreatmentSummary'
import OpinionText from '../components/OpinionText'

export default function CaseDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [caseData, setCaseData] = useState<CaseDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchCase = async () => {
      if (!id) return

      setLoading(true)
      setError(null)

      try {
        const data = await searchAPI.getCaseDetail(parseInt(id))
        setCaseData(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load case')
      } finally {
        setLoading(false)
      }
    }

    fetchCase()
  }, [id])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading case details...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error || !caseData) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <div className="mb-8">
            <Link to="/search" className="text-blue-600 hover:text-blue-700">
              ← Back to Search
            </Link>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <p className="text-red-800">{error || 'Case not found'}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Navigation */}
        <div className="mb-8 flex justify-between items-center">
          <Link to="/search" className="text-blue-600 hover:text-blue-700">
            ← Back to Search
          </Link>
          {caseData.opinions.length > 0 && (
            <Link
              to={`/citations/network/${caseData.opinions[0].id}`}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              View Citation Network
            </Link>
          )}
        </div>

        {/* Case Header */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            {caseData.case_name}
          </h1>

          <div className="grid md:grid-cols-2 gap-6 text-sm">
            {/* Left Column */}
            <div className="space-y-3">
              {caseData.court && (
                <div>
                  <span className="font-semibold text-gray-700">Court:</span>
                  <span className="ml-2 text-gray-600">{caseData.court.full_name}</span>
                </div>
              )}

              {caseData.date_filed && (
                <div>
                  <span className="font-semibold text-gray-700">Date Filed:</span>
                  <span className="ml-2 text-gray-600">
                    {new Date(caseData.date_filed).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                    {caseData.date_filed_is_approximate && (
                      <span className="ml-1 text-gray-400 text-xs">(approximate)</span>
                    )}
                  </span>
                </div>
              )}

              {caseData.docket?.docket_number && (
                <div>
                  <span className="font-semibold text-gray-700">Docket Number:</span>
                  <span className="ml-2 text-gray-600">{caseData.docket.docket_number}</span>
                </div>
              )}
            </div>

            {/* Right Column */}
            <div className="space-y-3">
              <div>
                <span className="font-semibold text-gray-700">Citation Count:</span>
                <span className="ml-2 text-gray-600">{caseData.citation_count}</span>
              </div>

              {caseData.precedential_status && (
                <div>
                  <span className="font-semibold text-gray-700">Status:</span>
                  <span className="ml-2 text-gray-600">{caseData.precedential_status}</span>
                </div>
              )}

              {caseData.judges && (
                <div>
                  <span className="font-semibold text-gray-700">Judges:</span>
                  <span className="ml-2 text-gray-600">{caseData.judges}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Treatment Summary */}
        {caseData.opinions.length > 0 && (
          <TreatmentSummary
            opinionId={caseData.opinions[0].id}
            showHistory={true}
            className="mb-6"
          />
        )}

        {/* Opinions */}
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-900">Opinions</h2>

          {caseData.opinions.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-gray-500">No opinions available for this case.</p>
            </div>
          ) : (
            caseData.opinions.map((opinion) => (
              <div key={opinion.id} className="bg-white rounded-lg shadow p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">
                      {opinion.type.charAt(0).toUpperCase() + opinion.type.slice(1)} Opinion
                    </h3>
                    {opinion.extracted_by_ocr && (
                      <span className="inline-block px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded">
                        Extracted by OCR
                      </span>
                    )}
                  </div>
                  <Link
                    to={`/citations/analytics/${opinion.id}`}
                    className="text-blue-600 hover:text-blue-700 text-sm"
                  >
                    View Analytics →
                  </Link>
                </div>

                <OpinionText
                  opinionId={opinion.id}
                  plainText={opinion.plain_text}
                  html={opinion.html}
                />
              </div>
            ))
          )}
        </div>

        {/* Quick Links */}
        {caseData.opinions.length > 0 && (
          <div className="mt-8 bg-blue-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Explore This Case</h3>
            <div className="flex flex-wrap gap-4">
              <Link
                to={`/citations/network/${caseData.opinions[0].id}`}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                Citation Network
              </Link>
              <Link
                to={`/citations/analytics/${caseData.opinions[0].id}`}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
              >
                Citation Analytics
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

