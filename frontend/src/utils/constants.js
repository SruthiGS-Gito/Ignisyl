// IEEE Paper Thresholds: 0-30 ALLOW, 31-50 MONITOR, 51-75 RESTRICT, 76-100 BLOCK
export const RISK_LEVELS = {
  LOW: {
    label: 'LOW',
    color: 'green',
    bgColor: 'rgba(76, 175, 80, 0.2)',
    textColor: '#4caf50',
    threshold: [0, 30]
  },
  MEDIUM: {
    label: 'MEDIUM',
    color: 'yellow',
    bgColor: 'rgba(255, 193, 7, 0.2)',
    textColor: '#ffc107',
    threshold: [31, 50]
  },
  HIGH: {
    label: 'HIGH',
    color: 'orange',
    bgColor: 'rgba(253, 126, 20, 0.2)',
    textColor: '#fd7e14',
    threshold: [51, 75]
  },
  CRITICAL: {
    label: 'CRITICAL',
    color: 'red',
    bgColor: 'rgba(220, 53, 69, 0.2)',
    textColor: '#dc3545',
    threshold: [76, 100]
  },
};

// IEEE Paper Graduated Response Policy
export const RESPONSE_LEVELS = {
  1: {
    level: 1,
    label: 'ALLOW',
    action: 'Normal operations with logging',
    color: 'green',
    description: 'Legitimate business activities',
    threshold: [0, 30]
  },
  2: {
    level: 2,
    label: 'MONITOR',
    action: 'Enhanced monitoring',
    color: 'yellow',
    description: 'Slightly unusual - enhanced logging',
    threshold: [31, 50]
  },
  3: {
    level: 3,
    label: 'RESTRICT',
    action: 'Limited network access',
    color: 'orange',
    description: 'Analyst review required',
    threshold: [51, 75]
  },
  4: {
    level: 4,
    label: 'BLOCK',
    action: 'Auto-blocked + incident response',
    color: 'red',
    description: 'Critical insider threat - auto-blocked',
    threshold: [76, 100]
  },
};

export const ACTIONS = {
  ALLOW: 'ALLOW',
  RESTRICT: 'RESTRICT',
  ISOLATE: 'ISOLATE',
  BLOCK: 'BLOCK',
};

export const ACTIVITY_TYPES = {
  file_access: 'File Access',
  network_access: 'Network Access',
  login: 'Login Attempt',
  data_transfer: 'Data Transfer',
  privilege_escalation: 'Privilege Escalation',
  usb_device: 'USB Device Usage',
  honeypot_access: 'Honeypot Access (CRITICAL)',
};

export const DEFAULT_RESTRICTIONS = {
  block_external_internet: true,
  rate_limit_mbps: 1,
  block_ports: [21, 22, 445, 3389], // FTP, SSH, SMB, RDP
  allow_internal_network: true,
  notify_user: true,
};

export const ESCALATION_TARGETS = [
  { value: 'admin', label: 'Admin' },
  { value: 'manager', label: 'Manager' },
  { value: 'incident_team', label: 'Incident Response Team' },
];

export const DURATION_OPTIONS = [
  { value: 30, label: '30 minutes' },
  { value: 60, label: '1 hour' },
  { value: 240, label: '4 hours' },
  { value: 480, label: '8 hours' },
  { value: 1440, label: '24 hours' },
];

export const API_BASE_URL = "http://127.0.0.1:8000/api/v1";
export const WS_BASE_URL = 'ws://127.0.0.1:8000';
