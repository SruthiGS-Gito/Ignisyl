import React, { useState, useEffect } from 'react';
import { dashboardAPI } from '../../services/api';
import Sidebar from '../Common/Sidebar';
import Loading from '../Common/Loading';
import { formatTimestamp, getRiskLevelDetails } from '../../utils/helpers';
import '../Admin/AdminDashboard.css';

const ActivityLog = () => {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadActivities();
  }, []);

  const loadActivities = async () => {
    try {
      setRefreshing(true);
      const response = await dashboardAPI.getActivities(200);
      setActivities(response.data.activities || []);
      setLoading(false);
      setRefreshing(false);
    } catch (error) {
      console.error('Error loading activities:', error);
      setLoading(false);
      setRefreshing(false);
    }
  };

  const filteredActivities = activities.filter(a => {
    const matchesFilter = filter === 'all' || a.risk_level?.toLowerCase() === filter;
    const matchesSearch = !searchTerm ||
      a.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.activity_type?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  if (loading) {
    return <Loading message="Loading activity log..." fullScreen={true} />;
  }

  return (
    <div className="admin-layout">
      <Sidebar />
      <div className="admin-main">
        <div className="admin-header">
          <div>
            <h1 className="admin-title">Activity Log</h1>
            <p className="admin-subtitle">Complete user activity history</p>
          </div>
          <button
            className="btn-admin btn-primary"
            onClick={loadActivities}
            disabled={refreshing}
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        <div className="admin-card">
          <div className="users-filters" style={{ marginBottom: '20px' }}>
            <input
              type="text"
              placeholder="Search activities..."
              className="search-input"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <select
              className="filter-select"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            >
              <option value="all">All Risk Levels</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div className="users-count">
            Showing {filteredActivities.length} of {activities.length} activities
          </div>

          <div className="users-table-container">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Activity Type</th>
                  <th>Risk Score</th>
                  <th>Risk Level</th>
                  <th>Action Taken</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {filteredActivities.map((activity, index) => {
                  const riskDetails = getRiskLevelDetails(activity.risk_score);
                  return (
                    <tr key={activity.id || index}>
                      <td>
                        <div className="user-cell">
                          <div className="user-avatar">
                            {activity.full_name?.charAt(0) || 'U'}
                          </div>
                          <div className="user-details">
                            <div className="user-name">{activity.full_name || 'Unknown'}</div>
                            <div className="user-email">{activity.username}</div>
                          </div>
                        </div>
                      </td>
                      <td>{activity.activity_type}</td>
                      <td>
                        <span className={`risk-badge ${riskDetails.label.toLowerCase()}`}>
                          {activity.risk_score || 0}
                        </span>
                      </td>
                      <td>
                        <span className={`status-badge ${activity.risk_level?.toLowerCase() || 'low'}`}>
                          {activity.risk_level || 'LOW'}
                        </span>
                      </td>
                      <td>
                        <span className={`status-badge ${activity.action === 'BLOCK' ? 'danger' : activity.action === 'RESTRICT' ? 'warning' : 'active'}`}>
                          {activity.action || 'ALLOW'}
                        </span>
                      </td>
                      <td>{formatTimestamp(activity.timestamp)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {filteredActivities.length === 0 && (
              <div className="empty-state">No activities found</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ActivityLog;
