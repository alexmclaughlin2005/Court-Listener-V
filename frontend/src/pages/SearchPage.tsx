import { useState } from 'react'
import { Link } from 'react-router-dom'
import { searchAPI, CaseResult } from '../lib/api'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<CaseResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [totalCount, setTotalCount] = useState(0)
  const [hasSearched, setHasSearched] = useState(false)

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
          <div className="mb-4">
            <p className="text-gray-600">
              {totalCount === 0 ? 'No results found' : `Found ${totalCount} cases`}
            </p>
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
            <Link
              key={result.id}
              to={`/case/${result.id}`}
              className="block bg-white p-6 rounded-lg shadow hover:shadow-md transition"
            >
              <h2 className="text-xl font-bold text-blue-600 hover:text-blue-700 mb-2">
                {result.case_name}
              </h2>
              <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                <span>
                  <strong>Court:</strong> {result.court.name}
                </span>
                {result.date_filed && (
                  <span>
                    <strong>Filed:</strong> {new Date(result.date_filed).toLocaleDateString()}
                  </span>
                )}
                <span>
                  <strong>Citations:</strong> {result.citation_count}
                </span>
                {result.precedential_status && (
                  <span>
                    <strong>Status:</strong> {result.precedential_status}
                  </span>
                )}
              </div>
            </Link>
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
