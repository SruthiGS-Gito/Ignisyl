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

[Keep the rest: Architecture, Quick Start, Login Credentials, Usage Guide, Graduated Response Levels table]

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

[Keep the rest: Contact, Acknowledgments, Project Status]

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
