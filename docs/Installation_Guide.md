<<<START Installation_Guide.md>>>
# IGNISYL - Installation Guide

## Table of Contents
1. [What Gets Installed](#what-gets-installed)
2. [System Requirements](#system-requirements)
3. [Prerequisites](#prerequisites)
4. [Backend Installation](#backend-installation)
5. [Frontend Installation](#frontend-installation)
6. [Database Setup](#database-setup)
7. [Configuration](#configuration)
8. [Running the Application](#running-the-application)
9. [Verification](#verification)
10. [Troubleshooting](#troubleshooting)

---

## What Gets Installed

### Included in This Installation

| Component | Description | Status |
|-----------|-------------|--------|
| Backend server | FastAPI Python application | ✅ Installed |
| Frontend web app | React dashboard | ✅ Installed |
| SQLite databases | 3 database files | ✅ Created |
| Pre-trained ML models | Ensemble detector | ✅ Included |

### NOT Included (Future Features)

| Component | Description | Status |
|-----------|-------------|--------|
| Endpoint agents | Software on user computers | ❌ Not available |
| Network monitoring | Infrastructure monitoring | ❌ Not available |
| Active Directory integration | Enterprise user sync | ❌ Not available |
| Real firewall execution | Actual network blocking | ❌ Simulation only |

> **Important:** The firewall controller generates OS-specific commands but does NOT execute them. This is intentional for academic demonstration safety.

---

## System Requirements

### Minimum Requirements
- **OS:** Windows 10/11, Ubuntu 20.04+, macOS 11+
- **RAM:** 8 GB
- **Storage:** 10 GB free space
- **CPU:** Intel i5 or equivalent (4 cores)
- **Network:** Internet connection for package installation

### Recommended Requirements
- **OS:** Windows 11, Ubuntu 22.04+, macOS 12+
- **RAM:** 16 GB
- **Storage:** 20 GB free space
- **CPU:** Intel i7 or equivalent (8 cores)

> **No GPU Required:** ML models are pre-trained and included. GPU is NOT needed for running the system.

---

## Prerequisites

### Required Software

#### 1. Python 3.11
**Windows:**
```bash
# Download from python.org
https://www.python.org/downloads/

# Or use Windows Store
winget install Python.Python.3.11
```

**Verify installation:**
```bash
python --version
# Should output: Python 3.11.x
```

#### 2. Node.js 18+
**Windows:**
```bash
# Download from nodejs.org
https://nodejs.org/

# Or use Chocolatey
choco install nodejs
```

**Verify installation:**
```bash
node --version
npm --version
```

#### 3. Git
**Windows:**
```bash
# Download from git-scm.com
https://git-scm.com/download/win

# Or use winget
winget install Git.Git
```

---

## Backend Installation

### Step 1: Clone Repository
```bash
# Clone the repository
git clone https://github.com/SruthiGS-Gito/Ignisyl.git
cd Ignisyl
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# You should see (venv) in your terminal prompt
```

**Alternative (if above doesn't work):**
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Python Dependencies
```bash
# Make sure virtual environment is activated
# Install required packages
pip install --break-system-packages -r requirements.txt

# This will install:
# - fastapi, uvicorn (web framework)
# - sqlalchemy, pydantic (database & validation)
# - python-jose, passlib, bcrypt (authentication)
# - scikit-learn (ML - Isolation Forest)
# - torch (PyTorch - Autoencoder)
# - xgboost (ML - gradient boosting)
# - reportlab, matplotlib (PDF reports)
# - websockets (real-time updates)
```

**If you encounter errors:**
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Then retry
pip install --break-system-packages -r requirements.txt
```

### Step 4: Verify Backend Dependencies
```bash
# Check installed packages
pip list

# Test imports
python -c "import fastapi; import torch; import xgboost; import sklearn; print('All imports successful!')"
```

---

## Frontend Installation

### Step 1: Navigate to Frontend Directory
```bash
# From project root
cd frontend
```

### Step 2: Install Node Dependencies
```bash
# Install all npm packages
npm install

# This will install:
# - react
# - react-dom
# - react-router-dom
# - axios
# - tailwindcss
# - recharts
# - websocket
```

**If you encounter errors:**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and package-lock.json
rmdir /s /q node_modules
del package-lock.json

# Reinstall
npm install
```

### Step 3: Verify Frontend Dependencies
```bash
# Check installed packages
npm list --depth=0

# Should show all dependencies installed
```

---

## Database Setup

### Step 1: Initialize Databases

The system uses **SQLite** for development/demo purposes.

> **Note:** PostgreSQL support is planned but not currently implemented.

```bash
# From backend directory with venv activated
cd backend

# Run database initialization
python -c "from models.database import init_db; init_db()"
```

This creates:
- `backend/data/ignisyl.db` - Main application database (users, activities, alerts)
- `data/activities.db` - Activity logs (optional)
- `data/users.db` - User data (optional)

### Step 2: Create Sample Data (Optional)
```bash
# Run with DEBUG=True to create sample users
python -c "from models.database import create_sample_data; create_sample_data()"
```

**Sample Users Created:**
| Username | Password | Role | Email |
|----------|----------|------|-------|
| admin | admin123 | admin | admin@ignisyl.demo |
| sruthi_g_s | analyst123 | analyst | sruthi.gs@ignisyl.demo |
| r_anand | analyst123 | analyst | r.anand@ignisyl.demo |

---

## Configuration

### Step 1: Backend Configuration

**Create `backend/.env` file:**
```bash
# In backend directory
# Create .env file (Windows)
type nul > .env
```

**Edit `.env` file with the following:**
```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./data/ignisyl.db

# ML Configuration
MODEL_PATH=./data/models
ENABLE_ML_TRAINING=True

# Logging
LOG_LEVEL=INFO
LOG_TO_FILE=True
```

### Step 2: Frontend Configuration

**Create `frontend/.env` file:**
```env
# API Configuration
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_WS_URL=ws://localhost:8000/ws

# Environment
NODE_ENV=development
```

### Step 3: Create Required Directories

The system auto-creates directories, but you can create them manually:
```bash
# From project root
mkdir data
mkdir data\honeypots
mkdir data\logs
mkdir data\models
mkdir data\reports
mkdir data\synthetic
```

---

## Running the Application

### Step 1: Start Backend

**Terminal 1 (Backend):**
```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
venv\Scripts\activate

# Start FastAPI server
python main.py

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
```

**Alternative (using uvicorn directly):**
```bash
uvicorn core.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Start Frontend

**Terminal 2 (Frontend):**
```bash
# Navigate to frontend directory
cd frontend

# Start React development server
npm start

# Browser will auto-open at http://localhost:3000
```

### Step 3: Access the Application

1. **Frontend Dashboard:** http://localhost:3000
2. **Backend API:** http://localhost:8000
3. **API Documentation:** http://localhost:8000/docs
4. **Alternative API Docs:** http://localhost:8000/redoc

---

## Verification

### Step 1: Check Backend Health

**Open browser or use curl:**
```bash
# Health check endpoint
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "timestamp": "2025-01-01T12:00:00"}
```

### Step 2: Test API Endpoints

**Login Test:**
```bash
# Test login endpoint
curl -X POST http://localhost:8000/api/v1/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"admin\",\"password\":\"admin123\"}"

# Expected: JSON with access_token
```

### Step 3: Test Frontend

1. Open browser to http://localhost:3000
2. You should see the **IGNISYL Login Page**
3. Login with credentials: `admin` / `admin123`
4. You should be redirected to the **Dashboard**

### Step 4: Test WebSocket Connection
```bash
# Check WebSocket endpoint
curl -i -N -H "Connection: Upgrade" ^
  -H "Upgrade: websocket" ^
  -H "Sec-WebSocket-Version: 13" ^
  -H "Sec-WebSocket-Key: test" ^
  http://localhost:8000/ws

# Should return 101 Switching Protocols
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Port Already in Use

**Error:** `Address already in use: 8000`

**Solution:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or use a different port
uvicorn core.main:app --port 8001
```

#### Issue 2: Module Not Found Error

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
# Make sure virtual environment is activated
venv\Scripts\activate

# Reinstall dependencies
pip install --break-system-packages -r requirements.txt
```

#### Issue 3: Database Connection Error

**Error:** `sqlite3.OperationalError: unable to open database file`

**Solution:**
```bash
# Create data directory
mkdir data

# Initialize database
python -c "from models.database import init_db; init_db()"
```

#### Issue 4: Frontend Not Loading

**Error:** `Cannot GET /`

**Solution:**
```bash
# Delete node_modules
rmdir /s /q node_modules

# Clear npm cache
npm cache clean --force

# Reinstall
npm install

# Restart
npm start
```

#### Issue 5: CORS Error

**Error:** `Access to XMLHttpRequest blocked by CORS policy`

**Solution:**
1. Check that backend is running on port 8000
2. Verify `REACT_APP_API_URL` in frontend `.env`
3. Restart both backend and frontend

#### Issue 6: PyTorch Installation Issues

**Error:** `Could not find a version that satisfies the requirement torch`

**Solution:**
```bash
# For Windows, install CPU version
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Or install with CUDA support (optional, for faster inference)
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

#### Issue 7: WebSocket Connection Failed

**Error:** `WebSocket connection failed`

**Solution:**
1. Verify backend is running
2. Check firewall settings
3. Verify WebSocket URL in frontend `.env`
4. Check browser console for detailed error

---

## Next Steps

After successful installation:

1. **Read the User Manual** → `docs/User_Manual.md`
2. **Review API Documentation** → http://localhost:8000/docs
3. **Check Architecture** → `docs/Architecture.md`
4. **Generate Test Data** → Use the dashboard to analyze sample activities

> **Note:** The system runs in simulation mode. Firewall actions are logged but not executed on actual network infrastructure.

---

## What This Installation Does NOT Include

| Feature | Status | Notes |
|---------|--------|-------|
| Endpoint agents | ❌ Not available | Would need separate development |
| Network monitor on laptops | ❌ Not available | Future feature |
| PostgreSQL database | ❌ Not configured | SQLite used for demo |
| Production deployment | ❌ Not configured | Single-server dev mode only |

---

## Support

For installation issues:
- **GitHub Issues:** https://github.com/SruthiGS-Gito/Ignisyl/issues
- **Developer:** Sruthi CS
- **Institution:** Sree Buddha College of Engineering, Kerala, India
<<<END Installation_Guide.md>>>
