import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import CytoscapeComponent from 'react-cytoscapejs'
import cytoscape from 'cytoscape'
import { citationAPI, CitationNetwork } from '../lib/api'
import TreatmentBadge from '../components/TreatmentBadge'
import CaseDetailFlyout from '../components/CaseDetailFlyout'
import MethodologyModal from '../components/MethodologyModal'

// Cytoscape stylesheet for citation network
const getCytoscapeStylesheet = (): any[] => [
  {
    selector: 'node',
    style: {
      'background-color': '#3b82f6',
      'label': 'data(label)',
      'color': '#ffffff',
      'text-valign': 'center',
      'text-halign': 'center',
      'font-size': '12px',
      'font-weight': 'bold',
      'text-wrap': 'wrap',
      'text-max-width': '180px',
      'width': '60px',
      'height': '60px',
      'border-width': '3px',
      'border-color': '#1e293b',
      'text-outline-width': '2px',
      'text-outline-color': '#1e293b',
    } as any,
  },
  {
    selector: 'node[nodeType="center"]',
    style: {
      'background-color': '#3b82f6',
      'width': '80px',
      'height': '80px',
      'border-width': '4px',
      'font-size': '14px',
    } as any,
  },
  {
    selector: 'node[nodeType="outbound"]',
    style: {
      'background-color': '#f59e0b',
    } as any,
  },
  {
    selector: 'node[nodeType="inbound"]',
    style: {
      'background-color': '#10b981',
    } as any,
  },
  {
    selector: 'node[treatment]',
    style: {
      'border-width': '5px',
      'border-color': '#ef4444',
    } as any,
  },
  {
    selector: 'edge',
    style: {
      'width': 4,
      'line-color': '#f59e0b',
      'target-arrow-color': '#f59e0b',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      'arrow-scale': 1.5,
    } as any,
  },
  {
    selector: 'edge[edgeType="inbound"]',
    style: {
      'line-color': '#10b981',
      'target-arrow-color': '#10b981',
    } as any,
  },
  {
    selector: 'node:selected',
    style: {
      'border-width': '6px',
      'border-color': '#2563eb',
    } as any,
  },
  {
    selector: 'edge:selected',
    style: {
      'width': 6,
      'line-color': '#2563eb',
      'target-arrow-color': '#2563eb',
    } as any,
  },
]

export default function CitationNetworkPage() {
  const { opinionId } = useParams<{ opinionId: string }>()
  const [networkData, setNetworkData] = useState<CitationNetwork | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [depth, setDepth] = useState(1)
  const [maxNodes, setMaxNodes] = useState(50)
  const cyRef = useRef<cytoscape.Core | null>(null)

  // Deep analysis state
  const [deepAnalysis, setDeepAnalysis] = useState<any>(null)
  const [showDeepAnalysis, setShowDeepAnalysis] = useState(false)
  const [loadingAnalysis, setLoadingAnalysis] = useState(false)

  // Flyout state
  const [selectedCase, setSelectedCase] = useState<{ clusterId: number; opinionId: number } | null>(null)

  // Methodology modal state
  const [showMethodology, setShowMethodology] = useState(false)

  const fetchNetwork = useCallback(async () => {
    if (!opinionId) return

    try {
      setLoading(true)
      const data = await citationAPI.getNetwork(Number(opinionId), {
        depth,
        max_nodes: maxNodes,
      })
      setNetworkData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load citation network')
    } finally {
      setLoading(false)
    }
  }, [opinionId, depth, maxNodes])

  const fetchDeepAnalysis = useCallback(async () => {
    if (!opinionId || loadingAnalysis) return

    try {
      setLoadingAnalysis(true)
      const analysis = await citationAPI.getDeepAnalysis(Number(opinionId), { depth })
      setDeepAnalysis(analysis)
      setShowDeepAnalysis(true)
    } catch (err) {
      console.error('Failed to load deep analysis:', err)
    } finally {
      setLoadingAnalysis(false)
    }
  }, [opinionId, depth, loadingAnalysis])

  useEffect(() => {
    fetchNetwork()
  }, [fetchNetwork])

  useEffect(() => {
    if (opinionId && !deepAnalysis && !loadingAnalysis) {
      fetchDeepAnalysis()
    }
  }, [opinionId, deepAnalysis, loadingAnalysis, fetchDeepAnalysis])

  // Convert API data to Cytoscape elements
  const getCytoscapeElements = (): cytoscape.ElementDefinition[] => {
    if (!networkData) {
      console.warn('No network data available')
      return []
    }

    console.log('Network data structure:', networkData)

    const elements: cytoscape.ElementDefinition[] = []
    const nodeIds = new Set<string>()

    // Check if nodes exist and is an object
    if (!networkData.nodes || typeof networkData.nodes !== 'object') {
      console.error('Invalid nodes structure:', networkData.nodes)
      return []
    }

    // Add nodes
    Object.entries(networkData.nodes).forEach(([layerKey, nodesArray]) => {
      console.log(`Processing layer ${layerKey}:`, nodesArray)

      if (Array.isArray(nodesArray)) {
        nodesArray.forEach((node) => {
          const nodeType = node.opinion_id === Number(opinionId) ? 'center' : layerKey.startsWith('inbound') ? 'inbound' : 'outbound'
          const nodeIdStr = node.opinion_id.toString()

          nodeIds.add(nodeIdStr)

          elements.push({
            data: {
              id: nodeIdStr,
              label: node.case_name_short || node.case_name || 'Unknown Case',
              nodeType,
              treatment: node.treatment?.type || null,
              clusterId: node.cluster_id,
              opinionId: node.opinion_id,
            },
          })
        })
      } else {
        console.warn(`Layer ${layerKey} is not an array:`, nodesArray)
      }
    })

    // Add edges - only if both source and target nodes exist
    if (networkData.edges) {
      networkData.edges.forEach((edge, index) => {
        const sourceStr = edge.source.toString()
        const targetStr = edge.target.toString()

        // Only add edge if both nodes exist
        if (nodeIds.has(sourceStr) && nodeIds.has(targetStr)) {
          elements.push({
            data: {
              id: `edge-${index}`,
              source: sourceStr,
              target: targetStr,
              edgeType: edge.type,
              depth: edge.depth,
            },
          })
        } else {
          console.warn(`Skipping edge ${index}: source=${sourceStr} (exists=${nodeIds.has(sourceStr)}), target=${targetStr} (exists=${nodeIds.has(targetStr)})`)
        }
      })
    }

    console.log(`Created ${nodeIds.size} nodes and ${elements.filter(e => e.data.id?.toString().startsWith('edge-')).length} valid edges`)

    return elements
  }

  const handleNodeClick = (event: cytoscape.EventObject) => {
    const node = event.target
    const data = node.data()

    if (data.clusterId && data.opinionId) {
      setSelectedCase({
        clusterId: data.clusterId,
        opinionId: data.opinionId,
      })
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading citation network...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error || !networkData) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-red-900 mb-2">Error Loading Network</h3>
            <p className="text-red-700">{error || 'Unknown error occurred'}</p>
            <Link to="/search" className="mt-4 inline-block text-blue-600 hover:text-blue-700">
              ← Back to Search
            </Link>
          </div>
        </div>
      </div>
    )
  }

  const totalNodes = Object.values(networkData.nodes).reduce((sum, layer) => sum + (Array.isArray(layer) ? layer.length : 0), 0)
  const totalEdges = networkData.edges?.length || 0

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <Link to="/search" className="text-blue-600 hover:text-blue-700 mb-4 inline-block">
            ← Back to Search
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Citation Network</h1>
          <p className="text-gray-600 mt-2">
            Showing {totalNodes} cases and {totalEdges} citation relationships
          </p>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex flex-wrap items-center gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Depth Level</label>
              <select
                value={depth}
                onChange={(e) => setDepth(Number(e.target.value))}
                className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500"
              >
                <option value={1}>1 Level</option>
                <option value={2}>2 Levels</option>
                <option value={3}>3 Levels</option>
                <option value={4}>4 Levels</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Max Nodes</label>
              <select
                value={maxNodes}
                onChange={(e) => setMaxNodes(Number(e.target.value))}
                className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500"
              >
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
                <option value={200}>200</option>
              </select>
            </div>
            <button
              onClick={fetchNetwork}
              className="mt-6 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
            >
              Refresh
            </button>
            <button
              onClick={fetchDeepAnalysis}
              disabled={loadingAnalysis}
              className="mt-6 bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition disabled:opacity-50"
            >
              {loadingAnalysis ? 'Analyzing...' : 'Risk Analysis'}
            </button>
          </div>

          {/* Risk Assessment */}
          {deepAnalysis && (
            <div className="mt-6 pt-6 border-t">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Citation Risk:</span>
                <TreatmentBadge
                  treatment={{
                    type: deepAnalysis.risk_assessment.level,
                    severity: deepAnalysis.risk_assessment.level.toLowerCase(),
                    confidence: deepAnalysis.risk_assessment.score / 100,
                  }}
                  size="md"
                  showConfidence={true}
                />
                <span className="text-sm text-gray-600">
                  {deepAnalysis.negative_treatment_count} of {deepAnalysis.total_cases_analyzed} cases have negative treatment
                </span>
                <span className="text-sm text-gray-600">
                  Score: {deepAnalysis.risk_assessment.score}/100
                </span>
                <button
                  onClick={() => setShowMethodology(true)}
                  className="text-sm text-gray-500 hover:text-gray-700 underline"
                  title="Learn about our risk scoring methodology"
                >
                  More Info
                </button>
                <button
                  onClick={() => setShowDeepAnalysis(!showDeepAnalysis)}
                  className="ml-auto text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  {showDeepAnalysis ? 'Hide Details' : 'Show Details'}
                </button>
              </div>
            </div>
          )}

          {/* Legend */}
          <div className="mt-4 pt-4 border-t flex flex-wrap gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ background: '#3b82f6' }}></div>
              <span>Center Case</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ background: '#f59e0b' }}></div>
              <span>Cases Cited (Outbound)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ background: '#10b981' }}></div>
              <span>Cases Citing (Inbound)</span>
            </div>
          </div>
        </div>

        {/* Network Graph */}
        <div className="bg-white rounded-lg shadow" style={{ height: '600px' }}>
          <CytoscapeComponent
            elements={getCytoscapeElements()}
            style={{ width: '100%', height: '100%' }}
            stylesheet={getCytoscapeStylesheet()}
            layout={{
              name: 'cose',
              animate: true,
              animationDuration: 500,
              nodeRepulsion: 8000,
              idealEdgeLength: 100,
              edgeElasticity: 100,
              nestingFactor: 1.2,
              gravity: 1,
              numIter: 1000,
              initialTemp: 200,
              coolingFactor: 0.95,
              minTemp: 1.0,
            }}
            cy={(cy: cytoscape.Core) => {
              cyRef.current = cy
              cy.on('tap', 'node', handleNodeClick)
              cy.on('layoutstop', () => {
                cy.fit(undefined, 50)
              })
            }}
          />
        </div>

        {/* Deep Analysis Details */}
        {showDeepAnalysis && deepAnalysis && (
          <div className="mt-6 bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Deep Citation Risk Analysis</h2>

            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Cases Analyzed</p>
                <p className="text-2xl font-bold text-gray-900">{deepAnalysis.total_cases_analyzed}</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Depth</p>
                <p className="text-2xl font-bold text-gray-900">{deepAnalysis.analysis_depth} Levels</p>
              </div>
              <div className="bg-red-50 p-4 rounded-lg">
                <p className="text-sm text-red-600 mb-1">Negative Treatments</p>
                <p className="text-2xl font-bold text-red-900">{deepAnalysis.negative_treatment_count}</p>
              </div>
              <div
                className={`p-4 rounded-lg ${
                  deepAnalysis.risk_assessment.level === 'HIGH'
                    ? 'bg-red-50'
                    : deepAnalysis.risk_assessment.level === 'MEDIUM'
                    ? 'bg-yellow-50'
                    : 'bg-green-50'
                }`}
              >
                <p
                  className={`text-sm mb-1 ${
                    deepAnalysis.risk_assessment.level === 'HIGH'
                      ? 'text-red-600'
                      : deepAnalysis.risk_assessment.level === 'MEDIUM'
                      ? 'text-yellow-600'
                      : 'text-green-600'
                  }`}
                >
                  Risk Score
                </p>
                <p
                  className={`text-2xl font-bold ${
                    deepAnalysis.risk_assessment.level === 'HIGH'
                      ? 'text-red-900'
                      : deepAnalysis.risk_assessment.level === 'MEDIUM'
                      ? 'text-yellow-900'
                      : 'text-green-900'
                  }`}
                >
                  {deepAnalysis.risk_assessment.score}/100
                </p>
              </div>
            </div>

            {/* Risk Assessment Details */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Risk Assessment</h3>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-gray-700 mb-2">
                  <span className="font-semibold">Level:</span> {deepAnalysis.risk_assessment.level}
                </p>
                <p className="text-gray-700 mb-2">
                  <span className="font-semibold">Confidence:</span> {(deepAnalysis.risk_assessment.confidence * 100).toFixed(1)}%
                </p>
                <p className="text-gray-700">
                  <span className="font-semibold">Factors:</span>
                </p>
                <ul className="list-disc list-inside ml-4 mt-2 text-gray-600">
                  {deepAnalysis.risk_assessment.factors.map((factor: string, idx: number) => (
                    <li key={idx}>{factor}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* High Risk Cases */}
            {deepAnalysis.high_risk_cases && deepAnalysis.high_risk_cases.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">High Risk Cases in Network</h3>
                <div className="space-y-3">
                  {deepAnalysis.high_risk_cases.map((riskCase: any, idx: number) => (
                    <div key={idx} className="border border-red-200 bg-red-50 rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-900 mb-1">{riskCase.case_name}</h4>
                          <p className="text-sm text-gray-600 mb-2">
                            Opinion ID: {riskCase.opinion_id} | Depth: {riskCase.depth}
                          </p>
                          <TreatmentBadge
                            treatment={{
                              type: riskCase.treatment_type,
                              severity: riskCase.severity,
                              confidence: 0.9,
                            }}
                            size="sm"
                            showIcon={true}
                          />
                        </div>
                        <button
                          onClick={() =>
                            setSelectedCase({
                              clusterId: riskCase.cluster_id,
                              opinionId: riskCase.opinion_id,
                            })
                          }
                          className="ml-4 text-blue-600 hover:text-blue-700 text-sm font-medium"
                        >
                          View Details →
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Case Detail Flyout */}
      {selectedCase && (
        <CaseDetailFlyout
          isOpen={true}
          clusterId={selectedCase.clusterId}
          opinionId={selectedCase.opinionId}
          onClose={() => setSelectedCase(null)}
        />
      )}

      {/* Methodology Modal */}
      <MethodologyModal isOpen={showMethodology} onClose={() => setShowMethodology(false)} />
    </div>
  )
}
