import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { citationAPI, CitationNetwork } from '../lib/api'
import TreatmentBadge from '../components/TreatmentBadge'

export default function CitationNetworkPage() {
  const { opinionId } = useParams<{ opinionId: string }>()
  const [networkData, setNetworkData] = useState<CitationNetwork | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [depth, setDepth] = useState(1)
  const [maxNodes, setMaxNodes] = useState(50)

  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

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

      // Convert API data to React Flow format
      const flowNodes: Node[] = data.nodes.map((node, index) => {
        // Calculate position in a circular layout
        const angle = (index / data.nodes.length) * 2 * Math.PI
        const radius = node.node_type === 'center' ? 0 : 300
        const x = radius * Math.cos(angle)
        const y = radius * Math.sin(angle)

        const nodeColor = getNodeColor(node)

        return {
          id: node.opinion_id.toString(),
          data: {
            label: node.case_name_short || node.case_name,
            ...node,
          },
          position: { x, y },
          style: {
            background: nodeColor,
            color: 'white',
            border: node.treatment ? '3px solid #1e293b' : '2px solid #1e293b',
            borderRadius: '8px',
            padding: '10px',
            fontSize: '12px',
            fontWeight: 'bold',
            boxShadow: node.treatment ? '0 4px 6px -1px rgba(0, 0, 0, 0.3)' : undefined,
          },
        }
      })

      const flowEdges: Edge[] = data.edges.map((edge, index) => ({
        id: `edge-${index}`,
        source: edge.source.toString(),
        target: edge.target.toString(),
        type: 'smoothstep',
        animated: true,
        style: {
          stroke: edge.type === 'inbound' ? '#10b981' : '#f59e0b',
          strokeWidth: 2,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: edge.type === 'inbound' ? '#10b981' : '#f59e0b',
        },
      }))

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

            <div className="flex items-end">
              <button
                onClick={fetchNetwork}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                Refresh
              </button>
            </div>
          </div>

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
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            fitView
            attributionPosition="bottom-right"
          >
            <Controls />
            <Background />
          </ReactFlow>
        </div>

        {/* Node Details */}
        <div className="mt-6 bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Cases in Network</h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {networkData.nodes.map((node) => (
              <div
                key={node.opinion_id}
                className="flex justify-between items-center p-3 border rounded hover:bg-gray-50"
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
                  <Link
                    to={`/case/${node.cluster_id}`}
                    className="text-blue-600 hover:text-blue-700 text-sm"
                  >
                    View Case →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
