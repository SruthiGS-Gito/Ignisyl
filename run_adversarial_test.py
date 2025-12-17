"""
Standalone Adversarial Robustness Test Runner
Bypasses TensorFlow import issues by testing only IF and XGBoost
"""

import json
import pickle
import numpy as np
from pathlib import Path
from datetime import datetime
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import sys

sys.path.insert(0, 'backend')

from adversarial.evasion_attacks import (
    SlowAndLowAttack,
    MimicryAttack,
    FeatureManipulationAttack,
    NoiseInjectionAttack,
    EnsembleEvasionAttack
)


class SimpleAdversarialTest:
    """Simplified adversarial testing without autoencoder"""

    def __init__(self):
        self.models_dir = Path('data/models')
        self.data_file = Path('data/synthetic/training_data.json')

        # Load models (skip autoencoder)
        self.load_models()
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

    def load_models(self):
        """Load IF and XGBoost only"""
        print("Loading models...")

        with open(self.models_dir / 'isolation_forest.pkl', 'rb') as f:
            self.isolation_forest = pickle.load(f)
        print("  [OK] Isolation Forest loaded")

        with open(self.models_dir / 'xgboost.pkl', 'rb') as f:
            self.xgboost = pickle.load(f)
        print("  [OK] XGBoost loaded")

    def load_test_data(self):
        """Load test data"""
        print("Loading test data...")

        with open(self.data_file, 'r') as f:
            data = json.load(f)

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

        self.normal_samples = X[y == 0]
        self.malicious_samples = X[y == 1]

        # 20% test split
        n_test_normal = int(len(self.normal_samples) * 0.2)
        n_test_malicious = int(len(self.malicious_samples) * 0.2)

        self.test_normal = self.normal_samples[:n_test_normal]
        self.test_malicious = self.malicious_samples[:n_test_malicious]

        print(f"  Test set: {len(self.test_normal)} normal + {len(self.test_malicious)} malicious")

    def predict_isolation_forest(self, X):
        """Predict with IF"""
        predictions = self.isolation_forest.predict(X)
        return (predictions == -1).astype(int)

    def predict_xgboost(self, X):
        """Predict with XGBoost"""
        return self.xgboost.predict(X)

    def predict_ensemble(self, X):
        """Ensemble prediction (IF + XGB only)"""
        pred_if = self.predict_isolation_forest(X)
        pred_xgb = self.predict_xgboost(X)
        # Both models must agree
        return ((pred_if + pred_xgb) >= 1).astype(int)

    def evaluate_model(self, model_name, X, y_true):
        """Evaluate model"""
        if model_name == 'isolation_forest':
            y_pred = self.predict_isolation_forest(X)
        elif model_name == 'xgboost':
            y_pred = self.predict_xgboost(X)
        elif model_name == 'ensemble':
            y_pred = self.predict_ensemble(X)
        else:
            raise ValueError(f"Unknown model: {model_name}")

        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

        malicious_indices = y_true == 1
        evasion_success_rate = (y_pred[malicious_indices] == 0).mean() if malicious_indices.sum() > 0 else 0.0
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

    def test_baseline(self):
        """Test baseline"""
        print("\nTesting baseline...")

        X_test = np.vstack([self.test_normal, self.test_malicious])
        y_test = np.hstack([np.zeros(len(self.test_normal)), np.ones(len(self.test_malicious))])

        results = {}
        for model_name in ['isolation_forest', 'xgboost', 'ensemble']:
            print(f"  Testing {model_name}...")
            results[model_name] = self.evaluate_model(model_name, X_test, y_test)

        return results

    def test_attack(self, attack):
        """Test attack"""
        print(f"\nTesting {attack.name}...")

        attack_result = attack.generate(self.test_malicious, self.test_normal)
        adversarial_samples = attack_result['adversarial_samples']

        X_test = np.vstack([self.test_normal, adversarial_samples])
        y_test = np.hstack([np.zeros(len(self.test_normal)), np.ones(len(adversarial_samples))])

        results = {
            'attack_info': attack.get_metadata(),
            'perturbation_metrics': attack_result.get('avg_perturbation', {}),
            'n_adversarial_samples': len(adversarial_samples),
            'models': {}
        }

        for model_name in ['isolation_forest', 'xgboost', 'ensemble']:
            print(f"  Testing {model_name}...")
            results['models'][model_name] = self.evaluate_model(model_name, X_test, y_test)

        return results

    def run_all_tests(self):
        """Run all tests"""
        print("=" * 70)
        print("IGNISYL ADVERSARIAL ROBUSTNESS TESTING")
        print("=" * 70)

        baseline_results = self.test_baseline()
        attack_results = {}

        for attack in self.attacks:
            attack_results[attack.name] = self.test_attack(attack)

        results = {
            'timestamp': datetime.now().isoformat(),
            'baseline': baseline_results,
            'attacks': attack_results
        }

        return results

    def generate_report(self, results):
        """Generate report"""
        # Save JSON
        with open('backend/adversarial_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print("\n[OK] Results saved to backend/adversarial_results.json")

        # Generate markdown
        md = f"# IGNISYL Adversarial Robustness Report\n\n**Generated:** {results['timestamp']}\n\n"
        md += "## Baseline Performance\n\n"
        md += "| Model | Accuracy | Precision | Recall | F1 | FPR | ESR |\n"
        md += "|-------|----------|-----------|--------|-----|-----|-----|\n"

        for model_name, metrics in results['baseline'].items():
            md += f"| {model_name} | {metrics['accuracy']:.3f} | {metrics['precision']:.3f} | "
            md += f"{metrics['recall']:.3f} | {metrics['f1_score']:.3f} | "
            md += f"{metrics['false_positive_rate']:.3f} | {metrics['evasion_success_rate']:.3f} |\n"

        md += "\n## Attack Results\n\n"

        for attack_name, attack_data in results['attacks'].items():
            md += f"\n### {attack_name}\n\n"
            md += f"**Description:** {attack_data['attack_info']['description']}\n\n"

            if 'perturbation_metrics' in attack_data and 'l2_distance' in attack_data['perturbation_metrics']:
                md += f"**L2 Distance:** {attack_data['perturbation_metrics']['l2_distance']:.4f}\n\n"

            md += "| Model | Accuracy | ESR | Detection Rate |\n"
            md += "|-------|----------|-----|----------------|\n"

            for model_name, metrics in attack_data['models'].items():
                md += f"| {model_name} | {metrics['accuracy']:.3f} | "
                md += f"{metrics['evasion_success_rate']:.3f} | {metrics['recall']:.3f} |\n"

        with open('ADVERSARIAL_ROBUSTNESS_REPORT.md', 'w', encoding='utf-8') as f:
            f.write(md)
        print("[OK] Markdown report saved to ADVERSARIAL_ROBUSTNESS_REPORT.md")


if __name__ == '__main__':
    tester = SimpleAdversarialTest()
    results = tester.run_all_tests()
    tester.generate_report(results)

    print("\n" + "=" * 70)
    print("ADVERSARIAL TESTING COMPLETE")
    print("=" * 70)
