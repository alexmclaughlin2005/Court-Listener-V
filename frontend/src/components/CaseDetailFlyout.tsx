/**
 * CaseDetailFlyout - Sliding panel showing comprehensive case information
 *
 * Displays:
 * - Full case details (name, court, date, etc.)
 * - Opinion text
 * - Treatment analysis with badges
 * - Citation network (inbound/outbound)
 * - Quick navigation links
 */
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { searchAPI, citationAPI, treatmentAPI, CaseDetail, CitationNode, TreatmentSummary } from '../lib/api';
import TreatmentBadge from './TreatmentBadge';

interface CaseDetailFlyoutProps {
  clusterId: number;
  opinionId: number;
  isOpen: boolean;
  onClose: () => void;
}

export const CaseDetailFlyout: React.FC<CaseDetailFlyoutProps> = ({
  clusterId,
  opinionId,
  isOpen,
  onClose
}) => {
  const [caseDetail, setCaseDetail] = useState<CaseDetail | null>(null);
  const [treatment, setTreatment] = useState<TreatmentSummary | null>(null);
  const [inboundCitations, setInboundCitations] = useState<CitationNode[]>([]);
  const [outboundCitations, setOutboundCitations] = useState<CitationNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'opinion' | 'treatment' | 'citations'>('opinion');
  const [syncingCitations, setSyncingCitations] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  const fetchCaseData = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    setSyncMessage(null);

    try {
      // Fetch all data in parallel
      const [caseData, treatmentData, inbound, outbound, citationStatus] = await Promise.all([
        searchAPI.getCaseDetail(clusterId).catch(() => null),
        treatmentAPI.getTreatment(opinionId).catch(() => null),
        citationAPI.getInbound(opinionId, { depth: 1, limit: 20 }).catch(() => ({ citations: [] })),
        citationAPI.getOutbound(opinionId, { depth: 1, limit: 20 }).catch(() => ({ citations: [] })),
        citationAPI.checkCitationStatus(opinionId).catch(() => null)
      ]);

      setCaseDetail(caseData);
      setTreatment(treatmentData);
      setInboundCitations(inbound.citations || []);
      setOutboundCitations(outbound.citations || []);

      // Check if opinions have no text and need to be fetched
      if (caseData?.opinions && caseData.opinions.length > 0) {
        const hasNoText = caseData.opinions.every(
          op => !op.plain_text && !op.html
        );

        if (hasNoText) {
          // Fetch opinion text from CourtListener API
          await fetchOpinionText(caseData.opinions[0].id);
        }
      }

      // If no citations exist, try to sync from API
      if (citationStatus?.needs_sync && !citationStatus.has_citations) {
        syncCitationsFromAPI();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load case details');
    } finally {
      setLoading(false);
    }
  }, [clusterId, opinionId]);

  useEffect(() => {
    if (isOpen) {
      fetchCaseData();
    }
  }, [isOpen, fetchCaseData]);

  const fetchOpinionText = async (fetchOpinionId: number) => {
    setSyncMessage('Fetching opinion text from CourtListener API...');

    try {
      // Use the opinions API to fetch and cache the text
      const result = await searchAPI.fetchOpinionText(fetchOpinionId);

      if (result.plain_text || result.html || result.html_with_citations) {
        setSyncMessage('✓ Loaded opinion text from CourtListener');

        // Refetch the case to get the updated opinion text
        const updatedCase = await searchAPI.getCaseDetail(clusterId);
        setCaseDetail(updatedCase);

        // Clear message after 3 seconds
        setTimeout(() => setSyncMessage(null), 3000);
      } else {
        setSyncMessage('No opinion text available from CourtListener');
        setTimeout(() => setSyncMessage(null), 5000);
      }
    } catch (err) {
      console.error('Error fetching opinion text:', err);
      setSyncMessage('Failed to fetch opinion text');
      setTimeout(() => setSyncMessage(null), 5000);
    }
  };

  const syncCitationsFromAPI = async () => {
    setSyncingCitations(true);
    setSyncMessage('Fetching citations from CourtListener API...');

    try {
      const result = await citationAPI.syncCitations(opinionId);

      if (result.status === 'success' && result.new_citations > 0) {
        setSyncMessage(`✓ Imported ${result.new_citations} new citations`);

        // Refetch citations to show the newly imported data
        const [inbound, outbound] = await Promise.all([
          citationAPI.getInbound(opinionId, { depth: 1, limit: 20 }).catch(() => ({ citations: [] })),
          citationAPI.getOutbound(opinionId, { depth: 1, limit: 20 }).catch(() => ({ citations: [] }))
        ]);

        setInboundCitations(inbound.citations || []);
        setOutboundCitations(outbound.citations || []);

        // Clear message after 5 seconds
        setTimeout(() => setSyncMessage(null), 5000);
      } else if (result.status === 'no_local_matches') {
        setSyncMessage('Citations found in API but cited cases not in local database');
        setTimeout(() => setSyncMessage(null), 5000);
      } else {
        setSyncMessage(result.message);
        setTimeout(() => setSyncMessage(null), 5000);
      }
    } catch (err) {
      console.error('Error syncing citations:', err);
      setSyncMessage(null);
    } finally {
      setSyncingCitations(false);
    }
  };

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Flyout Panel */}
      <div className="fixed right-0 top-0 h-full w-full md:w-2/3 lg:w-1/2 bg-white shadow-2xl z-50 overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-blue-600 text-white px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-bold">Case Details</h2>
          <button
            onClick={onClose}
            className="text-white hover:text-gray-200 text-2xl font-bold w-8 h-8 flex items-center justify-center"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : error ? (
            <div className="p-6">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800 font-semibold">Error loading case details</p>
                <p className="text-red-600 text-sm mt-1">{error}</p>
              </div>
            </div>
          ) : !caseDetail ? (
            <div className="p-6">
              <p className="text-gray-600">Case details not found</p>
            </div>
          ) : (
            <>
              {/* Case Header Info */}
              <div className="bg-gray-50 border-b px-6 py-4">
                <h3 className="text-lg font-bold text-gray-900 mb-2">
                  {caseDetail.case_name}
                </h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-gray-600">Court:</span>
                    <span className="ml-2 text-gray-900">{caseDetail.court?.full_name || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Date Filed:</span>
                    <span className="ml-2 text-gray-900">
                      {caseDetail.date_filed ? new Date(caseDetail.date_filed).toLocaleDateString() : 'N/A'}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Docket Number:</span>
                    <span className="ml-2 text-gray-900">{caseDetail.docket?.docket_number || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Citation Count:</span>
                    <span className="ml-2 text-gray-900">{caseDetail.citation_count || 0}</span>
                  </div>
                </div>

                {/* Treatment Badge */}
                {treatment && (
                  <div className="mt-3">
                    <TreatmentBadge
                      treatment={treatment}
                      size="md"
                      showConfidence={true}
                      showIcon={true}
                    />
                  </div>
                )}

                {/* Quick Actions */}
                <div className="mt-4 flex gap-2">
                  <Link
                    to={`/case/${clusterId}`}
                    className="text-sm px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
                    target="_blank"
                  >
                    Open Full Page →
                  </Link>
                  <Link
                    to={`/citation-network/${opinionId}`}
                    className="text-sm px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition"
                    target="_blank"
                  >
                    View Network →
                  </Link>
                </div>
              </div>

              {/* Tabs */}
              <div className="border-b">
                <div className="flex px-6">
                  <button
                    onClick={() => setActiveTab('opinion')}
                    className={`px-4 py-3 font-medium text-sm border-b-2 transition ${
                      activeTab === 'opinion'
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    Opinion Text
                  </button>
                  <button
                    onClick={() => setActiveTab('treatment')}
                    className={`px-4 py-3 font-medium text-sm border-b-2 transition ${
                      activeTab === 'treatment'
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    Treatment
                    {treatment && treatment.summary.total && treatment.summary.total > 0 && (
                      <span className="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full">
                        {treatment.summary.total}
                      </span>
                    )}
                  </button>
                  <button
                    onClick={() => setActiveTab('citations')}
                    className={`px-4 py-3 font-medium text-sm border-b-2 transition ${
                      activeTab === 'citations'
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    Citations
                    <span className="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full">
                      {inboundCitations.length + outboundCitations.length}
                    </span>
                  </button>
                </div>
              </div>

              {/* Tab Content */}
              <div className="px-6 py-4">
                {/* Opinion Tab */}
                {activeTab === 'opinion' && (
                  <div>
                    {/* Sync Status Message */}
                    {syncMessage && (
                      <div className={`rounded-lg p-3 text-sm mb-4 ${
                        syncMessage.startsWith('✓')
                          ? 'bg-green-50 text-green-700 border border-green-200'
                          : syncMessage.includes('Fetching')
                          ? 'bg-blue-50 text-blue-700 border border-blue-200'
                          : 'bg-gray-50 text-gray-700 border border-gray-200'
                      }`}>
                        <div className="flex items-center gap-2">
                          {syncMessage.includes('Fetching') && (
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                          )}
                          <span>{syncMessage}</span>
                        </div>
                      </div>
                    )}

                    {caseDetail.opinions.length === 0 ? (
                      <p className="text-gray-600">No opinion text available</p>
                    ) : (
                      <div className="space-y-6">
                        {caseDetail.opinions.map((opinion) => (
                          <div key={opinion.id} className="border-b pb-6 last:border-b-0">
                            <div className="flex items-center justify-between mb-3">
                              <h4 className="font-semibold text-gray-900">
                                {opinion.type === 'Lead Opinion' ? 'Majority Opinion' : opinion.type}
                              </h4>
                            </div>
                            <div className="prose prose-sm max-w-none">
                              {opinion.html_with_citations ? (
                                <div
                                  className="text-gray-700"
                                  style={{ fontFamily: 'Georgia, serif', lineHeight: '1.6' }}
                                  dangerouslySetInnerHTML={{ __html: opinion.html_with_citations }}
                                />
                              ) : (
                                <div
                                  className="text-gray-700 whitespace-pre-wrap"
                                  style={{ fontFamily: 'Georgia, serif', lineHeight: '1.6' }}
                                >
                                  {opinion.plain_text || opinion.html || 'Opinion text not available'}
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Treatment Tab */}
                {activeTab === 'treatment' && (
                  <div>
                    {!treatment || !treatment.summary.total || treatment.summary.total === 0 ? (
                      <div className="text-center py-8 text-gray-600">
                        <p>No treatment information available for this case.</p>
                      </div>
                    ) : (
                      <div className="space-y-6">
                        {/* Summary Stats */}
                        <div className="grid grid-cols-3 gap-4">
                          <div className="bg-red-50 rounded-lg p-4">
                            <div className="text-2xl font-bold text-red-700">
                              {treatment.summary.negative}
                            </div>
                            <div className="text-sm text-red-600">Negative</div>
                          </div>
                          <div className="bg-green-50 rounded-lg p-4">
                            <div className="text-2xl font-bold text-green-700">
                              {treatment.summary.positive}
                            </div>
                            <div className="text-sm text-green-600">Positive</div>
                          </div>
                          <div className="bg-gray-50 rounded-lg p-4">
                            <div className="text-2xl font-bold text-gray-700">
                              {treatment.summary.neutral}
                            </div>
                            <div className="text-sm text-gray-600">Neutral</div>
                          </div>
                        </div>

                        {/* Significant Treatments */}
                        {treatment.significant_treatments && treatment.significant_treatments.length > 0 && (
                          <div>
                            <h4 className="font-semibold text-gray-900 mb-3">Significant Treatments</h4>
                            <div className="space-y-3">
                              {treatment.significant_treatments.map((sig, index) => (
                                <div key={index} className="border rounded-lg p-4 hover:shadow-md transition">
                                  <div className="flex items-start justify-between mb-2">
                                    <TreatmentBadge
                                      treatment={{
                                        type: sig.type,
                                        severity: sig.severity,
                                        confidence: sig.confidence
                                      }}
                                      size="sm"
                                      showConfidence={true}
                                    />
                                  </div>
                                  <p className="text-sm text-gray-700 italic mt-2">
                                    "{sig.excerpt}"
                                  </p>
                                  {sig.keywords && sig.keywords.length > 0 && (
                                    <div className="mt-2 flex flex-wrap gap-1">
                                      {sig.keywords.map((keyword, i) => (
                                        <span
                                          key={i}
                                          className="inline-block px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded"
                                        >
                                          {keyword}
                                        </span>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Citations Tab */}
                {activeTab === 'citations' && (
                  <div className="space-y-6">
                    {/* Sync Status Message */}
                    {(syncingCitations || syncMessage) && (
                      <div className={`rounded-lg p-3 text-sm ${
                        syncingCitations
                          ? 'bg-blue-50 text-blue-700 border border-blue-200'
                          : syncMessage?.startsWith('✓')
                          ? 'bg-green-50 text-green-700 border border-green-200'
                          : 'bg-gray-50 text-gray-700 border border-gray-200'
                      }`}>
                        <div className="flex items-center gap-2">
                          {syncingCitations && (
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                          )}
                          <span>{syncMessage}</span>
                        </div>
                      </div>
                    )}

                    {/* Inbound Citations */}
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <span className="w-3 h-3 rounded-full bg-green-500 mr-2"></span>
                        Cases Citing This Opinion
                        <span className="ml-2 px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded-full">
                          {inboundCitations.length}
                        </span>
                      </h4>
                      {inboundCitations.length === 0 ? (
                        <p className="text-gray-600 text-sm">No citing cases found</p>
                      ) : (
                        <div className="space-y-2">
                          {inboundCitations.map((citation) => (
                            <Link
                              key={citation.opinion_id}
                              to={`/case/${citation.cluster_id}`}
                              className="block border rounded-lg p-3 hover:bg-gray-50 transition"
                            >
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <p className="font-medium text-gray-900 text-sm">
                                    {citation.case_name_short || citation.case_name}
                                  </p>
                                  <p className="text-xs text-gray-600 mt-1">
                                    {citation.court_name} • {citation.date_filed ? new Date(citation.date_filed).getFullYear() : 'N/A'}
                                  </p>
                                </div>
                                {citation.treatment && (
                                  <TreatmentBadge
                                    treatment={citation.treatment}
                                    size="sm"
                                    showConfidence={false}
                                    showIcon={true}
                                  />
                                )}
                              </div>
                            </Link>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Outbound Citations */}
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <span className="w-3 h-3 rounded-full bg-amber-500 mr-2"></span>
                        Cases Cited by This Opinion
                        <span className="ml-2 px-2 py-0.5 text-xs bg-amber-100 text-amber-700 rounded-full">
                          {outboundCitations.length}
                        </span>
                      </h4>
                      {outboundCitations.length === 0 ? (
                        <p className="text-gray-600 text-sm">No cited cases found</p>
                      ) : (
                        <div className="space-y-2">
                          {outboundCitations.map((citation) => (
                            <Link
                              key={citation.opinion_id}
                              to={`/case/${citation.cluster_id}`}
                              className="block border rounded-lg p-3 hover:bg-gray-50 transition"
                            >
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <p className="font-medium text-gray-900 text-sm">
                                    {citation.case_name_short || citation.case_name}
                                  </p>
                                  <p className="text-xs text-gray-600 mt-1">
                                    {citation.court_name} • {citation.date_filed ? new Date(citation.date_filed).getFullYear() : 'N/A'}
                                  </p>
                                </div>
                                {citation.treatment && (
                                  <TreatmentBadge
                                    treatment={citation.treatment}
                                    size="sm"
                                    showConfidence={false}
                                    showIcon={true}
                                  />
                                )}
                              </div>
                            </Link>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
};

export default CaseDetailFlyout;
