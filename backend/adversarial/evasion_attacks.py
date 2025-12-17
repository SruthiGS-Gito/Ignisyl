"""
Adversarial Evasion Attack Implementations for IGNISYL
5 attack strategies to test system robustness
"""

import numpy as np
from typing import Dict, List, Tuple
from .attack_utils import (
    clip_features,
    profile_normal_users,
    split_into_microactivities,
    add_gaussian_noise,
    find_decision_boundary,
    calculate_perturbation_distance
)


class BaseAttack:
    """Base class for all attacks"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def generate(self, malicious_samples: np.ndarray, normal_samples: np.ndarray = None) -> Dict:
        """Generate adversarial examples"""
        raise NotImplementedError

    def get_metadata(self) -> Dict:
        """Return attack metadata"""
        return {
            'name': self.name,
            'description': self.description
        }


class SlowAndLowAttack(BaseAttack):
    """
    Spread malicious activity over extended period to avoid detection

    Strategy: Convert single large malicious activity into multiple
    small activities spread across 30+ days
    """

    def __init__(self, n_splits: int = 10):
        super().__init__(
            name="Slow-and-Low Attack",
            description=f"Split malicious activities into {n_splits} micro-activities over time"
        )
        self.n_splits = n_splits

    def generate(self, malicious_samples: np.ndarray, normal_samples: np.ndarray = None) -> Dict:
        """Generate slow-and-low adversarial examples"""

        adversarial_samples = []
        original_indices = []

        for idx, sample in enumerate(malicious_samples):
            # Split into micro-activities
            micro_activities = split_into_microactivities(sample, self.n_splits)

            # Each micro-activity should appear benign
            adversarial_samples.extend(micro_activities)
            original_indices.extend([idx] * self.n_splits)

        adversarial_samples = np.array(adversarial_samples)
        adversarial_samples = clip_features(adversarial_samples, {})

        # Calculate perturbation distance
        # Compare average micro-activity to original
        distances = []
        for idx in set(original_indices):
            original = malicious_samples[idx]
            micro_avg = np.mean(adversarial_samples[np.array(original_indices) == idx], axis=0)
            dist = calculate_perturbation_distance(original.reshape(1, -1), micro_avg.reshape(1, -1))
            distances.append(dist)

        return {
            'adversarial_samples': adversarial_samples,
            'original_indices': original_indices,
            'n_samples': len(adversarial_samples),
            'avg_perturbation': {
                'l2_distance': float(np.mean([d['l2_distance'] for d in distances]))
            },
            'attack_params': {
                'n_splits': self.n_splits
            }
        }


class MimicryAttack(BaseAttack):
    """
    Copy legitimate user behavior patterns to disguise malicious activities

    Strategy: Profile normal users and generate malicious activities
    that match normal statistical distributions
    """

    def __init__(self):
        super().__init__(
            name="Mimicry Attack",
            description="Disguise malicious activities as normal user behavior"
        )

    def generate(self, malicious_samples: np.ndarray, normal_samples: np.ndarray) -> Dict:
        """Generate mimicry adversarial examples"""

        # Profile normal user behavior
        profile = profile_normal_users(normal_samples)

        adversarial_samples = []

        for sample in malicious_samples:
            mimicked = sample.copy()

            # Adjust timing to match normal patterns
            mimicked[0] = np.random.normal(profile['hour_mean'], profile['hour_std'])  # hour
            mimicked[0] = np.clip(mimicked[0], 9, 17)  # business hours

            # Adjust file sizes to match normal patterns
            mimicked[2] = np.random.normal(profile['file_size_mean'], profile['file_size_std'])  # file_size
            mimicked[3] = np.log1p(mimicked[2])  # file_size_log

            # Adjust bytes to match normal patterns
            mimicked[4] = np.random.normal(profile['bytes_mean'], profile['bytes_std'])  # bytes
            mimicked[5] = np.log1p(mimicked[4])  # bytes_log

            # Match binary feature distributions
            mimicked[6] = 1 if np.random.random() < profile['weekend_ratio'] else 0  # is_weekend
            mimicked[7] = 1 if np.random.random() < profile['business_hours_ratio'] else 0  # is_business_hours

            # Match confidence distribution
            mimicked[8] = np.random.normal(profile['confidence_mean'], profile['confidence_std'])  # confidence

            # Reduce suspicious indicators to match normal
            mimicked[9] = np.random.randint(0, 2)  # failed_login_count (low)
            mimicked[10] = np.random.uniform(1, 5)  # access_frequency (normal)
            mimicked[11] = 0  # unusual_location (normal)
            mimicked[13] = np.random.randint(30, 200)  # time_since_last (normal)

            adversarial_samples.append(mimicked)

        adversarial_samples = np.array(adversarial_samples)
        adversarial_samples = clip_features(adversarial_samples, {})

        # Calculate perturbation distance
        dist_metrics = calculate_perturbation_distance(malicious_samples, adversarial_samples)

        return {
            'adversarial_samples': adversarial_samples,
            'n_samples': len(adversarial_samples),
            'avg_perturbation': dist_metrics,
            'normal_profile': profile
        }


class FeatureManipulationAttack(BaseAttack):
    """
    Targeted feature modifications to evade detection thresholds

    Strategy: Identify decision boundaries and modify features
    to stay below detection thresholds
    """

    def __init__(self, manipulation_strength: float = 0.3):
        super().__init__(
            name="Feature Manipulation Attack",
            description=f"Modify features with strength {manipulation_strength} to evade thresholds"
        )
        self.manipulation_strength = manipulation_strength

    def generate(self, malicious_samples: np.ndarray, normal_samples: np.ndarray) -> Dict:
        """Generate feature-manipulated adversarial examples"""

        adversarial_samples = []

        for sample in malicious_samples:
            manipulated = sample.copy()

            # Target high-impact features for manipulation

            # 1. Reduce file sizes to appear more normal
            manipulated[2] *= (1 - self.manipulation_strength)  # file_size
            manipulated[3] = np.log1p(manipulated[2])  # file_size_log

            # 2. Reduce bytes transferred
            manipulated[4] *= (1 - self.manipulation_strength)  # bytes_transferred
            manipulated[5] = np.log1p(manipulated[4])  # network_bytes_log

            # 3. Shift to business hours
            if manipulated[0] < 9 or manipulated[0] > 17:
                manipulated[0] = np.random.randint(9, 17)  # hour
                manipulated[7] = 1  # is_business_hours

            # 4. Reduce confidence score
            manipulated[8] *= (1 - self.manipulation_strength)  # confidence_score

            # 5. Eliminate failed logins
            manipulated[9] = 0  # failed_login_count

            # 6. Reduce access frequency
            manipulated[10] *= (1 - self.manipulation_strength)  # access_frequency

            # 7. Mark as normal location
            manipulated[11] = 0  # unusual_location

            # 8. Reduce file type risk
            manipulated[12] *= (1 - self.manipulation_strength)  # file_type_risk

            # 9. Increase time since last access (looks less suspicious)
            manipulated[13] *= (1 + self.manipulation_strength)  # time_since_last

            adversarial_samples.append(manipulated)

        adversarial_samples = np.array(adversarial_samples)
        adversarial_samples = clip_features(adversarial_samples, {})

        # Calculate perturbation distance
        dist_metrics = calculate_perturbation_distance(malicious_samples, adversarial_samples)

        return {
            'adversarial_samples': adversarial_samples,
            'n_samples': len(adversarial_samples),
            'avg_perturbation': dist_metrics,
            'attack_params': {
                'manipulation_strength': self.manipulation_strength
            }
        }


class NoiseInjectionAttack(BaseAttack):
    """
    Add random noise to features to confuse models

    Strategy: Add small Gaussian perturbations while keeping
    features within valid ranges
    """

    def __init__(self, noise_level: float = 0.05):
        super().__init__(
            name="Noise Injection Attack",
            description=f"Add Gaussian noise with σ={noise_level} to confuse models"
        )
        self.noise_level = noise_level

    def generate(self, malicious_samples: np.ndarray, normal_samples: np.ndarray = None) -> Dict:
        """Generate noise-injected adversarial examples"""

        # Add Gaussian noise
        adversarial_samples = add_gaussian_noise(malicious_samples, self.noise_level)
        adversarial_samples = clip_features(adversarial_samples, {})

        # Calculate perturbation distance
        dist_metrics = calculate_perturbation_distance(malicious_samples, adversarial_samples)

        return {
            'adversarial_samples': adversarial_samples,
            'n_samples': len(adversarial_samples),
            'avg_perturbation': dist_metrics,
            'attack_params': {
                'noise_level': self.noise_level
            }
        }


class EnsembleEvasionAttack(BaseAttack):
    """
    Exploit disagreement between ensemble models

    Strategy: Find weaknesses in individual models and craft
    adversarial examples that pass majority vote
    """

    def __init__(self, target_model: str = 'ensemble'):
        super().__init__(
            name="Ensemble Evasion Attack",
            description=f"Target {target_model} weaknesses to evade detection"
        )
        self.target_model = target_model

    def generate(self, malicious_samples: np.ndarray, normal_samples: np.ndarray,
                 models: Dict = None) -> Dict:
        """Generate ensemble-evasion adversarial examples"""

        if models is None:
            # Fallback to generic manipulation if models not provided
            return self._generic_evasion(malicious_samples)

        adversarial_samples = []

        for sample in malicious_samples:
            evaded = sample.copy()

            # Strategy 1: Target Isolation Forest (tree-based)
            # IF uses feature splits - modify to cross decision boundaries
            evaded[0] = np.random.randint(10, 16)  # hour (business hours)
            evaded[2] *= 0.4  # Reduce file_size significantly
            evaded[3] = np.log1p(evaded[2])
            evaded[4] *= 0.4  # Reduce bytes_transferred
            evaded[5] = np.log1p(evaded[4])

            # Strategy 2: Target Autoencoder (reconstruction-based)
            # AE looks for deviations from normal manifold - stay close to normal
            evaded[8] = np.random.uniform(0.15, 0.30)  # Low confidence (normal range)
            evaded[9] = 0  # No failed logins
            evaded[10] = np.random.uniform(2, 5)  # Normal access frequency

            # Strategy 3: Target XGBoost (probability-based)
            # XGB combines features - reduce high-weight features
            evaded[6] = 0  # Weekday
            evaded[7] = 1  # Business hours
            evaded[11] = 0  # Normal location
            evaded[12] = 10  # Low file risk

            adversarial_samples.append(evaded)

        adversarial_samples = np.array(adversarial_samples)
        adversarial_samples = clip_features(adversarial_samples, {})

        # Calculate perturbation distance
        dist_metrics = calculate_perturbation_distance(malicious_samples, adversarial_samples)

        return {
            'adversarial_samples': adversarial_samples,
            'n_samples': len(adversarial_samples),
            'avg_perturbation': dist_metrics,
            'attack_params': {
                'target_model': self.target_model
            }
        }

    def _generic_evasion(self, malicious_samples: np.ndarray) -> Dict:
        """Fallback evasion without model access"""

        adversarial_samples = []

        for sample in malicious_samples:
            evaded = sample.copy()

            # Aggressive normalization
            evaded[0] = np.random.randint(9, 17)  # Business hours
            evaded[2] *= 0.3  # Drastically reduce file_size
            evaded[3] = np.log1p(evaded[2])
            evaded[4] *= 0.3  # Drastically reduce bytes
            evaded[5] = np.log1p(evaded[4])
            evaded[6] = 0  # Weekday
            evaded[7] = 1  # Business hours
            evaded[8] = 0.2  # Low confidence
            evaded[9] = 0  # No failed logins
            evaded[10] = 2.0  # Normal frequency
            evaded[11] = 0  # Normal location
            evaded[12] = 10  # Low risk file
            evaded[13] = 60  # Normal time gap

            adversarial_samples.append(evaded)

        adversarial_samples = np.array(adversarial_samples)
        adversarial_samples = clip_features(adversarial_samples, {})

        dist_metrics = calculate_perturbation_distance(malicious_samples, adversarial_samples)

        return {
            'adversarial_samples': adversarial_samples,
            'n_samples': len(adversarial_samples),
            'avg_perturbation': dist_metrics
        }
