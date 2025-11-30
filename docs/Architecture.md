<<<START Architecture.md>>>
# IGNISYL - System Architecture

## Table of Contents
1. [Overview](#overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [ML Pipeline](#ml-pipeline)
6. [Security Architecture](#security-architecture)

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

### 1. Backend (`backend/`)

#### **Core (`backend/core/`)**
- **`main.py`**: FastAPI application entry point
- **`auth.py`**: JWT authentication, session management
- **`routes.py`**: API endpoint definitions
- **`websocket.py`**: Real-time WebSocket connections
- **`config.py`**: Configuration management

#### **Models (`backend/models/`)**
- **`database.py`**: SQLAlchemy base and session management
- **`user.py`**: User model (SQLAlchemy)
- **`activity_log.py`**: Activity logging model
- **`risk_assessment.py`**: Risk assessment storage
- **`user_activity.py`**: User activity tracking

#### **ML Engine (`backend/ml_engine/`)**
- **`hybrid_detector.py`**: 3-model ensemble (Isolation Forest, Autoencoder, XGBoost)
- **`risk_scorer.py`**: Context-aware risk scoring (27 factors, 13 modifiers)
- **`model_trainer.py`**: ML model training pipeline

#### **Services (`backend/services/`)**
- **`intelligent_risk_engine.py`**: Real-time risk assessment
- **`system_monitor.py`**: System resource monitoring
- **`ml_performance_tracker.py`**: ML model performance tracking
- **`honeypot_watcher.py`**: Honeypot file monitoring
- **`comprehensive_monitor.py`**: Multi-vector threat monitoring
- **`report_generator.py`**: PDF report generation
- **`alert_manager.py`**: Alert lifecycle management
- **`firewall_controller.py`**: Adaptive firewall rules
- **`log_processor.py`**: SIEM-style log analysis
- **`network_monitor.py`**: Network activity monitoring

#### **Utilities (`backend/utils/`)**
- **`helpers.py`**: Common utility functions
- **`validators.py`**: Input validation

#### **User Management (`backend/user_management/`)**
- **`user_management.py`**: User CRUD operations

---

### 2. Frontend (`frontend/`)
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # Reusable UI components
│   ├── pages/           # Page components
│   ├── context/         # React Context (state management)
│   ├── services/        # API client
│   ├── utils/           # Helper functions
│   └── App.js           # Main application component
└── package.json

**Key Components:**
- **Dashboard**: Real-time threat visualization
- **User Management**: User administration
- **Activity Monitor**: Activity log viewer
- **Reports**: PDF report generation/viewing
- **Alerts**: Alert management interface

---

### 3. Data Storage (`data/`)

data/
├── honeypots/           # Decoy files (5 files)
├── logs/                # Application/security logs
├── models/              # Trained ML models (.pkl, .h5)
├── reports/             # Generated PDF reports
├── synthetic/           # Synthetic training data
├── activities.db        # Activity logs database
├── ignisyl.db           # Main application database
└── users.db             # User database

---

## Data Flow

### **1. Activity Analysis Flow**

Employee Laptop
│
│ 1. Network activity detected
│
▼
network_monitor.py (Client-side)
│
│ 2. POST /api/v1/analyze
│
▼
routes.py (API Endpoint)
│
│ 3. Validate & extract features
│
▼
intelligent_risk_engine.py
│
│ 4. ML prediction
│
▼
hybrid_detector.py
│
│ 5. Ensemble scoring
│    ├─► Isolation Forest
│    ├─► Autoencoder
│    └─► XGBoost
│
▼
risk_scorer.py
│
│ 6. Context-aware adjustment
│    ├─► 27 risk factors
│    └─► 13 contextual modifiers
│
▼
firewall_controller.py
│
│ 7. Adaptive response
│    ├─► ALLOW
│    ├─► MONITOR
│    ├─► RESTRICT
│    └─► BLOCK
│
▼
WebSocket Broadcast
│
│ 8. Real-time dashboard update
│
▼
Frontend Dashboard

---

### **2. Honeypot Detection Flow**

Employee accesses honeypot file
│
▼
comprehensive_monitor.py
│
│ check_honeypot_access()
│
▼
alert_manager.py
│
│ create_alert(priority=CRITICAL)
│
▼
firewall_controller.py
│
│ apply_block(duration=60)
│
▼
WebSocket → Dashboard Alert

---

## ML Pipeline

### **Training Pipeline**

1. Data Collection
   │
   ├─► Synthetic data generation
   ├─► Historical activity logs
   └─► User behavior patterns
   │
   ▼
2. Feature Engineering
   │
   ├─► Temporal features (hour, day_of_week)
   ├─► File features (size, type, path)
   ├─► Network features (bytes_transferred, IPs)
   └─► Behavioral features (access patterns)
   │
   ▼
3. Model Training (model_trainer.py)
   │
   ├─► Isolation Forest (anomaly detection)
   ├─► Autoencoder (reconstruction error)
   └─► XGBoost (supervised classification)
   │
   ▼
4. Model Evaluation
   │
   ├─► Accuracy, Precision, Recall, F1-score
   └─► Cross-validation
   │
   ▼
5. Model Persistence
   │
   └─► Save to data/models/

### **Inference Pipeline**

New Activity
│
▼
Feature Extraction
│
▼
Hybrid Detector
│
├─► Isolation Forest Score (0-1)
├─► Autoencoder Score (0-1)
└─► XGBoost Score (0-1)
│
▼
Score Aggregation
│
└─► risk_score = (IF×0.3 + AE×0.3 + XGB×0.4) × 100
│
▼
Contextual Risk Scorer
│
├─► Apply risk factors (+10 to +30 points)
└─► Apply modifiers (-20 to +20 points)
│
▼
Final Risk Score (0-100)

---

## Security Architecture

### **1. Authentication & Authorization**

Login Request
│
▼
auth.py
│
├─► Verify credentials (bcrypt)
├─► Generate JWT token
└─► Create session
│
▼
Protected Endpoints
│
├─► Verify JWT token
├─► Check user role
└─► Authorize access

### **2. Input Validation**

API Request
│
▼
validators.py
│
├─► validate_user_data()
├─► validate_activity_data()
├─► sanitize_input()
└─► validate_ip_address()
│
▼
Processed Safely

### **3. Audit Trail**

All Actions Logged
│
├─► activity_log.py (user activities)
├─► logging_config.py (system logs)
└─► risk_assessment.py (risk decisions)

---

## Deployment Architecture

### **Development**

Single Server
├─► Backend (FastAPI on port 8000)
├─► Frontend (React dev server on port 3000)
└─► SQLite database

### **Production**

Load Balancer
│
├─► Backend Cluster (Gunicorn + Uvicorn workers)
│   ├─► Worker 1
│   ├─► Worker 2
│   └─► Worker N
│
├─► Frontend (Nginx serving static React build)
│
├─► Database (PostgreSQL with replication)
│
└─► Redis (session storage, caching)

---

## Scalability Considerations

1. **Horizontal Scaling**: Add more backend workers
2. **Database Sharding**: Partition by user_id
3. **Caching**: Redis for frequent queries
4. **Message Queue**: RabbitMQ/Celery for async tasks
5. **CDN**: Static asset delivery

---

## Performance Metrics

- **API Response Time**: < 200ms (p95)
- **ML Inference Time**: < 100ms per prediction
- **WebSocket Latency**: < 50ms
- **Report Generation**: < 5 seconds
- **Concurrent Users**: 1000+ (production)

---

## Monitoring & Observability

- **System Monitor**: CPU, RAM, disk usage
- **ML Performance Tracker**: Model accuracy over time
- **Log Processor**: Centralized logging
- **Alert Manager**: Real-time alert dashboard

---

## Technology Justification

| Technology | Justification |
|------------|---------------|
| **FastAPI** | Async support, auto OpenAPI docs, fast |
| **React.js** | Component-based UI, real-time updates |
| **SQLAlchemy** | Database abstraction, migrations |
| **scikit-learn** | Production-grade ML library |
| **TensorFlow** | Deep learning (Autoencoder) |
| **XGBoost** | Best-in-class gradient boosting |
| **WebSockets** | Real-time bidirectional communication |
| **ReportLab** | Professional PDF generation |

---

## Future Enhancements

1. **Distributed Deployment**: Kubernetes orchestration
2. **Advanced ML**: LSTM for sequence prediction
3. **UEBA**: User and Entity Behavior Analytics
4. **SOAR Integration**: Security Orchestration, Automation and Response
5. **Multi-tenancy**: Support for multiple organizations
<<<END Architecture.md>>>
