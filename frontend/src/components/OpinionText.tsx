import { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'https://court-listener-v-production.up.railway.app'

interface OpinionTextProps {
  opinionId: number
  plainText?: string | null
  html?: string | null
}

interface OpinionTextResponse {
  opinion_id: number
  plain_text: string | null
  html: string | null
  html_with_citations: string | null
  source: string
  cached: boolean
}

export default function OpinionText({ opinionId, plainText, html }: OpinionTextProps) {
  const [text, setText] = useState<{ plain_text: string | null; html: string | null }>({
    plain_text: plainText || null,
    html: html || null,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fetchedFromAPI, setFetchedFromAPI] = useState(false)

  // If we don't have text, fetch it from the API
  useEffect(() => {
    const fetchOpinionText = async () => {
      // Skip if we already have text
      if (text.plain_text || text.html) {
        return
      }

      setLoading(true)
      setError(null)

      try {
        const response = await fetch(`${API_URL}/api/v1/opinions/${opinionId}/text`)

        if (!response.ok) {
          throw new Error(`Failed to fetch opinion text: ${response.statusText}`)
        }

        const data: OpinionTextResponse = await response.json()

        setText({
          plain_text: data.plain_text,
          html: data.html,
        })

        if (data.source === 'courtlistener_api') {
          setFetchedFromAPI(true)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load opinion text')
      } finally {
        setLoading(false)
      }
    }

    fetchOpinionText()
  }, [opinionId, text.plain_text, text.html])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="ml-3 text-gray-600">Loading opinion text...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded p-4">
        <p className="text-yellow-800">⚠️ {error}</p>
        <p className="text-sm text-yellow-700 mt-2">
          This opinion may not be available in CourtListener's public API.
        </p>
      </div>
    )
  }

  if (!text.plain_text && !text.html) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded p-4">
        <p className="text-gray-600 italic">No text available for this opinion.</p>
      </div>
    )
  }

  return (
    <div>
      {fetchedFromAPI && (
        <div className="mb-4 bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-700">
          ℹ️ Opinion text fetched from CourtListener API and cached for future visits
        </div>
      )}

      {text.plain_text ? (
        <div className="prose max-w-none">
          <div className="bg-gray-50 rounded p-4 text-gray-700 whitespace-pre-wrap font-serif leading-relaxed">
            {text.plain_text}
          </div>
        </div>
      ) : text.html ? (
        <div
          className="prose max-w-none"
          dangerouslySetInnerHTML={{ __html: text.html }}
        />
      ) : null}
    </div>
  )
}
