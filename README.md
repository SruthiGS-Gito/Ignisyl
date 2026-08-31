# IGNISYL

**AI-Powered Insider Threat Detection System with Adaptive Firewall Control**

IGNISYL is an intelligent security system that detects insider threats using machine learning and implements graduated response actions through an adaptive firewall. Unlike traditional binary ALLOW/BLOCK systems, IGNISYL provides a 4-tier graduated response framework with granular analyst controls.

---

**Developer:** Sruthi CS
**Institution:** Sree Buddha College of Engineering, Kerala, India
**Academic Year:** 2025-2026
**Project Type:** Final Year B.Tech Project
**Conference:** IEEE ICAECT 2026 (Submission Completed)

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Running the Project](#running-the-project)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Screenshots](#screenshots)
- [Future Enhancements](#future-enhancements)
- [Risk Thresholds](#risk-thresholds)
- [Important Notes](#important-notes)
- [Developer](#developer)
- [License](#license)

---

## Features

### Core Capabilities

- **3-Model ML Ensemble Detection**
  - Isolation Forest (unsupervised anomaly detection)
  - Autoencoder (deep learning pattern recognition)
  - XGBoost (supervised gradient boosting)
  - Weighted ensemble: 40% IF + 40% AE + 20% XGB

- **Graduated Response Framework:** 4-tier automated system
  - **ALLOW** (0-30): Normal operations with standard logging
  - **MONITOR** (31-50): Enhanced logging, analyst awareness
  - **RESTRICT** (51-75): Analyst review required, limited access
  - **BLOCK** (76-100): Complete block, incident response

- **Analyst Control Panel**
  - Custom restriction options (block external only, rate limit, port blocking)
  - Time-limited restrictions (30 min to 24 hours)
  - Escalation workflows (admin, manager, incident team)
  - Complete audit trail

- **Real-Time Monitoring**
  - WebSocket live updates
  - Browser notifications for critical threats
  - Auto-refreshing dashboards

- **Professional Reporting**
  - Automated PDF threat reports
  - Individual user behavioral analysis
  - System-wide security reports

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy |
| **Frontend** | React 18, Tailwind CSS, Recharts |
| **Machine Learning** | scikit-learn, TensorFlow/Keras, XGBoost |
| **Database** | SQLite (dev), PostgreSQL/MySQL (production) |
| **Real-time** | WebSockets |
| **PDF Generation** | ReportLab, Matplotlib |
| **Authentication** | JWT, bcrypt |
| **Containerization** | Docker, Docker Compose |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         IGNISYL SYSTEM                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Frontend   │    │   Backend    │    │  ML Engine   │      │
│  │   React.js   │◄──►│   FastAPI    │◄──►│   Ensemble   │      │
│  │  Tailwind    │    │  WebSocket   │    │  Detector    │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                             │                    │              │
│                             ▼                    ▼              │
│                      ┌──────────────┐    ┌──────────────┐      │
│                      │   Database   │    │    Models    │      │
│                      │ SQLite/PSQL  │    │  .pkl/.h5    │      │
│                      └──────────────┘    └──────────────┘      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                     Services Layer                        │  │
│  │  • Risk Scorer (27 factors + 13 business modifiers)      │  │
│  │  • Firewall Controller (4-tier graduated response)        │  │
│  │  • Report Generator (PDF with visualizations)             │  │
│  │  • System Monitor (real-time metrics)                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

For detailed architecture, see [docs/Architecture.md](docs/Architecture.md)

---

## Installation

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- Git

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/SruthiGS-Gito/Ignisyl.git
cd Ignisyl

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Return to project root
cd ..
```

### Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# For development, defaults work fine
```

---

## Running the Project

### Development Mode

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```
Backend runs at: http://localhost:8000

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```
Frontend runs at: http://localhost:3000

### Using Docker

```bash
# Build and start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

### Default Login Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Analyst | analyst | analyst123 |

---

## API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analyze` | Analyze user activity for threats |
| GET | `/dashboard/stats` | Get dashboard statistics |
| GET | `/users` | List all monitored users |
| GET | `/users/{id}/activities` | Get user activity history |
| GET | `/threats` | List detected threats |
| POST | `/threats/{id}/action` | Apply analyst action to threat |
| GET | `/reports/generate/{type}` | Generate PDF report |
| WS | `/ws` | WebSocket for real-time updates |

### Interactive API Docs

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

For complete API documentation, see [docs/API_Documentation.md](docs/API_Documentation.md)

---

## Project Structure

```
Ignisyl/
├── backend/
│   ├── api/                 # API routes and WebSocket handlers
│   ├── ml_engine/           # ML models and detection logic
│   │   ├── hybrid_detector.py
│   │   ├── risk_scorer.py
│   │   └── data_generator.py
│   ├── models/              # Database models
│   ├── services/            # Business logic services
│   │   ├── firewall_controller.py
│   │   ├── report_generator.py
│   │   └── system_monitor.py
│   └── main.py              # FastAPI application entry
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   └── App.js           # Main React app
│   └── package.json
├── config/
│   └── config.py            # Application configuration
├── data/
│   ├── models/              # Trained ML models (.pkl, .h5)
│   ├── synthetic/           # Training data
│   └── honeypots/           # Decoy files for detection
├── docs/                    # Documentation
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Screenshots

> Screenshots will be added after deployment. The application includes:
> - **Dashboard:** Real-time threat monitoring with risk metrics
> - **Analyst Panel:** Threat review and action controls
> - **User Activity:** Detailed activity logs with risk scores
> - **Reports:** PDF report generation interface

---

## Future Enhancements

- [ ] SIEM/SOAR integration (Splunk, QRadar)
- [ ] LSTM/Transformer models for sequential pattern detection
- [ ] Temporal correlation analysis for slow-and-low attack defense
- [ ] Active Directory integration
- [ ] Mobile application for alerts
- [ ] Automated threat hunting playbooks
- [ ] Multi-tenant support
- [ ] Cloud deployment templates (AWS, Azure, GCP)

---

## Developer

**Developer:** Sruthi CS
**Institution:** Sree Buddha College of Engineering, Kerala, India
**Academic Year:** 2025-2026
**Project Type:** Final Year B.Tech Project
**Conference:** IEEE ICAECT 2026 (Submission Completed)

| Role | Responsibility |
|------|----------------|
| Full Stack Development | Backend (FastAPI), Frontend (React), Database |
| ML Engineering | Ensemble model design, training, evaluation |
| Security Research | Threat detection algorithms, graduated response framework |
| Documentation | Technical docs, API reference, user guides |

---

## Risk Thresholds

| Level | Score Range | Response | Description |
|-------|-------------|----------|-------------|
| **LOW** | 0-30 | ALLOW | Normal operations, standard logging |
| **MEDIUM** | 31-50 | MONITOR | Enhanced logging, analyst awareness |
| **HIGH** | 51-75 | RESTRICT | Analyst decision required, limited access |
| **CRITICAL** | 76-100 | BLOCK | Auto-block, incident response triggered |

---

## Important Notes

**Simulation Mode:** The firewall controller generates OS-specific commands (Windows/Linux/macOS) but does NOT execute them. This is intentional for:
- Academic demonstration safety
- Cross-platform compatibility
- Production deployment requires agent installation on endpoints

**ML Performance:** Detection accuracy metrics are calculated from ensemble model predictions on synthetic data. For production deployment, retrain models on organization-specific data.

**Demo Data:** System includes 50 demo users with synthetic activities. For production, integrate with your organization's user directory (Active Directory, LDAP, etc.)

---

## License

This project is developed for academic research purposes.

**Conference:** IEEE ICAECT 2026 (Submission Completed)

---

## Documentation

| Document | Description |
|----------|-------------|
| [Installation Guide](docs/Installation_Guide.md) | Detailed setup instructions |
| [User Manual](docs/User_Manual.md) | User guide for analysts |
| [API Documentation](docs/API_Documentation.md) | Complete API reference |
| [Architecture](docs/Architecture.md) | System design details |
| [Firewall System](docs/FIREWALL_SYSTEM_DOCUMENTATION.md) | Graduated response framework |

---

<p align="center">
  <strong>IGNISYL</strong> - Intelligent Insider Threat Detection with Graduated Response
</p>
