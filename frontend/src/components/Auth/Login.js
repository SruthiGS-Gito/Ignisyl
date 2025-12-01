import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../../services/api';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      const isAdmin = localStorage.getItem('is_admin') === 'true';
      navigate(isAdmin ? '/admin' : '/dashboard');
    }
  }, [navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!username || !password) {
      setError('Please enter both username and password');
      return;
    }

    setLoading(true);

    try {
      const response = await authAPI.login(username, password);
      const data = response.data;

      setSuccess('Authentication successful! Redirecting...');

      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user_info', JSON.stringify(data.user));
      localStorage.setItem('login_time', new Date().toISOString());

      const isAdmin =
        data.user.role &&
        (data.user.role.toLowerCase().includes('admin') ||
          data.user.role.toLowerCase().includes('manager') ||
          data.user.username === 'admin');

      localStorage.setItem('is_admin', isAdmin);

      setTimeout(() => {
        navigate(isAdmin ? '/admin' : '/dashboard');
      }, 1500);
    } catch (err) {
      console.error('Login error:', err);
      setError('Invalid credentials. Please try again.');
      setPassword('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-purple p-5">
      <div className="bg-white rounded-3xl shadow-2xl overflow-hidden max-w-4xl w-full flex">
        {/* Left Side - Branding */}
        <div className="flex-1 bg-gradient-blue text-white p-16 flex flex-col justify-center">
          <div className="mb-8">
            <h1 className="text-5xl font-bold mb-4">🛡️ IGNISYL</h1>
            <p className="text-xl opacity-90 leading-relaxed">
              Enterprise Security Intelligence Platform
            </p>
          </div>

          <div className="space-y-4 mt-8">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-white bg-opacity-20 rounded-full flex items-center justify-center mr-4">
                ✓
              </div>
              <span>Advanced Threat Intelligence</span>
            </div>
            <div className="flex items-center">
              <div className="w-8 h-8 bg-white bg-opacity-20 rounded-full flex items-center justify-center mr-4">
                ✓
              </div>
              <span>Real-time Security Monitoring</span>
            </div>
            <div className="flex items-center">
              <div className="w-8 h-8 bg-white bg-opacity-20 rounded-full flex items-center justify-center mr-4">
                ✓
              </div>
              <span>AI-Powered Risk Analysis</span>
            </div>
            <div className="flex items-center">
              <div className="w-8 h-8 bg-white bg-opacity-20 rounded-full flex items-center justify-center mr-4">
                ✓
              </div>
              <span>Automated Incident Response</span>
            </div>
          </div>
        </div>

        {/* Right Side - Login Form */}
        <div className="flex-1 p-16">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <h2 className="text-3xl font-bold text-gray-800 mb-2">Secure Access</h2>
              <p className="text-gray-600">Enter your credentials to continue</p>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg animate-fadeIn">
                {error}
              </div>
            )}

            {success && (
              <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg animate-fadeIn">
                {success}
              </div>
            )}

            <div>
              <label className="block text-gray-700 font-semibold mb-2">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username"
                disabled={loading}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 transition disabled:bg-gray-100"
                autoComplete="username"
              />
            </div>

            <div>
              <label className="block text-gray-700 font-semibold mb-2">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                disabled={loading}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 transition disabled:bg-gray-100"
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-purple text-white font-semibold py-3 rounded-lg hover:shadow-lg transition transform hover:-translate-y-1 disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none"
            >
              {loading ? 'Authenticating...' : 'Sign In Securely'}
            </button>

            <div className="text-center text-sm text-gray-500 mt-6">
              <p>Protected by IGNISYL Security Systems</p>
              <p className="text-xs mt-1">All access attempts are logged and monitored</p>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
