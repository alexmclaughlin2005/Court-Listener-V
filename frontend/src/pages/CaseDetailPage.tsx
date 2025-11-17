import { useParams } from 'react-router-dom'

export default function CaseDetailPage() {
  const { caseId } = useParams()
  
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Case Details</h1>
        <div className="bg-white p-6 rounded-lg shadow">
          <p>Case ID: {caseId}</p>
          <p className="text-gray-500 mt-4">Case detail page coming soon...</p>
        </div>
      </div>
    </div>
  )
}

