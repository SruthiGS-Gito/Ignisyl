#!/bin/bash
# Professional Git Commit Script for IGNISYL Project
# Commits all completed fixes for ICAECT 2026 submission

set -e  # Exit on error

echo "============================================================================"
echo "IGNISYL - Git Commit Script for Fixes #1, #2, #3"
echo "============================================================================"
echo ""

# Navigate to project directory
cd "$(dirname "$0")"

# Verify we're in a git repository
if [ ! -d ".git" ]; then
    echo "ERROR: Not a git repository!"
    exit 1
fi

# Show current status
echo "Current Git Status:"
git status --short
echo ""

# Confirm with user
read -p "Do you want to proceed with commits? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted by user"
    exit 0
fi

echo ""
echo "============================================================================"
echo "COMMIT #1: Baseline Model Comparisons"
echo "============================================================================"
git add backend/compare_baselines.py \
        backend/ml_engine/baseline_models.py \
        backend/baseline_comparison_results.json \
        BASELINE_COMPARISON_REPORT.md \
        BASELINE_COMPARISON_FIXES.md \
        backend/RUN_BASELINE_COMPARISON.md

git commit -m "feat: Add comprehensive baseline model comparison framework

- Implement 5 baseline models (RF, SVM, LR, DT, NB) for comparison
- Add baseline_models.py with StandardScaler and evaluation metrics
- Generate detailed comparison report with accuracy, precision, recall, F1
- Results: RF (98.7%), SVM (96.3%), LR (95.5%), DT (98.3%), NB (95.0%)
- IGNISYL Ensemble achieves 95.6% accuracy, 0.4% FPR
- Add documentation for reproducing baseline tests

Fixes: #2 - Baseline comparison analysis
Related: ICAECT 2026 camera-ready submission"

echo "✓ Commit #1 complete"
echo ""

echo "============================================================================"
echo "COMMIT #2: Feature Engineering & Enhanced Training Data"
echo "============================================================================"
git add scripts/generate_data.py \
        data/synthetic/activities.json \
        data/synthetic/training_data.json \
        data/synthetic/users.json \
        data/models/isolation_forest.pkl \
        data/models/autoencoder.h5 \
        data/models/scaler.pkl \
        data/models/xgboost.pkl

git commit -m "feat: Enhance feature engineering with 14-feature model

BREAKING CHANGE: Expanded from 9 to 14 features for improved detection

New Features Added:
- failed_login_count: Track authentication failures
- access_frequency: Monitor unusual access patterns
- unusual_location: Detect geographical anomalies
- file_type_risk: Assess file sensitivity levels
- time_since_last: Measure temporal access patterns

Data Generation Improvements:
- Add get_file_risk() function for file type classification
- Implement realistic overlap between normal/malicious activities
- 60% of malicious activities occur during business hours (mimicry)
- File sizes: 100KB-50MB range (realistic distribution)
- Confidence scores: 0.15-0.45 range (overlap with normal)

Model Updates:
- Retrained all models with 14-feature vectors
- XGBoost: 100% training accuracy with class balancing
- Isolation Forest: Updated contamination=0.1
- Autoencoder: Retrained on expanded feature space
- Training data: 5,000 samples (10.4% malicious)

Training Script Updates:
- Extract all 14 features consistently
- Add scale_pos_weight for imbalanced data handling
- Increase n_estimators from 100 to 200 for XGBoost

Related: Feature consistency fixes for production deployment"

echo "✓ Commit #2 complete"
echo ""

echo "============================================================================"
echo "COMMIT #3: Adversarial Robustness Testing Framework"
echo "============================================================================"
git add backend/adversarial/ \
        run_adversarial_test.py \
        backend/adversarial_results.json \
        ADVERSARIAL_ROBUSTNESS_REPORT.md

git commit -m "feat: Implement comprehensive adversarial robustness testing

Add adversarial attack framework with 5 evasion strategies:

1. Slow-and-Low Attack (ESR: 99.5%)
   - Split malicious activities into 10 micro-activities over time
   - Most effective attack - exposes temporal correlation weakness

2. Mimicry Attack (ESR: 47.6%)
   - Disguise malicious activities as normal user behavior
   - Copy statistical distributions from legitimate users

3. Feature Manipulation Attack (ESR: 15.2%)
   - Targeted 30% reduction of high-impact features
   - Shift to business hours, reduce file sizes

4. Noise Injection Attack (ESR: 3.8%)
   - Add Gaussian noise (σ=0.05) to continuous features
   - Least effective - ensemble shows strong robustness

5. Ensemble Evasion Attack (ESR: 47.6%)
   - Target individual model weaknesses
   - Exploit IF tree splits and AE reconstruction

Results Summary:
- Baseline: XGBoost 100% accuracy, Ensemble 92.3% accuracy
- Strong defense against noise (96.2% detection rate)
- Strong defense against feature manipulation (84.8% detection)
- Moderate vulnerability to mimicry (52.4% detection)
- Critical weakness: Slow-and-low attacks (0.5% detection)

Implementation:
- backend/adversarial/evasion_attacks.py: Attack implementations
- backend/adversarial/robustness_test.py: Test orchestration
- backend/adversarial/attack_utils.py: Shared utilities
- run_adversarial_test.py: Standalone test runner
- Comprehensive JSON results and Markdown report generation

Recommendations:
- Add temporal correlation analysis for slow-and-low defense
- Implement behavioral profiling over extended periods
- Consider LSTM/Transformer models for sequential detection
- Deploy adversarial training for continuous improvement

Fixes: #3 - Adversarial robustness evaluation
Related: ICAECT 2026 paper - Section on system limitations"

echo "✓ Commit #3 complete"
echo ""

echo "============================================================================"
echo "COMMIT #4: Update Dependencies"
echo "============================================================================"
git add requirements.txt

git commit -m "chore: Update Python dependencies

Remove duplicate entries and clean up requirements.txt

No functional changes - maintenance only"

echo "✓ Commit #4 complete"
echo ""

echo "============================================================================"
echo "VERIFY COMMITS"
echo "============================================================================"
git log --oneline -5
echo ""

echo "============================================================================"
echo "PUSH TO GITHUB"
echo "============================================================================"
read -p "Push to GitHub origin/main? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push origin main
    echo ""
    echo "✓ Successfully pushed to GitHub!"
else
    echo "Skipped push. Run 'git push origin main' manually when ready."
fi

echo ""
echo "============================================================================"
echo "ALL COMMITS COMPLETE!"
echo "============================================================================"
echo ""
echo "Summary:"
echo "  ✓ Commit #1: Baseline model comparisons"
echo "  ✓ Commit #2: 14-feature engineering & training"
echo "  ✓ Commit #3: Adversarial robustness testing"
echo "  ✓ Commit #4: Dependencies update"
echo ""
echo "View commits: git log --oneline -5"
echo "View details: git show <commit-hash>"
echo ""
