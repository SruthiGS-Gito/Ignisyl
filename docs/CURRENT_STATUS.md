# IGNISYL - Current System Status

**Version:** 1.0 (Demo/Academic)
**Last Updated:** January 2026
**Developer:** Sruthi CS
**Institution:** Sree Buddha College of Engineering, Kerala, India
**Status:** Functional Demo System

---

## What Works

### Core Features
- User authentication (JWT tokens, session management)
- Dashboard with real-time metrics (WebSocket updates)
- ML-based threat detection (3-model ensemble)
- Activity logging and monitoring
- Risk score calculation (4-tier graduated response)
- Analyst control panel (action logging)
- PDF report generation (4 report types)
- User management (CRUD operations)

### ML Engine
- Isolation Forest (unsupervised anomaly detection)
- XGBoost (supervised gradient boosting)
- PyTorch Autoencoder (deep learning reconstruction)
- Weighted ensemble: 30% IF + 30% AE + 40% XGB
- Risk Scorer: 27 factors + 13 business modifiers

### Reports (All Functional)
| Report Type | Pages | Content |
|-------------|-------|---------|
| Comprehensive System Report | ~7 | Full system overview, all users |
| ML Performance Report | ~5 | Model metrics, accuracy, confusion matrix |
| Threat Summary Report | ~2 | Recent threats, risk distribution |
| Individual User Report | ~17 | Detailed user behavioral analysis |

### Data
- 50 demo users with realistic profiles
- Synthetic activity data (100+ activities)
- Risk scores distributed realistically (0-100)
- Timestamps spread across multiple days
- Honeypot files for detection testing

---

## Simulation Mode Features

These features are **LOGGED but NOT EXECUTED**:

| Feature | What Happens | What Doesn't Happen |
|---------|--------------|---------------------|
| Firewall rules | Commands generated and logged | Not executed on OS |
| Network blocking | Action recorded in database | No actual network change |
| User notifications | Contact attempt logged | No email/SMS sent |
| Escalations | Escalation logged with notes | No actual notification |

### Why Simulation Mode?

1. **Safety:** No risk of accidentally blocking real users during demo
2. **No Elevated Privileges:** Runs without admin/root access
3. **Cross-Platform:** Same code works on Windows/Linux/macOS
4. **Academic Scope:** Appropriate for research demonstration
5. **Reversibility:** No cleanup needed after testing

### Sample Generated Command (Not Executed)
```bash
# Windows example (logged but NOT run):
netsh advfirewall firewall add rule name="IGNISYL_BLOCK_john.doe" dir=out action=block

# Linux example (logged but NOT run):
iptables -A OUTPUT -m owner --uid-owner john.doe -j DROP
```

---

## Not Implemented (Future Work)

| Feature | Status | Notes |
|---------|--------|-------|
| Endpoint agents | Not available | Requires separate development |
| Real network monitoring | Not available | Needs agent on endpoints |
| Active Directory integration | Not available | Enterprise feature |
| Email/SMS notifications | Not available | Requires SMTP/Twilio setup |
| SIEM integration | Not available | Splunk/QRadar connectors needed |
| PostgreSQL database | Not available | SQLite only for demo |
| Docker/Kubernetes | Not available | Single-server deployment only |
| USB device control | Not available | Requires endpoint agent |
| Custom firewall rules | Not available | Granular rules planned |

---

## Best Use Cases

### Good For
- Academic demonstration and defense
- Research project presentation
- Portfolio showcase for interviews
- Proof of concept for insider threat detection
- ML algorithm testing and validation
- UI/UX demonstration
- IEEE conference submission

### Not Ready For
- Production enterprise deployment
- Real security enforcement
- Critical infrastructure protection
- Legal/compliance requirements
- Organizations requiring actual network control

---

## Technical Specifications

### Current Architecture
```
┌─────────────────────────────────────────┐
│           Single Server Setup           │
├─────────────────────────────────────────┤
│  Frontend: React 18 + Tailwind CSS      │
│  Backend:  FastAPI + Python 3.11        │
│  Database: SQLite (3 files)             │
│  ML:       PyTorch + XGBoost + sklearn  │
│  Reports:  ReportLab PDF                │
│  Realtime: WebSocket                    │
└─────────────────────────────────────────┘
```

### Risk Thresholds
| Level | Score | Response | Authority |
|-------|-------|----------|-----------|
| LOW | 0-30 | ALLOW | Automated |
| MEDIUM | 31-50 | MONITOR | Automated |
| HIGH | 51-75 | RESTRICT | Analyst Decision |
| CRITICAL | 76-100 | BLOCK | Auto (review recommended) |

### API Endpoints
- 25+ REST endpoints
- WebSocket for real-time updates
- Swagger docs at /docs
- ReDoc at /redoc

---

## Production Roadmap (Theoretical)

| Phase | Timeline | Features |
|-------|----------|----------|
| **Phase 1** (Current) | Complete | ML detection + UI + Simulation |
| **Phase 2** | +6 months | Endpoint agent development |
| **Phase 3** | +12 months | Enterprise integration (AD, SIEM) |
| **Phase 4** | +18 months | Multi-tenant SaaS platform |

> **Note:** This roadmap is theoretical. Current version is designed for academic demonstration only.

---

## File Locations

| Component | Path |
|-----------|------|
| Backend | `backend/` |
| Frontend | `frontend/` |
| ML Models | `backend/ml_engine/` |
| Database | `backend/data/ignisyl.db` |
| Reports (generated) | `backend/data/reports/` |
| Honeypots | `backend/data/honeypots/` |
| Documentation | `docs/` |

---

## Quick Start

```bash
# Backend (Terminal 1)
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py

# Frontend (Terminal 2)
cd frontend
npm install
npm start

# Access
# Dashboard: http://localhost:3000
# API Docs:  http://localhost:8000/docs
```

**Default Login:** admin / admin123

---

## Contact

**Developer:** Sruthi CS
**Institution:** Sree Buddha College of Engineering, Kerala, India
**Project:** B.Tech Final Year Project (2025-2026)
**Conference:** IEEE ICAECT 2026
**GitHub:** https://github.com/SruthiGS-Gito/Ignisyl

---

**Document Version:** 1.0
**Last Updated:** January 2026
