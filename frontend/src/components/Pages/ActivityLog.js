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
  const [dateRange, setDateRange] = useState('all');
  const [userFilter, setUserFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const itemsPerPage = 50;

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

  // Get unique users for filter dropdown
  const uniqueUsers = [...new Set(activities.map(a => a.username).filter(Boolean))];

  // Date range filter helper
  const isWithinDateRange = (timestamp) => {
    if (dateRange === 'all') return true;
    const activityDate = new Date(timestamp);
    const now = new Date();
    const diffDays = (now - activityDate) / (1000 * 60 * 60 * 24);

    switch (dateRange) {
      case 'today': return diffDays < 1;
      case '7days': return diffDays <= 7;
      case '30days': return diffDays <= 30;
      default: return true;
    }
  };

  const filteredActivities = activities.filter(a => {
    const matchesFilter = filter === 'all' || a.risk_level?.toLowerCase() === filter;
    const matchesSearch = !searchTerm ||
      a.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.activity_type?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDate = isWithinDateRange(a.timestamp);
    const matchesUser = userFilter === 'all' || a.username === userFilter;
    return matchesFilter && matchesSearch && matchesDate && matchesUser;
  });

  // Pagination
  const totalPages = Math.ceil(filteredActivities.length / itemsPerPage);
  const paginatedActivities = filteredActivities.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // Reset to first page when filters change
  const handleFilterChange = (setter) => (value) => {
    setter(value);
    setCurrentPage(1);
  };

  // Export to CSV
  const exportToCSV = () => {
    const headers = ['User', 'Username', 'Activity Type', 'Risk Score', 'Risk Level', 'Action', 'Timestamp'];
    const rows = filteredActivities.map(a => [
      a.full_name || 'Unknown',
      a.username || '',
      a.activity_type || '',
      a.risk_score || 0,
      a.risk_level || 'LOW',
      a.action || 'ALLOW',
      a.timestamp || ''
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `IGNISYL_Activity_Log_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

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
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              className="btn-admin"
              onClick={exportToCSV}
              style={{ backgroundColor: 'rgba(40, 167, 69, 0.8)' }}
              title="Export filtered activities to CSV"
            >
              Export CSV
            </button>
            <button
              className="btn-admin btn-primary"
              onClick={loadActivities}
              disabled={refreshing}
            >
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>

        <div className="admin-card">
          <div className="users-filters" style={{ marginBottom: '16px' }}>
            <input
              type="text"
              placeholder="Search activities..."
              className="search-input"
              value={searchTerm}
              onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
            />
            <select
              className="filter-select"
              value={filter}
              onChange={(e) => handleFilterChange(setFilter)(e.target.value)}
            >
              <option value="all">All Risk Levels</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <button
              className="btn-admin"
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              style={{
                backgroundColor: showAdvancedFilters ? 'rgba(102, 126, 234, 0.3)' : 'rgba(255,255,255,0.1)',
                border: showAdvancedFilters ? '1px solid #667eea' : '1px solid rgba(255,255,255,0.2)'
              }}
            >
              {showAdvancedFilters ? 'Hide Filters' : 'More Filters'}
            </button>
          </div>

          {/* Advanced Filters Panel */}
          {showAdvancedFilters && (
            <div style={{
              padding: '16px',
              backgroundColor: 'rgba(0,0,0,0.2)',
              borderRadius: '8px',
              marginBottom: '16px',
              display: 'flex',
              gap: '16px',
              flexWrap: 'wrap'
            }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ fontSize: '12px', color: '#a8d0ff' }}>Date Range</label>
                <select
                  className="filter-select"
                  value={dateRange}
                  onChange={(e) => handleFilterChange(setDateRange)(e.target.value)}
                >
                  <option value="all">All Time</option>
                  <option value="today">Today</option>
                  <option value="7days">Last 7 Days</option>
                  <option value="30days">Last 30 Days</option>
                </select>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ fontSize: '12px', color: '#a8d0ff' }}>User</label>
                <select
                  className="filter-select"
                  value={userFilter}
                  onChange={(e) => handleFilterChange(setUserFilter)(e.target.value)}
                >
                  <option value="all">All Users</option>
                  {uniqueUsers.map(user => (
                    <option key={user} value={user}>{user}</option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                <button
                  className="btn-admin"
                  onClick={() => {
                    setFilter('all');
                    setDateRange('all');
                    setUserFilter('all');
                    setSearchTerm('');
                    setCurrentPage(1);
                  }}
                  style={{ backgroundColor: 'rgba(220, 53, 69, 0.2)', border: '1px solid rgba(220, 53, 69, 0.4)' }}
                >
                  Clear Filters
                </button>
              </div>
            </div>
          )}

          <div className="users-count" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Showing {paginatedActivities.length} of {filteredActivities.length} activities (Page {currentPage} of {totalPages || 1})</span>
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
                {paginatedActivities.map((activity, index) => {
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
            {paginatedActivities.length === 0 && (
              <div className="empty-state">No activities found</div>
            )}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              gap: '8px',
              marginTop: '20px',
              padding: '16px',
              borderTop: '1px solid rgba(255,255,255,0.1)'
            }}>
              <button
                className="btn-admin"
                onClick={() => setCurrentPage(1)}
                disabled={currentPage === 1}
                style={{ padding: '6px 12px', fontSize: '13px' }}
              >
                First
              </button>
              <button
                className="btn-admin"
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                style={{ padding: '6px 12px', fontSize: '13px' }}
              >
                Previous
              </button>

              <div style={{ display: 'flex', gap: '4px' }}>
                {[...Array(Math.min(5, totalPages))].map((_, i) => {
                  let pageNum;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (currentPage <= 3) {
                    pageNum = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = currentPage - 2 + i;
                  }
                  return (
                    <button
                      key={pageNum}
                      className="btn-admin"
                      onClick={() => setCurrentPage(pageNum)}
                      style={{
                        padding: '6px 12px',
                        fontSize: '13px',
                        backgroundColor: currentPage === pageNum ? '#667eea' : 'rgba(255,255,255,0.1)',
                        minWidth: '40px'
                      }}
                    >
                      {pageNum}
                    </button>
                  );
                })}
              </div>

              <button
                className="btn-admin"
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                style={{ padding: '6px 12px', fontSize: '13px' }}
              >
                Next
              </button>
              <button
                className="btn-admin"
                onClick={() => setCurrentPage(totalPages)}
                disabled={currentPage === totalPages}
                style={{ padding: '6px 12px', fontSize: '13px' }}
              >
                Last
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ActivityLog;
