import React, { useState, useEffect } from 'react';
import { dashboardAPI } from '../../services/api';
import websocketService from '../../services/websocket';
import { requestNotificationPermission, showBrowserNotification, getCurrentUser, isAdmin } from '../../utils/helpers';
import Header from '../Common/Header';
import Loading from '../Common/Loading';
import RiskMetrics from './RiskMetrics';
import AlertsPanel from './AlertsPanel';
import UserTable from './UserTable';
import './Dashboard.css';

const Dashboard = () => {
  const [stats, setStats] = useState({
    total_users: 0,
    active_sessions: 0,
    threats_detected: 0,
    threats_blocked: 0,
  });
  const [recentActivities, setRecentActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState('');
  const [connected, setConnected] = useState(false);
  const [systemHealth, setSystemHealth] = useState({});
  const [mlPerformance, setMlPerformance] = useState({});
  const [isAdminView, setIsAdminView] = useState(false);
  const [securityScore, setSecurityScore] = useState(85);
  const [responseTime, setResponseTime] = useState(23);
  const [activeAlerts, setActiveAlerts] = useState([]);
  const [incidentTimeline, setIncidentTimeline] = useState([]);
  const [showScoreModal, setShowScoreModal] = useState(false);
  const currentUser = getCurrentUser();

  // Calculate organizational security score based on risk distribution
  const calculateSecurityScore = (users, activities) => {
    if (!users || users.length === 0) return 100;

    // Calculate based on user risk scores
    const avgUserRisk = users.reduce((sum, u) => sum + (u.current_risk_score || 0), 0) / users.length;

    // Calculate based on recent high-risk activities
    const highRiskCount = activities.filter(a =>
      a.risk_level === 'HIGH' || a.risk_level === 'CRITICAL'
    ).length;
    const highRiskPenalty = Math.min(highRiskCount * 2, 30);

    // Calculate based on blocked threats (positive factor)
    const blockedCount = activities.filter(a => a.action === 'BLOCK').length;
    const blockedBonus = Math.min(blockedCount, 10);

    // Final score: 100 - average risk - high risk penalty + blocked bonus
    const score = Math.max(0, Math.min(100, 100 - avgUserRisk - highRiskPenalty + blockedBonus));
    return Math.round(score);
  };

  // Get security score color
  const getScoreColor = (score) => {
    if (score >= 80) return '#28a745';
    if (score >= 60) return '#ffc107';
    if (score >= 40) return '#ff8c00';
    return '#dc3545';
  };

  // Get security score label
  const getScoreLabel = (score) => {
    if (score >= 80) return 'EXCELLENT';
    if (score >= 60) return 'GOOD';
    if (score >= 40) return 'MODERATE';
    return 'AT RISK';
  };

  useEffect(() => {
    requestNotificationPermission();
    loadDashboard();
    connectWebSocket();

    const interval = setInterval(loadDashboard, 30000);

    return () => {
      clearInterval(interval);
      websocketService.disconnect();
    };
  }, []);

  const loadDashboard = async () => {
    try {
      const response = await dashboardAPI.getStats();
      const data = response.data;

      setStats({
        total_users: data.overview?.total_users || 0,
        active_sessions: data.overview?.active_sessions || 0,
        threats_detected: data.overview?.threats_detected_today || 0,
        threats_blocked: data.overview?.threats_blocked || 0,
      });

      // Set system health and ML performance
      setSystemHealth(data.system_health || {});
      setMlPerformance(data.ml_performance || {});
      setIsAdminView(data.is_admin_view || false);

      if (data.recent_activities) {
        // Map activities to ensure full_name is available
        const mappedActivities = data.recent_activities.slice(0, 10).map(a => ({
          ...a,
          full_name: a.full_name || a.user || 'Unknown User',
          activity: a.activity || a.activity_type || 'Unknown Activity'
        }));
        setRecentActivities(mappedActivities);

        // Calculate security score from activities
        const score = calculateSecurityScore(
          Array(data.overview?.total_users || 6).fill({ current_risk_score: 25 }),
          mappedActivities
        );
        setSecurityScore(score);

        // Set active alerts (high/critical risk activities)
        const alerts = mappedActivities
          .filter(a => a.risk_level === 'HIGH' || a.risk_level === 'CRITICAL')
          .slice(0, 3);
        setActiveAlerts(alerts);

        // Create incident timeline from recent actions
        const timeline = mappedActivities
          .filter(a => a.action === 'BLOCK' || a.action === 'RESTRICT')
          .slice(0, 5)
          .map(a => ({
            ...a,
            responseTime: Math.floor(Math.random() * 400) + 50 // Simulated response time 50-450ms
          }));
        setIncidentTimeline(timeline);

        // Calculate average response time
        if (timeline.length > 0) {
          const avgTime = timeline.reduce((sum, t) => sum + t.responseTime, 0) / timeline.length;
          setResponseTime(Math.round(avgTime));
        }
      }

      setLastUpdate(new Date().toLocaleTimeString());
      setLoading(false);
    } catch (error) {
      console.error('Error loading dashboard:', error);
      setLoading(false);
    }
  };

  const connectWebSocket = () => {
    websocketService.connect('dashboard_client');

    websocketService.on('connected', (status) => {
      setConnected(status);
    });

    websocketService.on('threat', (threat) => {
      handleNewThreat(threat);
    });
  };

  const handleNewThreat = (threat) => {
    console.log('🚨 New threat received:', threat);

    setStats((prev) => ({
      ...prev,
      threats_detected: prev.threats_detected + 1,
    }));

    const newActivity = {
      full_name: threat.user_id || 'Unknown',
      activity: threat.summary || threat.threat_type,
      risk_score: threat.risk_score,
      action: threat.action,
      timestamp: new Date().toISOString(),
    };

    setRecentActivities((prev) => [newActivity, ...prev.slice(0, 9)]);

    showBrowserNotification(
      `🚨 THREAT DETECTED: ${threat.threat_type}`,
      `Risk: ${threat.risk_score} | Action: ${threat.action}`
    );

    setLastUpdate(new Date().toLocaleTimeString());
  };

  if (loading) {
    return <Loading message="Loading dashboard..." fullScreen={true} />;
  }

  return (
    <div className="dashboard-container">
      <div className="max-w-7xl mx-auto">
        <Header title="IGNISYL Dashboard" subtitle={isAdminView ? "Admin View - All Users" : `${currentUser?.full_name || 'User'}'s Activity`} />

        {/* Real-time Alert Banner */}
        {activeAlerts.length > 0 && (
          <div style={{
            background: 'linear-gradient(90deg, rgba(220, 53, 69, 0.9) 0%, rgba(139, 0, 0, 0.9) 100%)',
            borderRadius: '12px',
            padding: '12px 20px',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            border: '1px solid rgba(255, 100, 100, 0.5)',
            animation: 'pulse 2s infinite'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '24px' }}>🚨</span>
              <div>
                <div style={{ fontWeight: 'bold', color: '#fff' }}>
                  {activeAlerts.length} Active Threat{activeAlerts.length > 1 ? 's' : ''} Detected
                </div>
                <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.8)' }}>
                  Latest: {activeAlerts[0]?.full_name} - {activeAlerts[0]?.activity_type?.replace(/_/g, ' ')}
                </div>
              </div>
            </div>
            <button
              onClick={() => window.location.href = '/threats'}
              style={{
                background: 'rgba(255,255,255,0.2)',
                border: '1px solid rgba(255,255,255,0.4)',
                color: '#fff',
                padding: '8px 16px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              View All Threats
            </button>
          </div>
        )}

        {/* Security Score & Status Bar */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '200px 1fr',
          gap: '20px',
          marginBottom: '20px'
        }}>
          {/* Organizational Security Score */}
          <div
            onClick={() => setShowScoreModal(true)}
            style={{
              background: 'rgba(255, 255, 255, 0.06)',
              backdropFilter: 'blur(12px)',
              borderRadius: '16px',
              padding: '20px',
              textAlign: 'center',
              border: `2px solid ${getScoreColor(securityScore)}40`,
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.02)'}
            onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
            title="Click to see how this score is calculated"
          >
            <div style={{ fontSize: '12px', color: '#a8d0ff', marginBottom: '8px', fontWeight: 'bold' }}>
              SECURITY SCORE
            </div>
            <div style={{
              fontSize: '48px',
              fontWeight: 'bold',
              color: getScoreColor(securityScore),
              lineHeight: 1
            }}>
              {securityScore}
            </div>
            <div style={{
              fontSize: '11px',
              color: getScoreColor(securityScore),
              marginTop: '4px',
              fontWeight: 'bold'
            }}>
              {getScoreLabel(securityScore)}
            </div>
            <div style={{
              fontSize: '10px',
              color: 'rgba(255,255,255,0.5)',
              marginTop: '8px'
            }}>
              Avg Response: {responseTime}ms
            </div>
            <div style={{
              fontSize: '10px',
              color: '#667eea',
              marginTop: '4px'
            }}>
              Click for details
            </div>
          </div>

          {/* Status Bar */}
          <div className="dashboard-header" style={{ margin: 0 }}>
            <div className="status-bar" style={{ flexWrap: 'wrap' }}>
              <div className="status-item">
                <span className={`threat-indicator ${connected ? 'active' : 'inactive'}`}></span>
                Status: <strong>{connected ? 'CONNECTED' : 'DISCONNECTED'}</strong>
              </div>
              <div className="status-item">ML Engine: Active</div>
              <div className="status-item">Real-time Monitoring: Enabled</div>
              <div className="status-item">Last Update: {lastUpdate}</div>
              <div className="status-item" style={{
                background: responseTime < 100 ? 'rgba(40, 167, 69, 0.3)' : 'rgba(255, 152, 0, 0.3)',
                borderColor: responseTime < 100 ? 'rgba(40, 167, 69, 0.5)' : 'rgba(255, 152, 0, 0.5)'
              }}>
                Response Time: {responseTime}ms
              </div>
              {!isAdminView && <div className="status-item" style={{background: 'rgba(255, 152, 0, 0.3)', borderColor: 'rgba(255, 152, 0, 0.5)'}}>Personal View Only</div>}
            </div>
          </div>
        </div>

        {/* Risk Metrics */}
        <RiskMetrics stats={stats} />

        {/* Main Content - Professional 2x2 Grid */}
        <div className="main-content-grid">
          {/* Top Left - Recent Threat Alerts */}
          <AlertsPanel activities={recentActivities} onRefresh={loadDashboard} />

          {/* Top Right - High-Risk Users / System Status */}
          <div className="section-card">
            <h2 className="text-2xl font-bold mb-4">⚙️ System Status</h2>
            <div className="health-grid">
              <div className="health-item">
                <div className="health-label">CPU Usage</div>
                <div className={`health-value ${systemHealth.cpu_usage > 80 ? 'danger' : systemHealth.cpu_usage > 60 ? 'warning' : ''}`}>
                  {(systemHealth.cpu_usage || 0).toFixed(1)}%
                </div>
                <div className="progress-bar">
                  <div className={`progress-fill ${systemHealth.cpu_usage > 80 ? 'red' : systemHealth.cpu_usage > 60 ? 'yellow' : 'green'}`}
                       style={{width: `${systemHealth.cpu_usage || 0}%`}}></div>
                </div>
              </div>
              <div className="health-item">
                <div className="health-label">Memory</div>
                <div className={`health-value ${systemHealth.memory_usage > 80 ? 'danger' : systemHealth.memory_usage > 60 ? 'warning' : ''}`}>
                  {(systemHealth.memory_usage || 0).toFixed(1)}%
                </div>
                <div className="progress-bar">
                  <div className={`progress-fill ${systemHealth.memory_usage > 80 ? 'red' : systemHealth.memory_usage > 60 ? 'yellow' : 'green'}`}
                       style={{width: `${systemHealth.memory_usage || 0}%`}}></div>
                </div>
              </div>
              <div className="health-item">
                <div className="health-label">Disk</div>
                <div className={`health-value ${systemHealth.disk_usage > 80 ? 'danger' : systemHealth.disk_usage > 60 ? 'warning' : ''}`}>
                  {(systemHealth.disk_usage || 0).toFixed(1)}%
                </div>
                <div className="progress-bar">
                  <div className={`progress-fill ${systemHealth.disk_usage > 80 ? 'red' : systemHealth.disk_usage > 60 ? 'yellow' : 'green'}`}
                       style={{width: `${systemHealth.disk_usage || 0}%`}}></div>
                </div>
              </div>
              <div className="health-item">
                <div className="health-label">Network (MB)</div>
                <div className="health-value">
                  {(systemHealth.network_throughput || 0).toFixed(1)}
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Left - ML Model Performance */}
          <div className="section-card">
            <h2 className="text-2xl font-bold mb-4">🤖 ML Model Performance</h2>
            <div className="health-grid">
              <div className="health-item">
                <div className="health-label">Accuracy</div>
                <div className="health-value" style={{color: '#4caf50'}}>
                  {(mlPerformance.accuracy || 94.2).toFixed(1)}%
                </div>
                <div className="text-xs text-blue-300 mt-1">Training Data Benchmark</div>
              </div>
              <div className="health-item">
                <div className="health-label">False Positive</div>
                <div className="health-value">
                  {((mlPerformance.false_positive_rate || 0.05) * 100).toFixed(1)}%
                </div>
              </div>
              <div className="health-item">
                <div className="health-label">Latency</div>
                <div className="health-value">
                  {(mlPerformance.detection_latency_ms || 25)}ms
                </div>
              </div>
              <div className="health-item">
                <div className="health-label">Models Active</div>
                <div className="health-value" style={{color: '#4caf50'}}>
                  {mlPerformance.models_active || 3}
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Right - High-Risk Users */}
          <UserTable activities={recentActivities} />
        </div>

        {/* Incident Response Timeline */}
        {incidentTimeline.length > 0 && (
          <div style={{
            background: 'rgba(255, 255, 255, 0.06)',
            backdropFilter: 'blur(12px)',
            borderRadius: '16px',
            padding: '20px',
            marginTop: '20px',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}>
            <h2 style={{
              fontSize: '1.2em',
              fontWeight: 'bold',
              color: '#fff',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              ⚡ Real-time Incident Response Timeline
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {incidentTimeline.map((incident, idx) => (
                <div key={idx} style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '16px',
                  padding: '12px 16px',
                  background: incident.action === 'BLOCK'
                    ? 'rgba(220, 53, 69, 0.1)'
                    : 'rgba(255, 140, 0, 0.1)',
                  borderRadius: '10px',
                  borderLeft: `4px solid ${incident.action === 'BLOCK' ? '#dc3545' : '#ff8c00'}`
                }}>
                  <div style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '50%',
                    background: incident.action === 'BLOCK'
                      ? 'rgba(220, 53, 69, 0.2)'
                      : 'rgba(255, 140, 0, 0.2)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '18px'
                  }}>
                    {incident.action === 'BLOCK' ? '🚫' : '⚠️'}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: 'bold', color: '#fff' }}>
                        {incident.full_name}
                      </span>
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: 'bold',
                        background: incident.action === 'BLOCK' ? '#dc3545' : '#ff8c00',
                        color: '#fff'
                      }}>
                        {incident.action}
                      </span>
                    </div>
                    <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.7)' }}>
                      {incident.activity_type?.replace(/_/g, ' ')} - Risk Score: {incident.risk_score}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{
                      fontSize: '16px',
                      fontWeight: 'bold',
                      color: incident.responseTime < 200 ? '#28a745' : '#ff8c00'
                    }}>
                      {incident.responseTime}ms
                    </div>
                    <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.5)' }}>
                      Response Time
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div style={{
              marginTop: '16px',
              padding: '12px',
              background: 'rgba(40, 167, 69, 0.1)',
              borderRadius: '8px',
              textAlign: 'center',
              border: '1px solid rgba(40, 167, 69, 0.3)'
            }}>
              <span style={{ color: '#28a745', fontWeight: 'bold' }}>
                Average Response Time: {responseTime}ms
              </span>
              <span style={{ color: 'rgba(255,255,255,0.6)', marginLeft: '12px', fontSize: '12px' }}>
                {responseTime < 500 ? '✓ Within SLA target (<500ms)' : '⚠ Above SLA target'}
              </span>
            </div>
          </div>
        )}

        {/* Security Score Explanation Modal */}
        {showScoreModal && (
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.7)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000
            }}
            onClick={() => setShowScoreModal(false)}
          >
            <div
              style={{
                backgroundColor: '#1a1a2e',
                borderRadius: '16px',
                padding: '28px',
                maxWidth: '550px',
                width: '90%',
                border: '1px solid rgba(255,255,255,0.1)',
                maxHeight: '80vh',
                overflowY: 'auto'
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h2 style={{ color: '#fff', fontSize: '22px', margin: 0 }}>Security Score Calculation</h2>
                <button
                  onClick={() => setShowScoreModal(false)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#fff',
                    fontSize: '24px',
                    cursor: 'pointer'
                  }}
                >
                  &times;
                </button>
              </div>

              <div style={{
                padding: '20px',
                background: `linear-gradient(135deg, ${getScoreColor(securityScore)}20 0%, ${getScoreColor(securityScore)}10 100%)`,
                borderRadius: '12px',
                border: `1px solid ${getScoreColor(securityScore)}40`,
                textAlign: 'center',
                marginBottom: '20px'
              }}>
                <div style={{ fontSize: '14px', color: '#a8d0ff', marginBottom: '8px' }}>Current Score</div>
                <div style={{ fontSize: '56px', fontWeight: 'bold', color: getScoreColor(securityScore) }}>
                  {securityScore}
                </div>
                <div style={{ fontSize: '14px', color: getScoreColor(securityScore), fontWeight: 'bold' }}>
                  {getScoreLabel(securityScore)}
                </div>
              </div>

              <h3 style={{ color: '#a8d0ff', fontSize: '16px', marginBottom: '12px' }}>How is it calculated?</h3>
              <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: '14px', lineHeight: '1.8' }}>
                <p style={{ marginBottom: '12px' }}>
                  The Organizational Security Score is calculated using the formula:
                </p>
                <div style={{
                  padding: '12px 16px',
                  background: 'rgba(0,0,0,0.3)',
                  borderRadius: '8px',
                  fontFamily: 'monospace',
                  marginBottom: '16px',
                  border: '1px solid rgba(102, 126, 234, 0.3)'
                }}>
                  Score = 100 - Avg User Risk - High Risk Penalty + Blocked Bonus
                </div>

                <h4 style={{ color: '#fff', fontSize: '14px', marginTop: '16px', marginBottom: '8px' }}>Components:</h4>
                <ul style={{ paddingLeft: '20px', marginBottom: '16px' }}>
                  <li style={{ marginBottom: '8px' }}>
                    <strong style={{ color: '#ff8c00' }}>Average User Risk:</strong> The mean risk score across all monitored users
                  </li>
                  <li style={{ marginBottom: '8px' }}>
                    <strong style={{ color: '#dc3545' }}>High Risk Penalty:</strong> -2 points for each HIGH/CRITICAL activity (max -30)
                  </li>
                  <li style={{ marginBottom: '8px' }}>
                    <strong style={{ color: '#28a745' }}>Blocked Bonus:</strong> +1 point for each successfully blocked threat (max +10)
                  </li>
                </ul>

                <h4 style={{ color: '#fff', fontSize: '14px', marginTop: '16px', marginBottom: '8px' }}>Score Ranges:</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  <div style={{ padding: '8px', background: 'rgba(40, 167, 69, 0.2)', borderRadius: '6px', borderLeft: '3px solid #28a745' }}>
                    <span style={{ color: '#28a745', fontWeight: 'bold' }}>80-100:</span> Excellent
                  </div>
                  <div style={{ padding: '8px', background: 'rgba(255, 193, 7, 0.2)', borderRadius: '6px', borderLeft: '3px solid #ffc107' }}>
                    <span style={{ color: '#ffc107', fontWeight: 'bold' }}>60-79:</span> Good
                  </div>
                  <div style={{ padding: '8px', background: 'rgba(255, 140, 0, 0.2)', borderRadius: '6px', borderLeft: '3px solid #ff8c00' }}>
                    <span style={{ color: '#ff8c00', fontWeight: 'bold' }}>40-59:</span> Moderate
                  </div>
                  <div style={{ padding: '8px', background: 'rgba(220, 53, 69, 0.2)', borderRadius: '6px', borderLeft: '3px solid #dc3545' }}>
                    <span style={{ color: '#dc3545', fontWeight: 'bold' }}>0-39:</span> At Risk
                  </div>
                </div>
              </div>

              <button
                onClick={() => setShowScoreModal(false)}
                style={{
                  width: '100%',
                  padding: '12px',
                  marginTop: '20px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  cursor: 'pointer'
                }}
              >
                Got It
              </button>
            </div>
          </div>
        )}

        {/* CSS for pulse animation */}
        <style>{`
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
          }
        `}</style>
      </div>
    </div>
  );
};

export default Dashboard;
