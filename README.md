# IGNISYL

**AI-Powered Insider Threat Detection System with Adaptive Firewall Control**

IGNISYL is an intelligent security system that detects insider threats using machine learning and implements graduated response actions through an adaptive firewall. Unlike traditional binary ALLOW/BLOCK systems, IGNISYL provides a 4-tier graduated response framework with granular analyst controls.

**Publication:** IEEE ICAECT 2026, IEEE Xplore — https://ieeexplore.ieee.org/document/11425945

---

**Developer:** Sruthi G S
**Institution:** Sree Buddha College of Engineering, Kerala, India
**Academic Year:** 2025-2026
**Project Type:** Final Year B.Tech Project
**Conference:** IEEE ICAECT 2026 (published)

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
- [Evaluation Status](#evaluation-status)
- [Known Limitations](#known-limitations)
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
  - **BLOCK** (76-100): Block (simulated — commands generated, not executed)

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
| **Database** | SQLite |
| **Real-time** | WebSockets |
| **PDF Generation** | ReportLab, Matplotlib |
| **Authentication** | JWT, bcrypt |

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
│                      │    SQLite    │    │ (in memory)  │      │
│                      └──────────────┘    └──────────────┘      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                     Services Layer                        │  │
│  │  • Risk Scorer (19 implemented factors + modifiers)      │  │
│  │  • Firewall Controller (4-tier graduated response)        │  │
│  │  • Report Generator (PDF with visualizations)             │  │
│  │  • System Monitor (real-time metrics)                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

The risk scorer is a multi-factor risk scorer (19 implemented behavioral factors) with business-context modifiers.

Models are trained at startup; scripts/train_models.py exports them if needed.

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

### Demo Login Credentials

Local demo seed accounts (reset on startup):

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | demo123 |
| Monitored user | john.doe | demo123 |
| Monitored user | jane.smith | demo123 |
| Monitored user | bob.wilson | demo123 |
| Monitored user | alice.johnson | demo123 |
| Monitored user | charlie.brown | demo123 |

`demo123` is a local demo seed only, set in `backend/main.py`.

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
| GET | `/users/list` | List all monitored users |
| GET | `/users/{id}/profile` | Get user profile |
| GET | `/threats/active` | List active threats |
| POST | `/analyst/threat/{id}/action` | Apply analyst action to threat |
| POST | `/reports/generate` | Generate PDF report |
| WS | `/ws/{client_id}` | WebSocket for real-time updates (server root, not under `/api/v1`) |

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
│   ├── models/              # Exported models (git-ignored; trained at startup)
│   ├── synthetic/           # Synthetic data
│   └── honeypots/           # Decoy files for detection
├── docs/                    # Documentation
├── run_adversarial_test.py  # Adversarial evasion suite
├── requirements.txt
└── README.md
```

---

## Screenshots

Screenshots: coming soon

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

**Developer:** Sruthi G S
**Institution:** Sree Buddha College of Engineering, Kerala, India
**Academic Year:** 2025-2026
**Project Type:** Final Year B.Tech Project
**Conference:** IEEE ICAECT 2026 (published)

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
| **CRITICAL** | 76-100 | BLOCK | Block (simulated — commands generated, not executed) |

---

## Important Notes

**Simulation Mode:** The firewall controller generates OS-specific commands (Windows/Linux/macOS) but does NOT execute them. This is intentional for:
- Academic demonstration safety
- Cross-platform compatibility
- Production deployment requires agent installation on endpoints

**Demo Data:** The app seeds 6 demo accounts (admin plus 5 monitored users). The models train on a 46,934-event synthetic dataset (200 users, 4 threat scenarios: data exfiltration, privilege abuse, credential compromise, insider sabotage), generated at first startup with a fixed seed. For production, integrate with your organization's user directory (Active Directory, LDAP, etc.) and retrain on organization-specific data.

---

## Evaluation Status

The backend evaluates on a held-out 20% split at startup. On the current synthetic data it catches all 29 held-out anomalies (recall 100%) but precision is 2.77% (1,018 false alarms), so accuracy (89%) is not a meaningful figure at a 0.31% anomaly rate. Labels come from the data generator, so these numbers do not reflect real-world performance. The figures vary slightly between startups (precision 2.77-2.85% and 989-1,018 false alarms over three runs). The dashboard shows "Not evaluated" until real predictions have been logged.

An adversarial evasion suite (`run_adversarial_test.py`) runs evasion attacks against the detector, including slow-and-low. Slow-and-low evasion is a known blind spot.

---

## Known Limitations

- On the held-out 20% split, recall is 100% but precision is 2.77% (1,018 false alarms), so accuracy (89%) is not a meaningful figure at a 0.31% anomaly rate. Labels come from the data generator, so these numbers do not reflect real-world performance.
- Firewall enforcement is simulated (commands generated, not executed).
- Slow-and-low evasion is a known blind spot (adversarial suite: `run_adversarial_test.py`).
- Some defined risk factors and context modifiers are not yet implemented.

---

## License

This project is developed for academic research purposes.

**Conference:** IEEE ICAECT 2026 (published)

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
