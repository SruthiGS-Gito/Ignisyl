"""
Adversarial Robustness Test Runner for IGNISYL
Orchestrates all attack strategies and generates comprehensive report
"""

import json
import pickle
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

try:
    import tensorflow as tf
    from tensorflow import keras
except ImportError:
    # Fallback to keras directly
    from keras import models as keras_models
    keras = None
    tf = None

from .evasion_attacks import (
    SlowAndLowAttack,
    MimicryAttack,
    FeatureManipulationAttack,
    NoiseInjectionAttack,
    EnsembleEvasionAttack
)


class AdversarialRobustnessTest:
    """Comprehensive adversarial robustness testing framework"""

    def __init__(self, models_dir: str = 'data/models', data_file: str = 'data/synthetic/training_data.json'):
        self.models_dir = Path(models_dir)
        self.data_file = Path(data_file)

        # Load models
        self.models = self.load_models()

        # Load test data
        self.load_test_data()

        # Initialize attacks
        self.attacks = [
            SlowAndLowAttack(n_splits=10),
            MimicryAttack(),
            FeatureManipulationAttack(manipulation_strength=0.3),
            NoiseInjectionAttack(noise_level=0.05),
            EnsembleEvasionAttack(target_model='ensemble')
        ]

        print(f"Initialized {len(self.attacks)} attack strategies")

    def load_models(self) -> Dict:
        """Load all trained models"""

        print("Loading models...")

        models = {}

        try:
            # Load Isolation Forest
            with open(self.models_dir / 'isolation_forest.pkl', 'rb') as f:
                models['isolation_forest'] = pickle.load(f)
            print("  ✓ Isolation Forest loaded")

            # Load Autoencoder
            if tf is not None:
                models['autoencoder'] = tf.keras.models.load_model(
                    str(self.models_dir / 'autoencoder.h5'),
                    compile=False
                )
            else:
                from keras.models import load_model
                models['autoencoder'] = load_model(
                    str(self.models_dir / 'autoencoder.h5'),
                    compile=False
                )
            print("  ✓ Autoencoder loaded")

            # Load Scaler
            with open(self.models_dir / 'scaler.pkl', 'rb') as f:
                models['scaler'] = pickle.load(f)
            print("  ✓ Scaler loaded")

            # Load XGBoost
            with open(self.models_dir / 'xgboost.pkl', 'rb') as f:
                models['xgboost'] = pickle.load(f)
            print("  ✓ XGBoost loaded")

        except Exception as e:
            print(f"Error loading models: {e}")
            raise

        return models

    def load_test_data(self):
        """Load and prepare test data"""

        print("Loading test data...")

        with open(self.data_file, 'r') as f:
            data = json.load(f)

        # Extract features (14 features)
        X = []
        y = []

        for sample in data:
            features = [
                sample['hour'],
                sample['day_of_week'],
                sample.get('file_size', 0),
                np.log1p(sample.get('file_size', 0)),
                sample['bytes_transferred'],
                np.log1p(sample['bytes_transferred']),
                int(sample['is_weekend']),
                int(sample.get('is_business_hours', 0)),
                sample.get('confidence_score', 0.2),
                sample.get('failed_login_count', 0),
                sample.get('access_frequency', 1.0),
                int(sample.get('unusual_location', False)),
                sample.get('file_type_risk', 0),
                sample.get('time_since_last', 60)
            ]
            X.append(features)
            y.append(int(sample['is_malicious']))

        X = np.array(X)
        y = np.array(y)

        # Split into normal and malicious
        self.normal_samples = X[y == 0]
        self.malicious_samples = X[y == 1]
        self.normal_labels = y[y == 0]
        self.malicious_labels = y[y == 1]

        print(f"  Normal samples: {len(self.normal_samples)}")
        print(f"  Malicious samples: {len(self.malicious_samples)}")

        # Use 20% for testing
        n_test_normal = int(len(self.normal_samples) * 0.2)
        n_test_malicious = int(len(self.malicious_samples) * 0.2)

        self.test_normal = self.normal_samples[:n_test_normal]
        self.test_malicious = self.malicious_samples[:n_test_malicious]

        print(f"  Test set: {len(self.test_normal)} normal + {len(self.test_malicious)} malicious")

    def predict_isolation_forest(self, X: np.ndarray) -> np.ndarray:
        """Predict using Isolation Forest (-1 = anomaly, 1 = normal)"""
        predictions = self.models['isolation_forest'].predict(X)
        # Convert: -1 (anomaly) -> 1 (malicious), 1 (normal) -> 0 (normal)
        return (predictions == -1).astype(int)

    def predict_autoencoder(self, X: np.ndarray, threshold: float = 0.05) -> np.ndarray:
        """Predict using Autoencoder (reconstruction error > threshold = anomaly)"""
        X_scaled = self.models['scaler'].transform(X)
        reconstructed = self.models['autoencoder'].predict(X_scaled, verbose=0)
        reconstruction_errors = np.mean((X_scaled - reconstructed) ** 2, axis=1)
        return (reconstruction_errors > threshold).astype(int)

    def predict_xgboost(self, X: np.ndarray) -> np.ndarray:
        """Predict using XGBoost"""
        return self.models['xgboost'].predict(X)

    def predict_ensemble(self, X: np.ndarray) -> np.ndarray:
        """Predict using ensemble (majority vote)"""
        pred_if = self.predict_isolation_forest(X)
        pred_ae = self.predict_autoencoder(X)
        pred_xgb = self.predict_xgboost(X)

        # Majority vote
        votes = pred_if + pred_ae + pred_xgb
        return (votes >= 2).astype(int)  # At least 2 models agree on malicious

    def evaluate_model(self, model_name: str, X: np.ndarray, y_true: np.ndarray) -> Dict:
        """Evaluate a single model"""

        if model_name == 'isolation_forest':
            y_pred = self.predict_isolation_forest(X)
        elif model_name == 'autoencoder':
            y_pred = self.predict_autoencoder(X)
        elif model_name == 'xgboost':
            y_pred = self.predict_xgboost(X)
        elif model_name == 'ensemble':
            y_pred = self.predict_ensemble(X)
        else:
            raise ValueError(f"Unknown model: {model_name}")

        # Calculate metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        # Confusion matrix
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

        # Evasion success rate (for malicious samples classified as normal)
        malicious_indices = y_true == 1
        if malicious_indices.sum() > 0:
            evasion_success_rate = (y_pred[malicious_indices] == 0).mean()
        else:
            evasion_success_rate = 0.0

        # False positive rate
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

        return {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'true_positives': int(tp),
            'false_positives': int(fp),
            'true_negatives': int(tn),
            'false_negatives': int(fn),
            'evasion_success_rate': float(evasion_success_rate),
            'false_positive_rate': float(fpr)
        }

    def test_baseline(self) -> Dict:
        """Test baseline performance without attacks"""

        print("\nTesting baseline performance...")

        X_test = np.vstack([self.test_normal, self.test_malicious])
        y_test = np.hstack([
            np.zeros(len(self.test_normal)),
            np.ones(len(self.test_malicious))
        ])

        results = {}
        for model_name in ['isolation_forest', 'autoencoder', 'xgboost', 'ensemble']:
            print(f"  Testing {model_name}...")
            results[model_name] = self.evaluate_model(model_name, X_test, y_test)

        return results

    def test_attack(self, attack) -> Dict:
        """Test a single attack strategy"""

        print(f"\nTesting {attack.name}...")

        # Generate adversarial examples
        attack_result = attack.generate(
            self.test_malicious,
            self.test_normal
        )

        adversarial_samples = attack_result['adversarial_samples']
        n_adversarial = len(adversarial_samples)

        # Create test set: normal samples + adversarial samples
        X_test = np.vstack([self.test_normal, adversarial_samples])
        y_test = np.hstack([
            np.zeros(len(self.test_normal)),
            np.ones(n_adversarial)
        ])

        # Evaluate each model
        results = {
            'attack_info': attack.get_metadata(),
            'perturbation_metrics': attack_result.get('avg_perturbation', {}),
            'n_adversarial_samples': n_adversarial,
            'models': {}
        }

        for model_name in ['isolation_forest', 'autoencoder', 'xgboost', 'ensemble']:
            print(f"  Testing {model_name}...")
            results['models'][model_name] = self.evaluate_model(model_name, X_test, y_test)

        return results

    def run_all_tests(self) -> Dict:
        """Run all adversarial tests"""

        print("=" * 70)
        print("IGNISYL ADVERSARIAL ROBUSTNESS TESTING")
        print("=" * 70)

        # Test baseline
        baseline_results = self.test_baseline()

        # Test each attack
        attack_results = {}
        for attack in self.attacks:
            attack_results[attack.name] = self.test_attack(attack)

        # Compile results
        results = {
            'timestamp': datetime.now().isoformat(),
            'test_configuration': {
                'models_dir': str(self.models_dir),
                'data_file': str(self.data_file),
                'n_test_normal': len(self.test_normal),
                'n_test_malicious': len(self.test_malicious),
                'n_attacks': len(self.attacks)
            },
            'baseline': baseline_results,
            'attacks': attack_results
        }

        return results

    def generate_report(self, results: Dict, output_file: str = 'backend/adversarial_results.json'):
        """Generate detailed report"""

        print("\nGenerating report...")

        # Save JSON results
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"  ✓ Results saved to {output_path}")

        # Generate markdown report
        self.generate_markdown_report(results)

    def generate_markdown_report(self, results: Dict):
        """Generate markdown report"""

        md_content = f"""# IGNISYL Adversarial Robustness Testing Report

**Generated:** {results['timestamp']}

## Executive Summary

This report presents comprehensive adversarial robustness testing results for the IGNISYL insider threat detection system. We evaluated system resilience against 5 different evasion attack strategies.

---

## 1. Baseline Performance (No Attacks)

System performance on clean test data:

"""

        # Baseline table
        md_content += "\n### Model Performance\n\n"
        md_content += "| Model | Accuracy | Precision | Recall | F1 Score | FPR | ESR |\n"
        md_content += "|-------|----------|-----------|--------|----------|-----|-----|\n"

        for model_name, metrics in results['baseline'].items():
            md_content += f"| {model_name} | "
            md_content += f"{metrics['accuracy']:.3f} | "
            md_content += f"{metrics['precision']:.3f} | "
            md_content += f"{metrics['recall']:.3f} | "
            md_content += f"{metrics['f1_score']:.3f} | "
            md_content += f"{metrics['false_positive_rate']:.3f} | "
            md_content += f"{metrics['evasion_success_rate']:.3f} |\n"

        # Attack results
        md_content += "\n---\n\n## 2. Attack Results\n\n"

        for attack_name, attack_data in results['attacks'].items():
            md_content += f"\n### {attack_name}\n\n"
            md_content += f"**Description:** {attack_data['attack_info']['description']}\n\n"

            # Perturbation metrics
            if 'perturbation_metrics' in attack_data:
                perturb = attack_data['perturbation_metrics']
                if 'l2_distance' in perturb:
                    md_content += f"**Average L2 Perturbation:** {perturb['l2_distance']:.4f}\n\n"

            # Model results
            md_content += "\n| Model | Accuracy | ESR | ΔFPR | Detection Rate |\n"
            md_content += "|-------|----------|-----|------|----------------|\n"

            for model_name, metrics in attack_data['models'].items():
                baseline_fpr = results['baseline'][model_name]['false_positive_rate']
                delta_fpr = metrics['false_positive_rate'] - baseline_fpr

                md_content += f"| {model_name} | "
                md_content += f"{metrics['accuracy']:.3f} | "
                md_content += f"{metrics['evasion_success_rate']:.3f} | "
                md_content += f"{delta_fpr:+.3f} | "
                md_content += f"{metrics['recall']:.3f} |\n"

        # Summary analysis
        md_content += "\n---\n\n## 3. Key Findings\n\n"

        # Find most effective attack
        max_esr = 0
        worst_attack = ""
        for attack_name, attack_data in results['attacks'].items():
            ensemble_esr = attack_data['models']['ensemble']['evasion_success_rate']
            if ensemble_esr > max_esr:
                max_esr = ensemble_esr
                worst_attack = attack_name

        md_content += f"### Most Effective Attack\n"
        md_content += f"**{worst_attack}** achieved {max_esr:.1%} evasion success rate against the ensemble.\n\n"

        # Find most robust model
        model_esr = {}
        for model_name in ['isolation_forest', 'autoencoder', 'xgboost', 'ensemble']:
            avg_esr = np.mean([
                results['attacks'][attack_name]['models'][model_name]['evasion_success_rate']
                for attack_name in results['attacks'].keys()
            ])
            model_esr[model_name] = avg_esr

        most_robust = min(model_esr, key=model_esr.get)
        md_content += f"### Most Robust Model\n"
        md_content += f"**{most_robust}** showed the lowest average ESR of {model_esr[most_robust]:.1%}.\n\n"

        # Recommendations
        md_content += "\n## 4. Recommendations\n\n"
        md_content += "1. **Ensemble Diversity**: The ensemble approach provides reasonable robustness\n"
        md_content += "2. **Feature Engineering**: Consider adding more behavioral features\n"
        md_content += "3. **Anomaly Detection**: Autoencoder shows promise for novel attack detection\n"
        md_content += "4. **Continuous Learning**: Implement model retraining with adversarial examples\n"
        md_content += "5. **Monitoring**: Deploy attack detection mechanisms in production\n\n"

        # Save markdown
        md_path = Path('ADVERSARIAL_ROBUSTNESS_REPORT.md')
        with open(md_path, 'w') as f:
            f.write(md_content)

        print(f"  ✓ Markdown report saved to {md_path}")


if __name__ == '__main__':
    # Run adversarial robustness tests
    tester = AdversarialRobustnessTest()
    results = tester.run_all_tests()
    tester.generate_report(results)

    print("\n" + "=" * 70)
    print("ADVERSARIAL ROBUSTNESS TESTING COMPLETE")
    print("=" * 70)
    print(f"\nResults saved to:")
    print(f"  - backend/adversarial_results.json")
    print(f"  - ADVERSARIAL_ROBUSTNESS_REPORT.md")
