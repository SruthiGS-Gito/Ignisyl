<<<START API_Documentation.md>>>
# IGNISYL - API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Core Endpoints](#core-endpoints)
4. [WebSocket API](#websocket-api)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)

---

## Overview

IGNISYL provides a RESTful API for insider threat detection and adaptive firewall control.

**Base URL:** `http://localhost:8000/api/v1`

**Content-Type:** `application/json`

---

## Authentication

### Login
```http
POST /api/v1/auth/login
```

**Request Body:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response (200 OK):**
```json
{
  "message": "Login successful",
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "user_id": "admin",
    "username": "admin",
    "full_name": "System Administrator",
    "role": "admin"
  }
}
```

### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "user_id": "admin",
  "username": "admin",
  "full_name": "System Administrator",
  "email": "admin@company.com",
  "department": "IT Security",
  "role": "admin"
}
```

---

## Core Endpoints

### 1. Analyze Activity
```http
POST /api/v1/analyze
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "user_id": "sruthi_g_s",
  "activity_type": "file_access",
  "timestamp": "2025-10-21T14:30:00",
  "file_path": "/confidential/salary_data.xlsx",
  "file_size": 5242880,
  "bytes_transferred": 5242880,
  "source_ip": "192.168.1.105",
  "location": "Mumbai"
}
```

**Response (200 OK):**
```json
{
  "risk_score": 78.5,
  "risk_level": "HIGH",
  "action": "RESTRICT",
  "ml_scores": {
    "isolation_forest": 0.72,
    "autoencoder": 0.81,
    "xgboost": 0.83
  },
  "triggered_factors": [
    "Large file transfer (5.0 MB)",
    "Sensitive file access",
    "Unusual time (after hours)"
  ],
  "recommendations": [
    "Block file transfer immediately",
    "Alert security team",
    "Review user access permissions"
  ]
}
```

### 2. Get User Activities
```http
GET /api/v1/activities/{user_id}?limit=50
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "user_id": "sruthi_g_s",
  "activities": [
    {
      "id": 1,
      "activity_type": "file_access",
      "timestamp": "2025-10-21T14:30:00",
      "risk_score": 78.5,
      "risk_level": "HIGH",
      "action": "RESTRICT",
      "description": "Accessed confidential salary data"
    }
  ],
  "total": 1
}
```

### 3. Get All Users
```http
GET /api/v1/users
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "users": [
    {
      "user_id": "admin",
      "username": "admin",
      "full_name": "System Administrator",
      "department": "IT Security",
      "role": "admin",
      "email": "admin@company.com"
    },
    {
      "user_id": "sruthi_g_s",
      "username": "sruthi_g_s",
      "full_name": "Sruthi G S",
      "department": "Finance",
      "role": "analyst",
      "email": "sruthi.gs@company.com"
    }
  ],
  "total": 5
}
```

### 4. Apply Firewall Block
```http
POST /api/v1/firewall/block
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "user_id": "sruthi_g_s",
  "reason": "High-risk data exfiltration attempt",
  "duration_minutes": 60
}
```

**Response (200 OK):**
```json
{
  "message": "User blocked successfully",
  "rule_id": "FW_BLOCK_20251021_143045",
  "user_id": "sruthi_g_s",
  "action": "BLOCK",
  "expires_at": "2025-10-21T15:30:45"
}
```

### 5. Apply Firewall Restriction
```http
POST /api/v1/firewall/restrict
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "user_id": "sruthi_g_s",
  "restriction_type": "block_external",
  "reason": "Suspicious network activity",
  "duration_minutes": 30
}
```

**Response (200 OK):**
```json
{
  "message": "Restriction applied successfully",
  "rule_id": "FW_RESTRICT_20251021_143100",
  "restriction_type": "block_external",
  "expires_at": "2025-10-21T15:01:00"
}
```

### 6. Generate Threat Report
```http
POST /api/v1/reports/threat
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "user_id": "sruthi_g_s",
  "time_period_hours": 24
}
```

**Response (200 OK):**
```json
{
  "message": "Report generated successfully",
  "report_path": "data/reports/threat_report_sruthi_g_s_20251021_143200.pdf",
  "activities_analyzed": 15,
  "high_risk_count": 3
}
```

### 7. Get System Statistics
```http
GET /api/v1/stats
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "total_users": 5,
  "total_activities": 1247,
  "high_risk_activities": 23,
  "active_alerts": 3,
  "blocked_users": 1,
  "system_health": {
    "cpu_usage": 45.2,
    "memory_usage": 62.8,
    "disk_usage": 38.5
  }
}
```

---

## WebSocket API

### Connect to Real-Time Feed
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Threat detected:', data);
};
```

**Message Format:**
```json
{
  "type": "threat_detected",
  "user_id": "sruthi_g_s",
  "risk_score": 78.5,
  "risk_level": "HIGH",
  "activity_type": "file_access",
  "timestamp": "2025-10-21T14:30:00",
  "action": "RESTRICT"
}
```

---

## Error Handling

### Error Response Format
```json
{
  "detail": "Error message here",
  "status_code": 400,
  "error_type": "ValidationError"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing/invalid token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error |

---

## Rate Limiting

**Default Limits:**
- `/api/v1/analyze`: 100 requests/minute
- `/api/v1/auth/login`: 5 requests/minute
- Other endpoints: 60 requests/minute

**Rate Limit Headers:**

X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1634825400

---

## Example Usage (Python)
```python
import requests

# Login
response = requests.post(
    'http://localhost:8000/api/v1/auth/login',
    json={'username': 'admin', 'password': 'admin123'}
)
token = response.json()['access_token']

# Analyze activity
headers = {'Authorization': f'Bearer {token}'}
activity = {
    'user_id': 'sruthi_g_s',
    'activity_type': 'file_access',
    'timestamp': '2025-10-21T14:30:00',
    'file_path': '/confidential/data.xlsx',
    'file_size': 5242880
}

response = requests.post(
    'http://localhost:8000/api/v1/analyze',
    json=activity,
    headers=headers
)
result = response.json()
print(f"Risk Score: {result['risk_score']}")
print(f"Action: {result['action']}")
```

---

## Example Usage (JavaScript)
```javascript
// Login
const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({username: 'admin', password: 'admin123'})
});
const {access_token} = await loginResponse.json();

// Analyze activity
const activity = {
  user_id: 'sruthi_g_s',
  activity_type: 'file_access',
  timestamp: '2025-10-21T14:30:00',
  file_path: '/confidential/data.xlsx',
  file_size: 5242880
};

const analyzeResponse = await fetch('http://localhost:8000/api/v1/analyze', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify(activity)
});
const result = await analyzeResponse.json();
console.log(`Risk Score: ${result.risk_score}`);
console.log(`Action: ${result.action}`);
```

---

## Support

For API support, contact: security@company.com
<<<END API_Documentation.md>>>
