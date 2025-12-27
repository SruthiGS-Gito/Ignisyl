import React, { useState, useEffect } from 'react';
import { analystAPI, dashboardAPI } from '../../services/api';
import Sidebar from '../Common/Sidebar';
import Loading from '../Common/Loading';
import { formatTimestamp, getRiskLevelDetails } from '../../utils/helpers';
import { DURATION_OPTIONS, DEFAULT_RESTRICTIONS } from '../../utils/constants';
import './AnalystControl.css';

const AnalystControl = () => {
  const [pendingThreats, setPendingThreats] = useState([]);
  const [recentActions, setRecentActions] = useState([]);
  const [selectedThreat, setSelectedThreat] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [stats, setStats] = useState({ pending: 0, reviewed: 0, avgRisk: 0, responseTime: '4hrs' });

  // Form states
  const [action, setAction] = useState('RESTRICT');
  const [reason, setReason] = useState('');
  const [duration, setDuration] = useState(60);
  const [customRestrictions, setCustomRestrictions] = useState({ ...DEFAULT_RESTRICTIONS });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      // Fetch pending decisions
      const pendingResponse = await analystAPI.getPendingDecisions();
      const pending = pendingResponse.data.pending_decisions || [];
      setPendingThreats(pending);

      // Calculate stats
      const avgRisk = pending.length > 0
        ? Math.round(pending.reduce((sum, t) => sum + t.risk_score, 0) / pending.length)
        : 0;

      setStats({
        pending: pending.length,
        reviewed: 0,
        avgRisk: avgRisk,
        responseTime: '4hrs'
      });

      // Try to get recent analyst actions
      try {
        const actionsResponse = await analystAPI.getMyActions(10);
        setRecentActions(actionsResponse.data.actions || []);
        setStats(prev => ({ ...prev, reviewed: actionsResponse.data.count || 0 }));
      } catch (e) {
        // Actions endpoint might fail for non-analysts
      }

      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
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

      alert(`Action ${action} applied successfully!`);
      setShowModal(false);
      fetchData();
      resetForm();
    } catch (error) {
      console.error('Error applying action:', error);
      alert('Failed to apply action. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleContactUser = async () => {
    const message = prompt('Enter message to send to user:');
    if (!message) return;

    try {
      await analystAPI.contactUser(selectedThreat.user_id, message, 'notification');
      alert('Message sent to user successfully!');
    } catch (error) {
      console.error('Error contacting user:', error);
      alert('Failed to send message.');
    }
  };

  const handleEscalate = async () => {
    const escalateTo = prompt('Escalate to (admin/manager/incident_team):');
    if (!escalateTo) return;

    const notes = prompt('Enter escalation notes:');
    if (!notes) return;

    try {
      await analystAPI.escalateThreat(selectedThreat.user_id, escalateTo, notes);
      alert(`Threat escalated to ${escalateTo} successfully!`);
      setShowModal(false);
      fetchData();
    } catch (error) {
      console.error('Error escalating:', error);
      alert('Failed to escalate threat.');
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
    <div className="analyst-layout">
      <Sidebar />

      <div className="analyst-main">
        {/* Header */}
        <div className="analyst-header">
          <div>
            <h1 className="analyst-title">Analyst Threat Control</h1>
            <p className="analyst-subtitle">
              Review and respond to threats requiring manual decision (Risk Score 50-69)
            </p>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="analyst-stats-grid">
          <div className="analyst-stat-card">
            <div className="analyst-stat-label">Pending Decisions</div>
            <div className="analyst-stat-value orange">{stats.pending}</div>
          </div>
          <div className="analyst-stat-card">
            <div className="analyst-stat-label">Average Risk Score</div>
            <div className="analyst-stat-value blue">{stats.avgRisk}</div>
          </div>
          <div className="analyst-stat-card">
            <div className="analyst-stat-label">Actions Today</div>
            <div className="analyst-stat-value green">{stats.reviewed}</div>
          </div>
          <div className="analyst-stat-card">
            <div className="analyst-stat-label">Response Target</div>
            <div className="analyst-stat-value">{stats.responseTime}</div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="analyst-content-grid">
          {/* Left: Pending Threats Table */}
          <div className="analyst-card">
            <h2 className="analyst-card-title">Pending Threat Decisions</h2>

            {pendingThreats.length === 0 ? (
              <div className="analyst-empty-state">
                <div className="analyst-empty-icon">&#10003;</div>
                <div className="analyst-empty-title">No pending decisions</div>
                <div className="analyst-empty-desc">
                  All threats have been reviewed or automatically handled by the system
                </div>
              </div>
            ) : (
              <table className="analyst-table">
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Activity</th>
                    <th>Risk Score</th>
                    <th>Time</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {pendingThreats.map((threat) => {
                    const riskDetails = getRiskLevelDetails(threat.risk_score);
                    const riskClass = threat.risk_score >= 70 ? 'critical' :
                                     threat.risk_score >= 50 ? 'high' : 'medium';
                    return (
                      <tr key={threat.id} onClick={() => handleThreatClick(threat)}>
                        <td>
                          <div className="user-name">{threat.full_name}</div>
                          <div className="user-id">{threat.username}</div>
                        </td>
                        <td>
                          <div className="activity-type">{threat.activity_type?.replace(/_/g, ' ')}</div>
                          <div className="activity-summary">{threat.summary}</div>
                        </td>
                        <td>
                          <span className={`risk-badge-analyst ${riskClass}`}>
                            {threat.risk_score}
                          </span>
                        </td>
                        <td>{formatTimestamp(threat.timestamp)}</td>
                        <td>
                          <button
                            className="btn-review"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleThreatClick(threat);
                            }}
                          >
                            Review
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>

          {/* Right: Information Panel */}
          <div className="analyst-info-panel">
            <div className="info-section">
              <h3 className="info-section-title">&#128161; What is Analyst Control?</h3>
              <div className="info-section-content">
                This page displays threats that require <strong>manual analyst review</strong>.
                The ML system automatically handles low-risk (ALLOW) and high-risk (BLOCK)
                activities, but medium-risk activities (50-69 score) need human judgment.
              </div>
            </div>

            <div className="info-section">
              <h3 className="info-section-title">&#128203; Risk Score Thresholds</h3>
              <ul className="info-list">
                <li>
                  <span className="dot green"></span>
                  <span><strong>0-29:</strong> Low risk - Auto ALLOW</span>
                </li>
                <li>
                  <span className="dot orange"></span>
                  <span><strong>50-69:</strong> Medium risk - Analyst Review</span>
                </li>
                <li>
                  <span className="dot red"></span>
                  <span><strong>70+:</strong> High risk - Auto BLOCK</span>
                </li>
              </ul>
            </div>

            <div className="info-section">
              <h3 className="info-section-title">&#128736; Available Actions</h3>
              <ul className="info-list">
                <li>
                  <span className="dot green"></span>
                  <span><strong>ALLOW:</strong> Mark as false positive</span>
                </li>
                <li>
                  <span className="dot orange"></span>
                  <span><strong>RESTRICT:</strong> Limit user access</span>
                </li>
                <li>
                  <span className="dot red"></span>
                  <span><strong>ISOLATE:</strong> Quarantine user</span>
                </li>
                <li>
                  <span className="dot red"></span>
                  <span><strong>BLOCK:</strong> Complete access block</span>
                </li>
              </ul>
            </div>

            <div className="info-section">
              <h3 className="info-section-title">&#9889; Quick Actions</h3>
              <div className="quick-actions">
                <button className="quick-action-btn" onClick={fetchData}>
                  &#128260; Refresh Pending List
                </button>
                <button className="quick-action-btn" onClick={() => window.location.href = '/threats'}>
                  &#128680; View All Threats
                </button>
                <button className="quick-action-btn" onClick={() => window.location.href = '/activities'}>
                  &#128203; Activity Log
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Threat Review Modal */}
      {showModal && selectedThreat && (
        <div className="analyst-modal-overlay" onClick={closeModal}>
          <div className="analyst-modal" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="analyst-modal-header">
              <div>
                <h3 className="analyst-modal-title">
                  Threat Analysis: {selectedThreat.full_name}
                </h3>
                <p className="analyst-modal-subtitle">
                  Risk Score: {selectedThreat.risk_score} ({selectedThreat.risk_level})
                </p>
              </div>
              <button className="analyst-modal-close" onClick={closeModal}>
                &times;
              </button>
            </div>

            {/* Modal Body */}
            <div className="analyst-modal-body">
              {/* User Information */}
              <div className="analyst-modal-section">
                <h4 className="analyst-modal-section-title">User Information</h4>
                <div className="analyst-modal-info-grid">
                  <div className="analyst-modal-info-item">
                    <label>Username:</label>
                    <span>{selectedThreat.username}</span>
                  </div>
                  <div className="analyst-modal-info-item">
                    <label>Full Name:</label>
                    <span>{selectedThreat.full_name}</span>
                  </div>
                </div>
              </div>

              {/* Activity Details */}
              <div className="analyst-modal-section" style={{background: 'rgba(59, 130, 246, 0.1)'}}>
                <h4 className="analyst-modal-section-title">Activity Details</h4>
                <div className="analyst-modal-info-grid">
                  <div className="analyst-modal-info-item">
                    <label>Type:</label>
                    <span>{selectedThreat.activity_type?.replace(/_/g, ' ')}</span>
                  </div>
                  <div className="analyst-modal-info-item">
                    <label>Timestamp:</label>
                    <span>{formatTimestamp(selectedThreat.timestamp)}</span>
                  </div>
                </div>
                <div className="analyst-modal-info-item" style={{marginTop: '12px'}}>
                  <label>Summary:</label>
                  <span>{selectedThreat.summary}</span>
                </div>
              </div>

              {/* Action Selection */}
              <h4 className="analyst-modal-section-title">Select Action</h4>
              <div className="action-grid">
                <button
                  className={`action-btn ${action === 'ALLOW' ? 'selected allow' : ''}`}
                  onClick={() => setAction('ALLOW')}
                >
                  <div className="action-btn-icon">&#10003;</div>
                  <div className="action-btn-label">ALLOW</div>
                  <div className="action-btn-desc">False positive</div>
                </button>

                <button
                  className={`action-btn ${action === 'RESTRICT' ? 'selected restrict' : ''}`}
                  onClick={() => setAction('RESTRICT')}
                >
                  <div className="action-btn-icon">&#9888;</div>
                  <div className="action-btn-label">RESTRICT</div>
                  <div className="action-btn-desc">Limit access</div>
                </button>

                <button
                  className={`action-btn ${action === 'ISOLATE' ? 'selected isolate' : ''}`}
                  onClick={() => setAction('ISOLATE')}
                >
                  <div className="action-btn-icon">&#128683;</div>
                  <div className="action-btn-label">ISOLATE</div>
                  <div className="action-btn-desc">Quarantine</div>
                </button>

                <button
                  className={`action-btn ${action === 'BLOCK' ? 'selected block' : ''}`}
                  onClick={() => setAction('BLOCK')}
                >
                  <div className="action-btn-icon">&#9940;</div>
                  <div className="action-btn-label">BLOCK</div>
                  <div className="action-btn-desc">Complete block</div>
                </button>
              </div>

              {/* Custom Restrictions for RESTRICT action */}
              {action === 'RESTRICT' && (
                <div className="restrictions-panel">
                  <h5 className="restrictions-title">Custom Restrictions</h5>
                  <div className="restriction-item">
                    <input
                      type="checkbox"
                      id="block_internet"
                      checked={customRestrictions.block_external_internet}
                      onChange={(e) =>
                        setCustomRestrictions({
                          ...customRestrictions,
                          block_external_internet: e.target.checked,
                        })
                      }
                    />
                    <label htmlFor="block_internet">Block external internet</label>
                  </div>
                  <div className="restriction-item">
                    <input
                      type="checkbox"
                      id="notify_user"
                      checked={customRestrictions.notify_user}
                      onChange={(e) =>
                        setCustomRestrictions({
                          ...customRestrictions,
                          notify_user: e.target.checked,
                        })
                      }
                    />
                    <label htmlFor="notify_user">Send notification to user</label>
                  </div>
                  <div className="restriction-item">
                    <label>Rate limit (Mbps):</label>
                    <input
                      type="number"
                      value={customRestrictions.rate_limit_mbps}
                      onChange={(e) =>
                        setCustomRestrictions({
                          ...customRestrictions,
                          rate_limit_mbps: parseInt(e.target.value) || 1,
                        })
                      }
                      min="1"
                      max="100"
                    />
                  </div>
                </div>
              )}

              {/* Duration */}
              <div className="analyst-form-group">
                <label className="analyst-form-label">Duration</label>
                <select
                  value={duration}
                  onChange={(e) => setDuration(parseInt(e.target.value))}
                  className="analyst-form-select"
                >
                  {DURATION_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Reason */}
              <div className="analyst-form-group">
                <label className="analyst-form-label">Reason (Required) *</label>
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Explain your decision..."
                  className="analyst-form-textarea"
                />
              </div>
            </div>

            {/* Modal Footer */}
            <div className="analyst-modal-footer">
              <div className="analyst-modal-footer-left">
                <button className="btn-contact" onClick={handleContactUser}>
                  &#128231; Contact User
                </button>
                <button className="btn-escalate" onClick={handleEscalate}>
                  &#11014; Escalate
                </button>
              </div>
              <div className="analyst-modal-footer-right">
                <button className="btn-cancel" onClick={closeModal}>
                  Cancel
                </button>
                <button
                  className="btn-apply"
                  onClick={handleApplyAction}
                  disabled={submitting || !reason.trim()}
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
