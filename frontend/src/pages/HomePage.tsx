import { Link } from 'react-router-dom'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            CourtListener Case Law Browser
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Search 10M+ legal opinions and explore citation networks
          </p>
          <Link
            to="/search"
            className="inline-block bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
          >
            Start Searching
          </Link>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8 mt-16">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-2xl font-bold mb-3">Search Cases</h2>
            <p className="text-gray-600">
              Full-text search across millions of legal opinions from all US courts
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-2xl font-bold mb-3">Citation Networks</h2>
            <p className="text-gray-600">
              Visualize how cases cite each other and explore citation relationships
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-2xl font-bold mb-3">Analytics</h2>
            <p className="text-gray-600">
              Analyze citation patterns, find most cited cases, and track precedential authority
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

