import React, { useState, useEffect } from 'react';
import { dashboardAPI, firewallAPI } from '../../services/api';
import Sidebar from '../Common/Sidebar';
import Loading from '../Common/Loading';
import { formatTimestamp, getRiskLevelDetails } from '../../utils/helpers';
import { useToast } from '../Common/Toast';
import '../Admin/AdminDashboard.css';

const ActiveThreats = () => {
  const [threats, setThreats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedThreat, setSelectedThreat] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [blockConfirmModal, setBlockConfirmModal] = useState({ open: false, threat: null });
  const [sortBy, setSortBy] = useState('severity');
  const toast = useToast();

  // Sort threats by severity (Critical > High > Medium > Low)
  const getSeverityOrder = (severity) => {
    const order = { 'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3 };
    return order[severity?.toUpperCase()] ?? 4;
  };

  const sortedThreats = [...threats].sort((a, b) => {
    if (sortBy === 'severity') {
      const severityDiff = getSeverityOrder(a.severity) - getSeverityOrder(b.severity);
      if (severityDiff !== 0) return severityDiff;
      return b.risk_score - a.risk_score; // Secondary sort by risk score
    } else if (sortBy === 'risk_score') {
      return b.risk_score - a.risk_score;
    } else if (sortBy === 'time') {
      return new Date(b.detected_at) - new Date(a.detected_at);
    }
    return 0;
  });

  useEffect(() => {
    loadThreats();
    const interval = setInterval(loadThreats, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadThreats = async () => {
    try {
      setRefreshing(true);
      const response = await dashboardAPI.getThreats();
      setThreats(response.data.threats || []);
      setLoading(false);
      setRefreshing(false);
    } catch (error) {
      console.error('Error loading threats:', error);
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleBlockThreat = (threat) => {
    setBlockConfirmModal({ open: true, threat });
  };

  const confirmBlockThreat = async () => {
    const threat = blockConfirmModal.threat;
    if (!threat) return;

    setBlockConfirmModal({ open: false, threat: null });
    setActionLoading(true);
    try {
      await firewallAPI.blockUser(threat.user_id, null, 60);
      toast.success(`User ${threat.full_name} has been blocked`);
      loadThreats();
    } catch (error) {
      toast.error('Failed to block user: ' + (error.response?.data?.detail || error.message));
    }
    setActionLoading(false);
  };

  if (loading) {
    return <Loading message="Loading active threats..." fullScreen={true} />;
  }

  return (
    <div className="admin-layout">
      <Sidebar />
      <div className="admin-main">
        <div className="admin-header">
          <div>
            <h1 className="admin-title">Active Threats</h1>
            <p className="admin-subtitle">Real-time threat monitoring and response</p>
          </div>
          <button
            className="btn-admin btn-primary"
            onClick={loadThreats}
            disabled={refreshing}
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        <div className="admin-stats-grid" style={{ marginBottom: '24px' }}>
          <div className="admin-stat-card danger">
            <div className="stat-icon">🚨</div>
            <div className="stat-info">
              <div className="stat-value">{threats.filter(t => t.severity === 'CRITICAL').length}</div>
              <div className="stat-label">Critical</div>
            </div>
          </div>
          <div className="admin-stat-card warning">
            <div className="stat-icon">⚠️</div>
            <div className="stat-info">
              <div className="stat-value">{threats.filter(t => t.severity === 'HIGH').length}</div>
              <div className="stat-label">High Risk</div>
            </div>
          </div>
          <div className="admin-stat-card">
            <div className="stat-icon">📊</div>
            <div className="stat-info">
              <div className="stat-value">{threats.length}</div>
              <div className="stat-label">Total Active</div>
            </div>
          </div>
        </div>

        <div className="admin-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 className="card-title" style={{ margin: 0 }}>Active Threat List ({threats.length} threats)</h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <label style={{ color: '#a8d0ff', fontSize: '13px' }}>Sort by:</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                style={{
                  padding: '8px 12px',
                  backgroundColor: '#1a252f',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '6px',
                  color: '#fff',
                  fontSize: '13px'
                }}
              >
                <option value="severity">Severity (Critical first)</option>
                <option value="risk_score">Risk Score (Highest first)</option>
                <option value="time">Time (Most recent first)</option>
              </select>
            </div>
          </div>

          {sortedThreats.length === 0 ? (
            <div className="empty-state" style={{ padding: '60px', textAlign: 'center' }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>✓</div>
              <div style={{ fontSize: '18px', color: '#10b981' }}>No active threats detected</div>
              <div style={{ color: '#666', marginTop: '8px' }}>System is operating normally</div>
            </div>
          ) : (
            <div className="threats-list">
              {sortedThreats.map((threat, index) => {
                const riskDetails = getRiskLevelDetails(threat.risk_score);
                return (
                  <div
                    key={threat.threat_id || index}
                    className={`threat-item ${threat.severity?.toLowerCase() || 'high'}`}
                    style={{ cursor: 'pointer' }}
                    onClick={() => setSelectedThreat(threat)}
                  >
                    <div className="threat-info" style={{ flex: 1 }}>
                      <div className="threat-user">{threat.full_name}</div>
                      <div className="threat-activity">{threat.threat_type}</div>
                      <div className="threat-time">{formatTimestamp(threat.detected_at)}</div>
                      <div style={{ marginTop: '8px', fontSize: '13px', color: '#a8d0ff' }}>
                        {threat.summary}
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                      <div className="threat-score">
                        <span className={`risk-badge ${riskDetails.label.toLowerCase()}`}>
                          {threat.risk_score}
                        </span>
                      </div>
                      <button
                        className="btn-admin"
                        style={{ background: '#ef4444', padding: '8px 16px' }}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleBlockThreat(threat);
                        }}
                        disabled={actionLoading}
                      >
                        Block
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Block Confirmation Modal */}
        {blockConfirmModal.open && blockConfirmModal.threat && (
          <div className="modal-overlay" onClick={() => setBlockConfirmModal({ open: false, threat: null })}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
              <div className="modal-header">
                <h2>Confirm Block Action</h2>
                <button className="modal-close" onClick={() => setBlockConfirmModal({ open: false, threat: null })}>×</button>
              </div>
              <div className="modal-body">
                <div style={{
                  padding: '16px',
                  backgroundColor: 'rgba(220, 53, 69, 0.15)',
                  border: '1px solid #dc3545',
                  borderRadius: '8px',
                  marginBottom: '20px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontSize: '32px' }}>&#9888;</span>
                    <div>
                      <div style={{ color: '#dc3545', fontWeight: 'bold', fontSize: '16px', marginBottom: '4px' }}>
                        Security Action Required
                      </div>
                      <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: '14px' }}>
                        You are about to block user access. This action will:
                      </div>
                    </div>
                  </div>
                </div>

                <ul style={{ color: 'rgba(255,255,255,0.8)', marginLeft: '20px', marginBottom: '20px', lineHeight: '1.8' }}>
                  <li>Immediately terminate all active sessions</li>
                  <li>Prevent the user from logging in</li>
                  <li>Block all network access from this user</li>
                  <li>Log this action to the audit trail</li>
                </ul>

                <div style={{
                  padding: '16px',
                  backgroundColor: 'rgba(0,0,0,0.2)',
                  borderRadius: '8px'
                }}>
                  <div style={{ color: '#a8d0ff', fontSize: '12px', marginBottom: '8px' }}>Affected User</div>
                  <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#fff' }}>
                    {blockConfirmModal.threat.full_name}
                  </div>
                  <div style={{ color: 'rgba(255,255,255,0.6)', fontSize: '13px' }}>
                    {blockConfirmModal.threat.username} | Risk Score: {blockConfirmModal.threat.risk_score}
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button className="btn-admin" onClick={() => setBlockConfirmModal({ open: false, threat: null })}>
                  Cancel
                </button>
                <button
                  className="btn-admin"
                  style={{ backgroundColor: '#dc3545' }}
                  onClick={confirmBlockThreat}
                  disabled={actionLoading}
                >
                  {actionLoading ? 'Blocking...' : 'Confirm Block'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Threat Detail Modal */}
        {selectedThreat && (
          <div className="modal-overlay" onClick={() => setSelectedThreat(null)}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
              <div className="modal-header">
                <h2>Threat Details</h2>
                <button className="modal-close" onClick={() => setSelectedThreat(null)}>×</button>
              </div>
              <div className="modal-body">
                <div className="detail-grid">
                  <div className="detail-item">
                    <label>User</label>
                    <span>{selectedThreat.full_name}</span>
                  </div>
                  <div className="detail-item">
                    <label>Username</label>
                    <span>{selectedThreat.username}</span>
                  </div>
                  <div className="detail-item">
                    <label>Threat Type</label>
                    <span>{selectedThreat.threat_type}</span>
                  </div>
                  <div className="detail-item">
                    <label>Risk Score</label>
                    <span className={`risk-badge ${getRiskLevelDetails(selectedThreat.risk_score).label.toLowerCase()}`}>
                      {selectedThreat.risk_score}
                    </span>
                  </div>
                  <div className="detail-item">
                    <label>Severity</label>
                    <span>{selectedThreat.severity}</span>
                  </div>
                  <div className="detail-item">
                    <label>Detected At</label>
                    <span>{formatTimestamp(selectedThreat.detected_at)}</span>
                  </div>
                </div>
                <div className="detail-item" style={{ marginTop: '16px' }}>
                  <label>Summary</label>
                  <p style={{ marginTop: '8px', color: '#e0e0e0' }}>{selectedThreat.summary}</p>
                </div>
              </div>
              <div className="modal-footer">
                <button className="btn-admin" onClick={() => setSelectedThreat(null)}>Close</button>
                <button
                  className="btn-admin btn-danger"
                  onClick={() => {
                    handleBlockThreat(selectedThreat);
                    setSelectedThreat(null);
                  }}
                >
                  Block User
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ActiveThreats;
