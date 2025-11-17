import { memo } from 'react'

interface MethodologyModalProps {
  isOpen: boolean
  onClose: () => void
}

const MethodologyModal = memo(({ isOpen, onClose }: MethodologyModalProps) => {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Risk Scoring Methodology</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-6 space-y-6">
          {/* Overview */}
          <section>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">Overview</h3>
            <p className="text-gray-700 leading-relaxed">
              Our citation risk analysis evaluates the reliability of legal precedent by examining
              citation chains up to 4-5 levels deep. The system identifies cases that rely on other
              cases which have been negatively treated by subsequent courts.
            </p>
          </section>

          {/* Risk Score Calculation */}
          <section>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">Risk Score Calculation</h3>
            <p className="text-gray-700 mb-3">
              The risk score (0-100) is calculated using two key factors:
            </p>
            <div className="bg-gray-50 p-4 rounded-lg space-y-3">
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">1. Negative Treatment Percentage (50% weight)</h4>
                <p className="text-gray-700 text-sm">
                  Percentage of cited cases with negative treatment × 0.5
                </p>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">2. Depth-Weighted Risk (50% weight)</h4>
                <p className="text-gray-700 text-sm mb-2">
                  Citations closer to the source case are weighted more heavily than distant citations:
                </p>
                <ul className="text-sm text-gray-700 space-y-1 ml-4">
                  <li>• Depth 1 (direct citations): Full weight (1.0x)</li>
                  <li>• Depth 2: Half weight (0.5x)</li>
                  <li>• Depth 3: Third weight (0.33x)</li>
                  <li>• Depth 4+: Quarter weight (0.25x)</li>
                </ul>
              </div>
              <div className="mt-3 pt-3 border-t border-gray-300">
                <p className="text-xs font-mono text-gray-600">
                  risk_score = min((negative_percentage × 0.5) + (depth_weighted_risk × 10), 100)
                </p>
              </div>
            </div>
          </section>

          {/* Risk Levels */}
          <section>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">Risk Levels</h3>
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-20 h-10 bg-green-100 border-2 border-green-200 rounded flex items-center justify-center">
                  <span className="text-green-800 font-bold text-sm">LOW</span>
                </div>
                <div>
                  <p className="font-semibold text-gray-900">0-39 points</p>
                  <p className="text-sm text-gray-700">
                    Minimal citation risk. Few or no negatively treated cases in citation chain.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-20 h-10 bg-yellow-100 border-2 border-yellow-200 rounded flex items-center justify-center">
                  <span className="text-yellow-800 font-bold text-sm">MEDIUM</span>
                </div>
                <div>
                  <p className="font-semibold text-gray-900">40-70 points</p>
                  <p className="text-sm text-gray-700">
                    Moderate citation risk. Some negatively treated cases present, especially at greater depth.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-20 h-10 bg-red-100 border-2 border-red-200 rounded flex items-center justify-center">
                  <span className="text-red-800 font-bold text-sm">HIGH</span>
                </div>
                <div>
                  <p className="font-semibold text-gray-900">71-100 points</p>
                  <p className="text-sm text-gray-700">
                    Significant citation risk. Multiple negatively treated cases, particularly at shallow depth.
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* Treatment Types */}
          <section>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">Treatment Types & Severity</h3>
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold text-red-700 mb-2">Negative Treatment</h4>
                <ul className="space-y-1 text-sm text-gray-700">
                  <li>• <strong>OVERRULED:</strong> Case law has been explicitly overruled</li>
                  <li>• <strong>REVERSED:</strong> Decision was reversed on appeal</li>
                  <li>• <strong>VACATED:</strong> Decision was vacated by higher court</li>
                  <li>• <strong>CRITICIZED:</strong> Case has been criticized by later courts</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold text-gray-700 mb-2">Neutral Treatment</h4>
                <ul className="space-y-1 text-sm text-gray-700">
                  <li>• <strong>QUESTIONED:</strong> Validity has been questioned</li>
                  <li>• <strong>DISTINGUISHED:</strong> Case has been distinguished from others</li>
                  <li>• <strong>CITED:</strong> Case was cited (neutral treatment)</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold text-green-700 mb-2">Positive Treatment</h4>
                <ul className="space-y-1 text-sm text-gray-700">
                  <li>• <strong>AFFIRMED:</strong> Decision was affirmed on appeal</li>
                  <li>• <strong>FOLLOWED:</strong> Case precedent has been followed</li>
                </ul>
              </div>
            </div>
          </section>

          {/* Confidence Scores */}
          <section>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">Confidence Scores</h3>
            <p className="text-gray-700 leading-relaxed">
              Each treatment analysis includes a confidence score (0.0-1.0) indicating the reliability
              of the treatment classification. Higher confidence scores are weighted more heavily in
              the risk calculation.
            </p>
          </section>

          {/* Caching */}
          <section>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">Performance & Caching</h3>
            <p className="text-gray-700 leading-relaxed">
              Analysis results are cached for 7 days to improve performance on repeat visits. The system
              automatically invalidates cached results after this period to ensure data freshness as new
              case treatments may emerge.
            </p>
          </section>

          {/* Limitations */}
          <section>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">Limitations</h3>
            <ul className="space-y-2 text-gray-700 text-sm">
              <li>• Analysis is limited to available treatment data in the database</li>
              <li>• Very recent cases may not have comprehensive treatment history</li>
              <li>• Risk scores should be considered alongside manual legal research</li>
              <li>• Treatment classifications rely on automated and manual annotation</li>
            </ul>
          </section>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-50 border-t px-6 py-4">
          <button
            onClick={onClose}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
})

MethodologyModal.displayName = 'MethodologyModal'

export default MethodologyModal
