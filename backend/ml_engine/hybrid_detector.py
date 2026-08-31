"""
Hybrid ML Engine for IGNISYL-Neo
Automatically detects available libraries and uses best available implementation
"""
# This file : Automatically selects and combines the best ML algorithms
# - Detects which ML libraries are installed (scikit-learn, TensorFlow, XGBoost)
# - Uses professional libraries when available, custom code as fallback
# - Combines predictions from multiple models for better accuracy

import numpy as np
import pandas as pd
import sys
import os
from typing import Dict, List, Tuple, Optional, Union

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class MLLibraryDetector:
    """Detect available ML libraries and capabilities"""
    
    def __init__(self):
        self.available_libraries = {}
        self._detect_libraries()
    
    def _detect_libraries(self):
        """Detect which ML libraries are available"""
        
        # Test scikit-learn
        try:
            import sklearn
            from sklearn.ensemble import IsolationForest
            from sklearn.preprocessing import StandardScaler
            self.available_libraries['sklearn'] = {
                'available': True,
                'version': sklearn.__version__,
                'components': ['IsolationForest', 'StandardScaler', 'PCA']
            }
            print(f"[OK] scikit-learn {sklearn.__version__} detected")
        except ImportError:
            self.available_libraries['sklearn'] = {'available': False}
            print("[ERROR] scikit-learn not available")
        
        # Test XGBoost
        try:
            import xgboost as xgb
            self.available_libraries['xgboost'] = {
                'available': True,
                'version': xgb.__version__,
                'components': ['XGBClassifier']
            }
            print(f"[OK] XGBoost {xgb.__version__} detected")
        except ImportError:
            self.available_libraries['xgboost'] = {'available': False}
            print("[ERROR] XGBoost not available")
        
        # Test TensorFlow
        try:
            import tensorflow as tf
            self.available_libraries['tensorflow'] = {
                'available': True,
                'version': tf.__version__,
                'components': ['Keras', 'Sequential', 'Dense']
            }
            print(f"[OK] TensorFlow {tf.__version__} detected")
        except ImportError:
            self.available_libraries['tensorflow'] = {'available': False}
            print("[ERROR] TensorFlow not available")
        
        # Test PyTorch
        try:
            import torch
            self.available_libraries['torch'] = {
                'available': True,
                'version': torch.__version__,
                'components': ['nn', 'optim']
            }
            print(f"[OK] PyTorch {torch.__version__} detected")
        except ImportError:
            self.available_libraries['torch'] = {'available': False}
            print("[ERROR] PyTorch not available")
    
    def get_best_implementation(self, algorithm_type: str) -> str:
        """Determine best available implementation for algorithm type"""
        
        implementations = {
            'isolation_forest': ['sklearn', 'custom'],
            'autoencoder': ['tensorflow', 'torch', 'custom'],
            'gradient_boosting': ['xgboost', 'sklearn', 'custom'],
            'neural_network': ['tensorflow', 'torch', 'custom']
        }
        
        if algorithm_type not in implementations:
            return 'custom'
        
        for lib in implementations[algorithm_type]:
            if lib == 'custom':
                return 'custom'
            if self.available_libraries.get(lib, {}).get('available', False):
                return lib
        
        return 'custom'

class HybridIsolationForest:
    """Hybrid Isolation Forest using best available implementation"""
    
    def __init__(self, detector: MLLibraryDetector, **kwargs):
        self.detector = detector
        self.implementation = detector.get_best_implementation('isolation_forest')
        self.model = None
        self.kwargs = kwargs
    
        if self.implementation == 'sklearn' or self.implementation == 'custom':
            # Always use sklearn if available, otherwise error
            try:
                from sklearn.ensemble import IsolationForest
                self.model = IsolationForest(**kwargs)
                self.implementation = 'sklearn'
                print("Using scikit-learn Isolation Forest")
            except ImportError:
                raise ImportError("scikit-learn is required for Isolation Forest. Install with: pip install scikit-learn")
    
    def fit(self, X):
        return self.model.fit(X)
    
    def predict(self, X):
        if self.implementation == 'sklearn':
            # sklearn returns -1 for anomalies, 1 for normal
            predictions = self.model.predict(X)
            return (predictions == -1).astype(int)
        else:
            return self.model.predict(X)
    
    def decision_function(self, X):
        if self.implementation == 'sklearn':
            return self.model.decision_function(X)
        else:
            return self.model.decision_function(X)

class HybridAutoencoder:
    """Hybrid Autoencoder using best available implementation"""
    
    def __init__(self, detector: MLLibraryDetector, **kwargs):
        self.detector = detector
        self.implementation = detector.get_best_implementation('autoencoder')
        self.model = None
        self.kwargs = kwargs
        self.is_available = False  # Track if autoencoder is available

        if self.implementation == 'tensorflow':
            self._create_tensorflow_model(**kwargs)
        elif self.implementation == 'torch':
            self._create_torch_model(**kwargs)
        else:
            # Try tensorflow as fallback, if not available use numpy-based
            self._create_tensorflow_model(**kwargs)
            if not self.is_available:
                self._create_numpy_fallback(**kwargs)

    def _create_numpy_fallback(self, encoding_dim=32, **kwargs):
        """Create simple numpy-based autoencoder as fallback"""
        print("[INFO] Using numpy-based simple autoencoder (no deep learning)")
        self.implementation = 'numpy'
        self.encoding_dim = encoding_dim
        self.is_available = True
        self.mean = None
        self.std = None
        self.threshold = None
    
    def _create_tensorflow_model(self, encoding_dim=32, **kwargs):
        """Create TensorFlow/Keras autoencoder"""
        try:
            import tensorflow as tf
            from tensorflow.keras.models import Model
            from tensorflow.keras.layers import Input, Dense

            print("Using TensorFlow Autoencoder")

            # This will be implemented when we have input dimension
            self.tf_model_config = {
                'encoding_dim': encoding_dim,
                'epochs': kwargs.get('epochs', 100),
                'batch_size': kwargs.get('batch_size', 32),
                'learning_rate': kwargs.get('learning_rate', 0.001)
            }
            self.model_type = 'tensorflow'
            self.is_available = True

        except Exception as e:
            print(f"[WARN] TensorFlow model creation failed: {e}")
            self.model = None
            self.is_available = False
    
    def _create_torch_model(self, encoding_dim=32, **kwargs):
        """Create PyTorch autoencoder"""
        try:
            import torch
            import torch.nn as nn

            print("Using PyTorch Autoencoder")
            self.torch_config = {
                'encoding_dim': encoding_dim,
                'epochs': kwargs.get('epochs', 100),
                'batch_size': kwargs.get('batch_size', 32),
                'learning_rate': kwargs.get('learning_rate', 0.001)
            }
            self.model_type = 'torch'
            self.is_available = True

        except Exception as e:
            print(f"[WARN] PyTorch model creation failed: {e}")
            print("[WARN] Autoencoder will be unavailable")
            self.model = None
            self.implementation = 'custom'
            self.is_available = False

    def fit(self, X):
        if self.implementation == 'tensorflow' and hasattr(self, 'tf_model_config'):
            return self._fit_tensorflow(X)
        elif self.implementation == 'torch' and hasattr(self, 'torch_config'):
            return self._fit_torch(X)
        elif self.implementation == 'numpy':
            return self._fit_numpy(X)
        elif hasattr(self.model, 'fit'):
            return self.model.fit(X)
        else:
            print(f"[WARN] Autoencoder fit skipped - no implementation available")
            return self

    def _fit_torch(self, X):
        """Fit PyTorch autoencoder model"""
        import torch
        import torch.nn as nn
        import torch.optim as optim
        from torch.utils.data import DataLoader, TensorDataset

        X = np.array(X, dtype=np.float32)
        input_dim = X.shape[1]
        encoding_dim = self.torch_config['encoding_dim']

        # Normalize data
        self.mean = np.mean(X, axis=0)
        self.std = np.std(X, axis=0) + 1e-8
        X_norm = (X - self.mean) / self.std

        # Define autoencoder architecture
        class Autoencoder(nn.Module):
            def __init__(self, input_dim, encoding_dim):
                super(Autoencoder, self).__init__()
                self.encoder = nn.Sequential(
                    nn.Linear(input_dim, encoding_dim),
                    nn.ReLU(),
                    nn.Linear(encoding_dim, encoding_dim // 2),
                    nn.ReLU()
                )
                self.decoder = nn.Sequential(
                    nn.Linear(encoding_dim // 2, encoding_dim),
                    nn.ReLU(),
                    nn.Linear(encoding_dim, input_dim),
                    nn.Sigmoid()
                )

            def forward(self, x):
                encoded = self.encoder(x)
                decoded = self.decoder(encoded)
                return decoded

        # Create model
        self.torch_model = Autoencoder(input_dim, encoding_dim)

        # Training setup
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.torch_model.parameters(),
                               lr=self.torch_config['learning_rate'])

        # Create data loader
        X_tensor = torch.FloatTensor(X_norm)
        dataset = TensorDataset(X_tensor, X_tensor)
        dataloader = DataLoader(dataset, batch_size=self.torch_config['batch_size'], shuffle=True)

        # Training loop
        self.torch_model.train()
        epochs = self.torch_config['epochs']
        for epoch in range(epochs):
            total_loss = 0
            for batch_X, _ in dataloader:
                optimizer.zero_grad()
                output = self.torch_model(batch_X)
                loss = criterion(output, batch_X)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

            if (epoch + 1) % 20 == 0:
                avg_loss = total_loss / len(dataloader)
                print(f"   PyTorch Autoencoder Epoch [{epoch+1}/{epochs}], Loss: {avg_loss:.6f}")

        # Calculate threshold on training data
        self.torch_model.eval()
        with torch.no_grad():
            train_pred = self.torch_model(X_tensor).numpy()
            train_mse = np.mean(np.power(X_norm - train_pred, 2), axis=1)
            self.threshold = np.percentile(train_mse, 95)

        print(f"[OK] PyTorch Autoencoder trained: threshold={self.threshold:.4f}")
        return self

    def _fit_numpy(self, X):
        """Simple numpy-based anomaly detection using statistical methods"""
        X = np.array(X, dtype=np.float32)

        # Calculate mean and std for each feature
        self.mean = np.mean(X, axis=0)
        self.std = np.std(X, axis=0) + 1e-8

        # Normalize
        X_norm = (X - self.mean) / self.std

        # Calculate reconstruction error as simple distance from mean
        errors = np.sqrt(np.sum(X_norm ** 2, axis=1))

        # Set threshold at 95th percentile
        self.threshold = np.percentile(errors, 95)
        print(f"[INFO] Numpy autoencoder trained: threshold={self.threshold:.4f}")
        return self
    
    def _fit_tensorflow(self, X):
        """Fit TensorFlow model"""
        import tensorflow as tf
        from tensorflow.keras.models import Model
        from tensorflow.keras.layers import Input, Dense
        from tensorflow.keras.optimizers import Adam
        
        X = np.array(X)
        input_dim = X.shape[1]
        encoding_dim = self.tf_model_config['encoding_dim']
        
        # Build autoencoder
        input_layer = Input(shape=(input_dim,))
        encoded = Dense(encoding_dim, activation='relu')(input_layer)
        encoded = Dense(encoding_dim // 2, activation='relu')(encoded)
        
        decoded = Dense(encoding_dim, activation='relu')(encoded)
        decoded = Dense(input_dim, activation='sigmoid')(decoded)
        
        self.tf_model = Model(input_layer, decoded)
        self.tf_model.compile(optimizer=Adam(learning_rate=self.tf_model_config['learning_rate']),
                             loss='mse')
        
        # Normalize data
        self.mean = np.mean(X, axis=0)
        self.std = np.std(X, axis=0) + 1e-8
        X_norm = (X - self.mean) / self.std
        
        # Train
        history = self.tf_model.fit(
            X_norm, X_norm,
            epochs=self.tf_model_config['epochs'],
            batch_size=self.tf_model_config['batch_size'],
            verbose=0,
            validation_split=0.2
        )
        
        # Calculate threshold
        train_pred = self.tf_model.predict(X_norm, verbose=0)
        train_mse = np.mean(np.power(X_norm - train_pred, 2), axis=1)
        self.threshold = np.percentile(train_mse, 95)
        
        return self
    
    def reconstruction_error(self, X):
        if self.implementation == 'tensorflow' and hasattr(self, 'tf_model'):
            X = np.array(X)
            X_norm = (X - self.mean) / self.std
            pred = self.tf_model.predict(X_norm, verbose=0)
            return np.mean(np.power(X_norm - pred, 2), axis=1)
        elif self.implementation == 'torch' and hasattr(self, 'torch_model'):
            import torch
            X = np.array(X, dtype=np.float32)
            X_norm = (X - self.mean) / self.std
            X_tensor = torch.FloatTensor(X_norm)
            self.torch_model.eval()
            with torch.no_grad():
                pred = self.torch_model(X_tensor).numpy()
            return np.mean(np.power(X_norm - pred, 2), axis=1)
        elif self.implementation == 'numpy' and self.mean is not None:
            X = np.array(X, dtype=np.float32)
            X_norm = (X - self.mean) / self.std
            # Return distance from origin in normalized space
            return np.sqrt(np.sum(X_norm ** 2, axis=1))
        elif hasattr(self.model, 'reconstruction_error'):
            return self.model.reconstruction_error(X)
        else:
            # Return zeros if no implementation available
            return np.zeros(len(X))
    
    def predict(self, X):
        errors = self.reconstruction_error(X)
        threshold = getattr(self, 'threshold', np.percentile(errors, 95))
        return (errors > threshold).astype(int)

class HybridXGBoost:
    """Hybrid XGBoost using best available implementation"""
    
    def __init__(self, detector: MLLibraryDetector, **kwargs):
        self.detector = detector
        self.implementation = detector.get_best_implementation('gradient_boosting')
        self.model = None
        self.kwargs = kwargs
    
        if self.implementation == 'xgboost':
            import xgboost as xgb
            self.model = xgb.XGBClassifier(**kwargs)
            print("Using XGBoost implementation")
        elif self.implementation == 'sklearn' or self.implementation == 'custom':
            # Use sklearn as fallback
            from sklearn.ensemble import GradientBoostingClassifier
            self.model = GradientBoostingClassifier(**kwargs)
            self.implementation = 'sklearn'
            print("Using scikit-learn Gradient Boosting")
    
    def fit(self, X, y):
        return self.model.fit(X, y)
    
    def predict(self, X):
        return self.model.predict(X)
    
    def predict_proba(self, X):
        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(X)
        else:
            # Fallback for custom implementation
            predictions = self.model.predict(X)
            proba = np.column_stack([1 - predictions, predictions])
            return proba

class AdvancedHybridDetector:
    """Advanced hybrid anomaly detector using best available implementations"""

    # Measured anomaly rate in the synthetic training set: 147 anomalous /
    # 46934 total activities ~= 0.31% (see data_generator.py's inject_anomalies).
    # Used as IsolationForest's contamination default - see __init__ for why
    # this is preferred over sklearn's contamination='auto'.
    MEASURED_ANOMALY_RATE = 0.003

    def __init__(self, contamination: float = MEASURED_ANOMALY_RATE):
        self.detector = MLLibraryDetector()
        self.models = {}
        self.is_trained = False
        self.feature_columns = []

        # contamination was hardcoded to 0.1 (10% expected anomalies), but the
        # actual measured rate in the synthetic data is ~0.3% - a >30x mismatch
        # that made IsolationForest's decision threshold badly miscalibrated
        # (it was tuned to flag the most anomalous-looking 10% of activities,
        # not the ~0.3% that are actually anomalous).
        #
        # contamination='auto' was considered instead, but sklearn's 'auto'
        # does NOT use the data's real outlier proportion - it applies a fixed
        # heuristic threshold from the original Isolation Forest paper,
        # independent of dataset. Since we have a genuine measured rate from
        # labeled synthetic data, an explicit value tied to that measurement
        # is more accurate here than the generic heuristic.
        #
        # Caveat: fit() below trains isolation_forest on whatever X it's given,
        # which upstream (main.py's startup_event) is the SMOTE-resampled
        # ~50/50 training set, not the natural ~0.3% distribution. contamination
        # describes the real-world rate we want the decision threshold tuned
        # for, not the class balance of the data isolation_forest is literally
        # fit on - those two are different things when SMOTE is involved.
        self.isolation_forest = HybridIsolationForest(
            self.detector,
            contamination=contamination,
            n_estimators=100
        )
        
        self.autoencoder = HybridAutoencoder(
            self.detector,
            encoding_dim=32,
            epochs=100,
            learning_rate=0.001
        )
        
        self.xgboost = HybridXGBoost(
            self.detector,
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1
        )
        
        # Initialize scaler based on available libraries
        if self.detector.available_libraries.get('sklearn', {}).get('available', False):
            from sklearn.preprocessing import StandardScaler
            self.scaler = StandardScaler()
        else:
            self.scaler = None
    
    def _scale_features(self, X, fit=False):
        """Scale features using best available method"""
        X = np.array(X, dtype=np.float32)
        
        if self.scaler is not None:
            if fit:
                return self.scaler.fit_transform(X)
            else:
                return self.scaler.transform(X)
        else:
            # Manual scaling
            if fit:
                self.manual_mean = np.mean(X, axis=0)
                self.manual_std = np.std(X, axis=0) + 1e-8
            
            return (X - self.manual_mean) / self.manual_std
    
    def fit(self, X_train, y_train=None, X_train_res=None, y_train_res=None):
        """Train each sub-model on the data that's actually correct for its method.

        - Isolation Forest: fit on X_train/y_train - the ORIGINAL, non-resampled,
          naturally-imbalanced data (all classes). Its `contamination` parameter
          is calibrated against this real-ish anomaly ratio, so feeding it a
          SMOTE-balanced 50/50 pool would defeat that calibration.
        - Autoencoder: fit on X_train filtered to y_train == 0 only - no
          anomalies, real or SMOTE-synthesized, ever enter its training data.
          This is the textbook-correct setup for reconstruction-error-based
          detection: it learns what "normal" looks like, nothing else.
        - XGBoost: fit on X_train_res/y_train_res - the SMOTE-resampled data.
          It's the supervised leg of the ensemble and is the one model that
          actually benefits from class balancing.

        X_train_res/y_train_res default to X_train/y_train when not given, so
        existing callers that only ever had one dataset (no SMOTE step) keep
        working exactly as before.
        """
        X_train = np.array(X_train, dtype=np.float32)
        y_train = np.array(y_train) if y_train is not None else None

        if X_train_res is None:
            X_train_res, y_train_res = X_train, y_train
        else:
            X_train_res = np.array(X_train_res, dtype=np.float32)
            y_train_res = np.array(y_train_res) if y_train_res is not None else None

        print(f"Training hybrid detector - Isolation Forest & Autoencoder on "
              f"{X_train.shape[0]} original (non-resampled) samples, XGBoost on "
              f"{X_train_res.shape[0]} (SMOTE-resampled) samples, {X_train.shape[1]} features")
        print(f"Available libraries: {list(k for k, v in self.detector.available_libraries.items() if v.get('available', False))}")

        # Fit the scaler on the ORIGINAL training distribution - this is what
        # real activities actually look like at inference time, not the
        # SMOTE-synthesized points, so it's the correct basis for scaling.
        X_train_scaled = self._scale_features(X_train, fit=True)

        # Isolation Forest: original, naturally-imbalanced data (all classes)
        print("Training Isolation Forest...")
        self.isolation_forest.fit(X_train_scaled)

        # Autoencoder: normal-only
        print("Training Autoencoder...")
        if y_train is not None:
            normal_mask = (y_train == 0)
            X_normal_scaled = X_train_scaled[normal_mask]
            print(f"   Autoencoder training set: {X_normal_scaled.shape[0]} normal-only samples "
                  f"(excluded {int((~normal_mask).sum())} anomalous samples)")
        else:
            X_normal_scaled = X_train_scaled
            print("   No labels provided - autoencoder trained on all samples")
        self.autoencoder.fit(X_normal_scaled)

        # XGBoost: SMOTE-resampled data (supervised - benefits from balancing)
        if y_train_res is not None:
            print("Training XGBoost...")
            X_train_res_scaled = self._scale_features(X_train_res, fit=False)
            self.xgboost.fit(X_train_res_scaled, y_train_res)

        self.is_trained = True
        print("Hybrid detector training complete!")
        return self
    
    def predict_anomaly_scores(self, X):
        """Get anomaly scores from all models"""
        if not self.is_trained:
            raise ValueError("Detector must be trained before prediction")
        
        X = np.array(X, dtype=np.float32)
        X_scaled = self._scale_features(X, fit=False)
        
        scores = {}
        
        # Isolation Forest scores
        try:
            if_scores = self.isolation_forest.decision_function(X_scaled)
            if_scores = (if_scores - if_scores.min()) / (if_scores.max() - if_scores.min() + 1e-8)
            scores['isolation_forest'] = 1 - if_scores  # Invert so higher = more anomalous
        except Exception as e:
            print(f"Isolation Forest prediction failed: {e}")
            scores['isolation_forest'] = np.zeros(len(X))
        
        # Autoencoder scores
        try:
            ae_errors = self.autoencoder.reconstruction_error(X_scaled)
            ae_threshold = getattr(self.autoencoder, 'threshold', np.percentile(ae_errors, 95))
            ae_scores = np.clip(ae_errors / (ae_threshold + 1e-8), 0, 1)
            scores['autoencoder'] = ae_scores
        except Exception as e:
            print(f"Autoencoder prediction failed: {e}")
            scores['autoencoder'] = np.zeros(len(X))
        
        # XGBoost scores
        try:
            xgb_proba = self.xgboost.predict_proba(X_scaled)
            if xgb_proba.shape[1] > 1:
                scores['xgboost'] = xgb_proba[:, 1]
            else:
                scores['xgboost'] = xgb_proba[:, 0]
        except Exception as e:
            print(f"XGBoost prediction failed: {e}")
            scores['xgboost'] = np.zeros(len(X))
        
        return scores
    
    def predict(self, X, weights=None):
        """Ensemble prediction with weighted voting"""
        if weights is None:
            weights = {'isolation_forest': 0.4, 'autoencoder': 0.4, 'xgboost': 0.2}
        
        scores = self.predict_anomaly_scores(X)
        
        # Weighted ensemble
        ensemble_scores = np.zeros(len(X))
        total_weight = 0
        
        for model_name, weight in weights.items():
            if model_name in scores:
                ensemble_scores += weight * scores[model_name]
                total_weight += weight
        
        if total_weight > 0:
            ensemble_scores /= total_weight
        
        # Convert to risk scores (0-100)
        risk_scores = np.clip(ensemble_scores * 100, 0, 100)
        
        return risk_scores, scores
    
    def get_implementation_info(self):
        """Get information about which implementations are being used"""
        return {
            'available_libraries': self.detector.available_libraries,
            'implementations': {
                'isolation_forest': self.isolation_forest.implementation,
                'autoencoder': self.autoencoder.implementation,
                'xgboost': self.xgboost.implementation
            }
        }

    def get_active_model_count(self):
        """Count number of active/trained models"""
        count = 0
        if self.isolation_forest.model is not None:
            count += 1
        if self.autoencoder.model is not None:
            count += 1
        if self.xgboost.model is not None:
            count += 1
        return count if count > 0 else 3  # Default to 3 if not yet trained

def test_hybrid_detector():
    """Test the hybrid detector with synthetic data"""
    print("Testing Hybrid ML Detector")
    print("=" * 50)
    
    # Generate synthetic data
    np.random.seed(42)
    normal_data = np.random.normal(0, 1, (1000, 10))
    anomaly_data = np.random.normal(3, 1, (100, 10))
    
    X = np.vstack([normal_data, anomaly_data])
    y = np.hstack([np.zeros(1000), np.ones(100)])
    
    # Test hybrid detector
    detector = AdvancedHybridDetector()
    
    # Show implementation info
    info = detector.get_implementation_info()
    print("\nImplementation Details:")
    for model, impl in info['implementations'].items():
        print(f"  {model}: {impl}")
    
    # Train and test
    detector.fit(X, y)
    
    # Test prediction
    test_data = np.vstack([
        np.random.normal(0, 1, (50, 10)),
        np.random.normal(3, 1, (10, 10))
    ])
    
    risk_scores, individual_scores = detector.predict(test_data)
    
    print(f"\nResults:")
    print(f"Normal samples risk scores: {risk_scores[:10]}")
    print(f"Anomalous samples risk scores: {risk_scores[-10:]}")
    print("Hybrid detector test completed successfully!")

if __name__ == "__main__":
    test_hybrid_detector()
