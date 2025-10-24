"""
Hybrid ML Engine for IGNISYL
Automatically detects available libraries and uses best available implementation
Combines predictions from multiple models for better accuracy
"""

import numpy as np
import pandas as pd
import sys
import os
import logging
from typing import Dict, List, Tuple, Optional, Union

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            logger.info(f"✅ scikit-learn {sklearn.__version__} detected")
        except ImportError:
            self.available_libraries['sklearn'] = {'available': False}
            logger.warning("❌ scikit-learn not available")
        
        # Test XGBoost
        try:
            import xgboost as xgb
            self.available_libraries['xgboost'] = {
                'available': True,
                'version': xgb.__version__,
                'components': ['XGBClassifier']
            }
            logger.info(f"✅ XGBoost {xgb.__version__} detected")
        except ImportError:
            self.available_libraries['xgboost'] = {'available': False}
            logger.warning("❌ XGBoost not available")
        
        # Test TensorFlow
        try:
            import tensorflow as tf
            self.available_libraries['tensorflow'] = {
                'available': True,
                'version': tf.__version__,
                'components': ['Keras', 'Sequential', 'Dense']
            }
            logger.info(f"✅ TensorFlow {tf.__version__} detected")
        except ImportError:
            self.available_libraries['tensorflow'] = {'available': False}
            logger.warning("❌ TensorFlow not available")
        
        # Test PyTorch
        try:
            import torch
            self.available_libraries['torch'] = {
                'available': True,
                'version': torch.__version__,
                'components': ['nn', 'optim']
            }
            logger.info(f"✅ PyTorch {torch.__version__} detected")
        except ImportError:
            self.available_libraries['torch'] = {'available': False}
            logger.warning("❌ PyTorch not available")
    
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
        
        if self.implementation == 'sklearn':
            from sklearn.ensemble import IsolationForest
            self.model = IsolationForest(**kwargs)
            logger.info("Using scikit-learn Isolation Forest")
        else:
            # Check if custom algorithms module exists
            try:
                from .custom_algorithms import CustomIsolationForest
                self.model = CustomIsolationForest(**kwargs)
                logger.info("Using custom Isolation Forest implementation")
            except ImportError:
                logger.error("Custom algorithms not available")
                raise ImportError("No Isolation Forest implementation available")
    
    def fit(self, X):
        self.model.fit(X)
        return self
    
    def predict(self, X):
        if self.implementation == 'sklearn':
            # sklearn returns -1 for anomalies, 1 for normal
            predictions = self.model.predict(X)
            return (predictions == -1).astype(int)
        else:
            return self.model.predict(X)
    
    def decision_function(self, X):
        return self.model.decision_function(X)

class HybridAutoencoder:
    """Hybrid Autoencoder using best available implementation"""
    
    def __init__(self, detector: MLLibraryDetector, **kwargs):
        self.detector = detector
        self.implementation = detector.get_best_implementation('autoencoder')
        self.model = None
        self.kwargs = kwargs
        self.threshold = None
        self.mean = None
        self.std = None
        
        if self.implementation == 'tensorflow':
            self._prepare_tensorflow_model(**kwargs)
        elif self.implementation == 'torch':
            self._prepare_torch_model(**kwargs)
        else:
            try:
                from .custom_algorithms import CustomAutoencoder
                self.model = CustomAutoencoder(**kwargs)
                logger.info("Using custom Autoencoder implementation")
            except ImportError:
                logger.error("Custom algorithms not available")
                raise ImportError("No Autoencoder implementation available")
    
    def _prepare_tensorflow_model(self, encoding_dim=32, **kwargs):
        """Prepare TensorFlow/Keras autoencoder configuration"""
        logger.info("Using TensorFlow Autoencoder")
        
        self.tf_model_config = {
            'encoding_dim': encoding_dim,
            'epochs': kwargs.get('epochs', 100),
            'batch_size': kwargs.get('batch_size', 32),
            'learning_rate': kwargs.get('learning_rate', 0.001)
        }
        self.model_type = 'tensorflow'
    
    def _prepare_torch_model(self, **kwargs):
        """Prepare PyTorch autoencoder configuration"""
        logger.info("Using PyTorch Autoencoder")
        self.model_type = 'torch'
        # PyTorch implementation can be added here if needed
    
    def fit(self, X):
        """Train the autoencoder"""
        if self.implementation == 'tensorflow' and hasattr(self, 'tf_model_config'):
            return self._fit_tensorflow(X)
        elif hasattr(self.model, 'fit'):
            result = self.model.fit(X)
            # Store threshold if custom model provides it
            if hasattr(self.model, 'threshold'):
                self.threshold = self.model.threshold
            return result
        else:
            raise NotImplementedError(f"Fit method not implemented for {self.implementation}")
    
    def _fit_tensorflow(self, X):
        """Fit TensorFlow model"""
        import tensorflow as tf
        from tensorflow.keras.models import Model
        from tensorflow.keras.layers import Input, Dense, Dropout
        from tensorflow.keras.optimizers import Adam
        from tensorflow.keras.callbacks import EarlyStopping
        
        X = np.array(X, dtype=np.float32)
        
        # Validate input
        if len(X.shape) != 2:
            raise ValueError(f"Expected 2D array, got shape {X.shape}")
        if X.shape[0] == 0 or X.shape[1] == 0:
            raise ValueError("Input data cannot be empty")
        
        input_dim = X.shape[1]
        encoding_dim = min(self.tf_model_config['encoding_dim'], input_dim // 2)
        
        # Build autoencoder
        input_layer = Input(shape=(input_dim,))
        encoded = Dense(encoding_dim, activation='relu')(input_layer)
        encoded = Dropout(0.2)(encoded)
        encoded = Dense(encoding_dim // 2, activation='relu')(encoded)
        
        decoded = Dense(encoding_dim, activation='relu')(encoded)
        decoded = Dropout(0.2)(decoded)
        decoded = Dense(input_dim, activation='sigmoid')(decoded)
        
        self.tf_model = Model(input_layer, decoded)
        self.tf_model.compile(
            optimizer=Adam(learning_rate=self.tf_model_config['learning_rate']),
            loss='mse'
        )
        
        # Normalize data
        self.mean = np.mean(X, axis=0)
        self.std = np.std(X, axis=0) + 1e-8
        X_norm = (X - self.mean) / self.std
        
        # Train with early stopping
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )
        
        history = self.tf_model.fit(
            X_norm, X_norm,
            epochs=self.tf_model_config['epochs'],
            batch_size=self.tf_model_config['batch_size'],
            verbose=0,
            validation_split=0.2,
            callbacks=[early_stopping]
        )
        
        # Calculate threshold from training data
        train_pred = self.tf_model.predict(X_norm, verbose=0)
        train_mse = np.mean(np.power(X_norm - train_pred, 2), axis=1)
        self.threshold = np.percentile(train_mse, 95)
        
        logger.info(f"Autoencoder trained. Threshold: {self.threshold:.4f}")
        return self
    
    def reconstruction_error(self, X):
        """Calculate reconstruction error"""
        if self.implementation == 'tensorflow' and hasattr(self, 'tf_model'):
            X = np.array(X, dtype=np.float32)
            
            # Validate input shape
            if X.shape[1] != len(self.mean):
                raise ValueError(f"Input has {X.shape[1]} features, expected {len(self.mean)}")
            
            X_norm = (X - self.mean) / self.std
            pred = self.tf_model.predict(X_norm, verbose=0)
            return np.mean(np.power(X_norm - pred, 2), axis=1)
        elif hasattr(self.model, 'reconstruction_error'):
            return self.model.reconstruction_error(X)
        else:
            raise NotImplementedError(f"Reconstruction error not implemented for {self.implementation}")
    
    def predict(self, X):
        """Predict anomalies based on reconstruction error"""
        errors = self.reconstruction_error(X)
        
        if self.threshold is None:
            logger.warning("Threshold not set, calculating from current errors")
            self.threshold = np.percentile(errors, 95)
        
        return (errors > self.threshold).astype(int)

class HybridXGBoost:
    """Hybrid XGBoost using best available implementation"""
    
    def __init__(self, detector: MLLibraryDetector, **kwargs):
        self.detector = detector
        self.implementation = detector.get_best_implementation('gradient_boosting')
        self.model = None
        self.kwargs = kwargs
        self.is_fitted = False
        
        if self.implementation == 'xgboost':
            import xgboost as xgb
            self.model = xgb.XGBClassifier(**kwargs)
            logger.info("Using XGBoost implementation")
        elif self.implementation == 'sklearn':
            from sklearn.ensemble import GradientBoostingClassifier
            self.model = GradientBoostingClassifier(**kwargs)
            logger.info("Using scikit-learn Gradient Boosting")
        else:
            try:
                from .custom_algorithms import CustomXGBoostClassifier
                self.model = CustomXGBoostClassifier(**kwargs)
                logger.info("Using custom XGBoost implementation")
            except ImportError:
                logger.error("Custom algorithms not available")
                raise ImportError("No XGBoost implementation available")
    
    def fit(self, X, y):
        """Train the model"""
        self.model.fit(X, y)
        self.is_fitted = True
        return self
    
    def predict(self, X):
        """Predict class labels"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """Predict class probabilities"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(X)
        else:
            # Fallback for custom implementation
            predictions = self.model.predict(X)
            # Ensure predictions are in [0, 1]
            predictions = np.clip(predictions, 0, 1)
            proba = np.column_stack([1 - predictions, predictions])
            return proba

class AdvancedHybridDetector:
    """Advanced hybrid anomaly detector using best available implementations"""
    
    def __init__(self):
        self.detector = MLLibraryDetector()
        self.is_trained = False
        self.feature_columns = []
        self.n_features = None
        self.manual_mean = None
        self.manual_std = None
        
        # Initialize models with best available implementations
        self.isolation_forest = HybridIsolationForest(
            self.detector, 
            contamination=0.1, 
            n_estimators=100,
            random_state=42
        )
        
        self.autoencoder = HybridAutoencoder(
            self.detector,
            encoding_dim=32,
            epochs=100,
            batch_size=32,
            learning_rate=0.001
        )
        
        self.xgboost = HybridXGBoost(
            self.detector,
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
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
            # Manual scaling fallback
            if fit:
                self.manual_mean = np.mean(X, axis=0)
                self.manual_std = np.std(X, axis=0) + 1e-8
            
            if self.manual_mean is None or self.manual_std is None:
                raise ValueError("Scaler not fitted. Call fit() first.")
            
            return (X - self.manual_mean) / self.manual_std
    
    def fit(self, X, y=None):
        """Train all models in the ensemble"""
        X = np.array(X, dtype=np.float32)
        
        # Validate input
        if len(X.shape) != 2:
            raise ValueError(f"Expected 2D array, got shape {X.shape}")
        if X.shape[0] == 0:
            raise ValueError("Cannot fit with empty dataset")
        
        self.n_features = X.shape[1]
        
        logger.info(f"Training hybrid detector: {X.shape[0]} samples, {X.shape[1]} features")
        available_libs = [k for k, v in self.detector.available_libraries.items() if v.get('available', False)]
        logger.info(f"Available libraries: {available_libs}")
        
        # Scale features
        X_scaled = self._scale_features(X, fit=True)
        
        # Train isolation forest (unsupervised)
        logger.info("Training Isolation Forest...")
        self.isolation_forest.fit(X_scaled)
        
        # Train autoencoder (unsupervised)
        logger.info("Training Autoencoder...")
        self.autoencoder.fit(X_scaled)
        
        # Train XGBoost (supervised if labels available)
        if y is not None:
            logger.info("Training XGBoost...")
            y = np.array(y)
            self.xgboost.fit(X_scaled, y)
        else:
            logger.warning("No labels provided, XGBoost will not be trained")
        
        self.is_trained = True
        logger.info("Hybrid detector training complete!")
        return self
    
    def predict_anomaly_scores(self, X):
        """Get anomaly scores from all models"""
        if not self.is_trained:
            raise ValueError("Detector must be trained before prediction")
        
        X = np.array(X, dtype=np.float32)
        
        # Validate input shape
        if X.shape[1] != self.n_features:
            raise ValueError(f"Input has {X.shape[1]} features, expected {self.n_features}")
        
        X_scaled = self._scale_features(X, fit=False)
        
        scores = {}
        
        # Isolation Forest scores
        try:
            if_scores = self.isolation_forest.decision_function(X_scaled)
            
            # Normalize scores safely
            if_min, if_max = if_scores.min(), if_scores.max()
            if if_max - if_min > 1e-8:
                if_scores_normalized = (if_scores - if_min) / (if_max - if_min)
            else:
                if_scores_normalized = np.full(len(if_scores), 0.5)
            
            scores['isolation_forest'] = 1 - if_scores_normalized  # Invert
        except Exception as e:
            logger.error(f"Isolation Forest prediction failed: {e}")
            scores['isolation_forest'] = np.full(len(X), 0.5)
        
        # Autoencoder scores
        try:
            ae_errors = self.autoencoder.reconstruction_error(X_scaled)
            ae_threshold = self.autoencoder.threshold
            
            if ae_threshold is None or ae_threshold == 0:
                ae_threshold = np.percentile(ae_errors, 95)
            
            ae_scores = np.clip(ae_errors / (ae_threshold + 1e-8), 0, 1)
            scores['autoencoder'] = ae_scores
        except Exception as e:
            logger.error(f"Autoencoder prediction failed: {e}")
            scores['autoencoder'] = np.full(len(X), 0.5)
        
        # XGBoost scores (only if trained)
        if self.xgboost.is_fitted:
            try:
                xgb_proba = self.xgboost.predict_proba(X_scaled)
                if xgb_proba.shape[1] > 1:
                    scores['xgboost'] = xgb_proba[:, 1]
                else:
                    scores['xgboost'] = xgb_proba[:, 0]
            except Exception as e:
                logger.error(f"XGBoost prediction failed: {e}")
                scores['xgboost'] = np.full(len(X), 0.5)
        else:
            logger.warning("XGBoost not trained, using neutral scores")
            scores['xgboost'] = np.full(len(X), 0.5)
        
        return scores
    
    def predict(self, X, weights=None):
        """Ensemble prediction with weighted voting"""
        if weights is None:
            # Default weights based on whether XGBoost is trained
            if self.xgboost.is_fitted:
                weights = {'isolation_forest': 0.35, 'autoencoder': 0.35, 'xgboost': 0.30}
            else:
                weights = {'isolation_forest': 0.50, 'autoencoder': 0.50}
        
        scores = self.predict_anomaly_scores(X)
        
        # Weighted ensemble
        ensemble_scores = np.zeros(len(X))
        total_weight = 0
        
        for model_name, weight in weights.items():
            if model_name in scores:
                ensemble_scores += weight * scores[model_name]
                total_weight += weight
        
        # Normalize by total weight
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
            },
            'is_trained': self.is_trained,
            'xgboost_fitted': self.xgboost.is_fitted
        }

def test_hybrid_detector():
    """Test the hybrid detector with synthetic data"""
    logger.info("="*60)
    logger.info("Testing Hybrid ML Detector")
    logger.info("="*60)
    
    # Generate synthetic data
    np.random.seed(42)
    normal_data = np.random.normal(0, 1, (1000, 10))
    anomaly_data = np.random.normal(3, 1, (100, 10))
    
    X = np.vstack([normal_data, anomaly_data])
    y = np.hstack([np.zeros(1000), np.ones(100)])
    
    # Shuffle data
    shuffle_idx = np.random.permutation(len(X))
    X = X[shuffle_idx]
    y = y[shuffle_idx]
    
    # Test hybrid detector
    detector = AdvancedHybridDetector()
    
    # Show implementation info
    info = detector.get_implementation_info()
    logger.info("\n📊 Implementation Details:")
    for model, impl in info['implementations'].items():
        logger.info(f"   {model}: {impl}")
    
    # Train
    logger.info("\n🔧 Training...")
    detector.fit(X, y)
    
    # Test prediction
    logger.info("\n🧪 Testing predictions...")
    test_normal = np.random.normal(0, 1, (50, 10))
    test_anomaly = np.random.normal(3, 1, (10, 10))
    test_data = np.vstack([test_normal, test_anomaly])
    
    risk_scores, individual_scores = detector.predict(test_data)
    
    logger.info(f"\n📈 Results:")
    logger.info(f"   Normal samples (first 5): {risk_scores[:5]}")
    logger.info(f"   Anomaly samples (last 5): {risk_scores[-5:]}")
    logger.info(f"   Mean risk - Normal: {risk_scores[:50].mean():.2f}")
    logger.info(f"   Mean risk - Anomaly: {risk_scores[-10:].mean():.2f}")
    
    logger.info("\n✅ Hybrid detector test completed successfully!")
    
    return detector

if __name__ == "__main__":
    test_hybrid_detector()