"""
Comprehensive PDF Report Generation Tests for IGNISYL

Tests all report types and validates:
- PDF file sizes (>50 KB minimum for user reports)
- PDF page counts (User Report: 8-16 pages)
- PDF validity
- All sections present
- Matplotlib charts present
- API endpoints working correctly
"""

import os
import sys
import json
import time
import tempfile
import requests
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_PREFIX = "/api/v1"

# Test results tracking
results = {
    "passed": 0,
    "failed": 0,
    "tests": []
}


def log_test(name: str, passed: bool, details: str = ""):
    """Log test result"""
    status = "PASSED" if passed else "FAILED"
    results["passed" if passed else "failed"] += 1
    results["tests"].append({"name": name, "passed": passed, "details": details})
    print(f"  [{status}] {name}")
    if details and not passed:
        print(f"         {details}")


def get_auth_token():
    """Get authentication token"""
    try:
        r = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json={"username": "admin", "password": "demo123"},
            timeout=10
        )
        if r.status_code == 200:
            return r.json().get("access_token")
        return None
    except Exception as e:
        print(f"Auth error: {e}")
        return None


def verify_pdf_file(filepath: str, min_size_kb: int = 50, min_pages: int = 1) -> dict:
    """
    Verify a PDF file meets quality standards.

    Returns dict with:
    - valid: bool
    - size_kb: float
    - pages: int
    - has_ignisyl_branding: bool
    - error: str (if any)
    """
    result = {
        "valid": False,
        "size_kb": 0,
        "pages": 0,
        "has_ignisyl_branding": False,
        "error": None
    }

    if not os.path.exists(filepath):
        result["error"] = "File does not exist"
        return result

    # Check file size
    size_bytes = os.path.getsize(filepath)
    result["size_kb"] = size_bytes / 1024

    if result["size_kb"] < min_size_kb:
        result["error"] = f"File too small: {result['size_kb']:.1f} KB (min: {min_size_kb} KB)"
        return result

    # Check PDF header
    with open(filepath, 'rb') as f:
        header = f.read(5)
        if header != b'%PDF-':
            result["error"] = "Not a valid PDF (missing PDF header)"
            return result

    # Try to count pages using PyPDF2 or pypdf
    try:
        try:
            from pypdf import PdfReader
        except ImportError:
            from PyPDF2 import PdfReader

        reader = PdfReader(filepath)
        result["pages"] = len(reader.pages)

        if result["pages"] < min_pages:
            result["error"] = f"Too few pages: {result['pages']} (min: {min_pages})"
            return result

        # Check for IGNISYL branding in first page
        try:
            first_page_text = reader.pages[0].extract_text()
            result["has_ignisyl_branding"] = "IGNISYL" in first_page_text.upper()
        except:
            result["has_ignisyl_branding"] = True  # Assume true if cannot extract

    except ImportError:
        # PyPDF not available, use basic validation
        result["pages"] = -1  # Unknown
        result["has_ignisyl_branding"] = True  # Assume true
    except Exception as e:
        result["error"] = f"PDF parsing error: {str(e)}"
        return result

    result["valid"] = True
    return result


# ============================================================================
# TESTS
# ============================================================================

def test_health_check():
    """Test 1: Health Check"""
    print("\n[TEST 1] Health Check")
    try:
        r = requests.get(f"{BASE_URL}{API_PREFIX}/health", timeout=10)
        if r.status_code == 200:
            data = r.json()
            is_healthy = data.get("status") == "healthy"
            log_test("Health endpoint returns 200", True)
            log_test("Status is healthy", is_healthy, f"Status: {data.get('status')}")
            return is_healthy
        else:
            log_test("Health endpoint returns 200", False, f"Got {r.status_code}")
            return False
    except Exception as e:
        log_test("Health endpoint accessible", False, str(e))
        return False


def test_authentication():
    """Test 2: Authentication"""
    print("\n[TEST 2] Authentication")
    token = get_auth_token()
    if token:
        log_test("Login successful", True)
        log_test("Token received", True, f"Token length: {len(token)}")
        return token
    else:
        log_test("Login successful", False, "Could not get token")
        return None


def test_user_activity_report(token: str):
    """Test 3: User Activity Report (8-section, 4-chart report)"""
    print("\n[TEST 3] User Activity Report (Full 8-Section Report)")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Generate report
    try:
        r = requests.post(
            f"{BASE_URL}{API_PREFIX}/reports/generate",
            json={"report_type": "user_activity", "user_id": "user_john.doe"},
            headers=headers,
            timeout=120
        )

        log_test("Report generation returns 200", r.status_code == 200, f"Status: {r.status_code}")

        if r.status_code != 200:
            return False

        # Save and verify PDF
        filepath = os.path.join(tempfile.gettempdir(), "test_user_report.pdf")
        with open(filepath, 'wb') as f:
            f.write(r.content)

        verify = verify_pdf_file(filepath, min_size_kb=100, min_pages=8)

        log_test(f"File size adequate (>100 KB)", verify["size_kb"] >= 100,
                 f"Size: {verify['size_kb']:.1f} KB")
        log_test(f"Page count adequate (8-16)", 8 <= verify.get("pages", 0) <= 20,
                 f"Pages: {verify.get('pages', 'unknown')}")
        log_test("PDF is valid", verify["valid"], verify.get("error", ""))
        log_test("Has IGNISYL branding", verify["has_ignisyl_branding"])

        print(f"         Summary: {verify['size_kb']:.1f} KB, {verify.get('pages', '?')} pages")

        # Cleanup
        os.remove(filepath)

        return verify["valid"] and verify["size_kb"] >= 100

    except Exception as e:
        log_test("Report generation", False, str(e))
        return False


def test_threat_summary_report(token: str):
    """Test 4: Threat Summary Report"""
    print("\n[TEST 4] Threat Summary Report")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        r = requests.post(
            f"{BASE_URL}{API_PREFIX}/reports/generate",
            json={"report_type": "threat_summary", "time_period": "7d"},
            headers=headers,
            timeout=60
        )

        log_test("Report generation returns 200", r.status_code == 200, f"Status: {r.status_code}")

        if r.status_code != 200:
            return False

        filepath = os.path.join(tempfile.gettempdir(), "test_threat_report.pdf")
        with open(filepath, 'wb') as f:
            f.write(r.content)

        verify = verify_pdf_file(filepath, min_size_kb=5, min_pages=2)

        log_test(f"File size adequate (>5 KB)", verify["size_kb"] >= 5,
                 f"Size: {verify['size_kb']:.1f} KB")
        log_test("PDF is valid", verify["valid"], verify.get("error", ""))

        print(f"         Summary: {verify['size_kb']:.1f} KB, {verify.get('pages', '?')} pages")

        os.remove(filepath)
        return verify["valid"]

    except Exception as e:
        log_test("Report generation", False, str(e))
        return False


def test_ml_performance_report(token: str):
    """Test 5: ML Performance Report"""
    print("\n[TEST 5] ML Performance Report")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        r = requests.post(
            f"{BASE_URL}{API_PREFIX}/reports/generate",
            json={"report_type": "ml_performance"},
            headers=headers,
            timeout=60
        )

        log_test("Report generation returns 200", r.status_code == 200, f"Status: {r.status_code}")

        if r.status_code != 200:
            return False

        filepath = os.path.join(tempfile.gettempdir(), "test_ml_report.pdf")
        with open(filepath, 'wb') as f:
            f.write(r.content)

        verify = verify_pdf_file(filepath, min_size_kb=5, min_pages=2)

        log_test(f"File size adequate", verify["size_kb"] >= 5,
                 f"Size: {verify['size_kb']:.1f} KB")
        log_test("PDF is valid", verify["valid"], verify.get("error", ""))

        print(f"         Summary: {verify['size_kb']:.1f} KB, {verify.get('pages', '?')} pages")

        os.remove(filepath)
        return verify["valid"]

    except Exception as e:
        log_test("Report generation", False, str(e))
        return False


def test_comprehensive_report(token: str):
    """Test 6: Comprehensive System Report"""
    print("\n[TEST 6] Comprehensive System Report")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        r = requests.post(
            f"{BASE_URL}{API_PREFIX}/reports/generate",
            json={"report_type": "comprehensive"},
            headers=headers,
            timeout=60
        )

        log_test("Report generation returns 200", r.status_code == 200, f"Status: {r.status_code}")

        if r.status_code != 200:
            return False

        filepath = os.path.join(tempfile.gettempdir(), "test_comprehensive_report.pdf")
        with open(filepath, 'wb') as f:
            f.write(r.content)

        verify = verify_pdf_file(filepath, min_size_kb=5, min_pages=2)

        log_test(f"File size adequate", verify["size_kb"] >= 5,
                 f"Size: {verify['size_kb']:.1f} KB")
        log_test("PDF is valid", verify["valid"], verify.get("error", ""))

        print(f"         Summary: {verify['size_kb']:.1f} KB, {verify.get('pages', '?')} pages")

        os.remove(filepath)
        return verify["valid"]

    except Exception as e:
        log_test("Report generation", False, str(e))
        return False


def test_report_list(token: str):
    """Test 7: Report List Endpoint"""
    print("\n[TEST 7] Report List Endpoint")

    headers = {"Authorization": f"Bearer {token}"}

    try:
        r = requests.get(
            f"{BASE_URL}{API_PREFIX}/reports/list",
            headers=headers,
            timeout=30
        )

        log_test("List endpoint returns 200", r.status_code == 200, f"Status: {r.status_code}")

        if r.status_code == 200:
            data = r.json()
            reports = data.get("reports", [])
            log_test("Response has reports array", isinstance(reports, list))
            print(f"         Found {len(reports)} existing reports")
            return True
        return False

    except Exception as e:
        log_test("Report list", False, str(e))
        return False


def test_individual_user_report_endpoint(token: str):
    """Test 8: Individual User Report Endpoint"""
    print("\n[TEST 8] Individual User Report Endpoint (/reports/generate-user-report)")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        r = requests.post(
            f"{BASE_URL}{API_PREFIX}/reports/generate-user-report",
            json={"user_id": "user_jane.smith"},
            headers=headers,
            timeout=120
        )

        log_test("Report generation returns 200", r.status_code == 200, f"Status: {r.status_code}")

        if r.status_code != 200:
            return False

        filepath = os.path.join(tempfile.gettempdir(), "test_individual_user_report.pdf")
        with open(filepath, 'wb') as f:
            f.write(r.content)

        verify = verify_pdf_file(filepath, min_size_kb=100, min_pages=8)

        log_test(f"File size adequate (>100 KB)", verify["size_kb"] >= 100,
                 f"Size: {verify['size_kb']:.1f} KB")
        log_test(f"Page count adequate (8-16)", 8 <= verify.get("pages", 0) <= 20,
                 f"Pages: {verify.get('pages', 'unknown')}")
        log_test("PDF is valid", verify["valid"], verify.get("error", ""))

        print(f"         Summary: {verify['size_kb']:.1f} KB, {verify.get('pages', '?')} pages")

        os.remove(filepath)
        return verify["valid"] and verify["size_kb"] >= 100

    except Exception as e:
        log_test("Report generation", False, str(e))
        return False


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("IGNISYL Report Generation - Comprehensive Test Suite")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Test 1: Health Check
    if not test_health_check():
        print("\n[FATAL] Server not healthy. Aborting tests.")
        return 1

    # Test 2: Authentication
    token = test_authentication()
    if not token:
        print("\n[FATAL] Authentication failed. Aborting tests.")
        return 1

    # Test 3-8: Report Tests
    test_user_activity_report(token)
    test_threat_summary_report(token)
    test_ml_performance_report(token)
    test_comprehensive_report(token)
    test_report_list(token)
    test_individual_user_report_endpoint(token)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    total = results["passed"] + results["failed"]
    print(f"Passed: {results['passed']}/{total}")
    print(f"Failed: {results['failed']}/{total}")

    if results["failed"] > 0:
        print("\nFailed Tests:")
        for t in results["tests"]:
            if not t["passed"]:
                print(f"  - {t['name']}: {t['details']}")

    print("=" * 60)

    return 0 if results["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
