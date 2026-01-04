# IGNISYL Project Analysis Report

**Generated:** 2026-01-04
**Analyzed by:** Claude Code
**Project Location:** `D:/Projects/Ignisyl`

---

## 1. Executive Summary

### Project Overview
**IGNISYL** (Insider Threat Detection System) is a comprehensive security monitoring platform that uses machine learning to detect and respond to insider threats in real-time.

### Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | FastAPI + Python | 3.x |
| Frontend | React | 18.x |
| Database | SQLite | 3.x |
| ML Engine | scikit-learn, PyTorch, XGBoost | Latest |
| Authentication | JWT + bcrypt | - |
| Real-time | WebSocket | - |

### Code Statistics

| Metric | Count |
|--------|-------|
| Python Files | 59 |
| JavaScript Files | 26 |
| Python Lines of Code | 22,201 |
| JavaScript Lines of Code | ~8,500 |
| API Endpoints | 43 |
| React Components | 18 |
| Database Tables | 5 |

---

## 2. Backend Architecture

### 2.1 API Endpoints (43 total)

#### Authentication (`/api/v1/auth/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/login` | No | User login with rate limiting |
| POST | `/change-password` | Yes | Change user password |
| POST | `/validate-password` | Yes | Validate password complexity |

#### Dashboard & Analytics (`/api/v1/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/dashboard/stats` | Yes | Get comprehensive dashboard statistics |
| GET | `/activities/recent` | Yes | Get recent user activities (role-based) |
| GET | `/analytics/trends` | Yes | Get threat trends over time |
| GET | `/threats/active` | Yes | Get currently active threats |
| GET | `/health` | No | System health check |

#### Analyst Control (`/api/v1/analyst/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/threat/{id}/action` | Admin | Apply firewall action (SIMULATION) |
| GET | `/pending-decisions` | Admin | Get threats awaiting analyst review |
| POST | `/threat/{id}/contact-user` | Admin | Contact user about suspicious activity |
| POST | `/threat/{id}/escalate` | Admin | Escalate threat to higher authority |
| GET | `/my-actions` | Admin | Get analyst's action history |

#### User Management (`/api/v1/users/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/list` | No | List all users with risk scores |
| GET | `/{user_id}` | Yes | Get user details with activity |
| GET | `/{user_id}/profile` | No | Get detailed user profile |
| GET | `/{user_id}/risk-profile` | Yes | Get intelligent risk profile |
| POST | `/register` | No | Register new user |
| PUT | `/{user_id}` | Admin | Update user information |
| DELETE | `/{user_id}` | Admin | Deactivate user |
| POST | `/{user_id}/block` | Admin | Block user account |
| POST | `/{user_id}/unblock` | Admin | Unblock user account |
| GET | `/users-risk` | Yes | Get risk assessments for all users |

#### Report Generation (`/api/v1/reports/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/generate` | Admin | Generate PDF report (4 types) |
| POST | `/generate-user-report` | Admin | Generate 8-section user report |
| GET | `/list` | Admin | List available reports |
| GET | `/download/{filename}` | No | Download a report |
| GET | `/system` | Admin | Get system report data |
| GET | `/user` | Admin | Get user report data |

#### Firewall Control (`/api/v1/firewall/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/action` | Yes | Execute firewall action (SIMULATION) |

#### ML & Monitoring (`/api/v1/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/ml/model-info` | No | Get ML model information |
| POST | `/analyze` | Yes | Analyze behavior with ML |
| POST | `/simulate` | Yes | Simulate threat for testing |
| POST | `/monitoring/file-access` | Yes | Log file access event |
| POST | `/monitoring/login` | Yes | Log login event |
| POST | `/monitoring/usb` | Yes | Log USB event |
| POST | `/monitoring/suspicious` | Yes | Report suspicious activity |
| GET | `/monitoring/honeypots` | Yes | Get honeypot status |

#### System Settings (`/api/v1/settings/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | Admin | Get system settings |
| POST | `/` | Admin | Save system settings |

#### Debug & Testing (`/api/v1/debug/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/auth-check` | No | Verify auth system status |
| GET | `/users` | Admin | Debug user database |
| POST | `/simulate-activity` | Admin | Generate test activities |

---

### 2.2 Database Schema

#### `users.db` - User Database

| Column | Type | Description |
|--------|------|-------------|
| user_id | TEXT | Primary key (user_xxxxx) |
| username | TEXT | Unique login name |
| full_name | TEXT | Display name |
| password_hash | TEXT | bcrypt hash |
| department | TEXT | User department |
| role | TEXT | User role |
| email | TEXT | Email address |
| status | TEXT | active/blocked/inactive |
| current_risk_score | REAL | 0-100 risk score |
| total_threats | INTEGER | Threat count |
| last_activity | TEXT | ISO timestamp |
| registered_at | TEXT | ISO timestamp |

**Current Data:** 6 users

#### `activities.db` - Activity Logs

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment PK |
| user_id | TEXT | Foreign key to users |
| username | TEXT | Username |
| full_name | TEXT | Display name |
| activity_type | TEXT | Type of activity |
| timestamp | TEXT | ISO timestamp |
| risk_score | REAL | 0-100 risk score |
| risk_level | TEXT | LOW/MEDIUM/HIGH/CRITICAL |
| action | TEXT | ALLOW/MONITOR/RESTRICT/BLOCK |
| bytes_transferred | INTEGER | Data size |
| file_size | INTEGER | File size |
| summary | TEXT | Activity summary |
| details | TEXT | JSON details |

**Current Data:** 352 activities

**Activity Type Distribution:**
- after_hours_access: 32
- file_download: 28
- file_deletion: 27
- file_access: 27
- privileged_action: 26
- honeypot_access: 26
- email_received: 26
- file_upload: 23

#### `sessions.db` - Session Management

| Table | Purpose |
|-------|---------|
| sessions | Active JWT sessions |
| login_attempts | Rate limiting tracking |
| account_lockouts | Account lockout status |

---

### 2.3 Services & Business Logic

#### Core Services

| Service | File | Purpose |
|---------|------|---------|
| `HybridThreatDetector` | `ml_engine/hybrid_detector.py` | Multi-model threat detection (Autoencoder, IsolationForest, XGBoost, LSTM) |
| `UserManager` | `models/user_management.py` | User CRUD, risk score management |
| `ActivityLogger` | `models/activity_log.py` | Activity logging with deduplication |
| `AuthManager` | `api/auth.py` | JWT authentication, rate limiting, account lockout |
| `FirewallController` | `services/firewall_controller.py` | Firewall simulation (SIMULATION MODE) |
| `ReportGenerator` | `services/report_generator.py` | PDF report generation with charts |
| `IntelligentRiskEngine` | `services/intelligent_risk_engine.py` | ML-based risk scoring |
| `MLPerformanceTracker` | `services/ml_performance_tracker.py` | Track ML model metrics |

#### ML Models Implemented

| Model | Library | Purpose |
|-------|---------|---------|
| Autoencoder | PyTorch | Anomaly detection |
| Isolation Forest | scikit-learn | Outlier detection |
| XGBoost Classifier | XGBoost | Supervised threat classification |
| LSTM | PyTorch | Sequential behavior analysis |
| Ensemble | Custom | Multi-model voting |

**ML Performance Metrics:**
- Accuracy: 85.0%
- Models Active: 3
- Detection Latency: 25ms

---

### 2.4 Configuration

#### Dependencies (Key Packages)

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.115.12 | Web framework |
| pydantic | 2.11.5 | Request validation |
| sqlalchemy | 2.0.41 | ORM (available but using raw SQLite) |
| torch | 2.6.0+cu126 | PyTorch ML |
| scikit-learn | 1.7.2 | ML algorithms |
| xgboost | 3.0.2 | Gradient boosting |
| numpy | 2.2.6 | Numerical computing |
| pandas | 2.2.3 | Data manipulation |
| bcrypt | 4.3.0 | Password hashing |
| python-jose | 3.4.0 | JWT tokens |
| reportlab | 4.3.1 | PDF generation |
| matplotlib | 3.10.3 | Charts |

---

## 3. Frontend Architecture

### 3.1 Pages (7 total)

| Page | File | Purpose | Auth Required |
|------|------|---------|---------------|
| Login | `Auth/Login.js` | User authentication | No |
| Dashboard | `Dashboard/Dashboard.js` | Main monitoring view | Yes |
| Admin Dashboard | `Admin/AdminDashboard.js` | Admin controls, user management | Admin |
| Analyst Control | `AnalystControl/AnalystControl.js` | Threat response actions | Yes |
| Activity Log | `Pages/ActivityLog.js` | Activity history | Yes |
| Active Threats | `Pages/ActiveThreats.js` | Current threats | Yes |
| Reports | `Pages/Reports.js` | PDF report generation | Admin |
| System Status | `Pages/SystemStatus.js` | System health monitoring | Admin |

### 3.2 Reusable Components

| Component | Purpose |
|-----------|---------|
| Header | Navigation and branding |
| Sidebar | Navigation menu |
| Loading | Loading spinner |
| Toast | Notification system |
| RiskMetrics | Dashboard stat cards |
| AlertsPanel | Recent threat alerts |
| UserTable | User risk table |
| ActivityChart | Activity visualization |
| RiskChart | Risk distribution chart |
| ThreatMap | Threat visualization |

### 3.3 API Integration (`services/api.js`)

```javascript
// API modules available:
authAPI     - login()
dashboardAPI - getStats(), getActivities(), getThreats()
userAPI     - getUsers(), getUser(), updateUser(), blockUser()
analystAPI  - takeAction(), contactUser(), escalateThreat()
reportAPI   - generateReport(), generateUserReport(), listReports()
settingsAPI - getSettings(), saveSettings()
firewallAPI - blockUser(), restrictUser()
alertAPI    - acknowledge()
systemAPI   - getStatus(), simulateActivity()
```

---

## 4. Current Features

### 4.1 Working Features

| Feature | Status | Notes |
|---------|--------|-------|
| User Authentication | Working | JWT + bcrypt, rate limiting, account lockout |
| Role-Based Access | Working | Admin, Security Analyst, User roles |
| Dashboard Stats | Working | Real-time stats from database |
| Activity Logging | Working | 352 activities logged with deduplication |
| User Management | Working | CRUD operations, risk tracking |
| Threat Detection | Working | Multi-model ML (IsolationForest, XGBoost) |
| Risk Scoring | Working | Intelligent risk engine |
| WebSocket Updates | Working | Real-time threat notifications |
| PDF Reports | Working | 4 report types with charts |
| Analyst Actions | Working | SIMULATION MODE - commands logged |
| Honeypot Monitoring | Working | 4 honeypots active |
| System Health | Working | CPU, Memory, Disk, Network |

### 4.2 Partially Working Features

| Feature | Status | Issue |
|---------|--------|-------|
| Firewall Actions | Simulation | Commands logged but NOT executed (by design) |
| User Contact | Simulation | Messages logged but NOT sent |
| Threat Escalation | Simulation | Logged but no notification sent |
| Password Validation | Working | Complexity rules enforced |

### 4.3 Placeholder Features

| Feature | Status | Notes |
|---------|--------|-------|
| `IncidentTimeline.js` | Empty file | 0 bytes, not implemented |
| Email Notifications | Not implemented | Settings exist but no integration |
| Slack Integration | Not implemented | Setting exists, no code |
| SMS Alerts | Not implemented | Contact method exists, no integration |

---

## 5. Known Issues

### 5.1 Code Issues (from TODO/FIXME scan)

| Location | Issue |
|----------|-------|
| `routes.py:654` | TODO: Update alerts table in database (currently just returns acknowledgment) |
| `IncidentTimeline.js` | Empty file - component not implemented |

### 5.2 Architecture Observations

| Issue | Description | Severity |
|-------|-------------|----------|
| Raw SQLite | Using raw sqlite3 instead of SQLAlchemy ORM | Low |
| In-memory Settings | System settings stored in Python dict, lost on restart | Medium |
| Hardcoded API URL | Frontend uses `http://127.0.0.1:8000` | Low |
| Single-file routes | All 43 endpoints in one 1830-line file | Medium |

### 5.3 Missing Implementations

| Feature | Status |
|---------|--------|
| Persistent settings storage | Not implemented |
| Email notification service | Not implemented |
| Slack webhook integration | Not implemented |
| Real firewall enforcement | Intentionally simulation-only |
| User session revocation | Partial (cleanup on expiry only) |

---

## 6. Dependencies

### 6.1 Backend Dependencies (Key)

```
fastapi==0.115.12
uvicorn[standard]==0.34.3
pydantic==2.11.5
python-jose[cryptography]==3.4.0
bcrypt==4.3.0
pandas==2.2.3
numpy==2.2.6
scikit-learn==1.7.2
torch==2.6.0+cu126
xgboost==3.0.2
matplotlib==3.10.3
reportlab==4.3.1
psutil==7.0.0
websockets==15.0.1
```

### 6.2 Frontend Dependencies

```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "react-router-dom": "^6.28.0",
  "axios": "^1.7.9",
  "react-scripts": "5.0.1"
}
```

---

## 7. Configuration

### 7.1 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| SECRET_KEY | Auto-generated | JWT signing key (persisted to .secret_key) |
| DEBUG | True | Enable debug mode |
| PORT | 8000 | Backend port |

### 7.2 Security Settings

| Setting | Value |
|---------|-------|
| JWT Expiration | 8 hours |
| Rate Limit | 5 attempts / 5 minutes |
| Account Lockout | 10 failed attempts / 30 min lockout |
| Password Min Length | 8 characters |
| bcrypt Rounds | 12 |

### 7.3 Risk Thresholds (IEEE Paper)

| Score Range | Level | Auto Action |
|-------------|-------|-------------|
| 0-30 | LOW | ALLOW |
| 31-50 | MEDIUM | MONITOR |
| 51-75 | HIGH | RESTRICT (analyst review) |
| 76-100 | CRITICAL | BLOCK (automatic) |

---

## 8. Data Analysis

### 8.1 Database Contents

| Database | Table | Row Count |
|----------|-------|-----------|
| users.db | users | 6 |
| activities.db | activities | 352 |
| sessions.db | sessions | 1+ |

### 8.2 Sample Users

| Username | Role | Risk Score |
|----------|------|------------|
| admin | Administrator | 0.0 |
| john.doe | Senior Developer | 0.0 |
| jane.smith | Security Analyst | 0.0 |
| alice.johnson | HR Manager | 100.0 |
| bob.wilson | Financial Controller | 0.0 |

### 8.3 Test Data Generation

The system includes a debug endpoint to generate realistic test data:
```
POST /api/v1/debug/simulate-activity?count=50
```

---

## 9. Project Structure

```
D:/Projects/Ignisyl/
├── backend/
│   ├── main.py                 # FastAPI application entry
│   ├── api/
│   │   ├── auth.py             # Authentication system
│   │   └── routes.py           # All API endpoints (1830 lines)
│   ├── config/
│   │   └── config.py           # Application settings
│   ├── core/
│   │   └── middleware.py       # CORS, logging middleware
│   ├── models/
│   │   ├── user_management.py  # User database operations
│   │   ├── activity_log.py     # Activity logging
│   │   └── database.py         # Database initialization
│   ├── ml_engine/
│   │   ├── hybrid_detector.py  # Main ML detector (Autoencoder, IF, XGB)
│   │   ├── behavior_model.py   # LSTM behavior model
│   │   ├── risk_scorer.py      # Risk calculation
│   │   └── models/             # Saved ML models
│   ├── services/
│   │   ├── firewall_controller.py    # Firewall simulation
│   │   ├── report_generator.py       # PDF generation
│   │   ├── intelligent_risk_engine.py # ML risk scoring
│   │   └── ml_performance_tracker.py  # ML metrics
│   └── data/
│       ├── users.db            # User database
│       ├── activities.db       # Activity logs
│       ├── sessions.db         # Session management
│       └── reports/            # Generated PDFs
├── frontend/
│   ├── src/
│   │   ├── App.js              # React router setup
│   │   ├── components/
│   │   │   ├── Admin/          # Admin dashboard
│   │   │   ├── AnalystControl/ # Threat response UI
│   │   │   ├── Auth/           # Login page
│   │   │   ├── Charts/         # Visualization components
│   │   │   ├── Common/         # Shared components
│   │   │   ├── Dashboard/      # Main dashboard
│   │   │   └── Pages/          # Activity, Threats, Reports
│   │   ├── services/
│   │   │   ├── api.js          # API client
│   │   │   └── websocket.js    # WebSocket client
│   │   └── utils/
│   │       ├── constants.js    # App constants
│   │       └── helpers.js      # Utility functions
│   └── package.json
└── docs/
    ├── FIREWALL_SYSTEM_DOCUMENTATION.md
    └── PROJECT_ANALYSIS_REPORT.md (this file)
```

---

## 10. Next Steps (Prioritized)

### High Priority
1. **Persist system settings** - Save to database instead of in-memory
2. **Implement IncidentTimeline component** - Currently empty file
3. **Split routes.py** - Break 1830-line file into modules

### Medium Priority
4. **Add email notification service** - For threat alerts
5. **Implement alerts table** - Currently TODO in code
6. **Add user session management UI** - View/revoke sessions

### Low Priority
7. **Add Slack integration** - Webhook notifications
8. **Environment-based API URL** - Remove hardcoded localhost
9. **SQLAlchemy migration** - Replace raw sqlite3

### Documentation
10. **API documentation** - OpenAPI/Swagger already available at `/docs`
11. **User manual** - How to use the system
12. **Deployment guide** - Production setup instructions

---

## 11. Conclusion

IGNISYL is a **comprehensive and functional** insider threat detection system suitable for academic demonstration and IEEE publication. The system successfully implements:

- Multi-model ML threat detection
- Real-time monitoring with WebSocket
- Role-based access control
- Comprehensive API with 43 endpoints
- Professional React frontend
- PDF report generation with charts
- Firewall action simulation (appropriate for demo)

The codebase is well-structured and production-ready for its intended purpose as an academic/demo project. The main areas for improvement are code organization (splitting large files) and implementing placeholder features (notifications, persistent settings).

---

*Report generated by Claude Code on 2026-01-04*
