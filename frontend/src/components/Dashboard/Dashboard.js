import React, { useState, useEffect } from 'react';
import { dashboardAPI } from '../../services/api';
import websocketService from '../../services/websocket';
import { requestNotificationPermission, showBrowserNotification } from '../../utils/helpers';
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

      if (data.recent_activities) {
        setRecentActivities(data.recent_activities.slice(0, 10));
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
        <Header title="IGNISYL Dashboard" subtitle="Real-time Threat Monitoring" />

        {/* Status Bar */}
        <div className="dashboard-header">
          <div className="status-bar">
            <div className="status-item">
              <span className={`threat-indicator ${connected ? 'active' : 'inactive'}`}></span>
              Status: <strong>{connected ? 'CONNECTED' : 'DISCONNECTED'}</strong>
            </div>
            <div className="status-item">ML Engine: Active</div>
            <div className="status-item">Real-time Monitoring: Enabled</div>
            <div className="status-item">Last Update: {lastUpdate}</div>
          </div>
        </div>

        {/* Risk Metrics */}
        <RiskMetrics stats={stats} />

        {/* Alerts Panel & User Table */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <AlertsPanel activities={recentActivities} onRefresh={loadDashboard} />
          <UserTable activities={recentActivities} />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
