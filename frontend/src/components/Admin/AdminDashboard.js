import React, { useState, useEffect } from 'react';
import { dashboardAPI, userAPI } from '../../services/api';
import Sidebar from '../Common/Sidebar';
import Loading from '../Common/Loading';
import { formatTimestamp, getRiskLevelDetails } from '../../utils/helpers';
import './AdminDashboard.css';

const AdminDashboard = () => {
  const [stats, setStats] = useState({});
  const [users, setUsers] = useState([]);
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterDepartment, setFilterDepartment] = useState('all');
  const [filterRisk, setFilterRisk] = useState('all');
  const [reportGenerating, setReportGenerating] = useState(false);
  const [systemHealth, setSystemHealth] = useState({});
  const [settings, setSettings] = useState({
    autoBlockHighRisk: true,
    emailNotifications: true,
    slackIntegration: false,
    riskThresholdHigh: 70,
    riskThresholdMedium: 30,
    sessionTimeout: 480,
    maxLoginAttempts: 5,
  });

  useEffect(() => {
    loadAdminData();
  }, []);

  useEffect(() => {
    filterUsers();
  }, [users, searchTerm, filterDepartment, filterRisk]);

  const loadAdminData = async () => {
    try {
      const [statsRes, usersRes, activitiesRes] = await Promise.all([
        dashboardAPI.getStats(),
        userAPI.getUsers(),
        dashboardAPI.getActivities(50),
      ]);

      setStats(statsRes.data.overview || {});
      setUsers(usersRes.data.users || []);
      setActivities(activitiesRes.data.activities || []);
      setSystemHealth(statsRes.data.system_health || {});
      setLoading(false);
    } catch (error) {
      console.error('Error loading admin data:', error);
      setLoading(false);
    }
  };

  const filterUsers = () => {
    let result = [...users];

    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      result = result.filter(
        (u) =>
          u.full_name?.toLowerCase().includes(search) ||
          u.username?.toLowerCase().includes(search) ||
          u.email?.toLowerCase().includes(search)
      );
    }

    if (filterDepartment !== 'all') {
      result = result.filter((u) => u.department === filterDepartment);
    }

    if (filterRisk !== 'all') {
      result = result.filter((u) => {
        const score = u.current_risk_score || 0;
        if (filterRisk === 'high') return score >= 70;
        if (filterRisk === 'medium') return score >= 30 && score < 70;
        if (filterRisk === 'low') return score < 30;
        return true;
      });
    }

    setFilteredUsers(result);
  };

  const departments = [...new Set(users.map((u) => u.department).filter(Boolean))];

  const generateReport = async () => {
    setReportGenerating(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/reports/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ report_type: 'comprehensive' }),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `IGNISYL_Report_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else {
        alert('Failed to generate report');
      }
    } catch (error) {
      console.error('Error generating report:', error);
      alert('Error generating report');
    }
    setReportGenerating(false);
  };

  const handleSettingChange = (key, value) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  const saveSettings = async () => {
    try {
      await fetch('http://127.0.0.1:8000/api/v1/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(settings),
      });
      alert('Settings saved successfully');
    } catch (error) {
      console.error('Error saving settings:', error);
      alert('Error saving settings');
    }
  };

  if (loading) {
    return <Loading message="Loading admin dashboard..." fullScreen={true} />;
  }

  return (
    <div className="admin-layout">
      <Sidebar />

      <div className="admin-main">
        {/* Admin Header */}
        <div className="admin-header">
          <div>
            <h1 className="admin-title">Admin Dashboard</h1>
            <p className="admin-subtitle">System Administration & Threat Management</p>
          </div>
          <div className="admin-header-actions">
            <button className="btn-admin" onClick={loadAdminData}>
              <span>Refresh</span>
            </button>
            <button
              className="btn-admin btn-primary"
              onClick={generateReport}
              disabled={reportGenerating}
            >
              {reportGenerating ? 'Generating...' : 'Generate PDF Report'}
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="admin-tabs">
          {['overview', 'users', 'reports', 'settings'].map((tab) => (
            <button
              key={tab}
              className={`admin-tab ${activeTab === tab ? 'active' : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab === 'overview' && '📊 '}
              {tab === 'users' && '👥 '}
              {tab === 'reports' && '📄 '}
              {tab === 'settings' && '⚙️ '}
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="admin-content">
          {/* OVERVIEW TAB */}
          {activeTab === 'overview' && (
            <>
              {/* Stats Grid */}
              <div className="admin-stats-grid">
                <div className="admin-stat-card">
                  <div className="stat-icon">👥</div>
                  <div className="stat-info">
                    <div className="stat-value">{stats.total_users || 0}</div>
                    <div className="stat-label">Total Users</div>
                  </div>
                </div>
                <div className="admin-stat-card">
                  <div className="stat-icon">🟢</div>
                  <div className="stat-info">
                    <div className="stat-value">{stats.active_sessions || 0}</div>
                    <div className="stat-label">Active Sessions</div>
                  </div>
                </div>
                <div className="admin-stat-card warning">
                  <div className="stat-icon">⚠️</div>
                  <div className="stat-info">
                    <div className="stat-value">{stats.threats_detected_today || 0}</div>
                    <div className="stat-label">Threats Today</div>
                  </div>
                </div>
                <div className="admin-stat-card danger">
                  <div className="stat-icon">🛡️</div>
                  <div className="stat-info">
                    <div className="stat-value">{stats.threats_blocked || 0}</div>
                    <div className="stat-label">Threats Blocked</div>
                  </div>
                </div>
              </div>

              {/* System Health & Quick Actions */}
              <div className="admin-grid-2">
                <div className="admin-card">
                  <h3 className="card-title">System Health</h3>
                  <div className="health-metrics">
                    <div className="health-metric">
                      <span className="health-label">CPU Usage</span>
                      <div className="health-bar">
                        <div
                          className={`health-fill ${(systemHealth.cpu_usage || 0) > 80 ? 'danger' : (systemHealth.cpu_usage || 0) > 60 ? 'warning' : ''}`}
                          style={{ width: `${systemHealth.cpu_usage || 0}%` }}
                        ></div>
                      </div>
                      <span className="health-value">{(systemHealth.cpu_usage || 0).toFixed(1)}%</span>
                    </div>
                    <div className="health-metric">
                      <span className="health-label">Memory Usage</span>
                      <div className="health-bar">
                        <div
                          className={`health-fill ${(systemHealth.memory_usage || 0) > 80 ? 'danger' : (systemHealth.memory_usage || 0) > 60 ? 'warning' : ''}`}
                          style={{ width: `${systemHealth.memory_usage || 0}%` }}
                        ></div>
                      </div>
                      <span className="health-value">{(systemHealth.memory_usage || 0).toFixed(1)}%</span>
                    </div>
                    <div className="health-metric">
                      <span className="health-label">Disk Usage</span>
                      <div className="health-bar">
                        <div
                          className={`health-fill ${(systemHealth.disk_usage || 0) > 80 ? 'danger' : (systemHealth.disk_usage || 0) > 60 ? 'warning' : ''}`}
                          style={{ width: `${systemHealth.disk_usage || 0}%` }}
                        ></div>
                      </div>
                      <span className="health-value">{(systemHealth.disk_usage || 0).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>

                <div className="admin-card">
                  <h3 className="card-title">Quick Actions</h3>
                  <div className="quick-actions">
                    <button className="action-btn" onClick={() => setActiveTab('users')}>
                      <span className="action-icon">👤</span>
                      <span>Manage Users</span>
                    </button>
                    <button className="action-btn" onClick={generateReport}>
                      <span className="action-icon">📄</span>
                      <span>Generate Report</span>
                    </button>
                    <button className="action-btn" onClick={() => setActiveTab('settings')}>
                      <span className="action-icon">⚙️</span>
                      <span>Settings</span>
                    </button>
                    <button className="action-btn">
                      <span className="action-icon">🔄</span>
                      <span>Retrain ML Model</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Recent Threats */}
              <div className="admin-card">
                <h3 className="card-title">Recent Threat Alerts</h3>
                <div className="threats-list">
                  {activities.slice(0, 5).map((activity, index) => (
                    <div key={index} className={`threat-item ${activity.risk_level?.toLowerCase() || 'low'}`}>
                      <div className="threat-info">
                        <div className="threat-user">{activity.full_name}</div>
                        <div className="threat-activity">{activity.activity_type}</div>
                        <div className="threat-time">{formatTimestamp(activity.timestamp)}</div>
                      </div>
                      <div className="threat-score">
                        <span className={`risk-badge ${activity.risk_level?.toLowerCase() || 'low'}`}>
                          {activity.risk_score || 0}
                        </span>
                      </div>
                    </div>
                  ))}
                  {activities.length === 0 && (
                    <div className="empty-state">No recent threats detected</div>
                  )}
                </div>
              </div>
            </>
          )}

          {/* USERS TAB */}
          {activeTab === 'users' && (
            <div className="admin-card">
              <div className="users-header">
                <h3 className="card-title">User Management</h3>
                <div className="users-filters">
                  <input
                    type="text"
                    placeholder="Search users..."
                    className="search-input"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                  <select
                    className="filter-select"
                    value={filterDepartment}
                    onChange={(e) => setFilterDepartment(e.target.value)}
                  >
                    <option value="all">All Departments</option>
                    {departments.map((dept) => (
                      <option key={dept} value={dept}>
                        {dept}
                      </option>
                    ))}
                  </select>
                  <select
                    className="filter-select"
                    value={filterRisk}
                    onChange={(e) => setFilterRisk(e.target.value)}
                  >
                    <option value="all">All Risk Levels</option>
                    <option value="high">High Risk</option>
                    <option value="medium">Medium Risk</option>
                    <option value="low">Low Risk</option>
                  </select>
                </div>
              </div>

              <div className="users-count">
                Showing {filteredUsers.length} of {users.length} users
              </div>

              <div className="users-table-container">
                <table className="admin-table">
                  <thead>
                    <tr>
                      <th>User</th>
                      <th>Department</th>
                      <th>Role</th>
                      <th>Risk Score</th>
                      <th>Status</th>
                      <th>Last Activity</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredUsers.map((user) => {
                      const riskDetails = getRiskLevelDetails(user.current_risk_score);
                      return (
                        <tr key={user.user_id}>
                          <td>
                            <div className="user-cell">
                              <div className="user-avatar">
                                {user.full_name?.charAt(0) || 'U'}
                              </div>
                              <div className="user-details">
                                <div className="user-name">{user.full_name}</div>
                                <div className="user-email">{user.email || user.username}</div>
                              </div>
                            </div>
                          </td>
                          <td>{user.department}</td>
                          <td>{user.role}</td>
                          <td>
                            <span
                              className={`risk-badge ${riskDetails.label.toLowerCase()}`}
                            >
                              {user.current_risk_score || 0}
                            </span>
                          </td>
                          <td>
                            <span className={`status-badge ${user.status === 'active' ? 'active' : 'inactive'}`}>
                              {user.status || 'active'}
                            </span>
                          </td>
                          <td>{formatTimestamp(user.last_activity)}</td>
                          <td>
                            <div className="action-buttons">
                              <button className="btn-icon" title="View Details">👁️</button>
                              <button className="btn-icon" title="Edit User">✏️</button>
                              <button className="btn-icon danger" title="Block User">🚫</button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* REPORTS TAB */}
          {activeTab === 'reports' && (
            <div className="admin-card">
              <h3 className="card-title">Report Generation</h3>
              <div className="reports-grid">
                <div className="report-card" onClick={generateReport}>
                  <div className="report-icon">📊</div>
                  <div className="report-title">Comprehensive Report</div>
                  <div className="report-desc">
                    Full threat analysis with user risk scores and recommendations
                  </div>
                  <button className="btn-admin btn-primary" disabled={reportGenerating}>
                    {reportGenerating ? 'Generating...' : 'Generate PDF'}
                  </button>
                </div>
                <div className="report-card">
                  <div className="report-icon">👥</div>
                  <div className="report-title">User Activity Report</div>
                  <div className="report-desc">
                    Detailed user activity logs and behavioral analysis
                  </div>
                  <button className="btn-admin">Generate PDF</button>
                </div>
                <div className="report-card">
                  <div className="report-icon">🚨</div>
                  <div className="report-title">Threat Summary</div>
                  <div className="report-desc">
                    Summary of all detected threats and actions taken
                  </div>
                  <button className="btn-admin">Generate PDF</button>
                </div>
                <div className="report-card">
                  <div className="report-icon">📈</div>
                  <div className="report-title">ML Performance Report</div>
                  <div className="report-desc">
                    Machine learning model accuracy and performance metrics
                  </div>
                  <button className="btn-admin">Generate PDF</button>
                </div>
              </div>
            </div>
          )}

          {/* SETTINGS TAB */}
          {activeTab === 'settings' && (
            <div className="settings-container">
              <div className="admin-card">
                <h3 className="card-title">Security Settings</h3>
                <div className="settings-group">
                  <div className="setting-item">
                    <div className="setting-info">
                      <div className="setting-label">Auto-block High Risk Users</div>
                      <div className="setting-desc">
                        Automatically block users when risk score exceeds threshold
                      </div>
                    </div>
                    <label className="toggle-switch">
                      <input
                        type="checkbox"
                        checked={settings.autoBlockHighRisk}
                        onChange={(e) => handleSettingChange('autoBlockHighRisk', e.target.checked)}
                      />
                      <span className="toggle-slider"></span>
                    </label>
                  </div>
                  <div className="setting-item">
                    <div className="setting-info">
                      <div className="setting-label">High Risk Threshold</div>
                      <div className="setting-desc">Score above which users are considered high risk</div>
                    </div>
                    <input
                      type="number"
                      className="setting-input"
                      value={settings.riskThresholdHigh}
                      onChange={(e) => handleSettingChange('riskThresholdHigh', parseInt(e.target.value))}
                      min="0"
                      max="100"
                    />
                  </div>
                  <div className="setting-item">
                    <div className="setting-info">
                      <div className="setting-label">Medium Risk Threshold</div>
                      <div className="setting-desc">Score above which users are considered medium risk</div>
                    </div>
                    <input
                      type="number"
                      className="setting-input"
                      value={settings.riskThresholdMedium}
                      onChange={(e) => handleSettingChange('riskThresholdMedium', parseInt(e.target.value))}
                      min="0"
                      max="100"
                    />
                  </div>
                  <div className="setting-item">
                    <div className="setting-info">
                      <div className="setting-label">Max Login Attempts</div>
                      <div className="setting-desc">Number of failed attempts before account lockout</div>
                    </div>
                    <input
                      type="number"
                      className="setting-input"
                      value={settings.maxLoginAttempts}
                      onChange={(e) => handleSettingChange('maxLoginAttempts', parseInt(e.target.value))}
                      min="1"
                      max="20"
                    />
                  </div>
                </div>
              </div>

              <div className="admin-card">
                <h3 className="card-title">Notification Settings</h3>
                <div className="settings-group">
                  <div className="setting-item">
                    <div className="setting-info">
                      <div className="setting-label">Email Notifications</div>
                      <div className="setting-desc">Receive email alerts for high-risk threats</div>
                    </div>
                    <label className="toggle-switch">
                      <input
                        type="checkbox"
                        checked={settings.emailNotifications}
                        onChange={(e) => handleSettingChange('emailNotifications', e.target.checked)}
                      />
                      <span className="toggle-slider"></span>
                    </label>
                  </div>
                  <div className="setting-item">
                    <div className="setting-info">
                      <div className="setting-label">Slack Integration</div>
                      <div className="setting-desc">Send alerts to Slack channel</div>
                    </div>
                    <label className="toggle-switch">
                      <input
                        type="checkbox"
                        checked={settings.slackIntegration}
                        onChange={(e) => handleSettingChange('slackIntegration', e.target.checked)}
                      />
                      <span className="toggle-slider"></span>
                    </label>
                  </div>
                  <div className="setting-item">
                    <div className="setting-info">
                      <div className="setting-label">Session Timeout (minutes)</div>
                      <div className="setting-desc">Auto-logout after inactivity</div>
                    </div>
                    <input
                      type="number"
                      className="setting-input"
                      value={settings.sessionTimeout}
                      onChange={(e) => handleSettingChange('sessionTimeout', parseInt(e.target.value))}
                      min="5"
                      max="1440"
                    />
                  </div>
                </div>
              </div>

              <div className="settings-actions">
                <button className="btn-admin" onClick={() => window.location.reload()}>
                  Reset to Defaults
                </button>
                <button className="btn-admin btn-primary" onClick={saveSettings}>
                  Save Settings
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
