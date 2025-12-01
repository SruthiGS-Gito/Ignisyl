import React, { useState, useEffect } from 'react';
import { analystAPI } from '../../services/api';
import Sidebar from '../Common/Sidebar';
import Loading from '../Common/Loading';
import { formatTimestamp, getRiskLevelDetails } from '../../utils/helpers';
import { ACTIONS, DURATION_OPTIONS, DEFAULT_RESTRICTIONS } from '../../utils/constants';

const AnalystControl = () => {
  const [pendingThreats, setPendingThreats] = useState([]);
  const [selectedThreat, setSelectedThreat] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  // Form states
  const [action, setAction] = useState('RESTRICT');
  const [reason, setReason] = useState('');
  const [duration, setDuration] = useState(60);
  const [customRestrictions, setCustomRestrictions] = useState({ ...DEFAULT_RESTRICTIONS });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchPendingDecisions();
    const interval = setInterval(fetchPendingDecisions, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchPendingDecisions = async () => {
    try {
      const response = await analystAPI.getPendingDecisions();
      setPendingThreats(response.data.pending_decisions || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching pending decisions:', error);
      setLoading(false);
    }
  };

  const handleThreatClick = (threat) => {
    setSelectedThreat(threat);
    setShowModal(true);
    setAction('RESTRICT');
    setReason('');
    setCustomRestrictions({ ...DEFAULT_RESTRICTIONS });
  };

  const handleApplyAction = async () => {
    if (!reason.trim()) {
      alert('Please provide a reason for this action');
      return;
    }

    setSubmitting(true);
    try {
      await analystAPI.takeAction(selectedThreat.user_id, {
        action,
        custom_restrictions: customRestrictions,
        reason,
        duration_minutes: duration,
      });

      alert(`✅ Action ${action} applied successfully!`);
      setShowModal(false);
      fetchPendingDecisions();
      resetForm();
    } catch (error) {
      console.error('Error applying action:', error);
      alert('❌ Failed to apply action. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleContactUser = async () => {
    const message = prompt('Enter message to send to user:');
    if (!message) return;

    try {
      await analystAPI.contactUser(selectedThreat.user_id, message, 'notification');
      alert('✅ Message sent to user successfully!');
    } catch (error) {
      console.error('Error contacting user:', error);
      alert('❌ Failed to send message.');
    }
  };

  const handleEscalate = async () => {
    const escalateTo = prompt('Escalate to (admin/manager/incident_team):');
    if (!escalateTo) return;

    const notes = prompt('Enter escalation notes:');
    if (!notes) return;

    try {
      await analystAPI.escalateThreat(selectedThreat.user_id, escalateTo, notes);
      alert(`✅ Threat escalated to ${escalateTo} successfully!`);
      setShowModal(false);
      fetchPendingDecisions();
    } catch (error) {
      console.error('Error escalating:', error);
      alert('❌ Failed to escalate threat.');
    }
  };

  const resetForm = () => {
    setReason('');
    setAction('RESTRICT');
    setDuration(60);
    setCustomRestrictions({ ...DEFAULT_RESTRICTIONS });
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedThreat(null);
    resetForm();
  };

  if (loading) {
    return <Loading message="Loading analyst control panel..." fullScreen={true} />;
  }

  return (
    <div className="flex">
      <Sidebar />

      <div className="main-content bg-gray-50">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-gray-900">Analyst Threat Control</h1>
            <p className="text-gray-600 mt-2">
              Review and respond to threats requiring analyst decision (Risk Score 50-69)
            </p>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600">Pending Decisions</div>
              <div className="text-4xl font-bold text-orange-600 mt-2">
                {pendingThreats.length}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600">Avg Risk Score</div>
              <div className="text-4xl font-bold text-gray-900 mt-2">
                {pendingThreats.length > 0
                  ? Math.round(
                      pendingThreats.reduce((sum, t) => sum + t.risk_score, 0) /
                        pendingThreats.length
                    )
                  : 0}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600">Response Time Target</div>
              <div className="text-4xl font-bold text-blue-600 mt-2">4hrs</div>
            </div>
          </div>

          {/* Pending Threats Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">
                Pending Threat Decisions
              </h2>
            </div>

            {pendingThreats.length === 0 ? (
              <div className="p-12 text-center">
                <div className="text-gray-400 text-6xl mb-4">✓</div>
                <div className="text-xl text-gray-600">No pending decisions</div>
                <div className="text-sm text-gray-500 mt-2">
                  All threats have been reviewed or auto-handled
                </div>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        User
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Activity
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Risk Score
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Time
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Action
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {pendingThreats.map((threat) => {
                      const riskDetails = getRiskLevelDetails(threat.risk_score);
                      return (
                        <tr
                          key={threat.id}
                          className="hover:bg-gray-50 cursor-pointer"
                          onClick={() => handleThreatClick(threat)}
                        >
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">
                              {threat.full_name}
                            </div>
                            <div className="text-sm text-gray-500">{threat.username}</div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="text-sm text-gray-900">
                              {threat.activity_type}
                            </div>
                            <div className="text-sm text-gray-500 truncate max-w-xs">
                              {threat.summary}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span
                              className="px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full"
                              style={{
                                background: riskDetails.bgColor,
                                color: riskDetails.textColor,
                              }}
                            >
                              {threat.risk_score}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatTimestamp(threat.timestamp)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <button
                              className="text-blue-600 hover:text-blue-900"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleThreatClick(threat);
                              }}
                            >
                              Review →
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Threat Review Modal */}
      {showModal && selectedThreat && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-screen overflow-y-auto">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <div>
                <h3 className="text-2xl font-bold text-gray-900">
                  Threat Analysis: {selectedThreat.full_name}
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  Risk Score: {selectedThreat.risk_score} ({selectedThreat.risk_level})
                </p>
              </div>
              <button
                onClick={closeModal}
                className="text-gray-400 hover:text-gray-600 text-3xl leading-none"
              >
                ×
              </button>
            </div>

            {/* Modal Body */}
            <div className="px-6 py-4 space-y-6">
              {/* User Information */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-semibold text-gray-900 mb-2">User Information</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Username:</span>{' '}
                    <span className="font-medium">{selectedThreat.username}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Full Name:</span>{' '}
                    <span className="font-medium">{selectedThreat.full_name}</span>
                  </div>
                </div>
              </div>

              {/* Activity Details */}
              <div className="bg-blue-50 rounded-lg p-4">
                <h4 className="font-semibold text-gray-900 mb-2">Activity Details</h4>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-gray-600">Type:</span>{' '}
                    <span className="font-medium">{selectedThreat.activity_type}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Summary:</span>{' '}
                    <span className="font-medium">{selectedThreat.summary}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Timestamp:</span>{' '}
                    <span className="font-medium">
                      {formatTimestamp(selectedThreat.timestamp)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Action Selection */}
              <div className="space-y-4">
                <h4 className="font-semibold text-gray-900">Select Action</h4>

                <div className="grid grid-cols-4 gap-3">
                  <button
                    className={`p-4 rounded-lg border-2 text-center transition ${
                      action === 'ALLOW'
                        ? 'border-green-500 bg-green-50'
                        : 'border-gray-200 hover:border-green-300'
                    }`}
                    onClick={() => setAction('ALLOW')}
                  >
                    <div className="text-2xl mb-1">✓</div>
                    <div className="font-semibold text-sm">ALLOW</div>
                    <div className="text-xs text-gray-600">False positive</div>
                  </button>

                  <button
                    className={`p-4 rounded-lg border-2 text-center transition ${
                      action === 'RESTRICT'
                        ? 'border-orange-500 bg-orange-50'
                        : 'border-gray-200 hover:border-orange-300'
                    }`}
                    onClick={() => setAction('RESTRICT')}
                  >
                    <div className="text-2xl mb-1">⚠️</div>
                    <div className="font-semibold text-sm">RESTRICT</div>
                    <div className="text-xs text-gray-600">Limit access</div>
                  </button>

                  <button
                    className={`p-4 rounded-lg border-2 text-center transition ${
                      action === 'ISOLATE'
                        ? 'border-red-500 bg-red-50'
                        : 'border-gray-200 hover:border-red-300'
                    }`}
                    onClick={() => setAction('ISOLATE')}
                  >
                    <div className="text-2xl mb-1">🚫</div>
                    <div className="font-semibold text-sm">ISOLATE</div>
                    <div className="text-xs text-gray-600">Quarantine</div>
                  </button>

                  <button
                    className={`p-4 rounded-lg border-2 text-center transition ${
                      action === 'BLOCK'
                        ? 'border-red-700 bg-red-100'
                        : 'border-gray-200 hover:border-red-400'
                    }`}
                    onClick={() => setAction('BLOCK')}
                  >
                    <div className="text-2xl mb-1">⛔</div>
                    <div className="font-semibold text-sm">BLOCK</div>
                    <div className="text-xs text-gray-600">Complete block</div>
                  </button>
                </div>

                {/* Custom Restrictions for RESTRICT action */}
                {action === 'RESTRICT' && (
                  <div className="bg-orange-50 rounded-lg p-4 space-y-3">
                    <h5 className="font-semibold text-gray-900">Custom Restrictions</h5>
                    <div className="space-y-2">
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={customRestrictions.block_external_internet}
                          onChange={(e) =>
                            setCustomRestrictions({
                              ...customRestrictions,
                              block_external_internet: e.target.checked,
                            })
                          }
                          className="rounded"
                        />
                        <span className="text-sm">Block external internet</span>
                      </label>
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={customRestrictions.notify_user}
                          onChange={(e) =>
                            setCustomRestrictions({
                              ...customRestrictions,
                              notify_user: e.target.checked,
                            })
                          }
                          className="rounded"
                        />
                        <span className="text-sm">Send notification to user</span>
                      </label>
                      <div className="flex items-center space-x-2">
                        <label className="text-sm">Rate limit (Mbps):</label>
                        <input
                          type="number"
                          value={customRestrictions.rate_limit_mbps}
                          onChange={(e) =>
                            setCustomRestrictions({
                              ...customRestrictions,
                              rate_limit_mbps: parseInt(e.target.value),
                            })
                          }
                          className="w-20 px-2 py-1 border rounded"
                          min="1"
                          max="100"
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Duration */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Duration (minutes)
                  </label>
                  <select
                    value={duration}
                    onChange={(e) => setDuration(parseInt(e.target.value))}
                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {DURATION_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Reason */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Reason (Required) *
                  </label>
                  <textarea
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    placeholder="Explain your decision..."
                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows="3"
                  />
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-gray-200 flex justify-between">
              <div className="space-x-2">
                <button
                  onClick={handleContactUser}
                  className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition"
                >
                  📧 Contact User
                </button>
                <button
                  onClick={handleEscalate}
                  className="px-4 py-2 bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200 transition"
                >
                  ⬆️ Escalate
                </button>
              </div>
              <div className="space-x-2">
                <button
                  onClick={closeModal}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleApplyAction}
                  disabled={submitting || !reason.trim()}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {submitting ? 'Applying...' : `Apply ${action}`}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalystControl;
