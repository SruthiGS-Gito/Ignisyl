# IGNISYL Adversarial Robustness Report

**Generated:** 2025-12-17T20:05:28.688145

## Baseline Performance

| Model | Accuracy | Precision | Recall | F1 | FPR | ESR |
|-------|----------|-----------|--------|-----|-----|-----|
| isolation_forest | 0.831 | 0.144 | 0.124 | 0.133 | 0.086 | 0.876 |
| xgboost | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 |
| ensemble | 0.923 | 0.577 | 1.000 | 0.732 | 0.086 | 0.000 |

## Attack Results


### Slow-and-Low Attack

**Description:** Split malicious activities into 10 micro-activities over time

**L2 Distance:** 53117659.7696

| Model | Accuracy | ESR | Detection Rate |
|-------|----------|-----|----------------|
| isolation_forest | 0.423 | 0.995 | 0.005 |
| xgboost | 0.460 | 1.000 | 0.000 |
| ensemble | 0.423 | 0.995 | 0.005 |

### Mimicry Attack

**Description:** Disguise malicious activities as normal user behavior

**L2 Distance:** nan

| Model | Accuracy | ESR | Detection Rate |
|-------|----------|-----|----------------|
| isolation_forest | 0.820 | 0.981 | 0.019 |
| xgboost | 0.949 | 0.486 | 0.514 |
| ensemble | 0.873 | 0.476 | 0.524 |

### Feature Manipulation Attack

**Description:** Modify features with strength 0.3 to evade thresholds

**L2 Distance:** 17705886.5900

| Model | Accuracy | ESR | Detection Rate |
|-------|----------|-----|----------------|
| isolation_forest | 0.822 | 0.962 | 0.038 |
| xgboost | 0.981 | 0.181 | 0.819 |
| ensemble | 0.907 | 0.152 | 0.848 |

### Noise Injection Attack

**Description:** Add Gaussian noise with σ=0.05 to confuse models

**L2 Distance:** 1519318.2329

| Model | Accuracy | ESR | Detection Rate |
|-------|----------|-----|----------------|
| isolation_forest | 0.831 | 0.876 | 0.124 |
| xgboost | 0.995 | 0.048 | 0.952 |
| ensemble | 0.919 | 0.038 | 0.962 |

### Ensemble Evasion Attack

**Description:** Target ensemble weaknesses to evade detection

**L2 Distance:** 41313735.3765

| Model | Accuracy | ESR | Detection Rate |
|-------|----------|-----|----------------|
| isolation_forest | 0.818 | 1.000 | 0.000 |
| xgboost | 0.950 | 0.476 | 0.524 |
| ensemble | 0.873 | 0.476 | 0.524 |
