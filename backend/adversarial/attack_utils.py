"""
Utility functions for adversarial attacks
"""

import numpy as np
from typing import Dict, List, Tuple


def clip_features(features: np.ndarray, feature_ranges: Dict) -> np.ndarray:
    """Clip features to valid ranges"""
    clipped = features.copy()

    # Feature indices and ranges (14 features total)
    ranges = {
        0: (0, 23),           # hour
        1: (0, 6),            # day_of_week
        2: (0, 1e9),          # file_size
        3: (0, 30),           # file_size_log (log1p(1e9) ≈ 27.6)
        4: (0, 1e10),         # bytes_transferred
        5: (0, 30),           # network_bytes_log
        6: (0, 1),            # is_weekend
        7: (0, 1),            # is_business_hours
        8: (0, 1),            # confidence_score
        9: (0, 100),          # failed_login_count
        10: (0, 100),         # access_frequency
        11: (0, 1),           # unusual_location
        12: (0, 100),         # file_type_risk
        13: (0, 1000),        # time_since_last
    }

    for idx, (min_val, max_val) in ranges.items():
        clipped[:, idx] = np.clip(clipped[:, idx], min_val, max_val)

    return clipped


def calculate_perturbation_distance(original: np.ndarray, perturbed: np.ndarray) -> Dict:
    """Calculate distance metrics between original and perturbed samples"""

    # L1 distance (Manhattan)
    l1_dist = np.mean(np.abs(perturbed - original))

    # L2 distance (Euclidean)
    l2_dist = np.mean(np.sqrt(np.sum((perturbed - original) ** 2, axis=1)))

    # L-inf distance (Maximum change)
    linf_dist = np.max(np.abs(perturbed - original))

    # Feature-wise changes
    feature_changes = np.mean(np.abs(perturbed - original), axis=0)

    return {
        'l1_distance': float(l1_dist),
        'l2_distance': float(l2_dist),
        'linf_distance': float(linf_dist),
        'feature_changes': feature_changes.tolist()
    }


def profile_normal_users(normal_samples: np.ndarray) -> Dict:
    """Profile normal user behavior for mimicry attacks"""

    profile = {
        'hour_mean': float(np.mean(normal_samples[:, 0])),
        'hour_std': float(np.std(normal_samples[:, 0])),
        'file_size_mean': float(np.mean(normal_samples[:, 2])),
        'file_size_std': float(np.std(normal_samples[:, 2])),
        'bytes_mean': float(np.mean(normal_samples[:, 4])),
        'bytes_std': float(np.std(normal_samples[:, 4])),
        'confidence_mean': float(np.mean(normal_samples[:, 8])),
        'confidence_std': float(np.std(normal_samples[:, 8])),
        'weekend_ratio': float(np.mean(normal_samples[:, 6])),
        'business_hours_ratio': float(np.mean(normal_samples[:, 7])),
    }

    return profile


def split_into_microactivities(sample: np.ndarray, n_splits: int = 10) -> np.ndarray:
    """Split a malicious activity into multiple smaller activities"""

    microactivities = []

    for i in range(n_splits):
        micro = sample.copy()

        # Divide file sizes and bytes
        micro[2] = sample[2] / n_splits  # file_size
        micro[3] = np.log1p(micro[2])     # file_size_log
        micro[4] = sample[4] / n_splits   # bytes_transferred
        micro[5] = np.log1p(micro[4])     # network_bytes_log

        # Randomize timing across days
        micro[0] = np.random.randint(9, 17)  # business hours
        micro[1] = np.random.randint(0, 5)   # weekday
        micro[6] = 0                          # not weekend
        micro[7] = 1                          # business hours

        # Reduce suspicion indicators
        micro[8] = np.random.uniform(0.1, 0.3)  # low confidence
        micro[9] = 0                             # no failed logins
        micro[10] = np.random.uniform(1, 3)      # low access frequency
        micro[11] = 0                            # normal location

        microactivities.append(micro)

    return np.array(microactivities)


def add_gaussian_noise(samples: np.ndarray, noise_level: float = 0.05) -> np.ndarray:
    """Add Gaussian noise to features"""

    noisy_samples = samples.copy()

    # Add noise to continuous features only (not binary features)
    continuous_features = [0, 2, 3, 4, 5, 8, 9, 10, 13]

    for feat_idx in continuous_features:
        noise = np.random.normal(0, noise_level, size=samples.shape[0])
        noisy_samples[:, feat_idx] += noise * np.std(samples[:, feat_idx])

    return noisy_samples


def find_decision_boundary(model, sample: np.ndarray, target_class: int = 0,
                          max_iterations: int = 100) -> np.ndarray:
    """Find decision boundary by gradient-free search"""

    perturbed = sample.copy()
    step_size = 0.1

    for iteration in range(max_iterations):
        # Get current prediction
        pred = model.predict(perturbed.reshape(1, -1))[0]

        if pred == target_class:
            break

        # Random perturbation
        perturbation = np.random.randn(len(sample)) * step_size
        candidate = perturbed + perturbation

        # Check if closer to target
        candidate_pred = model.predict(candidate.reshape(1, -1))[0]
        if candidate_pred == target_class or abs(candidate_pred - target_class) < abs(pred - target_class):
            perturbed = candidate
            step_size *= 1.1  # Increase step
        else:
            step_size *= 0.9  # Decrease step

    return perturbed
