import React from 'react';
import { useNavigate } from 'react-router-dom';
import { getCurrentUser, isAdmin } from '../../utils/helpers';

const Header = ({ title, subtitle }) => {
  const navigate = useNavigate();
  const user = getCurrentUser();

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to logout?')) {
      localStorage.clear();
      navigate('/login');
    }
  };

  return (
    <header className="glass-effect rounded-2xl p-6 mb-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold mb-2">🛡️ {title || 'IGNISYL'}</h1>
          <p className="text-blue-200 text-lg">
            {subtitle || 'AI-Powered Insider Threat Detection System'}
          </p>
        </div>
        <div className="flex items-center gap-4">
          {user && (
            <div className="text-right mr-4">
              <div className="font-semibold">{user.full_name}</div>
              <div className="text-sm text-blue-200">{user.role}</div>
            </div>
          )}
          <button
            onClick={handleLogout}
            className="px-6 py-2 bg-red-500 bg-opacity-80 hover:bg-opacity-100 rounded-lg font-semibold transition"
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
