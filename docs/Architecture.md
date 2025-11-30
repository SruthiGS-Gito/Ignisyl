<<<START Architecture.md>>>
# IGNISYL - System Architecture

## Table of Contents
1. [Overview](#overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [ML Pipeline](#ml-pipeline)
6. [Security Architecture](#security-architecture)
7. [Deployment Architecture](#deployment-architecture)

---

## Overview

IGNISYL is an **AI-powered Insider Threat Detection and Adaptive Firewall System** built with a modular, microservices-inspired architecture.

**Tech Stack:**
- **Backend:** Python 3.11, FastAPI, SQLAlchemy
- **Frontend:** React.js, Tailwind CSS
- **ML:** scikit-learn, TensorFlow/Keras, XGBoost
- **Database:** SQLite (dev), PostgreSQL (production)
- **Real-time:** WebSockets
- **Reporting:** ReportLab (PDF generation)

---

## High-Level Architecture

### System Overview Diagram
┌────────────────────────────────────────────────────────────┐
│                      IGNISYL SYSTEM                        │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │   Frontend   │◄────►│   Backend    │                    │
│  │  (React.js)  │      │  (FastAPI)   │                    │
│  └──────────────┘      └──────┬───────┘                    │
│                               │                            │
│                    ┌──────────┼──────────┐                 │
│                    │          │          │                 │
│             ┌──────▼────┐ ┌───▼────┐ ┌──▼─────┐            │
│             │ ML Engine │ │Database│ │Services│            │
│             └───────────┘ └────────┘ └────────┘            │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Employee Laptops (Network Monitor)          │  │
│  │  • Monitors network activity                         │  │
│  │  • Sends data to central API                         │  │
│  │  • Receives adaptive firewall commands               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
└────────────────────────────────────────────────────────────┘

---

## Component Details

### 1. Backend Components

#### **Core Module** (`backend/core/`)
- **`main.py`**: FastAPI application entry point with CORS, middleware
- **`auth.py`**: JWT authentication, session management with SQLite
- **`routes.py`**: REST API endpoint definitions (25+ endpoints)
- **`websocket.py`**: Real-time WebSocket connections for live updates
- **`config.py`**: Environment configuration and directory management

#### **Data Models** (`backend/models/`)
- **`database.py`**: SQLAlchemy ORM setup, session factory
- **`user.py`**: User model with role-based access control
- **`activity_log.py`**: Activity logging with timestamps
- **`risk_assessment.py`**: Risk assessment results storage
- **`user_activity.py`**: Detailed user activity tracking

#### **ML Engine** (`backend/ml_engine/`)
- **`hybrid_detector.py`**: 3-model ensemble detector
  - Isolation Forest (anomaly detection)
  - Autoencoder (reconstruction error)
  - XGBoost (supervised classification)
- **`risk_scorer.py`**: Context-aware risk scoring engine
  - 27 risk factors
  - 13 contextual modifiers
  - Business intelligence integration
- **`model_trainer.py`**: ML model training and persistence pipeline

#### **Services** (`backend/services/`)
- **`intelligent_risk_engine.py`**: Real-time risk assessment orchestrator
- **`system_monitor.py`**: CPU, RAM, disk monitoring
- **`ml_performance_tracker.py`**: Model accuracy tracking over time
- **`honeypot_watcher.py`**: Decoy file access detection
- **`comprehensive_monitor.py`**: Multi-vector threat monitoring
- **`report_generator.py`**: Professional PDF report generation
- **`alert_manager.py`**: Alert lifecycle management (create→acknowledge→resolve)
- **`firewall_controller.py`**: OS-aware adaptive firewall rules
- **`log_processor.py`**: SIEM-style log analysis with pattern detection
- **`network_monitor.py`**: Client-side network activity monitoring

#### **Utilities** (`backend/utils/`)
- **`helpers.py`**: Common functions (formatting, hashing, time windows)
- **`validators.py`**: Input validation and sanitization

#### **User Management** (`backend/user_management/`)
- **`user_management.py`**: User CRUD operations with password support

---

### 2. Frontend Structure
frontend/
├── public/                 # Static assets, index.html
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── Dashboard.jsx   # Real-time threat visualization
│   │   ├── UserTable.jsx   # User management table
│   │   ├── ActivityFeed.jsx# Live activity feed
│   │   └── AlertPanel.jsx  # Alert notifications
│   ├── pages/              # Full page components
│   │   ├── Login.jsx       # Authentication page
│   │   ├── DashboardPage.jsx
│   │   ├── UsersPage.jsx
│   │   └── ReportsPage.jsx
│   ├── context/            # React Context for state
│   │   └── AuthContext.jsx # Authentication state
│   ├── services/           # API client services
│   │   └── api.js          # Axios configuration
│   ├── utils/              # Helper functions
│   └── App.js              # Main router and layout
└── package.json

**Key Features:**
- **Real-time Updates**: WebSocket integration for live threat feeds
- **Responsive Design**: Tailwind CSS for mobile-first UI
- **Role-Based Views**: Admin vs. analyst dashboards
- **Interactive Charts**: Risk score visualization over time
- **PDF Viewer**: In-browser report preview

---

### 3. Data Storage Architecture
data/
├── honeypots/              # 5 decoy files (honeypot traps)
│   ├── admin_passwords.txt
│   ├── confidential_salary_data.xlsx
│   ├── customer_credit_cards.csv
│   ├── financial_reports_q4.pdf
│   └── trade_secrets.docx
├── logs/                   # Application logs
│   ├── application.log     # General app logs
│   └── security.log        # Security events
├── models/                 # Trained ML models
│   ├── isolation_forest.pkl
│   ├── autoencoder.h5
│   └── xgboost_model.pkl
├── reports/                # Generated PDF reports
├── synthetic/              # Synthetic training data
│   ├── file_operations.csv
│   ├── network_logs.csv
│   └── user_activities.csv
├── activities.db           # Activity logs (SQLite)
├── ignisyl.db              # Main application database
└── users.db                # User authentication database

---

## Data Flow

### Activity Analysis Flow

**Step-by-step processing:**

1. **Employee Laptop** → Network activity detected
2. **network_monitor.py** → Monitors psutil.net_io_counters()
3. **POST /api/v1/analyze** → Sends activity to central API
4. **routes.py** → Validates request, extracts features
5. **intelligent_risk_engine.py** → Orchestrates risk assessment
6. **hybrid_detector.py** → Runs 3-model ensemble
   - Isolation Forest score (0-1)
   - Autoencoder reconstruction error (0-1)
   - XGBoost probability (0-1)
7. **risk_scorer.py** → Applies context-aware adjustments
   - Checks 27 risk factors
   - Applies 13 contextual modifiers
   - Calculates final risk score (0-100)
8. **firewall_controller.py** → Determines action
   - ALLOW (score < 30)
   - MONITOR (score 30-49)
   - RESTRICT (score 50-69)
   - BLOCK (score ≥ 70)
9. **WebSocket Broadcast** → Real-time update to dashboard
10. **Frontend Dashboard** → Displays threat in UI

### Honeypot Detection Flow

**Immediate response on honeypot access:**

1. **Employee accesses honeypot file** (e.g., admin_passwords.txt)
2. **comprehensive_monitor.py** → check_honeypot_access() detects within 5 minutes
3. **alert_manager.py** → create_alert(priority=CRITICAL)
4. **firewall_controller.py** → apply_block(user_id, duration=60)
5. **WebSocket** → Broadcasts CRITICAL alert to dashboard
6. **Dashboard** → Shows red alert banner with user details

---

## ML Pipeline

### Training Pipeline

**5-stage model training process:**

#### Stage 1: Data Collection
- Synthetic data generation (1000-2000 samples)
- Historical activity logs from database
- User behavior patterns from production

#### Stage 2: Feature Engineering
**Temporal Features:**
- hour (0-23)
- day_of_week (0-6)
- is_weekend (0/1)
- is_business_hours (0/1)

**File Features:**
- file_size (bytes)
- file_path (string)
- file_type (extension)

**Network Features:**
- bytes_transferred (int)
- source_ip (string)
- destination_ip (string)

**Behavioral Features:**
- access_frequency (count)
- typical_access_time (hour)
- deviation_from_baseline (float)

#### Stage 3: Model Training
**Isolation Forest:**
- Contamination: 0.1 (10% anomalies)
- n_estimators: 100
- max_samples: 256

**Autoencoder:**
- Input layer: Feature dimension
- Hidden layers: [64, 32, 16, 32, 64]
- Loss: Mean Squared Error
- Optimizer: Adam

**XGBoost:**
- Objective: binary:logistic
- Max depth: 6
- Learning rate: 0.1
- n_estimators: 100

#### Stage 4: Model Evaluation
**Metrics calculated:**
- Accuracy: Overall correctness
- Precision: True positives / (True positives + False positives)
- Recall: True positives / (True positives + False negatives)
- F1-Score: Harmonic mean of precision and recall
- Cross-validation: 5-fold CV

#### Stage 5: Model Persistence
- Save models to `data/models/`
- Pickle format for scikit-learn models
- HDF5 format for Keras models
- Versioning with timestamps

### Inference Pipeline

**Real-time prediction process:**

1. **New Activity** → Incoming user activity
2. **Feature Extraction** → Extract same features as training
3. **Hybrid Detector** → Run through 3 models
   - Isolation Forest: Anomaly score
   - Autoencoder: Reconstruction error
   - XGBoost: Classification probability
4. **Score Aggregation** → Weighted average
risk_score = (IF × 0.3 + AE × 0.3 + XGB × 0.4) × 100
5. **Contextual Risk Scorer** → Apply business context
   - Add risk factors (+10 to +30 points each)
   - Apply modifiers (-20 to +20 points)
6. **Final Risk Score** → Clamped to 0-100 range

---

## Security Architecture

### 1. Authentication & Authorization

**JWT-based authentication flow:**
User Login
↓
Credentials Validation (bcrypt password hashing)
↓
JWT Token Generation (HS256 algorithm)
↓
Session Creation (SQLite storage)
↓
Token Stored in Client (localStorage)
↓
Protected Endpoint Access
↓
Token Verification (signature check)
↓
Role-Based Authorization (admin/analyst)
↓
Access Granted/Denied

**Token Structure:**
```json
{
  "sub": "admin",
  "role": "admin",
  "exp": 1698765432,
  "iat": 1698679032
}
```

### 2. Input Validation

**Multi-layer validation:**

- **validators.py**: Regex validation, length checks, type checks
- **Pydantic models**: FastAPI automatic validation
- **sanitize_input()**: Remove dangerous characters (<, >, ", ', &, ;, |, `)
- **SQL injection prevention**: SQLAlchemy ORM parameterized queries

### 3. Audit Trail

**Complete activity logging:**

- **activity_log.py**: All user activities with timestamps
- **logging_config.py**: Structured logging with rotation (10MB files, 5 backups)
- **risk_assessment.py**: All ML predictions with reasoning
- **Retention**: 90 days default, configurable

---

## Deployment Architecture

### Development Environment

**Single-server setup:**
Localhost
├── Backend: http://localhost:8000 (FastAPI + Uvicorn)
├── Frontend: http://localhost:3000 (React dev server)
└── Database: data/ignisyl.db (SQLite)

**Start commands:**
```bash
# Backend
cd backend
python main.py

# Frontend
cd frontend
npm start
```

### Production Environment

**Multi-tier architecture:**
Internet
↓
Load Balancer (Nginx)
↓
┌───────────────────────────────────┐
│   Backend Cluster                 │
│   ├── Worker 1 (Gunicorn)         │
│   ├── Worker 2 (Gunicorn)         │
│   └── Worker N (Gunicorn)         │
└───────────────────────────────────┘
↓
┌───────────────────────────────────┐
│   Database Cluster                │
│   ├── PostgreSQL Primary          │
│   └── PostgreSQL Replica          │
└───────────────────────────────────┘
↓
Redis (Session Storage & Caching)

**Production stack:**
- **Web Server**: Nginx (reverse proxy, SSL termination)
- **WSGI Server**: Gunicorn with 4-8 Uvicorn workers
- **Database**: PostgreSQL 14+ with streaming replication
- **Cache**: Redis 7+ for sessions and API responses
- **SSL/TLS**: Let's Encrypt certificates

---

## Scalability Considerations

### Horizontal Scaling Strategies

1. **Backend Scaling**
   - Add more Gunicorn workers
   - Deploy multiple backend instances behind load balancer
   - Auto-scaling based on CPU/memory metrics

2. **Database Scaling**
   - Read replicas for SELECT queries
   - Connection pooling (SQLAlchemy pool_size=20)
   - Database sharding by user_id for large deployments

3. **Caching Strategy**
   - Redis for frequently accessed data
   - Cache TTL: 5 minutes for dynamic data, 1 hour for static
   - Cache invalidation on data updates

4. **Asynchronous Processing**
   - Celery task queue for report generation
   - RabbitMQ for message brokering
   - Separate workers for ML inference

5. **CDN for Static Assets**
   - CloudFlare or AWS CloudFront
   - Serve frontend build files
   - Cache API responses where appropriate

---

## Performance Metrics

**Target SLAs:**

| Metric | Target | Notes |
|--------|--------|-------|
| API Response Time (p95) | < 200ms | Excluding ML inference |
| ML Inference Time | < 100ms | Per activity analysis |
| WebSocket Latency | < 50ms | Message delivery time |
| Report Generation | < 5 seconds | Standard threat report |
| Concurrent Users | 1000+ | With proper scaling |
| Database Query Time (p95) | < 50ms | Indexed queries |
| Uptime | 99.9% | ~8.7 hours downtime/year |

---

## Monitoring & Observability

### System Monitoring

**Metrics tracked:**
- CPU usage per worker
- Memory consumption
- Disk I/O operations
- Network bandwidth
- Active WebSocket connections

**Tools:**
- **system_monitor.py**: Built-in monitoring service
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards

### Application Monitoring

**Log aggregation:**
- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Centralized logging**: All services → Logstash
- **Log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

**ML Performance:**
- **ml_performance_tracker.py**: Tracks model accuracy over time
- **Drift detection**: Alerts when model performance degrades
- **Retraining triggers**: Automatic when accuracy < 85%

---

## Technology Justification

| Technology | Why We Chose It |
|------------|----------------|
| **FastAPI** | Async support, automatic OpenAPI docs, 3x faster than Flask, type hints |
| **React.js** | Component reusability, virtual DOM performance, large ecosystem |
| **SQLAlchemy** | Database agnostic, ORM abstraction, migration support (Alembic) |
| **scikit-learn** | Industry standard, production-ready, extensive documentation |
| **TensorFlow** | Best for deep learning (Autoencoder), GPU acceleration, Keras API |
| **XGBoost** | SOTA gradient boosting, handles imbalanced data, feature importance |
| **WebSockets** | True real-time bidirectional communication, low latency |
| **ReportLab** | Professional PDF generation, precise layout control, Python native |
| **SQLite** | Zero-config for development, single-file portability |
| **PostgreSQL** | ACID compliance, JSON support, robust for production |

---

## Future Enhancements

### Roadmap for Next 6-12 Months

1. **Kubernetes Deployment**
   - Container orchestration
   - Auto-scaling pods
   - Self-healing infrastructure

2. **Advanced ML Models**
   - LSTM for sequence prediction
   - Graph Neural Networks for user relationships
   - Federated learning for privacy

3. **UEBA Integration**
   - User and Entity Behavior Analytics
   - Peer group analysis
   - Baseline behavior modeling

4. **SOAR Platform**
   - Security Orchestration, Automation, and Response
   - Automated incident response playbooks
   - Integration with ticketing systems

5. **Multi-Tenancy**
   - Support multiple organizations
   - Tenant isolation
   - Custom branding per tenant

6. **Advanced Reporting**
   - Executive dashboards
   - Compliance reports (SOC 2, ISO 27001)
   - Custom report builder

---

## System Diagram Summary

**Complete data flow visualization:**
Employee Laptops
↓
Network Monitor (psutil)
↓
POST /api/v1/analyze
↓
FastAPI Routes
↓
Intelligent Risk Engine
↓
┌───────────────────────┐
│   ML Hybrid Detector  │
│ ┌─────────────────┐   │
│ │ Isolation Forest│   │
│ │  Score: 0.72    │   │
│ └─────────────────┘   │
│ ┌─────────────────┐   │
│ │  Autoencoder    │   │
│ │  Score: 0.81    │   │
│ └─────────────────┘   │
│ ┌─────────────────┐   │
│ │    XGBoost      │   │
│ │  Score: 0.83    │   │
│ └─────────────────┘   │
└───────────────────────┘
↓
Contextual Risk Scorer
↓
Risk Score: 78.5 (HIGH)
↓
Firewall Controller
↓
Action: RESTRICT
↓
WebSocket Broadcast
↓
Dashboard Update

---

## Contact & Support

For architecture questions or deployment support:
- **Email**: architecture@company.com
- **Documentation**: https://docs.ignisyl.com
- **GitHub**: https://github.com/company/ignisyl
<<<END Architecture.md>>>

