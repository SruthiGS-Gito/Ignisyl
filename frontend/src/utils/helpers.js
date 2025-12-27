import { RISK_LEVELS } from './constants';

/**
 * Get risk color based on score
 * IEEE Paper Thresholds: 0-30 ALLOW, 31-50 MONITOR, 51-75 RESTRICT, 76-100 BLOCK
 */
export const getRiskColor = (score) => {
  if (score <= 30) return 'green';
  if (score <= 50) return 'yellow';
  if (score <= 75) return 'orange';
  return 'red';
};

/**
 * Get risk level label based on score
 * IEEE Paper Thresholds: 0-30 LOW, 31-50 MEDIUM, 51-75 HIGH, 76-100 CRITICAL
 */
export const getRiskLevel = (score) => {
  if (score <= 30) return 'LOW';
  if (score <= 50) return 'MEDIUM';
  if (score <= 75) return 'HIGH';
  return 'CRITICAL';
};

/**
 * Get risk level details (color, bgColor, etc.)
 * IEEE Paper Thresholds: 0-30 LOW, 31-50 MEDIUM, 51-75 HIGH, 76-100 CRITICAL
 */
export const getRiskLevelDetails = (score) => {
  if (score <= 30) return RISK_LEVELS.LOW;
  if (score <= 50) return RISK_LEVELS.MEDIUM;
  if (score <= 75) return RISK_LEVELS.HIGH;
  return RISK_LEVELS.CRITICAL;
};

/**
 * Get AI automated action based on risk score
 * IEEE Paper Graduated Response Policy:
 * 0-30: ALLOW (Low risk, normal access)
 * 31-50: MONITOR (Medium risk, enhanced monitoring)
 * 51-75: RESTRICT (High risk, limited access)
 * 76-100: BLOCK (Critical risk, auto-block)
 */
export const getAIAction = (score) => {
  if (score <= 30) return { action: 'ALLOW', icon: '✓', color: '#28a745', description: 'Normal access allowed' };
  if (score <= 50) return { action: 'MONITOR', icon: '👁', color: '#ffc107', description: 'Enhanced monitoring active' };
  if (score <= 75) return { action: 'RESTRICT', icon: '⚡', color: '#fd7e14', description: 'Access restricted' };
  return { action: 'BLOCK', icon: '🚫', color: '#dc3545', description: 'Auto-blocked by system' };
};

/**
 * Format timestamp to readable string
 */
export const formatTimestamp = (timestamp) => {
  if (!timestamp) return 'N/A';
  return new Date(timestamp).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

/**
 * Format date only
 */
export const formatDate = (timestamp) => {
  if (!timestamp) return 'N/A';
  return new Date(timestamp).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
  });
};

/**
 * Format time only
 */
export const formatTime = (timestamp) => {
  if (!timestamp) return 'N/A';
  return new Date(timestamp).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

/**
 * Show browser notification
 */
export const showBrowserNotification = (title, body) => {
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification(title, { 
      body, 
      icon: '🛡️',
      tag: 'ignisyl-notification',
    });
  }
};

/**
 * Request notification permission
 */
export const requestNotificationPermission = () => {
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission().then((permission) => {
      console.log('Notification permission:', permission);
    });
  }
};

/**
 * Format bytes to readable size
 */
export const formatBytes = (bytes, decimals = 2) => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

/**
 * Capitalize first letter
 */
export const capitalize = (str) => {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};

/**
 * Format activity type to readable string
 */
export const formatActivityType = (type) => {
  if (!type) return 'Unknown';
  return type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
};

/**
 * Get action badge color
 */
export const getActionBadgeColor = (action) => {
  const colors = {
    ALLOW: 'badge-success',
    MONITOR: 'badge-warning',
    RESTRICT: 'badge-warning',
    ISOLATE: 'badge-danger',
    BLOCK: 'badge-danger',
  };
  return colors[action] || 'badge-warning';
};

/**
 * Truncate text
 */
export const truncate = (str, maxLength = 50) => {
  if (!str) return '';
  if (str.length <= maxLength) return str;
  return str.substring(0, maxLength) + '...';
};

/**
 * Validate email
 */
export const validateEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
};

/**
 * Get initials from name
 */
export const getInitials = (name) => {
  if (!name) return '?';
  const parts = name.split(' ');
  if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
  return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
};

/**
 * Check if user is admin
 */
export const isAdmin = () => {
  return localStorage.getItem('is_admin') === 'true';
};

/**
 * Get current user info
 */
export const getCurrentUser = () => {
  const userInfo = localStorage.getItem('user_info');
  return userInfo ? JSON.parse(userInfo) : null;
};

/**
 * Logout user
 */
export const logout = () => {
  localStorage.clear();
  window.location.href = '/login';
};
