# IGNISYL

**AI-Powered Insider Threat Detection System with Adaptive Firewall Control**

IGNISYL is an intelligent security system that detects insider threats using machine learning and implements graduated response actions through an adaptive firewall. Unlike traditional binary ALLOW/BLOCK systems, IGNISYL provides 5-level graduated responses with granular analyst controls.

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
- [Team](#team)
- [License](#license)

---

## Features

### Core Capabilities

- **3-Model ML Ensemble Detection**
  - Isolation Forest (unsupervised anomaly detection)
  - Autoencoder (deep learning pattern recognition)
  - XGBoost (supervised gradient boosting)
  - Weighted ensemble: 30% IF + 30% AE + 40% XGB

- **Graduated Response Framework**
  - 5-level adaptive response system
  - Context-aware automation for clear cases
  - Analyst decision support for ambiguous threats

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
│  │  • Firewall Controller (5-level graduated response)       │  │
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
git clone https://github.com/yourusername/Ignisyl.git
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

## Team

**Project:** IGNISYL - AI-Powered Insider Threat Detection
**Institution:** Sree Buddha College of Engineering
**Academic Year:** 2025-2026
**Type:** B.Tech Final Year Project

| Name | Role |
|------|------|
| Sruthi G S | Lead Developer & ML Researcher |
| R Anand | Frontend Developer & UI/UX Designer |
| Aiswarya Lekshmi | Security Analyst & Testing Lead |
| Vrinda V | Data Engineer & Documentation Lead |

**Project Advisor:** Dr. Divya Mohan

---

## License

This project is developed for academic research purposes.

**Conference Target:** IEEE ICAECT 2026

---

## Documentation

| Document | Description |
|----------|-------------|
| [Installation Guide](docs/Installation_Guide.md) | Detailed setup instructions |
| [User Manual](docs/User_Manual.md) | User guide for analysts |
| [API Documentation](docs/API_Documentation.md) | Complete API reference |
| [Architecture](docs/Architecture.md) | System design details |
| [Quick Start Guide](docs/QUICK_START_GUIDE.md) | Get started quickly |

---

<p align="center">
  <strong>IGNISYL</strong> - Intelligent Insider Threat Detection with Graduated Response
</p>
