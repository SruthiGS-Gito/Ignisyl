"""
IGNISYL Installation Verification
Tests that all required packages are installed and importable
"""

import sys
import importlib
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(message):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def check_import(module_name, package_name=None, optional=False):
    """Try to import a module"""
    display_name = package_name or module_name

    try:
        module = importlib.import_module(module_name)

        # Try to get version if available
        version = ""
        if hasattr(module, '__version__'):
            version = f" (v{module.__version__})"
        elif module_name == "sklearn":
            import sklearn
            version = f" (v{sklearn.__version__})"

        print_success(f"{display_name}{version}")
        return True

    except ImportError as e:
        if optional:
            print_warning(f"{display_name} (optional) - Not installed")
        else:
            print_error(f"{display_name} - {str(e)}")
        return False

def main():
    """Main verification process"""
    print_header("IGNISYL Installation Verification")
    print(f"Python: {sys.version}\n")

    failed_imports = []
    optional_missing = []

    # Core Framework
    print_header("Core Framework")
    if not check_import("fastapi"):
        failed_imports.append("fastapi")
    if not check_import("uvicorn"):
        failed_imports.append("uvicorn")
    if not check_import("websockets"):
        failed_imports.append("websockets")
    if not check_import("pydantic"):
        failed_imports.append("pydantic")
    if not check_import("dotenv", "python-dotenv"):
        failed_imports.append("python-dotenv")

    # Database
    print_header("Database Support")
    if not check_import("sqlalchemy"):
        failed_imports.append("sqlalchemy")
    if not check_import("aiosqlite"):
        failed_imports.append("aiosqlite")
    if not check_import("psycopg2", "psycopg2-binary"):
        failed_imports.append("psycopg2-binary")
    if not check_import("mysql.connector", "mysql-connector-python"):
        failed_imports.append("mysql-connector-python")

    # Machine Learning - Core
    print_header("Machine Learning - Core")
    if not check_import("numpy"):
        failed_imports.append("numpy")
    if not check_import("pandas"):
        failed_imports.append("pandas")
    if not check_import("scipy"):
        failed_imports.append("scipy")
    if not check_import("sklearn", "scikit-learn"):
        failed_imports.append("scikit-learn")
    if not check_import("xgboost"):
        failed_imports.append("xgboost")
    if not check_import("joblib"):
        failed_imports.append("joblib")

    # Deep Learning
    print_header("Deep Learning")
    if not check_import("tensorflow"):
        failed_imports.append("tensorflow")
    if not check_import("keras"):
        failed_imports.append("keras")

    # PyTorch (Optional)
    print_header("PyTorch (Optional)")
    if not check_import("torch", optional=True):
        optional_missing.append("torch")
    if not check_import("torchvision", optional=True):
        optional_missing.append("torchvision")

    # Security
    print_header("Security & Authentication")
    if not check_import("jose", "python-jose"):
        failed_imports.append("python-jose")
    if not check_import("passlib"):
        failed_imports.append("passlib")
    if not check_import("cryptography"):
        failed_imports.append("cryptography")
    if not check_import("bcrypt"):
        failed_imports.append("bcrypt")

    # HTTP & API
    print_header("HTTP & API")
    if not check_import("httpx"):
        failed_imports.append("httpx")
    if not check_import("requests"):
        failed_imports.append("requests")
    if not check_import("aiofiles"):
        failed_imports.append("aiofiles")

    # Utilities
    print_header("Utilities")
    if not check_import("faker"):
        failed_imports.append("faker")
    if not check_import("reportlab"):
        failed_imports.append("reportlab")
    if not check_import("psutil"):
        failed_imports.append("psutil")
    if not check_import("watchdog"):
        failed_imports.append("watchdog")
    if not check_import("loguru"):
        failed_imports.append("loguru")

    # Development Tools
    print_header("Development Tools (Optional)")
    if not check_import("pytest", optional=True):
        optional_missing.append("pytest")

    # Summary
    print_header("Verification Summary")

    if not failed_imports:
        print_success("✓ All required packages are installed and working!")
    else:
        print_error(f"✗ {len(failed_imports)} required packages are missing or broken:")
        for package in failed_imports:
            print(f"  - {package}")

    if optional_missing:
        print_warning(f"\n{len(optional_missing)} optional packages are missing:")
        for package in optional_missing:
            print(f"  - {package}")

    # Test critical imports for IGNISYL
    print_header("Testing IGNISYL-Specific Imports")

    try:
        # Change to project root
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        sys.path.insert(0, str(project_root / "backend"))

        print("Testing backend imports...")

        # Test config
        try:
            from config.config import settings
            print_success("config.config")
        except Exception as e:
            print_error(f"config.config - {str(e)}")
            failed_imports.append("config")

        # Test ML engine
        try:
            from ml_engine.hybrid_detector import AdvancedHybridDetector
            print_success("ml_engine.hybrid_detector")
        except Exception as e:
            print_error(f"ml_engine.hybrid_detector - {str(e)}")
            failed_imports.append("ml_engine")

        # Test models
        try:
            from models.database import create_tables
            print_success("models.database")
        except Exception as e:
            print_error(f"models.database - {str(e)}")
            failed_imports.append("models")

    except Exception as e:
        print_error(f"Error testing IGNISYL imports: {e}")

    # Final verdict
    print_header("Final Verdict")

    if not failed_imports:
        print_success("✅ INSTALLATION VERIFIED - Ready to start backend!")
        print("\nNext steps:")
        print("  1. Start backend: python backend/main.py")
        print("  2. Test API: curl http://127.0.0.1:8000/api/v1/health")
        print("  3. Open frontend: cd frontend && npm start")
        return True
    else:
        print_error("❌ INSTALLATION INCOMPLETE")
        print("\nTo fix:")
        print("  1. Run: python scripts/install_dependencies.py")
        print("  2. Or manually install: pip install -r requirements.txt")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print_error(f"\nVerification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
