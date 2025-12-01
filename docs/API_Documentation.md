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

## Analyst Threat Control Endpoints

### 1. Apply Analyst Action
**Endpoint:** `POST /api/v1/analyst/threat/{threat_id}/action`

**Description:** Analyst manually controls firewall response for a specific threat.

**Authentication:** Required (Admin or Analyst role)

**Request Body:**
```json
{
  "action": "RESTRICT",
  "custom_restrictions": {
    "block_external_internet": true,
    "rate_limit_mbps": 1,
    "block_ports": [21, 22, 445],
    "duration_minutes": 60,
    "notify_user": true
  },
  "reason": "Employee accessing confidential files outside business hours",
  "duration_minutes": 60
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| threat_id | string | Yes | User ID of the threat |
| action | string | Yes | ALLOW, RESTRICT, ISOLATE, or BLOCK |
| custom_restrictions | object | Yes | Custom firewall restrictions |
| reason | string | Yes | Justification for action |
| duration_minutes | integer | No | Duration (default: 60) |

**Response (200 OK):**
```json
{
  "success": true,
  "result": {
    "status": "RESTRICTED",
    "action_applied": "RESTRICT",
    "analyst": "security_analyst",
    "timestamp": "2025-01-01T14:30:00",
    "reason": "Employee accessing confidential files outside business hours"
  },
  "message": "Action RESTRICT applied successfully by security_analyst"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid action type
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - User not found
- `500 Internal Server Error` - Failed to apply action

---

### 2. Get Pending Decisions
**Endpoint:** `GET /api/v1/analyst/pending-decisions`

**Description:** Get all threats waiting for analyst decision (risk score 50-69).

**Authentication:** Required (Admin or Analyst role)

**Response (200 OK):**
```json
{
  "success": true,
  "count": 5,
  "pending_decisions": [
    {
      "id": 12345,
      "user_id": "john_doe",
      "username": "john_doe",
      "full_name": "John Doe",
      "activity_type": "file_access",
      "risk_score": 62,
      "risk_level": "HIGH",
      "timestamp": "2025-01-01T14:25:00",
      "summary": "Accessed confidential_salary_data.xlsx outside business hours",
      "recommended_action": "RESTRICT"
    }
  ]
}
```

**Error Responses:**
- `403 Forbidden` - Insufficient permissions
- `500 Internal Server Error` - Failed to get pending decisions

---

### 3. Contact User
**Endpoint:** `POST /api/v1/analyst/threat/{threat_id}/contact-user`

**Description:** Analyst sends message to user about suspicious activity.

**Authentication:** Required (Admin or Analyst role)

**Request Body:**
```json
{
  "message": "We've detected unusual activity on your account. Please contact Security immediately.",
  "method": "notification"
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| threat_id | string | Yes | User ID to contact |
| message | string | Yes | Message to send |
| method | string | No | notification, email, or sms (default: notification) |

**Response (200 OK):**
```json
{
  "success": true,
  "status": "message_sent",
  "method": "notification",
  "target_user": "john_doe",
  "timestamp": "2025-01-01T14:30:00",
  "message": "Message sent to John Doe via notification"
}
```

**Error Responses:**
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - User not found
- `500 Internal Server Error` - Failed to contact user

---

### 4. Escalate Threat
**Endpoint:** `POST /api/v1/analyst/threat/{threat_id}/escalate`

**Description:** Escalate threat to higher authority (admin, manager, incident team).

**Authentication:** Required (Admin or Analyst role)

**Request Body:**
```json
{
  "escalate_to": "incident_team",
  "notes": "Suspected insider threat - multiple honeypot accesses and large data transfer"
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| threat_id | string | Yes | User ID of threat |
| escalate_to | string | Yes | admin, manager, or incident_team |
| notes | string | Yes | Escalation notes |

**Response (200 OK):**
```json
{
  "success": true,
  "escalated_to": "incident_team",
  "target_user": "john_doe",
  "analyst": "security_analyst",
  "timestamp": "2025-01-01T14:35:00",
  "message": "Threat escalated to incident_team"
}
```

**Error Responses:**
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - User not found
- `500 Internal Server Error` - Failed to escalate

---

### 5. Get Analyst Actions (Audit Trail)
**Endpoint:** `GET /api/v1/analyst/my-actions`

**Description:** Get analyst's recent actions for audit trail.

**Authentication:** Required (Admin or Analyst role)

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 50 | Number of actions to return (1-200) |

**Response (200 OK):**
```json
{
  "success": true,
  "analyst": "security_analyst",
  "count": 3,
  "actions": [
    {
      "action_id": 12345,
      "action_type": "analyst_action",
      "target_user": "john_doe",
      "timestamp": "2025-01-01T14:30:00",
      "details": {
        "action": "RESTRICT",
        "reason": "Suspicious activity detected"
      },
      "summary": "Applied RESTRICT action to john_doe"
    }
  ]
}
```

**Error Responses:**
- `403 Forbidden` - Insufficient permissions
- `500 Internal Server Error` - Failed to get actions

---

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

