# IGNISYL Quick Start Guide

**Get your demo running in 3 simple steps!**

---

## 🚀 Step 1: Install Dependencies

Run the automated installer:

```bash
cd D:\Projects\Ignisyl
python scripts/install_dependencies.py
```

**What this does:**
- Upgrades pip
- Installs all required packages (FastAPI, ML libraries, database drivers)
- Shows progress for each package
- Generates installation report
- Estimated time: 10-30 minutes (depending on internet speed)

**Alternative (manual):**
```bash
pip install -r requirements.txt
```

---

## ✅ Step 2: Verify Installation

Test that everything is installed correctly:

```bash
python scripts/verify_installation.py
```

**Expected output:**
```
✓ fastapi (v0.104.1)
✓ uvicorn
✓ tensorflow
✓ scikit-learn
...
✅ INSTALLATION VERIFIED - Ready to start backend!
```

If you see any ✗ errors, re-run the installer for those specific packages.

---

## 🎯 Step 3: Start Backend Server

### Option A: Using Startup Script (Recommended)

**Windows:**
```bash
scripts\start_backend.bat
```

**Linux/Mac:**
```bash
bash scripts/start_backend.sh
```

### Option B: Manual Start

```bash
cd backend
python main.py
```

**Expected output:**
```
🚀 Starting IGNISYL v2.0
👥 Checking for real database users...
📝 Creating default monitored users...
✅ Created 5 monitored users
🧠 Initializing ML components...
📊 Training ML models...
Training features shape: (5000, 14)
✅ ML models trained successfully!
🌟 IGNISYL is ready!
📡 API running on http://127.0.0.1:8000
```

---

## 🧪 Step 4: Test Backend API

Open a new terminal and test:

```bash
curl http://127.0.0.1:8000/api/v1/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-18T...",
  "version": "2.0",
  "components": {
    "ml_detector": "ready",
    "risk_scorer": "ready",
    "database": "connected",
    "firewall": "ready"
  }
}
```

---

## 🌐 Step 5: Start Frontend (Optional)

```bash
cd frontend
npm install  # First time only
npm start
```

Frontend opens at: http://localhost:3000

---

## 🎭 Demo Mode (For Conference Presentation)

### Generate Simulated Threat Activity

```bash
# In a new terminal
curl -X POST http://127.0.0.1:8000/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{"type": "data_exfiltration"}'
```

### Available Scenarios:
- `data_exfiltration` - Late-night large file download (HIGH risk)
- `privilege_abuse` - Cross-department data access (MEDIUM risk)
- `suspicious_login` - After-hours login from unknown location (HIGH risk)

---

## 🔧 Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'XXX'"

**Solution:**
```bash
pip install XXX
# Or re-run: python scripts/install_dependencies.py
```

### Problem: "Address already in use" (Port 8000 occupied)

**Solution:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Linux/Mac

# Kill the process or change port in backend/config/config.py
```

### Problem: TensorFlow import errors

**Solution (Temporary):**
```bash
# Skip TensorFlow for now (system will use fallback)
# Or install CPU-only version:
pip install tensorflow-cpu
```

### Problem: Frontend can't connect to backend

**Check:**
1. Backend is running: `curl http://127.0.0.1:8000/api/v1/health`
2. CORS is configured: Check `backend/main.py` lines 54-65
3. Frontend API URL: Check `frontend/src/services/api.js` line 3

---

## 📊 Verify Everything is Working

Run this comprehensive test:

```bash
# Terminal 1: Backend
python backend/main.py

# Terminal 2: Test all endpoints
curl http://127.0.0.1:8000/api/v1/health
curl http://127.0.0.1:8000/api/v1/dashboard/stats
curl http://127.0.0.1:8000/api/v1/users/list

# All should return JSON responses
```

---

## 🎉 You're Ready!

Your IGNISYL system is now running! You can:

✅ View API docs: http://127.0.0.1:8000/docs
✅ Test threat detection: Use `/api/v1/simulate` endpoint
✅ Monitor dashboard: http://localhost:3000 (if frontend running)
✅ Generate reports: Use `/api/v1/reports/system` endpoint

---

## 📝 Next Steps for Demo

1. **Create Demo Users:** Already created automatically (john.doe, jane.smith, etc.)
2. **Simulate Threats:** Use curl commands above
3. **Monitor Dashboard:** Watch real-time threat detection
4. **Generate Reports:** PDF reports for presentation

---

## 💡 Pro Tips

- **Keep backend running** in one terminal while testing
- **Use Postman** for easier API testing (import from /docs)
- **Check logs** in backend terminal for debugging
- **Database location:** `data/ignisyl.db` (SQLite)
- **Generated reports:** `data/reports/` directory

---

## 🆘 Need Help?

1. Check logs in backend terminal
2. Run verification: `python scripts/verify_installation.py`
3. Check [PROJECT_STATUS.md](PROJECT_STATUS.md) for system overview
4. Review [docs/API_Documentation.md](docs/API_Documentation.md)

---

**Made with ❤️ for ICAECT 2026 Conference Demo**

Last updated: December 18, 2025
