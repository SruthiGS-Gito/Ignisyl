import React, { useState, useEffect } from 'react';
import { dashboardAPI, userAPI, reportAPI, settingsAPI } from '../../services/api';
import Sidebar from '../Common/Sidebar';
import Loading from '../Common/Loading';
import { useToast } from '../Common/Toast';
import { formatTimestamp, getRiskLevelDetails } from '../../utils/helpers';
import './AdminDashboard.css';

const AdminDashboard = () => {
  const toast = useToast();
  const [stats, setStats] = useState({});
  const [users, setUsers] = useState([]);
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('users');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterDepartment, setFilterDepartment] = useState('all');
  const [filterRisk, setFilterRisk] = useState('all');
  const [systemHealth, setSystemHealth] = useState({});
  const [refreshing, setRefreshing] = useState(false);

  // Modal states
  const [viewModal, setViewModal] = useState({ open: false, user: null, loading: false, data: null });
  const [editModal, setEditModal] = useState({ open: false, user: null, loading: false });
  const [blockModal, setBlockModal] = useState({ open: false, user: null, loading: false, reason: '' });
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [overrideModal, setOverrideModal] = useState({
    open: false,
    user: null,
    loading: false,
    newAction: '',
    reason: '',
    duration: 60
  });

  // Helper function to get automated action based on risk score (IEEE Paper compliance)
  const getAutomatedAction = (riskScore) => {
    if (riskScore >= 76) return { action: 'BLOCK', color: '#dc3545', label: 'BLOCKED', icon: '🚫' };
    if (riskScore >= 51) return { action: 'RESTRICT', color: '#ff8c00', label: 'RESTRICTED', icon: '⚠️' };
    if (riskScore >= 31) return { action: 'MONITOR', color: '#ffc107', label: 'MONITORED', icon: '👁️' };
    return { action: 'ALLOW', color: '#28a745', label: 'ALLOWED', icon: '✓' };
  };

  // Helper to get risk trend indicator
  const getRiskTrend = (user) => {
    // This would normally compare current vs previous risk score
    const score = user.current_risk_score || 0;
    if (score > 50) return { icon: '↑', color: '#dc3545', label: 'Increasing' };
    if (score > 30) return { icon: '→', color: '#ffc107', label: 'Stable' };
    return { icon: '↓', color: '#28a745', label: 'Decreasing' };
  };

  // Settings state
  const [settings, setSettings] = useState({
    autoBlockHighRisk: true,
    emailNotifications: true,
    riskThresholdHigh: 60,
    riskThresholdMedium: 30,
    sessionTimeout: 60,
    maxLoginAttempts: 5,
  });
  const [sessionTimeoutWarning, setSessionTimeoutWarning] = useState(false);
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [settingsSaving, setSettingsSaving] = useState(false);

  useEffect(() => {
    loadAdminData();
    loadSettings();
  }, []);

  useEffect(() => {
    filterUsers();
  }, [users, searchTerm, filterDepartment, filterRisk]);

  const loadAdminData = async () => {
    try {
      setRefreshing(true);
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
      setRefreshing(false);
    } catch (error) {
      console.error('Error loading admin data:', error);
      toast.error('Failed to load dashboard data');
      setLoading(false);
      setRefreshing(false);
    }
  };

  const loadSettings = async () => {
    try {
      setSettingsLoading(true);
      const response = await settingsAPI.getSettings();
      if (response.data.settings) {
        setSettings(response.data.settings);
      }
      setSettingsLoading(false);
    } catch (error) {
      console.error('Error loading settings:', error);
      setSettingsLoading(false);
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
        if (filterRisk === 'high') return score >= 60;
        if (filterRisk === 'medium') return score >= 30 && score < 60;
        if (filterRisk === 'low') return score < 30;
        return true;
      });
    }

    setFilteredUsers(result);
  };

  const departments = [...new Set(users.map((u) => u.department).filter(Boolean))];

  // View User Handler
  const handleViewUser = async (user) => {
    setViewModal({ open: true, user, loading: true, data: null });
    try {
      const response = await userAPI.getUser(user.user_id);
      setViewModal({ open: true, user, loading: false, data: response.data });
    } catch (error) {
      toast.error('Failed to load user details');
      setViewModal({ open: false, user: null, loading: false, data: null });
    }
  };

  // Edit User Handler
  const handleEditUser = (user) => {
    setEditModal({
      open: true,
      user: { ...user },
      loading: false
    });
  };

  const saveUserEdit = async () => {
    setEditModal(prev => ({ ...prev, loading: true }));
    try {
      await userAPI.updateUser(editModal.user.user_id, {
        full_name: editModal.user.full_name,
        department: editModal.user.department,
        role: editModal.user.role,
        email: editModal.user.email,
      });
      toast.success(`User ${editModal.user.full_name} updated successfully`);
      setEditModal({ open: false, user: null, loading: false });
      loadAdminData();
    } catch (error) {
      toast.error('Failed to update user: ' + (error.response?.data?.detail || error.message));
      setEditModal(prev => ({ ...prev, loading: false }));
    }
  };

  // Block User Handler
  const handleBlockUser = (user) => {
    setBlockModal({ open: true, user, loading: false, reason: '' });
  };

  const confirmBlockUser = async () => {
    if (!blockModal.reason.trim()) {
      toast.warning('Please provide a reason for blocking');
      return;
    }

    setBlockModal(prev => ({ ...prev, loading: true }));
    try {
      await userAPI.blockUser(blockModal.user.user_id, blockModal.reason, 60);
      toast.success(`User ${blockModal.user.full_name} has been blocked`);
      setBlockModal({ open: false, user: null, loading: false, reason: '' });
      loadAdminData();
    } catch (error) {
      toast.error('Failed to block user: ' + (error.response?.data?.detail || error.message));
      setBlockModal(prev => ({ ...prev, loading: false }));
    }
  };

  // Unblock User Handler
  const handleUnblockUser = async (user) => {
    if (!window.confirm(`Are you sure you want to unblock ${user.full_name}?`)) return;

    try {
      await userAPI.unblockUser(user.user_id);
      toast.success(`User ${user.full_name} has been unblocked`);
      loadAdminData();
    } catch (error) {
      toast.error('Failed to unblock user');
    }
  };

  // Settings Handlers
  const handleSettingChange = (key, value) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  const saveSettings = async () => {
    setSettingsSaving(true);
    try {
      await settingsAPI.saveSettings(settings);
      toast.success('Settings saved successfully');
    } catch (error) {
      toast.error('Failed to save settings: ' + (error.response?.data?.detail || error.message));
    }
    setSettingsSaving(false);
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
            <h1 className="admin-title">User Management</h1>
            <p className="admin-subtitle">Manage users, permissions, and system settings</p>
          </div>
          <div className="admin-header-actions">
            <button
              className="btn-admin"
              onClick={loadAdminData}
              disabled={refreshing}
            >
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>

        {/* Tab Navigation - Single set of tabs */}
        <div className="admin-tabs">
          {['users', 'settings'].map((tab) => (
            <button
              key={tab}
              className={`admin-tab ${activeTab === tab ? 'active' : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab === 'users' && '👥 '}
              {tab === 'settings' && '⚙️ '}
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="admin-content">
          {/* USERS TAB */}
          {activeTab === 'users' && (
            <div className="admin-card">
              <div className="users-header">
                <h3 className="card-title">All Users</h3>
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
                      <option key={dept} value={dept}>{dept}</option>
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
                      <th style={{ width: '40px' }}>
                        <input
                          type="checkbox"
                          checked={selectedUsers.length === filteredUsers.length && filteredUsers.length > 0}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedUsers(filteredUsers.map(u => u.user_id));
                            } else {
                              setSelectedUsers([]);
                            }
                          }}
                          title="Select all users"
                          style={{ cursor: 'pointer' }}
                        />
                      </th>
                      <th>User</th>
                      <th>Department</th>
                      <th>Role</th>
                      <th>Risk Score</th>
                      <th>AI Action</th>
                      <th>Trend</th>
                      <th>Last Activity</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredUsers.map((user) => {
                      const riskScore = user.current_risk_score || 0;
                      const riskDetails = getRiskLevelDetails(riskScore);
                      const autoAction = getAutomatedAction(riskScore);
                      const trend = getRiskTrend(user);
                      const isOverridden = user.status === 'blocked' || user.status === 'restricted';
                      return (
                        <tr key={user.user_id} className={autoAction.action === 'BLOCK' ? 'blocked-row' : ''}>
                          <td onClick={(e) => e.stopPropagation()}>
                            <input
                              type="checkbox"
                              checked={selectedUsers.includes(user.user_id)}
                              onChange={() => {
                                setSelectedUsers(prev =>
                                  prev.includes(user.user_id)
                                    ? prev.filter(id => id !== user.user_id)
                                    : [...prev, user.user_id]
                                );
                              }}
                              style={{ cursor: 'pointer' }}
                            />
                          </td>
                          <td>
                            <div className="user-cell">
                              <div className="user-avatar" style={{
                                background: `linear-gradient(135deg, ${autoAction.color}80 0%, ${autoAction.color} 100%)`
                              }}>
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
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <span className={`risk-badge ${riskDetails.label.toLowerCase()}`}>
                                {riskScore}
                              </span>
                            </div>
                          </td>
                          <td>
                            <div style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '6px',
                              padding: '6px 12px',
                              borderRadius: '6px',
                              background: `${autoAction.color}20`,
                              border: `1px solid ${autoAction.color}`,
                              width: 'fit-content'
                            }}>
                              <span>{autoAction.icon}</span>
                              <span style={{ color: autoAction.color, fontWeight: 'bold', fontSize: '12px' }}>
                                {autoAction.label}
                              </span>
                              {isOverridden && (
                                <span style={{ color: '#ff6b6b', fontSize: '10px' }}>(Override)</span>
                              )}
                            </div>
                          </td>
                          <td>
                            <span style={{ color: trend.color, fontWeight: 'bold', fontSize: '16px' }} title={trend.label}>
                              {trend.icon}
                            </span>
                          </td>
                          <td>{formatTimestamp(user.last_activity)}</td>
                          <td>
                            <div className="action-buttons" style={{ position: 'relative' }}>
                              <button
                                className="btn-icon"
                                title="View Details - See user profile, activities, and statistics"
                                onClick={() => handleViewUser(user)}
                                style={{ position: 'relative' }}
                              >
                                👁️
                                <span style={{
                                  position: 'absolute',
                                  bottom: '-20px',
                                  left: '50%',
                                  transform: 'translateX(-50%)',
                                  fontSize: '9px',
                                  color: '#a8d0ff',
                                  whiteSpace: 'nowrap',
                                  opacity: 0.7
                                }}>View</span>
                              </button>
                              <button
                                className="btn-icon"
                                title="Edit User - Modify name, department, role, and email"
                                onClick={() => handleEditUser(user)}
                                style={{ position: 'relative' }}
                              >
                                ✏️
                                <span style={{
                                  position: 'absolute',
                                  bottom: '-20px',
                                  left: '50%',
                                  transform: 'translateX(-50%)',
                                  fontSize: '9px',
                                  color: '#a8d0ff',
                                  whiteSpace: 'nowrap',
                                  opacity: 0.7
                                }}>Edit</span>
                              </button>
                              <button
                                className="btn-icon"
                                title="Quick Actions - Override AI decision (ALLOW/MONITOR/RESTRICT/BLOCK)"
                                style={{ background: 'rgba(102, 126, 234, 0.2)', position: 'relative' }}
                                onClick={() => setOverrideModal({
                                  open: true,
                                  user: user,
                                  loading: false,
                                  newAction: autoAction.action,
                                  reason: '',
                                  duration: 60
                                })}
                              >
                                ⚡
                                <span style={{
                                  position: 'absolute',
                                  bottom: '-20px',
                                  left: '50%',
                                  transform: 'translateX(-50%)',
                                  fontSize: '9px',
                                  color: '#a8d0ff',
                                  whiteSpace: 'nowrap',
                                  opacity: 0.7
                                }}>Actions</span>
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                {filteredUsers.length === 0 && (
                  <div className="empty-state">No users found matching your criteria</div>
                )}
              </div>
            </div>
          )}

          {/* SETTINGS TAB */}
          {activeTab === 'settings' && (
            <div className="settings-container">
              {settingsLoading ? (
                <Loading message="Loading settings..." />
              ) : (
                <>
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
                          <div className="setting-label">Session Timeout (minutes)</div>
                          <div className="setting-desc">Auto-logout after inactivity</div>
                        </div>
                        <input
                          type="number"
                          className="setting-input"
                          value={settings.sessionTimeout}
                          onChange={(e) => {
                            const value = parseInt(e.target.value) || 60;
                            handleSettingChange('sessionTimeout', value);
                            if (value > 120) {
                              setSessionTimeoutWarning(true);
                            } else {
                              setSessionTimeoutWarning(false);
                            }
                          }}
                          min="5"
                          max="1440"
                        />
                      </div>
                      {sessionTimeoutWarning && (
                        <div style={{
                          marginTop: '12px',
                          padding: '12px 16px',
                          backgroundColor: 'rgba(255, 193, 7, 0.15)',
                          border: '1px solid #ffc107',
                          borderRadius: '8px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '10px'
                        }}>
                          <span style={{ fontSize: '20px' }}>&#9888;</span>
                          <div>
                            <div style={{ color: '#ffc107', fontWeight: 'bold', marginBottom: '4px' }}>
                              Security Warning
                            </div>
                            <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: '13px' }}>
                              Session timeout over 2 hours is not recommended for a security system.
                              Long sessions increase the risk of unauthorized access if a workstation is left unattended.
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="settings-actions">
                    <button className="btn-admin" onClick={loadSettings}>
                      Reset
                    </button>
                    <button
                      className="btn-admin btn-primary"
                      onClick={saveSettings}
                      disabled={settingsSaving}
                    >
                      {settingsSaving ? 'Saving...' : 'Save Settings'}
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* VIEW USER MODAL */}
      {viewModal.open && (
        <div className="modal-overlay" onClick={() => setViewModal({ open: false, user: null, loading: false, data: null })}>
          <div className="modal-content modal-large" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>User Details: {viewModal.user?.full_name}</h2>
              <button className="modal-close" onClick={() => setViewModal({ open: false, user: null, loading: false, data: null })}>×</button>
            </div>
            <div className="modal-body">
              {viewModal.loading ? (
                <Loading message="Loading user details..." />
              ) : viewModal.data ? (
                <>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <label>Full Name</label>
                      <span>{viewModal.data.user?.full_name}</span>
                    </div>
                    <div className="detail-item">
                      <label>Username</label>
                      <span>{viewModal.data.user?.username}</span>
                    </div>
                    <div className="detail-item">
                      <label>Email</label>
                      <span>{viewModal.data.user?.email || 'N/A'}</span>
                    </div>
                    <div className="detail-item">
                      <label>Department</label>
                      <span>{viewModal.data.user?.department}</span>
                    </div>
                    <div className="detail-item">
                      <label>Role</label>
                      <span>{viewModal.data.user?.role}</span>
                    </div>
                    <div className="detail-item">
                      <label>Status</label>
                      <span className={`status-badge ${viewModal.data.user?.status === 'blocked' ? 'blocked' : 'active'}`}>
                        {viewModal.data.user?.status || 'active'}
                      </span>
                    </div>
                    <div className="detail-item">
                      <label>Risk Score</label>
                      <span className={`risk-badge ${getRiskLevelDetails(viewModal.data.user?.current_risk_score).label.toLowerCase()}`}>
                        {viewModal.data.user?.current_risk_score || 0}
                      </span>
                    </div>
                    <div className="detail-item">
                      <label>Total Threats</label>
                      <span>{viewModal.data.user?.total_threats || 0}</span>
                    </div>
                  </div>

                  <h3 style={{ marginTop: '24px', marginBottom: '16px' }}>Activity Statistics</h3>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <label>Total Activities</label>
                      <span>{viewModal.data.stats?.total_activities || 0}</span>
                    </div>
                    <div className="detail-item">
                      <label>High Risk Activities</label>
                      <span style={{ color: '#ef4444' }}>{viewModal.data.stats?.high_risk_activities || 0}</span>
                    </div>
                    <div className="detail-item">
                      <label>Blocked Actions</label>
                      <span>{viewModal.data.stats?.blocked_actions || 0}</span>
                    </div>
                    <div className="detail-item">
                      <label>Average Risk Score</label>
                      <span>{(viewModal.data.stats?.average_risk_score || 0).toFixed(1)}</span>
                    </div>
                  </div>

                  {viewModal.data.activities?.length > 0 && (
                    <>
                      <h3 style={{ marginTop: '24px', marginBottom: '16px' }}>Recent Activities</h3>
                      <div className="mini-table">
                        <table className="admin-table">
                          <thead>
                            <tr>
                              <th>Activity</th>
                              <th>Risk</th>
                              <th>Action</th>
                              <th>Time</th>
                            </tr>
                          </thead>
                          <tbody>
                            {viewModal.data.activities.slice(0, 5).map((activity, i) => (
                              <tr key={i}>
                                <td>{activity.activity_type}</td>
                                <td>
                                  <span className={`risk-badge ${getRiskLevelDetails(activity.risk_score).label.toLowerCase()}`}>
                                    {activity.risk_score}
                                  </span>
                                </td>
                                <td>{activity.action}</td>
                                <td>{formatTimestamp(activity.timestamp)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </>
                  )}
                </>
              ) : (
                <div className="empty-state">Failed to load user data</div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn-admin" onClick={() => setViewModal({ open: false, user: null, loading: false, data: null })}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* EDIT USER MODAL */}
      {editModal.open && (
        <div className="modal-overlay" onClick={() => setEditModal({ open: false, user: null, loading: false })}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Edit User</h2>
              <button className="modal-close" onClick={() => setEditModal({ open: false, user: null, loading: false })}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>Full Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={editModal.user?.full_name || ''}
                  onChange={(e) => setEditModal(prev => ({
                    ...prev,
                    user: { ...prev.user, full_name: e.target.value }
                  }))}
                />
              </div>
              <div className="form-group">
                <label>Department</label>
                <input
                  type="text"
                  className="form-input"
                  value={editModal.user?.department || ''}
                  onChange={(e) => setEditModal(prev => ({
                    ...prev,
                    user: { ...prev.user, department: e.target.value }
                  }))}
                />
              </div>
              <div className="form-group">
                <label>Role</label>
                <select
                  className="form-input"
                  value={editModal.user?.role || ''}
                  onChange={(e) => setEditModal(prev => ({
                    ...prev,
                    user: { ...prev.user, role: e.target.value }
                  }))}
                >
                  <option value="User">User</option>
                  <option value="Analyst">Analyst</option>
                  <option value="Manager">Manager</option>
                  <option value="Administrator">Administrator</option>
                </select>
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  className="form-input"
                  value={editModal.user?.email || ''}
                  onChange={(e) => setEditModal(prev => ({
                    ...prev,
                    user: { ...prev.user, email: e.target.value }
                  }))}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-admin" onClick={() => setEditModal({ open: false, user: null, loading: false })}>
                Cancel
              </button>
              <button
                className="btn-admin btn-primary"
                onClick={saveUserEdit}
                disabled={editModal.loading}
              >
                {editModal.loading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* BLOCK USER MODAL */}
      {blockModal.open && (
        <div className="modal-overlay" onClick={() => setBlockModal({ open: false, user: null, loading: false, reason: '' })}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Block User</h2>
              <button className="modal-close" onClick={() => setBlockModal({ open: false, user: null, loading: false, reason: '' })}>×</button>
            </div>
            <div className="modal-body">
              <div className="warning-box">
                <span className="warning-icon">⚠️</span>
                <div>
                  <strong>Warning:</strong> You are about to block <strong>{blockModal.user?.full_name}</strong>.
                  This will prevent the user from logging in and accessing the system.
                </div>
              </div>
              <div className="form-group" style={{ marginTop: '20px' }}>
                <label>Reason for blocking (required)</label>
                <textarea
                  className="form-input"
                  rows="3"
                  placeholder="Enter the reason for blocking this user..."
                  value={blockModal.reason}
                  onChange={(e) => setBlockModal(prev => ({ ...prev, reason: e.target.value }))}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-admin" onClick={() => setBlockModal({ open: false, user: null, loading: false, reason: '' })}>
                Cancel
              </button>
              <button
                className="btn-admin btn-danger"
                onClick={confirmBlockUser}
                disabled={blockModal.loading || !blockModal.reason.trim()}
              >
                {blockModal.loading ? 'Blocking...' : 'Confirm Block'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* OVERRIDE AI ACTION MODAL */}
      {overrideModal.open && overrideModal.user && (
        <div className="modal-overlay" onClick={() => setOverrideModal({ open: false, user: null, loading: false, newAction: '', reason: '', duration: 60 })}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Override AI Action</h2>
              <button className="modal-close" onClick={() => setOverrideModal({ open: false, user: null, loading: false, newAction: '', reason: '', duration: 60 })}>×</button>
            </div>
            <div className="modal-body">
              <div style={{
                padding: '16px',
                background: 'rgba(102, 126, 234, 0.1)',
                borderRadius: '10px',
                marginBottom: '20px',
                border: '1px solid rgba(102, 126, 234, 0.3)'
              }}>
                <div style={{ fontSize: '14px', color: '#a8d0ff', marginBottom: '8px' }}>
                  <strong>IGNISYL AI-Driven Response System</strong>
                </div>
                <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.7)' }}>
                  The AI automatically determines actions based on risk scores. Override only when
                  manual intervention is justified. All overrides are logged for audit.
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
                <div style={{ padding: '12px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
                  <div style={{ fontSize: '12px', color: '#a8d0ff' }}>User</div>
                  <div style={{ fontSize: '16px', color: '#fff', fontWeight: 'bold' }}>{overrideModal.user.full_name}</div>
                </div>
                <div style={{ padding: '12px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
                  <div style={{ fontSize: '12px', color: '#a8d0ff' }}>Current Risk Score</div>
                  <div style={{ fontSize: '16px', color: getAutomatedAction(overrideModal.user.current_risk_score || 0).color, fontWeight: 'bold' }}>
                    {overrideModal.user.current_risk_score || 0} - {getAutomatedAction(overrideModal.user.current_risk_score || 0).label}
                  </div>
                </div>
              </div>

              <div className="form-group">
                <label>New Action</label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', marginTop: '8px' }}>
                  {[
                    { action: 'ALLOW', color: '#28a745', icon: '✓' },
                    { action: 'MONITOR', color: '#ffc107', icon: '👁️' },
                    { action: 'RESTRICT', color: '#ff8c00', icon: '⚠️' },
                    { action: 'BLOCK', color: '#dc3545', icon: '🚫' }
                  ].map(opt => (
                    <button
                      key={opt.action}
                      onClick={() => setOverrideModal(prev => ({ ...prev, newAction: opt.action }))}
                      style={{
                        padding: '12px 8px',
                        border: overrideModal.newAction === opt.action ? `2px solid ${opt.color}` : '1px solid rgba(255,255,255,0.2)',
                        background: overrideModal.newAction === opt.action ? `${opt.color}20` : 'rgba(0,0,0,0.2)',
                        borderRadius: '8px',
                        color: opt.color,
                        cursor: 'pointer',
                        fontWeight: 'bold',
                        fontSize: '12px',
                        transition: 'all 0.2s'
                      }}
                    >
                      <div>{opt.icon}</div>
                      <div>{opt.action}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label>Duration</label>
                <select
                  className="form-input"
                  value={overrideModal.duration}
                  onChange={(e) => setOverrideModal(prev => ({ ...prev, duration: parseInt(e.target.value) }))}
                >
                  <option value={30}>30 minutes</option>
                  <option value={60}>1 hour</option>
                  <option value={240}>4 hours</option>
                  <option value={480}>8 hours</option>
                  <option value={1440}>24 hours</option>
                  <option value={10080}>1 week</option>
                </select>
              </div>

              <div className="form-group">
                <label>Justification (Required for Audit) *</label>
                <textarea
                  className="form-input"
                  rows="3"
                  placeholder="Explain why you are overriding the AI decision..."
                  value={overrideModal.reason}
                  onChange={(e) => setOverrideModal(prev => ({ ...prev, reason: e.target.value }))}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-admin" onClick={() => setOverrideModal({ open: false, user: null, loading: false, newAction: '', reason: '', duration: 60 })}>
                Cancel
              </button>
              <button
                className="btn-admin btn-primary"
                onClick={async () => {
                  if (!overrideModal.reason.trim()) {
                    toast.warning('Justification is required for audit trail');
                    return;
                  }
                  setOverrideModal(prev => ({ ...prev, loading: true }));
                  try {
                    // Apply the override via firewall API
                    await userAPI.blockUser(overrideModal.user.user_id,
                      `[OVERRIDE] ${overrideModal.newAction}: ${overrideModal.reason}`,
                      overrideModal.duration
                    );
                    toast.success(`Action override applied: ${overrideModal.newAction}`);
                    setOverrideModal({ open: false, user: null, loading: false, newAction: '', reason: '', duration: 60 });
                    loadAdminData();
                  } catch (error) {
                    toast.error('Failed to apply override: ' + (error.response?.data?.detail || error.message));
                    setOverrideModal(prev => ({ ...prev, loading: false }));
                  }
                }}
                disabled={overrideModal.loading || !overrideModal.reason.trim() || !overrideModal.newAction}
              >
                {overrideModal.loading ? 'Applying...' : 'Apply Override'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
