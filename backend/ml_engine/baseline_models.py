"""Baseline model comparison for IGNISYL validation"""
import time
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix
)


class BaselineComparison:
    """Compare IGNISYL against baseline machine learning models"""

    def __init__(self):
        """Initialize baseline models"""
        self.models = {
            'Random Forest': RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                n_jobs=-1
            ),
            'SVM (RBF)': SVC(
                kernel='rbf',
                probability=True,
                random_state=42
            ),
            'Logistic Regression': LogisticRegression(
                max_iter=1000,
                random_state=42,
                n_jobs=-1
            ),
            'Decision Tree': DecisionTreeClassifier(
                max_depth=10,
                random_state=42
            ),
            'Naive Bayes': GaussianNB()
        }

        self.trained_models = {}
        self.training_times = {}
        self.results = {}

    def train_all_baselines(self, X_train, y_train, verbose=True):
        """Train all baseline models

        Args:
            X_train: Training features
            y_train: Training labels
            verbose: Print progress messages

        Returns:
            Dictionary of trained models
        """
        if verbose:
            print("\n" + "="*70)
            print("[*]️ Training Baseline Models")
            print("="*70)

        for name, model in self.models.items():
            if verbose:
                print(f"\nTraining {name}...", end=" ", flush=True)

            start_time = time.time()
            model.fit(X_train, y_train)
            training_time = time.time() - start_time

            self.trained_models[name] = model
            self.training_times[name] = training_time

            if verbose:
                print(f"[OK] Done ({training_time:.2f}s)")

        if verbose:
            print("\n[OK] All baseline models trained successfully!")

        return self.trained_models

    def evaluate_model(self, model, X_test, y_test, model_name="Model"):
        """Evaluate a single model

        Args:
            model: Trained model
            X_test: Test features
            y_test: Test labels
            model_name: Name of the model for display

        Returns:
            Dictionary with evaluation metrics
        """
        # Measure prediction time
        start_time = time.time()
        y_pred = model.predict(X_test)
        prediction_time = (time.time() - start_time) * 1000  # Convert to ms

        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)

        # Calculate False Positive Rate
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0

        # Prediction time per sample
        time_per_sample = prediction_time / len(X_test)

        results = {
            'model_name': model_name,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'fpr': fpr,
            'training_time': self.training_times.get(model_name, 0),
            'prediction_time_ms': time_per_sample,
            'total_samples': len(X_test),
            'confusion_matrix': {
                'tn': int(tn),
                'fp': int(fp),
                'fn': int(fn),
                'tp': int(tp)
            }
        }

        return results

    def compare_all_models(self, X_test, y_test, verbose=True):
        """Compare all trained baseline models

        Args:
            X_test: Test features
            y_test: Test labels
            verbose: Print progress messages

        Returns:
            Dictionary with results for all models
        """
        if verbose:
            print("\n" + "="*70)
            print("[DATA] Evaluating Baseline Models")
            print("="*70)

        all_results = {}

        for name, model in self.trained_models.items():
            if verbose:
                print(f"\nEvaluating {name}...", end=" ", flush=True)

            results = self.evaluate_model(model, X_test, y_test, name)
            all_results[name] = results

            if verbose:
                print(f"[OK] Accuracy: {results['accuracy']*100:.1f}%")

        self.results = all_results

        if verbose:
            print("\n[OK] All baseline models evaluated!")

        return all_results

    def print_comparison_table(self, include_ignisyl=None):
        """Print formatted comparison table

        Args:
            include_ignisyl: Optional dict with IGNISYL results to include
        """
        print("\n" + "="*70)
        print("[DATA] BASELINE MODEL COMPARISON")
        print("="*70)

        # Header
        print(f"\n{'Model':<20} {'Acc':<8} {'Prec':<8} {'Rec':<8} {'F1':<8} {'FPR':<8} {'Time(s)':<8}")
        print("-" * 70)

        # Baseline models
        for name, results in self.results.items():
            print(
                f"{name:<20} "
                f"{results['accuracy']*100:>6.1f}% "
                f"{results['precision']*100:>6.1f}% "
                f"{results['recall']*100:>6.1f}% "
                f"{results['f1_score']*100:>6.1f}% "
                f"{results['fpr']*100:>6.1f}% "
                f"{results['training_time']:>6.1f}s"
            )

        # IGNISYL results if provided
        if include_ignisyl:
            print("-" * 70)
            for name, results in include_ignisyl.items():
                print(
                    f"{name:<20} "
                    f"{results['accuracy']*100:>6.1f}% "
                    f"{results['precision']*100:>6.1f}% "
                    f"{results['recall']*100:>6.1f}% "
                    f"{results['f1_score']*100:>6.1f}% "
                    f"{results['fpr']*100:>6.1f}% "
                    f"{results.get('training_time', 0):>6.1f}s"
                )

        print("=" * 70)

    def get_best_baseline(self):
        """Get the best performing baseline model

        Returns:
            Tuple of (model_name, accuracy)
        """
        if not self.results:
            return None, 0

        best_name = max(self.results, key=lambda x: self.results[x]['accuracy'])
        best_accuracy = self.results[best_name]['accuracy']

        return best_name, best_accuracy

    def calculate_improvement(self, ignisyl_accuracy):
        """Calculate improvement of IGNISYL over best baseline

        Args:
            ignisyl_accuracy: IGNISYL accuracy score

        Returns:
            Tuple of (improvement_percentage, best_baseline_name, best_baseline_accuracy)
        """
        best_name, best_accuracy = self.get_best_baseline()

        if best_accuracy == 0:
            return 0, best_name, 0

        improvement = ((ignisyl_accuracy - best_accuracy) / best_accuracy) * 100

        return improvement, best_name, best_accuracy

    def get_summary_statistics(self):
        """Get summary statistics for all models

        Returns:
            Dictionary with summary stats
        """
        if not self.results:
            return {}

        accuracies = [r['accuracy'] for r in self.results.values()]
        f1_scores = [r['f1_score'] for r in self.results.values()]
        fprs = [r['fpr'] for r in self.results.values()]

        summary = {
            'num_models': len(self.results),
            'mean_accuracy': np.mean(accuracies),
            'std_accuracy': np.std(accuracies),
            'max_accuracy': np.max(accuracies),
            'min_accuracy': np.min(accuracies),
            'mean_f1': np.mean(f1_scores),
            'mean_fpr': np.mean(fprs),
            'best_model': self.get_best_baseline()[0]
        }

        return summary
