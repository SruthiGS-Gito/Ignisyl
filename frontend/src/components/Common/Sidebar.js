import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { getCurrentUser, isAdmin } from '../../utils/helpers';

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const user = getCurrentUser();
  const admin = isAdmin();

  const menuItems = [
    { path: '/dashboard', icon: '📊', label: 'Dashboard', adminOnly: false },
    { path: '/admin', icon: '👤', label: 'User Management', adminOnly: true },
    { path: '/analyst-control', icon: '🎯', label: 'Analyst Control', adminOnly: false },
    { path: '/activities', icon: '📋', label: 'Activity Log', adminOnly: false },
    { path: '/reports', icon: '📄', label: 'Reports', adminOnly: false },
    { path: '/threats', icon: '🚨', label: 'Active Threats', adminOnly: false },
    { path: '/system', icon: '⚙️', label: 'System Status', adminOnly: true },
  ];

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to logout?')) {
      localStorage.clear();
      navigate('/login');
    }
  };

  return (
    <div className="sidebar">
      <div className="p-6 border-b border-white border-opacity-20">
        <h1 className="text-2xl font-bold">🛡️ IGNISYL</h1>
      </div>

      <nav className="p-4">
        <ul className="space-y-2">
          {menuItems.map((item) => {
            // Hide admin-only items for non-admins
            if (item.adminOnly && !admin) return null;

            const isActive = location.pathname === item.path;

            return (
              <li key={item.path}>
                <button
                  onClick={() => navigate(item.path)}
                  className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition ${
                    isActive
                      ? 'bg-white bg-opacity-20 font-semibold'
                      : 'hover:bg-white hover:bg-opacity-10'
                  }`}
                >
                  <span className="text-xl">{item.icon}</span>
                  <span>{item.label}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* User Profile */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-white border-opacity-20">
        <div className="flex items-center mb-4">
          <div className="w-10 h-10 rounded-full bg-white bg-opacity-30 flex items-center justify-center font-bold text-lg mr-3">
            {user?.full_name?.charAt(0).toUpperCase() || 'U'}
          </div>
          <div className="flex-1">
            <div className="font-semibold">{user?.full_name || 'User'}</div>
            <div className="text-sm opacity-80">{user?.role || 'Role'}</div>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full py-2 bg-red-500 bg-opacity-80 hover:bg-opacity-100 rounded-lg font-semibold transition"
        >
          Logout
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
