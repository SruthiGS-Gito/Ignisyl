import React, { useState, useEffect } from 'react';
import { dashboardAPI, userAPI } from '../../services/api';
import Sidebar from '../Common/Sidebar';
import Loading from '../Common/Loading';
import { formatTimestamp, getRiskLevelDetails } from '../../utils/helpers';

const AdminDashboard = () => {
  const [stats, setStats] = useState({});
  const [users, setUsers] = useState([]);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState('overview');

  useEffect(() => {
    loadAdminData();
  }, []);

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
      setLoading(false);
    } catch (error) {
      console.error('Error loading admin data:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return <Loading message="Loading admin dashboard..." fullScreen={true} />;
  }

  return (
    <div className="flex">
      <Sidebar />
      
      <div className="main-content">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-4xl font-bold text-gray-800 mb-8">Admin Dashboard</h1>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="stat-card">
              <div className="text-gray-500 text-sm uppercase mb-2">Total Users</div>
              <div className="text-4xl font-bold text-blue-600">{stats.total_users || 0}</div>
            </div>
            <div className="stat-card">
              <div className="text-gray-500 text-sm uppercase mb-2">Active Sessions</div>
              <div className="text-4xl font-bold text-green-600">{stats.active_sessions || 0}</div>
            </div>
            <div className="stat-card">
              <div className="text-gray-500 text-sm uppercase mb-2">Threats Today</div>
              <div className="text-4xl font-bold text-orange-600">{stats.threats_detected_today || 0}</div>
            </div>
            <div className="stat-card">
              <div className="text-gray-500 text-sm uppercase mb-2">Threats Blocked</div>
              <div className="text-4xl font-bold text-red-600">{stats.threats_blocked || 0}</div>
            </div>
          </div>

          {/* Users Table */}
          <div className="card mb-8">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-800">User Management</h2>
              <button className="btn btn-primary">+ Add User</button>
            </div>

            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Username</th>
                    <th>Full Name</th>
                    <th>Department</th>
                    <th>Role</th>
                    <th>Risk Score</th>
                    <th>Threats</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => {
                    const riskDetails = getRiskLevelDetails(user.current_risk_score);
                    return (
                      <tr key={user.user_id}>
                        <td>{user.username}</td>
                        <td>{user.full_name}</td>
                        <td>{user.department}</td>
                        <td>{user.role}</td>
                        <td>
                          <span
                            className="badge"
                            style={{
                              background: riskDetails.bgColor,
                              color: riskDetails.textColor,
                            }}
                          >
                            {user.current_risk_score}
                          </span>
                        </td>
                        <td>{user.total_threats}</td>
                        <td>
                          <button className="btn btn-primary btn-sm">View</button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Recent Activities */}
          <div className="card">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Recent Activities</h2>
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>User</th>
                    <th>Activity</th>
                    <th>Risk Level</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {activities.slice(0, 10).map((activity, index) => (
                    <tr key={index}>
                      <td>{formatTimestamp(activity.timestamp)}</td>
                      <td>{activity.full_name}</td>
                      <td>{activity.activity_type}</td>
                      <td>
                        <span className={`badge badge-${activity.risk_level === 'HIGH' || activity.risk_level === 'CRITICAL' ? 'danger' : activity.risk_level === 'MEDIUM' ? 'warning' : 'success'}`}>
                          {activity.risk_level}
                        </span>
                      </td>
                      <td>{activity.action}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
