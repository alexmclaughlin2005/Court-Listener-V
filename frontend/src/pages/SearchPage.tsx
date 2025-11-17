import { useState } from 'react'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Search Cases</h1>
        
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search case law..."
            className="w-full px-4 py-2 border rounded-lg text-lg"
          />
        </div>
        
        <div className="text-center text-gray-500">
          Search functionality coming soon...
        </div>
      </div>
    </div>
  )
}

