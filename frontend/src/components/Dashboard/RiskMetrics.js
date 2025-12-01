import React from 'react';

const RiskMetrics = ({ stats }) => {
  return (
    <div className="metrics-grid">
      <div className="metric-card">
        <div className="metric-label">Total Users</div>
        <div className="metric-value">{stats.total_users}</div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Active Sessions</div>
        <div className="metric-value">{stats.active_sessions}</div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Threats Detected</div>
        <div className="metric-value" style={{ color: '#ff9800' }}>
          {stats.threats_detected}
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Threats Blocked</div>
        <div className="metric-value" style={{ color: '#f44336' }}>
          {stats.threats_blocked}
        </div>
      </div>
    </div>
  );
};

export default RiskMetrics;
