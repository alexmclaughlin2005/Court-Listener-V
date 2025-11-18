import { useState, useEffect, useCallback, memo } from 'react'
import { useParams, Link } from 'react-router-dom'
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
  NodeProps,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { citationAPI, CitationNetwork } from '../lib/api'
import TreatmentBadge from '../components/TreatmentBadge'
import CaseDetailFlyout from '../components/CaseDetailFlyout'
import MethodologyModal from '../components/MethodologyModal'

// Custom node component with treatment badge and depth indicator
const CustomNode = memo(({ data }: NodeProps) => {
  const TREATMENT_ICONS: Record<string, string> = {
    OVERRULED: '⛔',
    REVERSED: '🔴',
    VACATED: '⭕',
    CRITICIZED: '🟠',
    QUESTIONED: '🟡',
    AFFIRMED: '✅',
    FOLLOWED: '🟢',
    DISTINGUISHED: '🔵',
    CITED: '📄',
    UNKNOWN: '❓',
  }

  // Truncate long case names
  const truncateText = (text: string, maxLength: number = 40) => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  const fullCaseName = data.label || ''
  const displayName = truncateText(fullCaseName)

  // Get treatment label for tooltip
  const treatmentLabel = data.treatment
    ? `${data.treatment.type} (${data.treatment.severity})`
    : ''

  // Get depth for display
  const nodeDepth = data.depth || 0

  return (
    <div
      style={{
        padding: '12px',
        borderRadius: '8px',
        minWidth: '180px',
        maxWidth: '220px',
        textAlign: 'center',
        position: 'relative',
        cursor: 'pointer',
        transition: 'transform 0.2s',
      }}
      title={`${fullCaseName}${treatmentLabel ? '\n' + treatmentLabel : ''}${nodeDepth > 0 ? '\nDepth: ' + nodeDepth : ''}`}
    >
      {data.treatment && (
        <div
          style={{
            position: 'absolute',
            top: '-12px',
            right: '-12px',
            fontSize: '24px',
            background: 'white',
            borderRadius: '50%',
            width: '40px',
            height: '40px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 6px rgba(0,0,0,0.4)',
            border: '3px solid #1e293b',
            zIndex: 10,
          }}
          title={treatmentLabel}
        >
          {TREATMENT_ICONS[data.treatment.type] || '❓'}
        </div>
      )}
      {nodeDepth > 0 && (
        <div
          style={{
            position: 'absolute',
            top: '-8px',
            left: '-8px',
            fontSize: '10px',
            fontWeight: 'bold',
            background: '#1e293b',
            color: 'white',
            borderRadius: '50%',
            width: '24px',
            height: '24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
            border: '2px solid white',
            zIndex: 10,
          }}
          title={`Depth: ${nodeDepth} level${nodeDepth > 1 ? 's' : ''} from center`}
        >
          {nodeDepth}
        </div>
      )}
      <div style={{
        fontSize: '11px',
        fontWeight: '600',
        color: 'white',
        lineHeight: '1.3',
        wordWrap: 'break-word',
      }}>
        {displayName}
      </div>
    </div>
  )
})

const nodeTypes = {
  custom: CustomNode,
}

export default function CitationNetworkPage() {
  const { opinionId } = useParams<{ opinionId: string }>()
  const [networkData, setNetworkData] = useState<CitationNetwork | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [depth, setDepth] = useState(1)
  const [maxNodes, setMaxNodes] = useState(50)

  // Deep analysis state
  const [deepAnalysis, setDeepAnalysis] = useState<any>(null)
  const [showDeepAnalysis, setShowDeepAnalysis] = useState(false)
  const [loadingAnalysis, setLoadingAnalysis] = useState(false)

  // Flyout state
  const [selectedCase, setSelectedCase] = useState<{ clusterId: number; opinionId: number } | null>(null)
  const [isFlyoutOpen, setIsFlyoutOpen] = useState(false)

  // Methodology modal state
  const [showMethodology, setShowMethodology] = useState(false)

  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  // Handle node click
  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    const nodeData = node.data
    setSelectedCase({
      clusterId: nodeData.cluster_id,
      opinionId: nodeData.opinion_id
    })
    setIsFlyoutOpen(true)
  }, [])

  // Handle flyout close
  const handleCloseFlyout = useCallback(() => {
    setIsFlyoutOpen(false)
    // Keep selectedCase for a moment to allow smooth closing animation
    setTimeout(() => setSelectedCase(null), 300)
  }, [])

  // Fetch deep analysis
  const fetchDeepAnalysis = useCallback(async () => {
    if (!opinionId) return

    setLoadingAnalysis(true)
    try {
      const analysis = await citationAPI.getDeepAnalysis(parseInt(opinionId), { depth: 4 })
      setDeepAnalysis(analysis)
      // Automatically show details if there are warnings
      if (analysis.negative_treatment_count > 0) {
        setShowDeepAnalysis(true)
      }
    } catch (err) {
      console.error('Failed to fetch deep analysis:', err)
    } finally {
      setLoadingAnalysis(false)
    }
  }, [opinionId])

  const fetchNetwork = useCallback(async () => {
    if (!opinionId) return

    setLoading(true)
    setError(null)

    try {
      const data = await citationAPI.getNetwork(parseInt(opinionId), {
        depth,
        max_nodes: maxNodes,
      })
      setNetworkData(data)

      // Helper function to get node color based on treatment
      const getNodeColor = (nodeData: typeof data.nodes[0]): string => {
        // Center node is always blue
        if (nodeData.node_type === 'center') {
          return '#3b82f6' // blue
        }

        // If node has treatment data, color based on severity
        if (nodeData.treatment) {
          switch (nodeData.treatment.severity) {
            case 'NEGATIVE':
              return '#ef4444' // red
            case 'POSITIVE':
              return '#10b981' // green
            case 'NEUTRAL':
              return '#6b7280' // gray
            default:
              return nodeData.node_type === 'citing' ? '#10b981' : '#f59e0b'
          }
        }

        // Default colors based on node type
        return nodeData.node_type === 'citing' ? '#10b981' : '#f59e0b'
      }

      // Check if we have valid data
      if (!data.nodes || data.nodes.length === 0) {
        setError('No citation network data available for this opinion')
        setLoading(false)
        return
      }

      // Calculate depth for each node from edges
      const nodeDepths = new Map<number, number>()
      nodeDepths.set(data.center_opinion_id, 0)

      // Build adjacency map from edges
      const adjacencyMap = new Map<number, Array<{ node: number; depth: number }>>()
      data.edges.forEach(edge => {
        if (edge.source === data.center_opinion_id) {
          // Outbound: target is at depth 1+
          if (!adjacencyMap.has(edge.source)) adjacencyMap.set(edge.source, [])
          adjacencyMap.get(edge.source)!.push({ node: edge.target, depth: edge.depth || 1 })
        } else if (edge.target === data.center_opinion_id) {
          // Inbound: source is at depth 1+
          if (!adjacencyMap.has(edge.target)) adjacencyMap.set(edge.target, [])
          adjacencyMap.get(edge.target)!.push({ node: edge.source, depth: edge.depth || 1 })
        }
      })

      // BFS to assign depths
      const queue = [data.center_opinion_id]
      const visited = new Set([data.center_opinion_id])

      while (queue.length > 0) {
        const current = queue.shift()!
        const neighbors = adjacencyMap.get(current) || []

        neighbors.forEach(({ node, depth }) => {
          if (!visited.has(node)) {
            visited.add(node)
            nodeDepths.set(node, depth)
            queue.push(node)
          }
        })
      }

      // Group nodes by depth for layout
      const nodesByDepth = new Map<number, typeof data.nodes>()
      data.nodes.forEach(node => {
        const depth = nodeDepths.get(node.opinion_id) || 0
        if (!nodesByDepth.has(depth)) nodesByDepth.set(depth, [])
        nodesByDepth.get(depth)!.push(node)
      })

      // Convert API data to React Flow format with depth-based layout
      const flowNodes: Node[] = []

      nodesByDepth.forEach((nodesAtDepth, depthLevel) => {
        const nodesCount = nodesAtDepth.length
        const layerRadius = depthLevel === 0 ? 0 : 200 + (depthLevel * 250)

        nodesAtDepth.forEach((node, indexInDepth) => {
          // Calculate position based on depth level
          let x = 0, y = 0

          if (depthLevel === 0) {
            // Center node at origin
            x = 0
            y = 0
          } else {
            // Arrange in circular layout at this depth
            const angle = (indexInDepth / nodesCount) * 2 * Math.PI - Math.PI / 2
            x = layerRadius * Math.cos(angle)
            y = layerRadius * Math.sin(angle)
          }

          const nodeColor = getNodeColor(node)
          const nodeDepth = nodeDepths.get(node.opinion_id) || 0

          flowNodes.push({
            id: node.opinion_id.toString(),
            type: 'custom',
            data: {
              label: node.case_name_short || node.case_name || 'Unknown Case',
              ...node,
              depth: nodeDepth,
            },
            position: { x, y },
            style: {
              background: nodeColor,
              color: 'white',
              border: node.treatment ? '3px solid #1e293b' : '2px solid #1e293b',
              borderRadius: '8px',
              boxShadow: node.treatment ? '0 4px 6px -1px rgba(0, 0, 0, 0.3)' : undefined,
            },
          })
        })
      })

      const flowEdges: Edge[] = (data.edges || []).map((edge, index) => ({
        id: `edge-${index}`,
        source: edge.source.toString(),
        target: edge.target.toString(),
        type: 'straight',
        animated: false,
        label: edge.depth > 1 ? `D${edge.depth}` : undefined,
        labelStyle: { fontSize: 11, fill: '#374151', fontWeight: 600 },
        labelBgStyle: { fill: 'white', fillOpacity: 0.8 },
        style: {
          stroke: edge.type === 'inbound' ? '#10b981' : '#f59e0b',
          strokeWidth: 4,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: edge.type === 'inbound' ? '#10b981' : '#f59e0b',
          width: 25,
          height: 25,
        },
        zIndex: 1,
      }))

      console.log(`Created ${flowEdges.length} edges:`, flowEdges)
      console.log(`Created ${flowNodes.length} nodes`)

      setNodes(flowNodes)
      setEdges(flowEdges)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load citation network')
    } finally {
      setLoading(false)
    }
  }, [opinionId, depth, maxNodes, setNodes, setEdges])

  useEffect(() => {
    fetchNetwork()
  }, [fetchNetwork])

  // Automatically fetch deep analysis when page loads
  useEffect(() => {
    if (opinionId && !deepAnalysis && !loadingAnalysis) {
      fetchDeepAnalysis()
    }
  }, [opinionId, deepAnalysis, loadingAnalysis, fetchDeepAnalysis])

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
          <div className="mb-8">
            <Link to="/search" className="text-blue-600 hover:text-blue-700">
              ← Back to Search
            </Link>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <p className="text-red-800">{error || 'Citation network not found'}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <Link to="/search" className="text-blue-600 hover:text-blue-700 mb-4 inline-block">
            ← Back to Search
          </Link>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Citation Network</h1>
          <p className="text-gray-600">
            Showing {networkData.node_count} cases and {networkData.edge_count} citation relationships
          </p>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex flex-wrap gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Depth Level
              </label>
              <select
                value={depth}
                onChange={(e) => setDepth(parseInt(e.target.value))}
                className="px-3 py-2 border rounded-lg"
              >
                <option value="1">1 Level</option>
                <option value="2">2 Levels</option>
                <option value="3">3 Levels</option>
                <option value="4">4 Levels</option>
                <option value="5">5 Levels</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Nodes
              </label>
              <select
                value={maxNodes}
                onChange={(e) => setMaxNodes(parseInt(e.target.value))}
                className="px-3 py-2 border rounded-lg"
              >
                <option value="25">25</option>
                <option value="50">50</option>
                <option value="100">100</option>
                <option value="200">200</option>
              </select>
            </div>

            <div className="flex items-end gap-3">
              <button
                onClick={fetchNetwork}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                Refresh
              </button>
              <button
                onClick={fetchDeepAnalysis}
                disabled={loadingAnalysis}
                className={`px-4 py-2 rounded-lg transition font-medium ${
                  loadingAnalysis
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-purple-600 text-white hover:bg-purple-700'
                }`}
              >
                {loadingAnalysis ? 'Analyzing...' : 'Risk Analysis'}
              </button>
            </div>
          </div>

          {/* Risk Analysis Badge */}
          {deepAnalysis && (
            <div className="mt-4 pt-4 border-t">
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-gray-700">Citation Risk:</span>
                <div className={`px-3 py-1 rounded-full text-sm font-semibold ${
                  deepAnalysis.risk_assessment.level === 'HIGH'
                    ? 'bg-red-100 text-red-800'
                    : deepAnalysis.risk_assessment.level === 'MEDIUM'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-green-100 text-green-800'
                }`}>
                  {deepAnalysis.risk_assessment.level} RISK ({deepAnalysis.risk_assessment.score}/100)
                </div>
                <span className="text-sm text-gray-600">
                  {deepAnalysis.negative_treatment_count} of {deepAnalysis.total_cases_analyzed} cases have negative treatment
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
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            fitView
            attributionPosition="bottom-right"
            elevateEdgesOnSelect={false}
            defaultEdgeOptions={{
              style: { strokeWidth: 4 },
              zIndex: 10,
            }}
          >
            <Controls />
            <Background color="#93c5fd" gap={16} />
          </ReactFlow>
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
              <div className={`p-4 rounded-lg ${
                deepAnalysis.risk_assessment.level === 'HIGH' ? 'bg-red-50' :
                deepAnalysis.risk_assessment.level === 'MEDIUM' ? 'bg-yellow-50' :
                'bg-green-50'
              }`}>
                <p className={`text-sm mb-1 ${
                  deepAnalysis.risk_assessment.level === 'HIGH' ? 'text-red-600' :
                  deepAnalysis.risk_assessment.level === 'MEDIUM' ? 'text-yellow-600' :
                  'text-green-600'
                }`}>Risk Score</p>
                <p className={`text-2xl font-bold ${
                  deepAnalysis.risk_assessment.level === 'HIGH' ? 'text-red-900' :
                  deepAnalysis.risk_assessment.level === 'MEDIUM' ? 'text-yellow-900' :
                  'text-green-900'
                }`}>{deepAnalysis.risk_assessment.score}/100</p>
              </div>
            </div>

            {/* Treatment Warnings */}
            {deepAnalysis.treatment_warnings.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Treatment Warnings</h3>
                <div className="space-y-2">
                  {deepAnalysis.treatment_warnings.map((warning: any, index: number) => (
                    <div key={index} className="flex items-start gap-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                      <span className="text-2xl">⚠️</span>
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">{warning.case_name}</p>
                        <p className="text-sm text-gray-600 mt-1">
                          <span className="font-semibold text-red-700">{warning.treatment_type}</span>
                          {' • '}Depth: {warning.depth}
                          {' • '}Confidence: {Math.round((warning.confidence || 0) * 100)}%
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Warnings by Type */}
            {Object.keys(deepAnalysis.warnings_by_type).length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Warnings by Treatment Type</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(deepAnalysis.warnings_by_type).map(([type, warnings]: [string, any]) => (
                    <div key={type} className="bg-gray-50 p-4 rounded-lg border">
                      <p className="font-semibold text-gray-900 mb-2">{type}</p>
                      <p className="text-2xl font-bold text-red-600">{warnings.length}</p>
                      <p className="text-sm text-gray-600 mt-1">cases affected</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Problematic Citation Chains */}
            {deepAnalysis.problematic_citation_chains.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Problematic Citation Chains</h3>
                <div className="space-y-3">
                  {deepAnalysis.problematic_citation_chains.slice(0, 5).map((chain: any, index: number) => (
                    <div key={index} className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-sm font-semibold text-gray-700">Chain Length:</span>
                        <span className="text-sm text-gray-600">{chain.chain_length} cases</span>
                      </div>
                      <div className="text-sm text-gray-700">
                        <p className="mb-1">
                          <span className="font-medium">Starts at:</span> {chain.start_case?.case_name_short || chain.start_case?.case_name || 'Unknown'}
                        </p>
                        <p>
                          <span className="font-medium text-red-700">Problem:</span> {chain.problem_case?.case_name_short || chain.problem_case?.case_name || 'Unknown'}
                          {chain.problem_case?.treatment && (
                            <span className="ml-2 px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-semibold">
                              {chain.problem_case.treatment.type}
                            </span>
                          )}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Node Details */}
        <div className="mt-6 bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Cases in Network</h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {networkData.nodes.map((node) => (
              <div
                key={node.opinion_id}
                className="flex justify-between items-center p-3 border rounded hover:bg-gray-50 cursor-pointer transition"
                onClick={() => {
                  setSelectedCase({
                    clusterId: node.cluster_id,
                    opinionId: node.opinion_id
                  })
                  setIsFlyoutOpen(true)
                }}
              >
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{node.case_name_short || node.case_name}</p>
                  <p className="text-sm text-gray-600">
                    {node.court_name} • {node.date_filed ? new Date(node.date_filed).getFullYear() : 'N/A'} • {node.citation_count} citations
                  </p>
                </div>
                <div className="flex gap-2 items-center">
                  {node.treatment && (
                    <TreatmentBadge
                      treatment={node.treatment}
                      size="sm"
                      showConfidence={false}
                      showIcon={true}
                    />
                  )}
                  <span
                    className="px-2 py-1 text-xs rounded"
                    style={{
                      background: node.node_type === 'center'
                        ? '#3b82f6'
                        : node.node_type === 'citing'
                        ? '#10b981'
                        : '#f59e0b',
                      color: 'white',
                    }}
                  >
                    {node.node_type}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      setSelectedCase({
                        clusterId: node.cluster_id,
                        opinionId: node.opinion_id
                      })
                      setIsFlyoutOpen(true)
                    }}
                    className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                  >
                    Quick View
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Case Detail Flyout */}
      {selectedCase && (
        <CaseDetailFlyout
          clusterId={selectedCase.clusterId}
          opinionId={selectedCase.opinionId}
          isOpen={isFlyoutOpen}
          onClose={handleCloseFlyout}
        />
      )}

      {/* Methodology Modal */}
      <MethodologyModal
        isOpen={showMethodology}
        onClose={() => setShowMethodology(false)}
      />
    </div>
  )
}
