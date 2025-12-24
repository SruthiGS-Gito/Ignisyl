"""
IGNISYL Dependency Installer
Installs all required packages with progress tracking and error handling
"""

import subprocess
import sys
import os
from pathlib import Path
import time

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
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

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message):
    """Print info message"""
    print(f"{Colors.BLUE}→ {message}{Colors.END}")

def check_python_version():
    """Check if Python version is compatible"""
    print_header("Checking Python Environment")

    version = sys.version_info
    print_info(f"Python Version: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print_error("Python 3.9 or higher is required!")
        return False

    print_success("Python version is compatible")
    return True

def upgrade_pip():
    """Upgrade pip to latest version"""
    print_header("Upgrading pip")

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            capture_output=True
        )
        print_success("pip upgraded successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_warning(f"pip upgrade failed (continuing anyway): {e}")
        return True  # Continue even if upgrade fails

def install_package_group(name, packages, optional=False):
    """Install a group of packages"""
    print_header(f"Installing {name}")

    failed_packages = []

    for i, package in enumerate(packages, 1):
        print_info(f"[{i}/{len(packages)}] Installing {package}...")

        try:
            # Install package
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package, "--no-cache-dir"],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout per package
            )

            if result.returncode == 0:
                print_success(f"Installed {package}")
            else:
                if optional:
                    print_warning(f"Optional package {package} failed (skipping)")
                else:
                    print_error(f"Failed to install {package}")
                    print_error(result.stderr[:200])  # Print first 200 chars of error
                failed_packages.append(package)

        except subprocess.TimeoutExpired:
            print_error(f"Timeout installing {package} (took >10 minutes)")
            failed_packages.append(package)
        except Exception as e:
            print_error(f"Error installing {package}: {str(e)}")
            failed_packages.append(package)

    if failed_packages:
        if not optional:
            print_warning(f"Failed packages in {name}: {', '.join(failed_packages)}")
    else:
        print_success(f"All {name} installed successfully!")

    return failed_packages

def main():
    """Main installation process"""
    start_time = time.time()

    print_header("IGNISYL Dependency Installer")
    print_info("This will install all required packages for IGNISYL")
    print_info(f"Python: {sys.executable}")

    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Step 1: Check Python version
    if not check_python_version():
        sys.exit(1)

    # Step 2: Upgrade pip
    upgrade_pip()

    # Step 3: Install core dependencies (critical)
    core_packages = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "websockets==12.0",
        "pydantic==2.5.2",
        "pydantic-settings==2.1.0",
        "python-dotenv==1.0.0",
    ]
    core_failed = install_package_group("Core Framework", core_packages)

    # Step 4: Install database dependencies
    database_packages = [
        "sqlalchemy==2.0.23",
        "aiosqlite>=0.19.0",
        "psycopg2-binary>=2.9.9",
        "mysql-connector-python>=8.2.0",
    ]
    db_failed = install_package_group("Database Support", database_packages)

    # Step 5: Install ML dependencies (can take a while)
    ml_packages = [
        "numpy>=1.26.0",  # Install numpy first
        "pandas==2.1.4",
        "scipy>=1.10.0",
        "scikit-learn>=1.2.0",
        "xgboost>=1.7.0",
        "joblib>=1.3.0",
    ]
    ml_failed = install_package_group("Machine Learning Core", ml_packages)

    # Step 6: Install TensorFlow (heavy package)
    tf_packages = [
        "tensorflow>=2.13.0",
        "keras>=2.13.0",
    ]
    tf_failed = install_package_group("Deep Learning (TensorFlow)", tf_packages)

    # Step 7: Install PyTorch (optional, very heavy)
    print_header("PyTorch Installation")
    print_info("PyTorch is optional and very large (>2GB)")
    response = input("Install PyTorch? (y/n): ").strip().lower()

    torch_failed = []
    if response == 'y':
        torch_packages = [
            "torch>=2.0.0",
            "torchvision>=0.15.0",
        ]
        torch_failed = install_package_group("PyTorch", torch_packages, optional=True)
    else:
        print_warning("Skipping PyTorch installation")

    # Step 8: Install security dependencies
    security_packages = [
        "python-jose[cryptography]==3.3.0",
        "passlib[bcrypt]==1.7.4",
        "cryptography>=43.0.0",
        "bcrypt>=4.0.0",
    ]
    security_failed = install_package_group("Security & Authentication", security_packages)

    # Step 9: Install HTTP & API dependencies
    http_packages = [
        "httpx==0.25.2",
        "requests==2.31.0",
        "aiofiles>=23.0.0",
        "python-multipart==0.0.6",
    ]
    http_failed = install_package_group("HTTP & API", http_packages)

    # Step 10: Install utility dependencies
    utility_packages = [
        "faker==21.0.0",
        "python-dateutil>=2.8.2",
        "jsonschema>=4.20.0",
        "reportlab==4.0.7",
        "psutil>=5.9.0",
        "watchdog>=3.0.0",
        "loguru==0.7.2",
        "markdown>=3.5",
    ]
    utility_failed = install_package_group("Utilities", utility_packages)

    # Step 11: Install optional development dependencies
    dev_packages = [
        "pytest==7.4.3",
        "pytest-asyncio==0.21.1",
    ]
    dev_failed = install_package_group("Development Tools", dev_packages, optional=True)

    # Summary
    elapsed_time = time.time() - start_time

    print_header("Installation Summary")

    all_failed = (core_failed + db_failed + ml_failed + tf_failed +
                  torch_failed + security_failed + http_failed + utility_failed + dev_failed)

    if not all_failed:
        print_success("✓ All packages installed successfully!")
    else:
        print_warning(f"Installation completed with {len(all_failed)} failures:")
        for package in all_failed:
            print(f"  - {package}")

    print_info(f"\nTotal installation time: {elapsed_time/60:.1f} minutes")

    print_header("Next Steps")
    print_info("1. Run verification script: python scripts/verify_installation.py")
    print_info("2. Start backend: python backend/main.py")
    print_info("3. Test API: curl http://127.0.0.1:8000/api/v1/health")

    # Create installation report
    report_path = project_root / "INSTALLATION_REPORT.md"
    with open(report_path, "w") as f:
        f.write("# IGNISYL Installation Report\n\n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Python:** {sys.version}\n")
        f.write(f"**Installation Time:** {elapsed_time/60:.1f} minutes\n\n")

        if all_failed:
            f.write(f"## ⚠️ Failed Packages ({len(all_failed)})\n\n")
            for package in all_failed:
                f.write(f"- {package}\n")
            f.write("\n")
        else:
            f.write("## ✓ All Packages Installed Successfully\n\n")

        f.write("## Installed Package Groups\n\n")
        f.write("- Core Framework\n")
        f.write("- Database Support\n")
        f.write("- Machine Learning Core\n")
        f.write("- Deep Learning (TensorFlow)\n")
        if response == 'y':
            f.write("- PyTorch\n")
        f.write("- Security & Authentication\n")
        f.write("- HTTP & API\n")
        f.write("- Utilities\n")
        f.write("- Development Tools\n")

    print_success(f"Installation report saved to {report_path}")

    return len(all_failed) == 0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_error("\n\nInstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
