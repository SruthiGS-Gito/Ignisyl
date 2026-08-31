import React, { useState, useEffect } from 'react';
import { systemAPI } from '../../services/api';
import Sidebar from '../Common/Sidebar';
import Loading from '../Common/Loading';
import { useToast } from '../Common/Toast';
import '../Admin/AdminDashboard.css';

const SystemStatus = () => {
  const [stats, setStats] = useState({});
  const [systemHealth, setSystemHealth] = useState({});
  const [mlPerformance, setMlPerformance] = useState({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const toast = useToast();

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const loadStatus = async () => {
    try {
      setRefreshing(true);
      const response = await systemAPI.getStatus();
      setStats(response.data.overview || {});
      setSystemHealth(response.data.system_health || {});
      setMlPerformance(response.data.ml_performance || {});
      setLoading(false);
      setRefreshing(false);
    } catch (error) {
      console.error('Error loading system status:', error);
      setLoading(false);
      setRefreshing(false);
    }
  };

  const getStatusColor = (value, warning = 60, danger = 80) => {
    if (value >= danger) return 'danger';
    if (value >= warning) return 'warning';
    return '';
  };

  if (loading) {
    return <Loading message="Loading system status..." fullScreen={true} />;
  }

  return (
    <div className="admin-layout">
      <Sidebar />
      <div className="admin-main">
        <div className="admin-header">
          <div>
            <h1 className="admin-title">System Status</h1>
            <p className="admin-subtitle">Real-time system monitoring and health metrics</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span style={{ fontSize: '14px', color: '#a8d0ff' }}>
              Auto-refresh: 10s
            </span>
            <button
              className="btn-admin btn-primary"
              onClick={loadStatus}
              disabled={refreshing}
            >
              {refreshing ? 'Refreshing...' : 'Refresh Now'}
            </button>
          </div>
        </div>

        {/* System Health Overview */}
        <div className="admin-card" style={{ marginBottom: '24px' }}>
          <h3 className="card-title">System Health</h3>
          <div className="health-metrics" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px' }}>
            <div className="health-metric-card">
              <div className="health-metric">
                <span className="health-label">CPU Usage</span>
                <div className="health-bar">
                  <div
                    className={`health-fill ${getStatusColor(systemHealth.cpu_usage || 0)}`}
                    style={{ width: `${systemHealth.cpu_usage || 0}%` }}
                  ></div>
                </div>
                <span className={`health-value ${getStatusColor(systemHealth.cpu_usage || 0)}`}>
                  {(systemHealth.cpu_usage || 0).toFixed(1)}%
                </span>
              </div>
            </div>

            <div className="health-metric-card">
              <div className="health-metric">
                <span className="health-label">Memory Usage</span>
                <div className="health-bar">
                  <div
                    className={`health-fill ${getStatusColor(systemHealth.memory_usage || 0)}`}
                    style={{ width: `${systemHealth.memory_usage || 0}%` }}
                  ></div>
                </div>
                <span className={`health-value ${getStatusColor(systemHealth.memory_usage || 0)}`}>
                  {(systemHealth.memory_usage || 0).toFixed(1)}%
                </span>
              </div>
            </div>

            <div className="health-metric-card">
              <div className="health-metric">
                <span className="health-label">Disk Usage</span>
                <div className="health-bar">
                  <div
                    className={`health-fill ${getStatusColor(systemHealth.disk_usage || 0)}`}
                    style={{ width: `${systemHealth.disk_usage || 0}%` }}
                  ></div>
                </div>
                <span className={`health-value ${getStatusColor(systemHealth.disk_usage || 0)}`}>
                  {(systemHealth.disk_usage || 0).toFixed(1)}%
                </span>
              </div>
            </div>

            <div className="health-metric-card">
              <div className="health-metric">
                <span className="health-label">Network I/O</span>
                <div className="health-bar">
                  <div className="health-fill" style={{ width: '50%' }}></div>
                </div>
                <span className="health-value">
                  {(systemHealth.network_throughput || 0).toFixed(2)} MB
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* ML Performance */}
        <div className="admin-grid-2" style={{ marginBottom: '24px' }}>
          <div className="admin-card">
            <h3 className="card-title">ML Model Performance</h3>
            <div className="health-metrics">
              <div className="health-metric">
                <span className="health-label">Model Accuracy</span>
                <div className="health-bar">
                  <div
                    className="health-fill"
                    style={{ width: `${mlPerformance.accuracy || 0}%`, background: '#10b981' }}
                  ></div>
                </div>
                <span className="health-value" style={{ color: '#10b981' }}>
                  {(mlPerformance.accuracy || 0).toFixed(1)}%
                </span>
              </div>
              <div className="health-metric">
                <span className="health-label">False Positive Rate</span>
                <div className="health-bar">
                  <div
                    className="health-fill"
                    style={{ width: `${(mlPerformance.false_positive_rate || 0) * 100}%`, background: '#ef4444' }}
                  ></div>
                </div>
                <span className="health-value">
                  {((mlPerformance.false_positive_rate || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="health-metric">
                <span className="health-label">Detection Latency</span>
                <span className="health-value">{mlPerformance.detection_latency_ms || 0}ms</span>
              </div>
              <div className="health-metric">
                <span className="health-label">Active Models</span>
                <span className="health-value" style={{ color: '#10b981' }}>{mlPerformance.models_active || 3}</span>
              </div>
            </div>

            {/* ML Model Details */}
            <div style={{ marginTop: '20px', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '16px' }}>
              <h4 style={{ color: '#a8d0ff', fontSize: '13px', marginBottom: '12px', fontWeight: 'bold' }}>
                3-Model Ensemble (IEEE Paper)
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '10px 14px',
                  background: 'rgba(40, 167, 69, 0.1)',
                  borderRadius: '8px',
                  border: '1px solid rgba(40, 167, 69, 0.3)'
                }}>
                  <span style={{ fontSize: '20px' }}>&#127795;</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ color: '#fff', fontWeight: 'bold', fontSize: '14px' }}>Isolation Forest</div>
                    <div style={{ color: 'rgba(255,255,255,0.6)', fontSize: '11px' }}>Unsupervised anomaly detection | Weight: 40%</div>
                  </div>
                  <span style={{ color: '#10b981', fontSize: '12px', fontWeight: 'bold' }}>ACTIVE</span>
                </div>

                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '10px 14px',
                  background: 'rgba(102, 126, 234, 0.1)',
                  borderRadius: '8px',
                  border: '1px solid rgba(102, 126, 234, 0.3)'
                }}>
                  <span style={{ fontSize: '20px' }}>&#129504;</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ color: '#fff', fontWeight: 'bold', fontSize: '14px' }}>Autoencoder</div>
                    <div style={{ color: 'rgba(255,255,255,0.6)', fontSize: '11px' }}>Deep learning pattern recognition | Weight: 40%</div>
                  </div>
                  <span style={{ color: '#10b981', fontSize: '12px', fontWeight: 'bold' }}>ACTIVE</span>
                </div>

                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '10px 14px',
                  background: 'rgba(255, 140, 0, 0.1)',
                  borderRadius: '8px',
                  border: '1px solid rgba(255, 140, 0, 0.3)'
                }}>
                  <span style={{ fontSize: '20px' }}>&#128640;</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ color: '#fff', fontWeight: 'bold', fontSize: '14px' }}>XGBoost</div>
                    <div style={{ color: 'rgba(255,255,255,0.6)', fontSize: '11px' }}>Supervised gradient boosting | Weight: 20%</div>
                  </div>
                  <span style={{ color: '#10b981', fontSize: '12px', fontWeight: 'bold' }}>ACTIVE</span>
                </div>
              </div>
            </div>
          </div>

          <div className="admin-card">
            <h3 className="card-title">Platform Statistics</h3>
            <div className="admin-stats-grid" style={{ gridTemplateColumns: 'repeat(2, 1fr)' }}>
              <div className="admin-stat-card" style={{ padding: '16px' }}>
                <div className="stat-info">
                  <div className="stat-value">{stats.total_users || 0}</div>
                  <div className="stat-label">Total Users</div>
                </div>
              </div>
              <div className="admin-stat-card" style={{ padding: '16px' }}>
                <div className="stat-info">
                  <div className="stat-value">{stats.active_sessions || 0}</div>
                  <div className="stat-label">Active Sessions</div>
                </div>
              </div>
              <div className="admin-stat-card warning" style={{ padding: '16px' }}>
                <div className="stat-info">
                  <div className="stat-value">{stats.threats_detected_today || 0}</div>
                  <div className="stat-label">Threats Today</div>
                </div>
              </div>
              <div className="admin-stat-card danger" style={{ padding: '16px' }}>
                <div className="stat-info">
                  <div className="stat-value">{stats.threats_blocked || 0}</div>
                  <div className="stat-label">Blocked</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* System Information */}
        <div className="admin-card">
          <h3 className="card-title">System Information</h3>
          <div className="detail-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
            <div className="detail-item">
              <label>Platform</label>
              <span>IGNISYL v1.0</span>
            </div>
            <div className="detail-item">
              <label>Backend Status</label>
              <span style={{ color: '#10b981' }}>Online</span>
            </div>
            <div className="detail-item">
              <label>ML Engine</label>
              <span style={{ color: '#10b981' }}>Active (3 Models)</span>
            </div>
            <div className="detail-item">
              <label>Database</label>
              <span style={{ color: '#10b981' }}>Connected</span>
            </div>
            <div className="detail-item">
              <label>WebSocket</label>
              <span style={{ color: '#10b981' }}>Enabled</span>
            </div>
            <div className="detail-item">
              <label>Last Update</label>
              <span>{new Date().toLocaleTimeString()}</span>
            </div>
          </div>

          {/* Database Details */}
          <div style={{
            marginTop: '20px',
            padding: '16px',
            background: 'rgba(0,0,0,0.2)',
            borderRadius: '10px',
            border: '1px solid rgba(255,255,255,0.1)'
          }}>
            <h4 style={{ color: '#a8d0ff', fontSize: '13px', marginBottom: '12px', fontWeight: 'bold' }}>
              Database Configuration
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '11px', marginBottom: '4px' }}>Type</div>
                <div style={{ color: '#fff', fontSize: '14px', fontFamily: 'monospace' }}>SQLite (Development)</div>
              </div>
              <div>
                <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '11px', marginBottom: '4px' }}>Status</div>
                <div style={{ color: '#10b981', fontSize: '14px' }}>Connected</div>
              </div>
              <div style={{ gridColumn: 'span 2' }}>
                <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '11px', marginBottom: '4px' }}>Database Files</div>
                <div style={{
                  padding: '10px 12px',
                  background: 'rgba(0,0,0,0.3)',
                  borderRadius: '6px',
                  fontFamily: 'monospace',
                  fontSize: '12px',
                  color: '#a8d0ff'
                }}>
                  <div>users.db &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; - User accounts & profiles</div>
                  <div>activities.db &nbsp; - Activity logs & threats</div>
                  <div>sessions.db &nbsp;&nbsp;&nbsp; - Authentication sessions</div>
                </div>
              </div>
              <div style={{ gridColumn: 'span 2' }}>
                <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '11px', marginBottom: '4px' }}>Data Path</div>
                <div style={{
                  padding: '8px 12px',
                  background: 'rgba(102, 126, 234, 0.1)',
                  borderRadius: '6px',
                  fontFamily: 'monospace',
                  fontSize: '12px',
                  color: '#667eea',
                  border: '1px solid rgba(102, 126, 234, 0.3)'
                }}>
                  backend/data/
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemStatus;
