import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors (unauthorized)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.clear();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth APIs
export const authAPI = {
  login: (username, password) =>
    axios.post(`${API_BASE}/api/v1/auth/login`, {
      username,
      password,
      ip_address: '127.0.0.1',
    }),
};

// Dashboard APIs
export const dashboardAPI = {
  getStats: () => api.get('/api/v1/dashboard/stats'),
  getActivities: (limit = 50) => api.get(`/api/v1/activities/recent?limit=${limit}`),
  getThreats: () => api.get('/api/v1/threats/active'),
};

// User APIs
export const userAPI = {
  getUsers: () => api.get('/api/v1/users/list'),
  registerUser: (userData) => api.post('/api/v1/users/register', userData),
};

// Analyst APIs
export const analystAPI = {
  getPendingDecisions: () => api.get('/api/v1/analyst/pending-decisions'),
  
  takeAction: (threatId, actionData) =>
    api.post(`/api/v1/analyst/threat/${threatId}/action`, actionData),
  
  contactUser: (threatId, message, method = 'notification') =>
    api.post(`/api/v1/analyst/threat/${threatId}/contact-user`, { message, method }),
  
  escalateThreat: (threatId, escalateTo, notes) =>
    api.post(`/api/v1/analyst/threat/${threatId}/escalate`, { escalate_to: escalateTo, notes }),
  
  getMyActions: (limit = 50) =>
    api.get(`/api/v1/analyst/my-actions?limit=${limit}`),
};

// Report APIs
export const reportAPI = {
  generateUserReport: (userId) =>
    api.post('/api/v1/reports/user', { user_id: userId }),
  
  generateSystemReport: (timePeriod = '24h') =>
    api.post('/api/v1/reports/system', { time_period: timePeriod }),
};

// Firewall APIs
export const firewallAPI = {
  blockUser: (userId, ipAddress, duration = 60) =>
    api.post('/api/v1/firewall/action', {
      user_id: userId,
      action: 'BLOCK',
      duration_minutes: duration,
    }),
  
  restrictUser: (userId, ipAddress, restrictions, duration = 30) =>
    api.post('/api/v1/firewall/action', {
      user_id: userId,
      action: 'RESTRICT',
      restrictions,
      duration_minutes: duration,
    }),
};

// Alert APIs
export const alertAPI = {
  acknowledge: (alertId, reviewer, notes = '') =>
    api.post('/api/v1/alerts/acknowledge', {
      alert_id: alertId,
      reviewer,
      notes,
    }),
};

export default api;
