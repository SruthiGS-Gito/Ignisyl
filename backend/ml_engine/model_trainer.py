"""
ML Model Trainer for IGNISYL
Trains and saves the hybrid ML models
"""

import numpy as np
import pandas as pd
from datetime import datetime
import pickle
import os
from pathlib import Path
from typing import Dict, Tuple, Optional

# Import ML models
from ml_engine.hybrid_detector import AdvancedHybridDetector
from ml_engine.risk_scorer import ContextualRiskScorer


class ModelTrainer:
    """
    Trains and manages ML models for threat detection
    Handles model training, evaluation, and persistence
    """
    
    def __init__(self, models_dir: str = "data/models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.hybrid_detector = None
        self.risk_scorer = None
        
        print(f"[EDU] Model Trainer initialized")
        print(f"[*] Models directory: {self.models_dir}")
    
    def prepare_training_data(self, activities: list) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare training data from activities
        
        Args:
            activities: List of activity dictionaries
            
        Returns:
            Tuple of (features, labels)
        """
        if not activities:
            print("[WARN] No training data provided, using synthetic data")
            return self._generate_synthetic_data()
        
        features = []
        labels = []
        
        for activity in activities:
            # Extract features
            feature_vector = [
                activity.get('hour', 12),
                activity.get('day_of_week', 2),
                activity.get('file_size', 0),
                activity.get('bytes_transferred', 0),
                activity.get('is_weekend', 0),
                activity.get('is_business_hours', 1),
                # Add more features as needed
            ]
            
            features.append(feature_vector)
            
            # Label: 1 if high risk, 0 if normal
            risk_level = activity.get('risk_level', 'LOW')
            label = 1 if risk_level in ['HIGH', 'CRITICAL'] else 0
            labels.append(label)
        
        X = np.array(features, dtype=np.float32)
        y = np.array(labels, dtype=np.int32)
        
        print(f"[OK] Prepared {len(features)} training samples")
        return X, y
    
    def _generate_synthetic_data(self, n_samples: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate synthetic training data for initial model training
        
        Args:
            n_samples: Number of samples to generate
            
        Returns:
            Tuple of (features, labels)
        """
        print(f"[*] Generating {n_samples} synthetic training samples...")
        
        # Normal behavior (80% of data)
        n_normal = int(n_samples * 0.8)
        normal_data = np.random.normal(0, 1, (n_normal, 6))
        normal_labels = np.zeros(n_normal)
        
        # Anomalous behavior (20% of data)
        n_anomaly = n_samples - n_normal
        anomaly_data = np.random.normal(3, 1.5, (n_anomaly, 6))
        anomaly_labels = np.ones(n_anomaly)
        
        # Combine
        X = np.vstack([normal_data, anomaly_data])
        y = np.hstack([normal_labels, anomaly_labels])
        
        # Shuffle
        indices = np.random.permutation(len(X))
        X = X[indices]
        y = y[indices]
        
        print(f"[OK] Generated {len(X)} synthetic samples ({n_normal} normal, {n_anomaly} anomalous)")
        return X, y
    
    def train_models(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """
        Train all ML models
        
        Args:
            X: Training features
            y: Training labels
            
        Returns:
            Training metrics
        """
        print("\n" + "="*60)
        print("[EDU] STARTING MODEL TRAINING")
        print("="*60)
        
        # Initialize models
        self.hybrid_detector = AdvancedHybridDetector()
        self.risk_scorer = ContextualRiskScorer()
        
        # Train hybrid detector
        print("\n[DATA] Training Hybrid Detector...")
        start_time = datetime.now()
        
        self.hybrid_detector.fit(X, y)
        
        train_time = (datetime.now() - start_time).total_seconds()
        print(f"[OK] Training completed in {train_time:.2f} seconds")
        
        # Evaluate on training data
        risk_scores, model_scores = self.hybrid_detector.predict(X)
        
        # Calculate accuracy
        predictions = (risk_scores > 50).astype(int)
        accuracy = np.mean(predictions == y) * 100
        
        metrics = {
            "training_samples": len(X),
            "training_time_seconds": train_time,
            "accuracy": round(accuracy, 2),
            "model_implementations": self.hybrid_detector.get_implementation_info()['implementations'],
            "trained_at": datetime.now().isoformat()
        }
        
        print(f"\n[UP] Training Metrics:")
        print(f"   Samples: {metrics['training_samples']}")
        print(f"   Accuracy: {metrics['accuracy']}%")
        print(f"   Training Time: {metrics['training_time_seconds']:.2f}s")
        
        return metrics
    
    def save_models(self) -> str:
        """
        Save trained models to disk
        
        Returns:
            Path where models were saved
        """
        if self.hybrid_detector is None:
            raise ValueError("No models to save. Train models first.")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = self.models_dir / f"hybrid_detector_{timestamp}.pkl"
        
        # Save hybrid detector
        with open(model_path, 'wb') as f:
            pickle.dump(self.hybrid_detector, f)
        
        print(f"[SAVE] Models saved to: {model_path}")
        
        # Also save as "latest"
        latest_path = self.models_dir / "hybrid_detector_latest.pkl"
        with open(latest_path, 'wb') as f:
            pickle.dump(self.hybrid_detector, f)
        
        print(f"[SAVE] Latest model saved to: {latest_path}")
        
        return str(model_path)
    
    def load_models(self, model_path: str = None) -> bool:
        """
        Load trained models from disk
        
        Args:
            model_path: Path to model file (or use latest)
            
        Returns:
            True if successful, False otherwise
        """
        if model_path is None:
            model_path = self.models_dir / "hybrid_detector_latest.pkl"
        else:
            model_path = Path(model_path)
        
        if not model_path.exists():
            print(f"[ERROR] Model file not found: {model_path}")
            return False
        
        try:
            with open(model_path, 'rb') as f:
                self.hybrid_detector = pickle.load(f)
            
            self.risk_scorer = ContextualRiskScorer()
            
            print(f"[OK] Models loaded from: {model_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error loading models: {e}")
            return False
    
    def evaluate_model(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """
        Evaluate model performance
        
        Args:
            X_test: Test features
            y_test: Test labels
            
        Returns:
            Evaluation metrics
        """
        if self.hybrid_detector is None:
            raise ValueError("No model loaded. Train or load a model first.")
        
        # Get predictions
        risk_scores, _ = self.hybrid_detector.predict(X_test)
        predictions = (risk_scores > 50).astype(int)
        
        # Calculate metrics
        accuracy = np.mean(predictions == y_test) * 100
        
        # True/False Positives/Negatives
        tp = np.sum((predictions == 1) & (y_test == 1))
        fp = np.sum((predictions == 1) & (y_test == 0))
        tn = np.sum((predictions == 0) & (y_test == 0))
        fn = np.sum((predictions == 0) & (y_test == 1))
        
        precision = (tp / (tp + fp) * 100) if (tp + fp) > 0 else 0
        recall = (tp / (tp + fn) * 100) if (tp + fn) > 0 else 0
        f1_score = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0
        
        metrics = {
            "accuracy": round(accuracy, 2),
            "precision": round(precision, 2),
            "recall": round(recall, 2),
            "f1_score": round(f1_score, 2),
            "true_positives": int(tp),
            "false_positives": int(fp),
            "true_negatives": int(tn),
            "false_negatives": int(fn),
            "test_samples": len(X_test)
        }
        
        print("\n[DATA] Evaluation Metrics:")
        print(f"   Accuracy: {metrics['accuracy']}%")
        print(f"   Precision: {metrics['precision']}%")
        print(f"   Recall: {metrics['recall']}%")
        print(f"   F1 Score: {metrics['f1_score']}%")
        
        return metrics


# Global instance
model_trainer = ModelTrainer()


# Standalone training script
if __name__ == "__main__":
    print("="*60)
    print("IGNISYL - ML Model Trainer")
    print("="*60)
    
    trainer = ModelTrainer()
    
    # Generate synthetic training data
    X, y = trainer._generate_synthetic_data(n_samples=2000)
    
    # Train models
    metrics = trainer.train_models(X, y)
    
    # Save models
    model_path = trainer.save_models()
    
    print("\n[OK] Training complete!")
    print(f"[*] Models saved to: {model_path}")
