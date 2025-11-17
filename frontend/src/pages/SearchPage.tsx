import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { searchAPI, CaseResult, citationAPI } from '../lib/api'

// Component to display risk score for a case
function RiskScoreBadge({ clusterId }: { clusterId: number }) {
  const [riskData, setRiskData] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const fetchRisk = async () => {
      setLoading(true)
      try {
        // First get the case details to find the opinion ID
        const caseDetail = await searchAPI.getCaseDetail(clusterId)

        if (caseDetail.opinions && caseDetail.opinions.length > 0) {
          const opinionId = caseDetail.opinions[0].id
          const analysis = await citationAPI.getDeepAnalysis(opinionId, { depth: 2 })
          setRiskData(analysis.risk_assessment)
        }
      } catch (err) {
        console.error('Failed to fetch risk score:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchRisk()
  }, [clusterId])

  if (loading) {
    return <span className="text-xs text-gray-500">Analyzing...</span>
  }

  if (!riskData) {
    return null
  }

  const levelColors = {
    'HIGH': 'bg-red-100 text-red-800 border-red-200',
    'MEDIUM': 'bg-yellow-100 text-yellow-800 border-yellow-200',
    'LOW': 'bg-green-100 text-green-800 border-green-200'
  }

  const levelEmoji = {
    'HIGH': '🔴',
    'MEDIUM': '🟡',
    'LOW': '🟢'
  }

  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded border text-xs font-semibold ${levelColors[riskData.level as keyof typeof levelColors]}`}>
      <span>{levelEmoji[riskData.level as keyof typeof levelEmoji]}</span>
      <span>Citation Risk: {riskData.level}</span>
      <span className="font-mono">({riskData.score}/100)</span>
    </div>
  )
}

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<CaseResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [totalCount, setTotalCount] = useState(0)
  const [hasSearched, setHasSearched] = useState(false)
  const [showRiskScores, setShowRiskScores] = useState(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()

    if (query.length < 3) {
      setError('Please enter at least 3 characters')
      return
    }

    setLoading(true)
    setError(null)
    setHasSearched(true)

    try {
      const response = await searchAPI.searchCases({
        q: query,
        sort: 'date',
        limit: 20,
      })

      setResults(response.results)
      setTotalCount(response.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <Link to="/" className="text-blue-600 hover:text-blue-700">
            ← Back to Home
          </Link>
        </div>

        <h1 className="text-3xl font-bold mb-6">Search Case Law</h1>

        <form onSubmit={handleSearch} className="bg-white p-6 rounded-lg shadow mb-6">
          <div className="flex gap-4">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search case law... (e.g., Anderson, Brown)"
              className="flex-1 px-4 py-2 border rounded-lg text-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || query.length < 3}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
          {error && (
            <p className="mt-2 text-red-600 text-sm">{error}</p>
          )}
        </form>

        {hasSearched && !loading && (
          <div className="mb-4 flex items-center justify-between">
            <p className="text-gray-600">
              {totalCount === 0 ? 'No results found' : `Found ${totalCount} cases`}
            </p>
            {results.length > 0 && (
              <button
                onClick={() => setShowRiskScores(!showRiskScores)}
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  showRiskScores
                    ? 'bg-purple-600 text-white hover:bg-purple-700'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {showRiskScores ? 'Hide Risk Scores' : 'Show Risk Scores'}
              </button>
            )}
          </div>
        )}

        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Searching...</p>
          </div>
        )}

        <div className="space-y-4">
          {results.map((result) => (
            <div key={result.id} className="bg-white p-6 rounded-lg shadow hover:shadow-md transition">
              <Link
                to={`/case/${result.id}`}
                className="block"
              >
                <div className="flex items-start justify-between gap-4 mb-2">
                  <h2 className="text-xl font-bold text-blue-600 hover:text-blue-700 flex-1">
                    {result.case_name}
                  </h2>
                  {showRiskScores && result.opinion_count > 0 && (
                    <RiskScoreBadge clusterId={result.id} />
                  )}
                </div>
                <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                  <span>
                    <strong>Court:</strong> {result.court.full_name || result.court.name}
                  </span>
                  {result.date_filed && (
                    <span>
                      <strong>Filed:</strong> {new Date(result.date_filed).toLocaleDateString()}
                    </span>
                  )}
                  <span>
                    <strong>Citations:</strong> {result.citation_count}
                  </span>
                  {result.opinion_count > 0 && (
                    <span className="text-green-600">
                      <strong>Opinions:</strong> {result.opinion_count}
                    </span>
                  )}
                  {result.precedential_status && (
                    <span>
                      <strong>Status:</strong> {result.precedential_status}
                    </span>
                  )}
                </div>
              </Link>
            </div>
          ))}
        </div>

        {!hasSearched && !loading && (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg">Enter a search query to find cases</p>
            <p className="mt-2">Try searching for "Anderson" or "Brown"</p>
          </div>
        )}
      </div>
    </div>
  )
}
