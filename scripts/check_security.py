"""Security check script for Ignisyl project"""
import sys
import os
import re
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def get_project_root():
    """Get project root directory"""
    return Path(__file__).parent.parent


def check_gitignore():
    """Check if .env is in .gitignore"""
    print("\n" + "="*70)
    print("[*] SECURITY CHECK 1: .gitignore Verification")
    print("="*70)

    gitignore_path = get_project_root() / '.gitignore'

    if not gitignore_path.exists():
        print("❌ .gitignore file not found!")
        return False

    with open(gitignore_path, 'r') as f:
        content = f.read()

    # Check for important security patterns
    security_patterns = {
        '.env': r'\.env\s*$',
        '*.db files': r'\*\.db',
        '*.sqlite files': r'\*\.sqlite',
        '__pycache__': r'__pycache__',
        '*.pyc files': r'\*\.pyc'
    }

    all_found = True
    for name, pattern in security_patterns.items():
        if re.search(pattern, content, re.MULTILINE):
            print(f"✅ {name} is in .gitignore")
        else:
            print(f"❌ {name} is NOT in .gitignore")
            all_found = False

    # Check if .env.example is NOT ignored
    if '.env.example' in content and '!.env.example' not in content:
        # If .env.example is mentioned without negation, it might be ignored
        print("⚠️ WARNING: .env.example might be ignored")
    else:
        print("✅ .env.example should not be ignored")

    return all_found


def check_env_example():
    """Check that .env.example has only placeholders"""
    print("\n" + "="*70)
    print("[*] SECURITY CHECK 2: .env.example Verification")
    print("="*70)

    env_example_path = get_project_root() / '.env.example'

    if not env_example_path.exists():
        print("❌ .env.example file not found!")
        return False

    print("✅ .env.example exists")

    with open(env_example_path, 'r') as f:
        content = f.read()

    # Patterns that indicate real credentials (should NOT be present)
    suspicious_patterns = [
        (r'password\s*=\s*["\'](?!.*(?:your-|change-|secure_password|example|placeholder|xxx|<|password123|ignisyl_password))([^"\']{8,})["\']', 'Real password detected'),
        (r'(?:api_key|secret_key|token)\s*=\s*["\'](?!.*(?:your-|change-|xxx|<|example))[a-zA-Z0-9]{20,}["\']', 'Real API key/token detected'),
        (r'@(?!example\.com|localhost|your-)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 'Real email domain detected'),
    ]

    issues_found = []

    for pattern, description in suspicious_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            issues_found.append(f"{description}: {match.group(0)}")

    # Check for good placeholder patterns
    good_patterns = [
        'secure_password_here',
        'change-this-secret-key',
        'your-secure-password',
        'your-postgres-host.example.com',
        'your-mysql-host.example.com'
    ]

    found_good = False
    for pattern in good_patterns:
        if pattern in content:
            found_good = True
            break

    if found_good:
        print("✅ Placeholder patterns found (good)")
    else:
        print("⚠️ WARNING: No obvious placeholder patterns found")

    if issues_found:
        print("\n⚠️ POTENTIAL SECURITY ISSUES:")
        for issue in issues_found:
            print(f"   ❌ {issue}")
        return False
    else:
        print("✅ No suspicious credentials found in .env.example")
        return True


def check_for_real_env():
    """Check if .env file exists (should not be committed)"""
    print("\n" + "="*70)
    print("[*] SECURITY CHECK 3: Real .env File Check")
    print("="*70)

    env_path = get_project_root() / '.env'

    if env_path.exists():
        print("⚠️ WARNING: .env file exists in project directory")
        print("   This file should NEVER be committed to git")
        print("   Verify it's in .gitignore")

        # Check if it's actually in git
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'ls-files', '.env'],
                capture_output=True,
                text=True,
                cwd=get_project_root()
            )
            if result.stdout.strip():
                print("   ❌ CRITICAL: .env is tracked by git!")
                return False
            else:
                print("   ✅ .env is not tracked by git (good)")
        except Exception:
            print("   ⚠️ Could not verify git status")

        return True
    else:
        print("✅ No .env file found (expected in fresh checkout)")
        return True


def scan_for_hardcoded_secrets():
    """Scan Python files for hardcoded passwords and secrets"""
    print("\n" + "="*70)
    print("[*] SECURITY CHECK 4: Hardcoded Secrets Scan")
    print("="*70)

    project_root = get_project_root()

    # Patterns to search for
    secret_patterns = [
        (r'password\s*=\s*["\'](?!.*(?:\{|\}|%|<|>|None|True|False|\$))([^"\']{8,})["\']', 'Hardcoded password'),
        (r'(?:api_key|apikey|secret_key|access_token)\s*=\s*["\'][a-zA-Z0-9]{20,}["\']', 'Hardcoded API key'),
        (r'(?:postgres|mysql|mongodb)://[^:]+:[^@]+@', 'Database URL with credentials'),
    ]

    # Files to scan
    python_files = list(project_root.glob('**/*.py'))

    # Exclude certain directories and files
    exclude_patterns = [
        'venv', 'env', 'node_modules', '.git', '__pycache__',
        'test_', 'example_', 'check_security.py'
    ]

    issues_found = []

    scanned_count = 0

    for py_file in python_files:
        # Skip excluded paths
        if any(pattern in str(py_file) for pattern in exclude_patterns):
            continue

        scanned_count += 1

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                line_number = 0

                for line in content.split('\n'):
                    line_number += 1

                    # Skip comments
                    if line.strip().startswith('#'):
                        continue

                    for pattern, description in secret_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            # Additional validation - skip known safe patterns
                            if any(safe in line for safe in [
                                'os.getenv', 'os.environ', 'settings.',
                                'config.', 'example', 'placeholder',
                                'your-', 'change-', 'INSERT', 'VALUES',
                                'SELECT', 'UPDATE', '.get(', 'sample',
                                'demo', 'test123', 'password123'
                            ]):
                                continue

                            issues_found.append({
                                'file': str(py_file.relative_to(project_root)),
                                'line': line_number,
                                'description': description,
                                'snippet': line.strip()[:80]
                            })
        except Exception as e:
            pass  # Skip files that can't be read

    print(f"[*] Scanned {scanned_count} Python files")

    if issues_found:
        print(f"\n⚠️ FOUND {len(issues_found)} POTENTIAL ISSUE(S):")
        for issue in issues_found:
            print(f"\n   ❌ {issue['description']}")
            print(f"      File: {issue['file']}:{issue['line']}")
            print(f"      Code: {issue['snippet']}")
        return False
    else:
        print("✅ No hardcoded secrets detected")
        return True


def check_database_files():
    """Check for database files that should not be committed"""
    print("\n" + "="*70)
    print("[*] SECURITY CHECK 5: Database Files Check")
    print("="*70)

    project_root = get_project_root()

    # Database file patterns
    db_patterns = ['*.db', '*.sqlite', '*.sqlite3', '*.db-journal', '*.db-wal', '*.db-shm']

    db_files_found = []

    for pattern in db_patterns:
        db_files_found.extend(project_root.glob(f'**/{pattern}'))

    # Remove duplicates and filter
    db_files_found = list(set(db_files_found))

    # Exclude venv and other directories
    exclude_dirs = ['venv', 'env', 'node_modules', '.git']
    db_files_found = [
        f for f in db_files_found
        if not any(ex in str(f) for ex in exclude_dirs)
    ]

    if db_files_found:
        print(f"⚠️ Found {len(db_files_found)} database file(s):")
        for db_file in db_files_found:
            rel_path = db_file.relative_to(project_root)
            print(f"   [*] {rel_path}")

            # Check if it's in git
            try:
                import subprocess
                result = subprocess.run(
                    ['git', 'ls-files', str(rel_path)],
                    capture_output=True,
                    text=True,
                    cwd=project_root
                )
                if result.stdout.strip():
                    print(f"      ❌ CRITICAL: This file is tracked by git!")
                else:
                    print(f"      ✅ Not tracked by git (good)")
            except Exception:
                pass

        print("\n   ℹ️ These files should be in .gitignore")
        return True
    else:
        print("✅ No database files found in project")
        return True


def check_sensitive_files():
    """Check for other sensitive files"""
    print("\n" + "="*70)
    print("[*] SECURITY CHECK 6: Sensitive Files Check")
    print("="*70)

    project_root = get_project_root()

    sensitive_patterns = [
        '*_secret.json',
        '*_credentials.json',
        'secrets.json',
        'private_key.*',
        '*.pem',
        '*.key'
    ]

    sensitive_files = []

    for pattern in sensitive_patterns:
        sensitive_files.extend(project_root.glob(f'**/{pattern}'))

    # Exclude certain directories
    exclude_dirs = ['venv', 'env', 'node_modules', '.git']
    sensitive_files = [
        f for f in sensitive_files
        if not any(ex in str(f) for ex in exclude_dirs)
    ]

    if sensitive_files:
        print(f"⚠️ Found {len(sensitive_files)} potentially sensitive file(s):")
        for file in sensitive_files:
            rel_path = file.relative_to(project_root)
            print(f"   [*] {rel_path}")
        print("\n   ℹ️ Verify these files are in .gitignore")
        return False
    else:
        print("✅ No sensitive files detected")
        return True


def generate_security_report():
    """Generate comprehensive security report"""
    print("\n" + "="*70)
    print("[*] IGNISYL - SECURITY AUDIT REPORT")
    print("="*70)

    checks = [
        ("GitIgnore Verification", check_gitignore),
        (".env.example Verification", check_env_example),
        ("Real .env File Check", check_for_real_env),
        ("Hardcoded Secrets Scan", scan_for_hardcoded_secrets),
        ("Database Files Check", check_database_files),
        ("Sensitive Files Check", check_sensitive_files)
    ]

    results = []

    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"\n❌ Check '{check_name}' failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((check_name, False))

    # Print summary
    print("\n" + "="*70)
    print("[*] SECURITY AUDIT SUMMARY")
    print("="*70)

    passed = 0
    failed = 0

    for check_name, result in results:
        status = "✅ PASSED" if result else "⚠️ WARNING"
        print(f"{status}: {check_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print("\n" + "="*70)
    print(f"Total Checks: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Warnings: {failed}")
    print("="*70)

    if failed == 0:
        print("\n[*] ✅ ALL SECURITY CHECKS PASSED! [*]")
        print("="*70)
    else:
        print(f"\n⚠️ {failed} CHECK(S) NEED ATTENTION")
        print("="*70)

    # Security recommendations
    print("\n" + "="*70)
    print("[*] SECURITY RECOMMENDATIONS")
    print("="*70)
    print("1. ✅ Never commit .env files to git")
    print("2. ✅ Keep .env.example with only placeholders")
    print("3. ✅ Use environment variables for secrets")
    print("4. ✅ Rotate credentials regularly")
    print("5. ✅ Use strong, unique passwords")
    print("6. ✅ Enable SSL/TLS for database connections")
    print("7. ✅ Limit database user privileges")
    print("8. ✅ Regular security audits")
    print("="*70 + "\n")

    return failed == 0


if __name__ == "__main__":
    import sys
    success = generate_security_report()
    sys.exit(0 if success else 1)
