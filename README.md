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

✅ **Core Features:** Complete  
✅ **Documentation:** Complete  
✅ **Testing:** Complete (Unit tests with synthetic data)  
✅ **Analyst Control Panel:** Complete  
⏳ **Production Evaluation:** Requires deployment  
⏳ **IEEE Paper:** In preparation  

---

**Made with ❤️ for cybersecurity research and academic innovation**

🛡️ **IGNISYL** - Exploring graduated response frameworks for insider threat detection

