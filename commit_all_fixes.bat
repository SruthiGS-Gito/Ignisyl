@echo off
REM Professional Git Commit Script for IGNISYL Project
REM Commits all completed fixes for ICAECT 2026 submission

setlocal enabledelayedexpansion

echo ============================================================================
echo IGNISYL - Git Commit Script for Fixes #1, #2, #3
echo ============================================================================
echo.

REM Navigate to project directory
cd /d "%~dp0"

REM Verify we're in a git repository
if not exist ".git" (
    echo ERROR: Not a git repository!
    exit /b 1
)

REM Show current status
echo Current Git Status:
git status --short
echo.

REM Confirm with user
set /p CONTINUE="Do you want to proceed with commits? (y/n): "
if /i not "%CONTINUE%"=="y" (
    echo Aborted by user
    exit /b 0
)

echo.
echo ============================================================================
echo COMMIT #1: Baseline Model Comparisons
echo ============================================================================
git add backend/compare_baselines.py backend/ml_engine/baseline_models.py backend/baseline_comparison_results.json BASELINE_COMPARISON_REPORT.md BASELINE_COMPARISON_FIXES.md backend/RUN_BASELINE_COMPARISON.md

git commit -m "feat: Add comprehensive baseline model comparison framework" -m "" -m "- Implement 5 baseline models (RF, SVM, LR, DT, NB) for comparison" -m "- Add baseline_models.py with StandardScaler and evaluation metrics" -m "- Generate detailed comparison report with accuracy, precision, recall, F1" -m "- Results: RF (98.7%%), SVM (96.3%%), LR (95.5%%), DT (98.3%%), NB (95.0%%)" -m "- IGNISYL Ensemble achieves 95.6%% accuracy, 0.4%% FPR" -m "- Add documentation for reproducing baseline tests" -m "" -m "Fixes: #2 - Baseline comparison analysis" -m "Related: ICAECT 2026 camera-ready submission"

if errorlevel 1 (
    echo ERROR: Commit #1 failed!
    exit /b 1
)
echo [OK] Commit #1 complete
echo.

echo ============================================================================
echo COMMIT #2: Feature Engineering ^& Enhanced Training Data
echo ============================================================================
git add scripts/generate_data.py data/synthetic/activities.json data/synthetic/training_data.json data/synthetic/users.json data/models/isolation_forest.pkl data/models/autoencoder.h5 data/models/scaler.pkl data/models/xgboost.pkl

git commit -m "feat: Enhance feature engineering with 14-feature model" -m "" -m "BREAKING CHANGE: Expanded from 9 to 14 features for improved detection" -m "" -m "New Features Added:" -m "- failed_login_count: Track authentication failures" -m "- access_frequency: Monitor unusual access patterns" -m "- unusual_location: Detect geographical anomalies" -m "- file_type_risk: Assess file sensitivity levels" -m "- time_since_last: Measure temporal access patterns" -m "" -m "Data Generation Improvements:" -m "- Add get_file_risk() function for file type classification" -m "- Implement realistic overlap between normal/malicious activities" -m "- 60%% of malicious activities occur during business hours (mimicry)" -m "- File sizes: 100KB-50MB range (realistic distribution)" -m "- Confidence scores: 0.15-0.45 range (overlap with normal)" -m "" -m "Model Updates:" -m "- Retrained all models with 14-feature vectors" -m "- XGBoost: 100%% training accuracy with class balancing" -m "- Isolation Forest: Updated contamination=0.1" -m "- Autoencoder: Retrained on expanded feature space" -m "- Training data: 5,000 samples (10.4%% malicious)" -m "" -m "Training Script Updates:" -m "- Extract all 14 features consistently" -m "- Add scale_pos_weight for imbalanced data handling" -m "- Increase n_estimators from 100 to 200 for XGBoost" -m "" -m "Related: Feature consistency fixes for production deployment"

if errorlevel 1 (
    echo ERROR: Commit #2 failed!
    exit /b 1
)
echo [OK] Commit #2 complete
echo.

echo ============================================================================
echo COMMIT #3: Adversarial Robustness Testing Framework
echo ============================================================================
git add backend/adversarial/ run_adversarial_test.py backend/adversarial_results.json ADVERSARIAL_ROBUSTNESS_REPORT.md

git commit -m "feat: Implement comprehensive adversarial robustness testing" -m "" -m "Add adversarial attack framework with 5 evasion strategies:" -m "" -m "1. Slow-and-Low Attack (ESR: 99.5%%)" -m "   - Split malicious activities into 10 micro-activities over time" -m "   - Most effective attack - exposes temporal correlation weakness" -m "" -m "2. Mimicry Attack (ESR: 47.6%%)" -m "   - Disguise malicious activities as normal user behavior" -m "   - Copy statistical distributions from legitimate users" -m "" -m "3. Feature Manipulation Attack (ESR: 15.2%%)" -m "   - Targeted 30%% reduction of high-impact features" -m "   - Shift to business hours, reduce file sizes" -m "" -m "4. Noise Injection Attack (ESR: 3.8%%)" -m "   - Add Gaussian noise (sigma=0.05) to continuous features" -m "   - Least effective - ensemble shows strong robustness" -m "" -m "5. Ensemble Evasion Attack (ESR: 47.6%%)" -m "   - Target individual model weaknesses" -m "   - Exploit IF tree splits and AE reconstruction" -m "" -m "Results Summary:" -m "- Baseline: XGBoost 100%% accuracy, Ensemble 92.3%% accuracy" -m "- Strong defense against noise (96.2%% detection rate)" -m "- Strong defense against feature manipulation (84.8%% detection)" -m "- Moderate vulnerability to mimicry (52.4%% detection)" -m "- Critical weakness: Slow-and-low attacks (0.5%% detection)" -m "" -m "Implementation:" -m "- backend/adversarial/evasion_attacks.py: Attack implementations" -m "- backend/adversarial/robustness_test.py: Test orchestration" -m "- backend/adversarial/attack_utils.py: Shared utilities" -m "- run_adversarial_test.py: Standalone test runner" -m "- Comprehensive JSON results and Markdown report generation" -m "" -m "Recommendations:" -m "- Add temporal correlation analysis for slow-and-low defense" -m "- Implement behavioral profiling over extended periods" -m "- Consider LSTM/Transformer models for sequential detection" -m "- Deploy adversarial training for continuous improvement" -m "" -m "Fixes: #3 - Adversarial robustness evaluation" -m "Related: ICAECT 2026 paper - Section on system limitations"

if errorlevel 1 (
    echo ERROR: Commit #3 failed!
    exit /b 1
)
echo [OK] Commit #3 complete
echo.

echo ============================================================================
echo COMMIT #4: Update Dependencies
echo ============================================================================
git add requirements.txt

git commit -m "chore: Update Python dependencies" -m "" -m "Remove duplicate entries and clean up requirements.txt" -m "" -m "No functional changes - maintenance only"

if errorlevel 1 (
    echo ERROR: Commit #4 failed!
    exit /b 1
)
echo [OK] Commit #4 complete
echo.

echo ============================================================================
echo VERIFY COMMITS
echo ============================================================================
git log --oneline -5
echo.

echo ============================================================================
echo PUSH TO GITHUB
echo ============================================================================
set /p PUSH="Push to GitHub origin/main? (y/n): "
if /i "%PUSH%"=="y" (
    git push origin main
    if errorlevel 1 (
        echo ERROR: Push failed!
        exit /b 1
    )
    echo.
    echo [OK] Successfully pushed to GitHub!
) else (
    echo Skipped push. Run 'git push origin main' manually when ready.
)

echo.
echo ============================================================================
echo ALL COMMITS COMPLETE!
echo ============================================================================
echo.
echo Summary:
echo   [OK] Commit #1: Baseline model comparisons
echo   [OK] Commit #2: 14-feature engineering ^& training
echo   [OK] Commit #3: Adversarial robustness testing
echo   [OK] Commit #4: Dependencies update
echo.
echo View commits: git log --oneline -5
echo View details: git show ^<commit-hash^>
echo.

pause
