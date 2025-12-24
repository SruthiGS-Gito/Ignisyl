#!/bin/bash
# IGNISYL Backend Startup Script (Linux/Mac)

echo "============================================================================"
echo "IGNISYL Backend Server"
echo "============================================================================"
echo ""

# Navigate to project root
cd "$(dirname "$0")/.."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please create it first: python -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Verify Python
echo ""
echo "Python: $(which python)"
python --version
echo ""

# Check if dependencies are installed
echo "Checking dependencies..."
python -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Required dependencies not installed!"
    echo ""
    echo "Please install dependencies first:"
    echo "  python scripts/install_dependencies.py"
    echo ""
    echo "Or install manually:"
    echo "  pip install -r requirements.txt"
    echo ""
    exit 1
fi

echo "Dependencies OK"
echo ""

# Start backend server
echo "============================================================================"
echo "Starting backend server on http://127.0.0.1:8000"
echo "============================================================================"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

cd backend
python main.py
