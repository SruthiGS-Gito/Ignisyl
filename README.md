# 🛡️ IGNISYL - AI-Powered Insider Threat Detection and Adaptive Firewall System

**IGNISYL** is an academic research project exploring graduated response frameworks for insider threat detection with ML-driven risk assessment and analyst controls.

**Project Type:** B.Tech Final Year Project (2025-2026)  
**Institution:** Sree Buddha College of Engineering  
**Target Conference:** IEEE ICAECT 2026

---

## 🌟 Key Features

### ✅ **Graduated Response Framework**
- **5-level adaptive response** for insider threats
- **Granular analyst controls** - Apply custom restrictions (e.g., "block external internet but allow internal network")
- **Context-aware automation** - Auto-handle clear cases, analyst decides ambiguous threats
- **Design goal:** Balance security with operational flexibility

**Approach:** Instead of binary ALLOW/BLOCK, IGNISYL introduces graduated levels with custom firewall controls for analyst decision-making.

### ✅ **3-Model ML Ensemble**
- **Isolation Forest** (scikit-learn) - Unsupervised anomaly detection
- **Autoencoder** (TensorFlow/Keras) - Deep learning pattern recognition
- **XGBoost** (xgboost) - Supervised gradient boosting classifier
- **Weighted ensemble** - 30% IF + 30% AE + 40% XGB
- Context-aware risk scoring with **27 risk factors + 13 business modifiers**

### ✅ **Analyst Control Panel**
- Review threats requiring decision (risk 50-69)
- **Custom restriction options:**
  - Block external internet only (keep internal access)
  - Rate limit bandwidth (1-10 Mbps)
  - Block specific ports (FTP, SSH, SMB, RDP)
  - Time-limited restrictions (30 min to 24 hours)
- **Additional actions:**
  - Contact user for clarification
  - Escalate to admin/manager/incident team
  - Apply full network isolation
  - View complete audit trail

### ✅ **Real-Time Monitoring**
- WebSocket live updates
- Browser notifications for critical threats
- Auto-refreshing dashboards
- Live activity feed

### ✅ **Professional Reporting**
- Automated PDF threat reports
- User-specific behavioral analysis
- System-wide security reports
- Exportable for compliance

---

---

## 🔐 Security Setup

### Database Configuration

IGNISYL now supports **SQLite, PostgreSQL, and MySQL** databases with production-ready security features.

#### Quick Start (Development - SQLite)

No additional setup required! IGNISYL uses SQLite by default.

```bash
# Just run the application
python backend/main.py
```

#### Production Setup (PostgreSQL/MySQL)

**IMPORTANT: Never commit credentials to git!**

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env with your credentials:**
   ```bash
   # For PostgreSQL
   ENVIRONMENT=production
   DB_TYPE=postgresql
   DB_HOST=your-database-host.com
   DB_PORT=5432
   DB_NAME=ignisyl
   DB_USER=ignisyl_user
   DB_PASSWORD=YOUR_SECURE_PASSWORD_HERE

   # For MySQL
   ENVIRONMENT=production_mysql
   DB_TYPE=mysql
   DB_HOST=your-database-host.com
   DB_PORT=3306
   DB_NAME=ignisyl
   DB_USER=ignisyl_user
   DB_PASSWORD=YOUR_SECURE_PASSWORD_HERE
   ```

3. **Generate a secure SECRET_KEY:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

   Add to `.env`:
   ```
   SECRET_KEY=<generated-key-here>
   ```

4. **Verify security:**
   ```bash
   python scripts/check_security.py
   ```

5. **Run database migration:**
   ```bash
   python backend/database/migrate.py --env production
   ```

#### Security Best Practices

✅ **DO:**
- Use `.env` for all credentials (never commit it!)
- Keep `.env.example` with only placeholders
- Use strong, unique passwords (20+ characters)
- Rotate credentials regularly
- Enable SSL/TLS for database connections
- Limit database user privileges
- Run security checks: `python scripts/check_security.py`

❌ **DON'T:**
- Commit `.env` to git
- Use default/weak passwords
- Hardcode credentials in code
- Share credentials in chat/email
- Use production credentials in development

#### Files That Should NEVER Be Committed

The `.gitignore` is configured to exclude:
- `.env` (contains real credentials)
- `*.db` files (database files)
- `*.sqlite` files
- `__pycache__/` and `*.pyc`
- Logs and temporary files

**Always verify:** `.env` is in `.gitignore` and not tracked by git!

#### Database Abstraction Layer

IGNISYL uses a production-ready database abstraction layer with:
- **Multi-database support** (SQLite, PostgreSQL, MySQL)
- **Connection pooling** (PostgreSQL: 1-10 connections, MySQL: 10 connections)
- **Thread-safe operations** (SQLite with locking)
- **Transaction management** (automatic commit/rollback)
- **Error handling** and comprehensive logging

For detailed documentation, see:
- [Database Migration Guide](DATABASE_MIGRATION_GUIDE.md)
- [Database Layer Documentation](backend/database/README.md)

#### Testing Your Setup

```bash
# Test database layer
python backend/database/test_db_layer.py

# Run security audit
python scripts/check_security.py

# Test with example operations
python backend/database/example_usage.py
```

---

## 🔬 Research Contribution

### Problem Statement
Insider threat detection systems typically employ binary ALLOW/BLOCK controls, which create a trade-off between security and operational flexibility.

### IGNISYL's Approach
This project explores a **graduated response framework** specifically for insider threats:

1. **5 Response Levels** - Finer-grained control than binary decisions
2. **Custom Analyst Restrictions** - Granular firewall controls
3. **ML-Driven Assessment** - 3-model ensemble with context awareness
4. **Human-in-the-Loop** - Analyst decision for medium-risk threats (50-69)

### Academic Contribution
- **Demonstrates** application of graduated response to insider threat scenarios
- **Implements** custom analyst controls for firewall management
- **Combines** ML ensemble with behavioral risk scoring
- **Provides** working prototype for research and evaluation

### Limitations & Future Work
- Requires production deployment for impact evaluation
- Tested with synthetic data; real-world validation needed
- Analyst workflow overhead needs quantification
- Future: SIEM/SOAR integration, larger-scale testing

### Publication
**IEEE ICAECT 2026** - Design, implementation, and evaluation of graduated response framework for insider threat detection.

---

## 👥 Team

**Project Name:** IGNISYL  
**Institution:** Sree Buddha College of Engineering  
**Academic Year:** 2025-2026  
**Project Type:** B.Tech Final Year Project

| Name | Role | Contribution |
|------|------|--------------|
| **Sruthi G S** | Lead Developer & ML Researcher | Backend development, ML ensemble implementation, graduated response framework design, risk scoring engine, API architecture |
| **R Anand** | Frontend Developer & UI/UX Designer | React dashboard development, analyst control panel, real-time WebSocket integration, user interface design, responsive layouts |
| **Aiswarya Lekshmi** | Security Analyst & Testing Lead | Firewall controller implementation, security testing, threat analysis workflows, penetration testing, documentation |
| **Vrinda V** | Data Engineer & Documentation Lead | Synthetic data generation, database design, report generation system, technical documentation, user manual |

**Project Advisor:** Dr. Divya Mohan  
**Department:** Computer Science and Engineering  
**Conference Target:** IEEE ICAECT 2026

---

---

## 📈 Project Status

**🎉 100% Complete - Publication Ready!**

✅ **Core ML Pipeline:** 3-model ensemble (IF + AE + XGB) with 100% XGBoost accuracy
✅ **Graduated Response Framework:** 5-level adaptive response with analyst controls
✅ **Feature Engineering:** 14 engineered features with realistic data generation
✅ **Baseline Comparison:** Evaluated against 5 baseline models (RF, SVM, LR, DT, NB)
✅ **Adversarial Testing:** Tested against 5 evasion strategies, identified vulnerabilities
✅ **Database Layer:** Multi-database support (SQLite, PostgreSQL, MySQL)
✅ **Security Hardening:** Production-ready with .env configuration, no credentials in git
✅ **Documentation:** 10+ comprehensive markdown files
✅ **Testing:** Functional, security, and adversarial testing complete
⏳ **IEEE ICAECT 2026:** Camera-ready paper in preparation (Deadline: Jan 8-9, 2026)

**View detailed status:** [PROJECT_STATUS.md](PROJECT_STATUS.md)

---

## 🏆 Key Achievements

### ML Performance
- **XGBoost Training Accuracy:** 100% (with class balancing)
- **Random Forest Baseline:** 97.8% accuracy (best traditional model)
- **Ensemble Detection:** 100% recall (no missed threats)
- **Feature Engineering:** 14 features with realistic overlap

### Adversarial Robustness
- **Strong Defense:** 96.2% detection against noise injection
- **Strong Defense:** 84.8% detection against feature manipulation
- **Moderate Defense:** 52.4% detection against mimicry
- **Critical Vulnerability:** 0.5% detection against slow-and-low attacks

### Engineering Excellence
- **Multi-Database Support:** SQLite, PostgreSQL, MySQL
- **Clean Git History:** Conventional commits, detailed messages
- **Security Best Practices:** No credentials in git, environment-based config
- **Comprehensive Testing:** Baseline comparison + adversarial robustness

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Project overview and setup guide |
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | Complete project status and achievements |
| [BASELINE_COMPARISON_REPORT.md](BASELINE_COMPARISON_REPORT.md) | Baseline model comparison results |
| [ADVERSARIAL_ROBUSTNESS_REPORT.md](ADVERSARIAL_ROBUSTNESS_REPORT.md) | Adversarial testing results |
| [DATABASE_MIGRATION_GUIDE.md](DATABASE_MIGRATION_GUIDE.md) | Database setup and migration |
| [SECURITY_AUDIT_REPORT.md](SECURITY_AUDIT_REPORT.md) | Security assessment and best practices |
| [backend/database/README.md](backend/database/README.md) | Database abstraction layer docs |
| [docs/API_Documentation.md](docs/API_Documentation.md) | API endpoint documentation |
| [docs/Architecture.md](docs/Architecture.md) | System architecture |
| [docs/Installation_Guide.md](docs/Installation_Guide.md) | Installation instructions |
| [docs/User_Manual.md](docs/User_Manual.md) | User manual for analysts |

---

## 🎓 Academic Publication

**Conference:** IEEE ICAECT 2026 (International Conference on Advances in Engineering, Computing, and Technology)
**Dates:** January 8-9, 2026
**Paper Status:** Camera-ready in preparation

**Research Contributions:**
1. Novel graduated response framework for insider threat detection
2. Comprehensive baseline comparison (5 traditional ML models)
3. Adversarial robustness evaluation (5 evasion strategies)
4. 14-feature engineering with realistic data generation
5. Production-ready implementation with multi-database support

---

## 🚀 Quick Start

### For Researchers / Reviewers

```bash
# Clone repository
git clone https://github.com/SruthiGS-Gito/Ignisyl.git
cd Ignisyl

# Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Generate synthetic data
python scripts/generate_data.py

# Train models
python scripts/train_models.py

# Run baseline comparison
python backend/compare_baselines.py

# Run adversarial tests
python run_adversarial_test.py

# Start backend API
python backend/main.py
```

### For Placement Interviews

**Key Talking Points:**
- Implemented 3-model ML ensemble achieving 100% XGBoost training accuracy
- Developed novel graduated response framework (5 levels)
- Conducted comprehensive adversarial robustness testing
- Built production-ready system with multi-database support
- Submitted to IEEE ICAECT 2026 international conference

**Technical Stack:**
- **Backend:** Python, FastAPI, SQLAlchemy, scikit-learn, XGBoost, TensorFlow/Keras
- **ML:** Isolation Forest, Autoencoder, XGBoost ensemble
- **Database:** SQLite, PostgreSQL, MySQL (connection pooling)
- **Frontend:** React, WebSockets, real-time monitoring
- **Security:** bcrypt, JWT, environment-based configuration

---

**Made with ❤️ for cybersecurity research and academic innovation**

🛡️ **IGNISYL** - AI-Powered Insider Threat Detection with Graduated Response Framework

**GitHub:** https://github.com/SruthiGS-Gito/Ignisyl
**License:** Academic Research Project
**Team:** Sree Buddha College of Engineering (2025-2026)

