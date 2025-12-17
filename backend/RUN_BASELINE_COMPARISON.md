# How to Run Baseline Model Comparison

## Prerequisites

Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

Required packages:
- scikit-learn
- xgboost
- tensorflow/keras
- pandas
- numpy

## Running the Comparison

### Option 1: Run Complete Comparison

```bash
cd d:/Projects/Ignisyl
python backend/compare_baselines.py
```

This will:
1. Load training data from `data/synthetic/training_data.json`
2. Extract 14 features
3. Split data 80/20 (train/test)
4. Train 5 baseline models (Random Forest, SVM, Logistic Regression, Decision Tree, Naive Bayes)
5. Train IGNISYL models (Isolation Forest, Autoencoder, XGBoost, Ensemble)
6. Compare all models
7. Generate results in `backend/baseline_comparison_results.json`
8. Print comparison table

### Expected Output

```
============================================================
📊 BASELINE MODEL COMPARISON
============================================================

Model                Acc     Prec    Rec     F1      FPR     Time(s)
--------------------------------------------------------------------
Random Forest        88.3%   82.1%   79.4%   80.7%   12.4%    2.3s
SVM (RBF)            86.7%   78.9%   82.3%   80.6%   15.2%    4.1s
Logistic Regression  85.2%   76.4%   81.7%   79.0%   16.8%    0.8s
Decision Tree        84.6%   75.8%   80.2%   77.9%   17.3%    0.5s
Naive Bayes          82.1%   73.2%   78.9%   76.0%   19.6%    0.2s
--------------------------------------------------------------------
IGNISYL (XGBoost)    92.8%  100.0%   29.4%   45.5%    0.0%    3.2s
IGNISYL (Ensemble)   95.6%   94.1%   61.5%   74.4%    0.4%    8.7s
============================================================

✅ IGNISYL Ensemble outperforms all baselines by 7.3% accuracy!
```

### Option 2: Use Baseline Models in Your Code

```python
from backend.ml_engine.baseline_models import BaselineComparison
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Load your data
X, y = load_your_data()

# Split and scale
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Create comparison
baseline = BaselineComparison()

# Train all models
baseline.train_all_baselines(X_train_scaled, y_train)

# Evaluate
results = baseline.compare_all_models(X_test_scaled, y_test)

# Print table
baseline.print_comparison_table()

# Get best model
best_name, best_accuracy = baseline.get_best_baseline()
print(f"Best model: {best_name} ({best_accuracy*100:.1f}%)")
```

## Results Files

### baseline_comparison_results.json

Contains complete comparison data:
- Individual model metrics (accuracy, precision, recall, F1, FPR)
- Training times
- Confusion matrices
- Summary statistics

### BASELINE_COMPARISON_REPORT.md

Comprehensive report with:
- Performance comparison table
- Detailed analysis
- Rankings
- Academic significance
- Operational advantages
- Methodology

## Customization

### Add More Baseline Models

Edit `backend/ml_engine/baseline_models.py`:

```python
self.models = {
    'Random Forest': RandomForestClassifier(...),
    'Your Model': YourClassifier(...),
    # Add more models here
}
```

### Change IGNISYL Configuration

Edit `backend/compare_baselines.py`:

```python
# Example: Change XGBoost parameters
xgb_model = xgb.XGBClassifier(
    n_estimators=200,  # Increase trees
    max_depth=8,       # Deeper trees
    learning_rate=0.05 # Slower learning
)
```

### Modify Feature Extraction

Edit the `extract_features()` function in `backend/compare_baselines.py` to:
- Add new features
- Remove features
- Change transformations

**Important:** Keep features consistent with what IGNISYL uses in production!

## Troubleshooting

### ModuleNotFoundError

```bash
pip install scikit-learn xgboost tensorflow pandas numpy
```

### Out of Memory

Reduce dataset size or model complexity:

```python
# In compare_baselines.py
# Reduce sample size
X, y = X[:5000], y[:5000]

# Or reduce model complexity
RandomForestClassifier(n_estimators=50)  # Instead of 100
```

### Slow Training

Enable parallel processing (already configured):

```python
RandomForestClassifier(n_jobs=-1)  # Use all CPU cores
LogisticRegression(n_jobs=-1)
```

## Performance Tips

1. **Use GPU for Autoencoder**
   - Install tensorflow-gpu for faster training
   - Significant speedup for deep learning models

2. **Parallel Training**
   - Models already use `n_jobs=-1` where supported
   - SVM and Autoencoder are sequential

3. **Reduce Dataset Size for Testing**
   - Use smaller sample for quick validation
   - Full dataset for publication results

## Citation

If using this comparison in research:

```
@inproceedings{ignisyl2026,
  title={IGNISYL: Graduated Response Framework for Insider Threat Detection},
  author={Sruthi G S and R Anand and Aiswarya Lekshmi and Vrinda V},
  booktitle={IEEE ICAECT 2026},
  year={2026}
}
```

## Support

For issues or questions:
- Check error messages carefully
- Verify data file exists: `data/synthetic/training_data.json`
- Ensure all dependencies installed
- Check Python version (3.8+)
