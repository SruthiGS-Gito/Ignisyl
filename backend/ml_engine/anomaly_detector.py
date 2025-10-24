"""
Advanced Anomaly Detection Engine for IGNISYL
Implements multiple ML algorithms for behavioral anomaly detection
"""

import numpy as np
import pandas as pd
import joblib
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
import warnings
warnings.filterwarnings('ignore')

# Machine Learning imports
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import tensorflow as tf
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.layers import Dense, Input, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
import xgboost as xgb

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.config import settings

class BehavioralAnomalyDetector:
    """Advanced anomaly detection using ensemble of ML models"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.scaler = None  # Initialize scaler
        self.feature_columns = []
        self.is_trained = False
        self.autoencoder_threshold = 0.0  # Initialize threshold
        
        # Model configurations
        self.config = {
            'isolation_forest': {
                'contamination': 0.1,
                'n_estimators': 100,
                'max_samples': 'auto',
                'random_state': 42
            },
            'autoencoder': {
                'encoding_dim': 32,
                'epochs': 100,
                'batch_size': 32,
                'learning_rate': 0.001
            },
            'xgboost': {
                'n_estimators': 100,
                'max_depth': 6,
                'learning_rate': 0.1,
                'random_state': 42
            }
        }
    
    def load_and_preprocess_data(self, data_path: str) -> pd.DataFrame:
        """Load and preprocess training data"""
        print("Loading training data...")
        
        # Load data from CSV
        csv_path = f"{data_path}/combined_activities.csv"
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            print(f"Loaded {len(df)} records from {csv_path}")
        else:
            print(f"Training data not found at {csv_path}")
            print("Generating synthetic training data...")
            from ml_engine.data_generator import BehavioralDataGenerator
            generator = BehavioralDataGenerator()
            normal, anomalous = generator.generate_complete_dataset()
            df = pd.DataFrame(normal + anomalous)
            
            # Save generated data for future use
            os.makedirs(data_path, exist_ok=True)
            df.to_csv(csv_path, index=False)
            print(f"Generated and saved {len(df)} training records")
        
        # Convert timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        else:
            # Add timestamp if missing
            df['timestamp'] = pd.Timestamp.now()
        
        # Extract temporal features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6])
        df['is_business_hours'] = df['hour'].between(9, 17)
        
        # Process nested JSON fields
        df = self._process_nested_fields(df)
        
        # Feature engineering
        df = self._engineer_features(df)
        
        return df
    
    def _process_nested_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process nested JSON fields and extract relevant features"""
        
        # Define numeric columns with defaults
        numeric_defaults = {
            'file_size': 0,
            'network_bytes': 0,
            'bytes_transferred': 0,
            'total_size': 0,
            'rows_affected': 0,
            'file_count': 0,
            'recipient_count': 0,
            'external_recipients': 0,
            'attachment_count': 0,
            'total_attachment_size': 0,
            'memory_usage_mb': 0,
            'cpu_usage_percent': 0,
            'files_opened': 0,
            'execution_time_ms': 0,
            'session_duration_minutes': 0,
            'data_transferred_mb': 0,
            'files_transferred': 0,
            'confidence_score': 0.5  # Default medium confidence
        }
        
        # Fill missing numeric values
        for col, default_val in numeric_defaults.items():
            if col in df.columns:
                df[col] = df[col].fillna(default_val)
            else:
                df[col] = default_val
        
        # Convert boolean fields
        bool_columns = ['is_suspicious', 'is_weekend', 'is_business_hours', 
                       'encryption_used', 'sensitive_data_accessed']
        for col in bool_columns:
            if col in df.columns:
                df[col] = df[col].fillna(False).astype(bool)
            else:
                df[col] = False
        
        # Ensure categorical columns exist
        categorical_defaults = {
            'activity_type': 'unknown',
            'department': 'unknown',
            'protocol': 'unknown'
        }
        
        for col, default_val in categorical_defaults.items():
            if col not in df.columns:
                df[col] = default_val
            else:
                df[col] = df[col].fillna(default_val).astype(str)
        
        return df
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer additional features for better anomaly detection"""
        
        # Check if user_id exists
        if 'user_id' not in df.columns:
            df['user_id'] = 'unknown_user'
        
        # User-based aggregation features (only if multiple users exist)
        if df['user_id'].nunique() > 1:
            user_stats = df.groupby('user_id').agg({
                'file_size': ['mean', 'std', 'max'],
                'network_bytes': ['mean', 'std', 'max'],
                'hour': ['mean', 'std'],
                'day_of_week': ['mean'],
                'activity_type': 'count'
            }).fillna(0)
            
            # Flatten column names
            user_stats.columns = ['_'.join(col).strip() for col in user_stats.columns]
            user_stats = user_stats.add_prefix('user_')
            
            # Merge back to main dataframe
            df = df.merge(user_stats, left_on='user_id', right_index=True, how='left')
        else:
            # Single user - use global stats
            df['user_file_size_mean'] = df['file_size'].mean()
            df['user_file_size_std'] = df['file_size'].std() if len(df) > 1 else 0
            df['user_file_size_max'] = df['file_size'].max()
            df['user_network_bytes_mean'] = df['network_bytes'].mean()
            df['user_network_bytes_std'] = df['network_bytes'].std() if len(df) > 1 else 0
            df['user_network_bytes_max'] = df['network_bytes'].max()
            df['user_hour_mean'] = df['hour'].mean()
            df['user_hour_std'] = df['hour'].std() if len(df) > 1 else 0
            df['user_activity_type_count'] = len(df)
        
        # Fill any remaining NaN values in user stats
        user_stat_cols = [col for col in df.columns if col.startswith('user_')]
        for col in user_stat_cols:
            df[col] = df[col].fillna(0)
        
        # Activity frequency features
        if len(df) > 1:
            df['activities_per_day'] = df.groupby(['user_id', df['timestamp'].dt.date])['activity_type'].transform('count')
        else:
            df['activities_per_day'] = 1
        
        # Time-based cyclical features
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        # Log-transformed size features (avoid log(0))
        df['file_size_log'] = np.log1p(df['file_size'])
        df['network_bytes_log'] = np.log1p(df['network_bytes'])
        
        # Risk indicators
        df['off_hours_activity'] = ~df['is_business_hours']
        df['weekend_activity'] = df['is_weekend']
        
        # Anomaly indicators (avoid division by zero)
        df['large_file_indicator'] = (
            (df['file_size'] > df['user_file_size_mean'] + 2 * df['user_file_size_std']) & 
            (df['user_file_size_std'] > 0)
        )
        df['high_network_indicator'] = (
            (df['network_bytes'] > df['user_network_bytes_mean'] + 2 * df['user_network_bytes_std']) &
            (df['user_network_bytes_std'] > 0)
        )
        
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Prepare feature matrix for ML models"""
        
        # Select relevant features for ML
        feature_columns = [
            # Basic activity features
            'hour', 'day_of_week', 'is_weekend', 'is_business_hours',
            'hour_sin', 'hour_cos', 'day_sin', 'day_cos',
            
            # Size and transfer features
            'file_size_log', 'network_bytes_log', 'confidence_score',
            
            # User behavior patterns
            'user_file_size_mean', 'user_file_size_std', 'user_file_size_max',
            'user_network_bytes_mean', 'user_network_bytes_std', 'user_network_bytes_max',
            'user_hour_mean', 'user_hour_std', 'user_activity_type_count',
            
            # Activity patterns
            'activities_per_day',
            
            # Risk indicators
            'off_hours_activity', 'weekend_activity', 
            'large_file_indicator', 'high_network_indicator'
        ]
        
        # Categorical encoding
        categorical_columns = ['activity_type', 'department', 'protocol']
        
        for col in categorical_columns:
            if col in df.columns:
                if col not in self.encoders:
                    self.encoders[col] = LabelEncoder()
                    df[f'{col}_encoded'] = self.encoders[col].fit_transform(df[col].astype(str))
                else:
                    # Handle unseen categories during prediction
                    known_categories = set(self.encoders[col].classes_)
                    df[col] = df[col].astype(str)
                    
                    # Map unknown categories to 'unknown'
                    df[col] = df[col].apply(lambda x: x if x in known_categories else 'unknown')
                    
                    # Add 'unknown' to encoder if not present
                    if 'unknown' not in known_categories:
                        self.encoders[col].classes_ = np.append(self.encoders[col].classes_, 'unknown')
                    
                    df[f'{col}_encoded'] = self.encoders[col].transform(df[col])
                
                feature_columns.append(f'{col}_encoded')
        
        # Filter to available columns only
        available_columns = [col for col in feature_columns if col in df.columns]
        self.feature_columns = available_columns
        
        # Extract feature matrix
        X = df[available_columns].fillna(0)
        
        # Scale features
        if self.scaler is None:
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)
        
        return X_scaled
    
    def train_isolation_forest(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train Isolation Forest model (unsupervised anomaly detection)"""
        print("Training Isolation Forest...")
        
        # Isolation Forest works on unlabeled data
        # Train on normal data only (y == 0 means normal behavior)
        X_normal = X[y == 0]
        
        if len(X_normal) == 0:
            print("⚠️ No normal samples found. Training on all data.")
            X_normal = X
        
        model = IsolationForest(**self.config['isolation_forest'])
        model.fit(X_normal)
        
        self.models['isolation_forest'] = model
        print(f"✅ Isolation Forest trained on {len(X_normal)} normal samples")
    
    def train_autoencoder(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train Autoencoder for anomaly detection via reconstruction error"""
        print("Training Autoencoder...")
        
        # Train autoencoder on normal data only (y == 0 means normal)
        X_normal = X[y == 0]
        
        if len(X_normal) < 10:
            print("⚠️ Insufficient normal samples. Training on all data.")
            X_normal = X
        
        input_dim = X.shape[1]
        encoding_dim = min(self.config['autoencoder']['encoding_dim'], input_dim // 2)
        
        # Build autoencoder architecture
        input_layer = Input(shape=(input_dim,))
        encoder = Dense(encoding_dim, activation="relu")(input_layer)
        encoder = Dropout(0.2)(encoder)
        encoder = Dense(encoding_dim // 2, activation="relu")(encoder)
        
        decoder = Dense(encoding_dim // 2, activation='relu')(encoder)
        decoder = Dropout(0.2)(decoder)
        decoder = Dense(encoding_dim, activation='relu')(decoder)
        decoder = Dense(input_dim, activation='sigmoid')(decoder)
        
        autoencoder = Model(inputs=input_layer, outputs=decoder)
        autoencoder.compile(
            optimizer=Adam(learning_rate=self.config['autoencoder']['learning_rate']),
            loss='mse'
        )
        
        # Train the autoencoder
        early_stopping = EarlyStopping(
            monitor='val_loss', 
            patience=10, 
            restore_best_weights=True
        )
        
        # Split into train/validation
        if len(X_normal) > 10:
            X_train, X_val = train_test_split(X_normal, test_size=0.2, random_state=42)
        else:
            X_train = X_val = X_normal
        
        history = autoencoder.fit(
            X_train, X_train,
            epochs=self.config['autoencoder']['epochs'],
            batch_size=self.config['autoencoder']['batch_size'],
            validation_data=(X_val, X_val),
            callbacks=[early_stopping],
            verbose=0
        )
        
        self.models['autoencoder'] = autoencoder
        
        # Calculate reconstruction threshold
        train_predictions = autoencoder.predict(X_train, verbose=0)
        train_mse = np.mean(np.power(X_train - train_predictions, 2), axis=1)
        self.autoencoder_threshold = np.percentile(train_mse, 95)  # 95th percentile
        
        print(f"✅ Autoencoder trained. Reconstruction threshold: {self.autoencoder_threshold:.4f}")
    
    def train_xgboost(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train XGBoost classifier for supervised anomaly detection"""
        print("Training XGBoost...")
        
        # Check if we have both classes
        unique_classes = np.unique(y)
        if len(unique_classes) < 2:
            print("⚠️ Only one class present. Cannot train classifier.")
            # Create a dummy classifier
            self.models['xgboost'] = None
            return
        
        # Split data for training
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        model = xgb.XGBClassifier(**self.config['xgboost'])
        model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        print("XGBoost Classification Report:")
        print(classification_report(y_test, y_pred))
        print(f"ROC AUC Score: {roc_auc_score(y_test, y_pred_proba):.4f}")
        
        self.models['xgboost'] = model
        print("✅ XGBoost trained successfully")
    
    def train_models(self, data_path: str) -> None:
        """Train all anomaly detection models"""
        print("\n" + "="*60)
        print("IGNISYL ML Model Training")
        print("="*60)
        
        # Load and preprocess data
        df = self.load_and_preprocess_data(data_path)
        
        # Prepare features
        X = self.prepare_features(df)
        
        # Get labels (is_suspicious column)
        if 'is_suspicious' in df.columns:
            y = df['is_suspicious'].astype(int).values
        else:
            print("⚠️ No labels found. Assuming all data is normal.")
            y = np.zeros(len(df), dtype=int)
        
        print(f"\n📊 Training Dataset:")
        print(f"   - Total samples: {len(X)}")
        print(f"   - Features: {X.shape[1]}")
        print(f"   - Normal samples: {np.sum(y == 0)}")
        print(f"   - Anomalous samples: {np.sum(y == 1)}")
        
        # Train individual models
        print("\n🔧 Training Models:")
        self.train_isolation_forest(X, y)
        self.train_autoencoder(X, y)
        self.train_xgboost(X, y)
        
        self.is_trained = True
        print("\n✅ All models trained successfully!")
        print("="*60 + "\n")
    
    def predict_anomaly_scores(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """Get anomaly scores from all models"""
        if not self.is_trained:
            raise ValueError("Models must be trained before prediction")
        
        scores = {}
        
        # Isolation Forest scores
        if_scores = self.models['isolation_forest'].decision_function(X)
        # Convert to 0-1 scale (lower scores = more anomalous)
        if len(if_scores) > 1:
            if_scores_normalized = (if_scores - if_scores.min()) / (if_scores.max() - if_scores.min() + 1e-8)
        else:
            if_scores_normalized = np.array([0.5])
        scores['isolation_forest'] = 1 - if_scores_normalized  # Invert so higher = more anomalous
        
        # Autoencoder reconstruction error
        ae_predictions = self.models['autoencoder'].predict(X, verbose=0)
        ae_mse = np.mean(np.power(X - ae_predictions, 2), axis=1)
        # Normalize reconstruction error
        ae_scores_normalized = np.clip(ae_mse / (self.autoencoder_threshold + 1e-8), 0, 1)
        scores['autoencoder'] = ae_scores_normalized
        
        # XGBoost probability scores
        if self.models['xgboost'] is not None:
            xgb_proba = self.models['xgboost'].predict_proba(X)[:, 1]
            scores['xgboost'] = xgb_proba
        else:
            # No XGBoost model - use neutral score
            scores['xgboost'] = np.full(len(X), 0.5)
        
        return scores
    
    def ensemble_prediction(self, X: np.ndarray, weights: Dict[str, float] = None) -> Tuple[np.ndarray, Dict]:
        """Combine predictions from multiple models using weighted ensemble"""
        if weights is None:
            weights = {
                'isolation_forest': 0.3,
                'autoencoder': 0.3,
                'xgboost': 0.4
            }
        
        # Get individual model scores
        individual_scores = self.predict_anomaly_scores(X)
        
        # Weighted ensemble
        ensemble_scores = np.zeros(len(X))
        for model_name, score in individual_scores.items():
            ensemble_scores += weights[model_name] * score
        
        # Convert to risk scores (0-100 scale)
        risk_scores = np.clip(ensemble_scores * 100, 0, 100)
        
        return risk_scores, individual_scores
    
    def predict_single_activity(self, activity_data: Dict) -> Dict:
        """Predict anomaly score for a single activity"""
        if not self.is_trained:
            raise ValueError("Models must be trained before prediction. Call train_models() first.")
        
        # Convert to DataFrame
        df = pd.DataFrame([activity_data])
        
        # Add timestamp features if not present
        if 'timestamp' in activity_data:
            if isinstance(activity_data['timestamp'], str):
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            elif not isinstance(df['timestamp'].iloc[0], pd.Timestamp):
                df['timestamp'] = pd.to_datetime(df['timestamp'])
        else:
            df['timestamp'] = pd.Timestamp.now()
        
        # Extract temporal features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6])
        df['is_business_hours'] = df['hour'].between(9, 17)
        
        # Process and engineer features
        df = self._process_nested_fields(df)
        df = self._engineer_features(df)
        
        # Prepare features
        X = self.prepare_features(df)
        
        # Get predictions
        risk_score, individual_scores = self.ensemble_prediction(X)
        
        # Determine risk level
        risk_level = self._get_risk_level(risk_score[0])
        
        # Generate explanation
        explanation = self._generate_explanation(activity_data, individual_scores, risk_score[0])
        
        return {
            'risk_score': float(risk_score[0]),
            'risk_level': risk_level,
            'individual_scores': {k: float(v[0]) for k, v in individual_scores.items()},
            'explanation': explanation,
            'models_used': list(self.models.keys()),
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level category"""
        # Use settings if available, otherwise use defaults
        low_threshold = getattr(settings, 'LOW_RISK_THRESHOLD', 30)
        medium_threshold = getattr(settings, 'MEDIUM_RISK_THRESHOLD', 70)
        
        if risk_score < low_threshold:
            return "LOW"
        elif risk_score < medium_threshold:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _generate_explanation(self, activity_data: Dict, individual_scores: Dict, risk_score: float) -> List[str]:
        """Generate human-readable explanation for the risk assessment"""
        explanations = []
        
        # Check individual model contributions
        if individual_scores['isolation_forest'][0] > 0.7:
            explanations.append("Activity pattern significantly deviates from normal behavior")
        
        if individual_scores['autoencoder'][0] > 0.7:
            explanations.append("Activity features show unusual reconstruction patterns")
        
        if individual_scores['xgboost'][0] > 0.7:
            explanations.append("Classification model indicates high threat probability")
        
        # Check specific risk factors
        if activity_data.get('is_suspicious', False):
            explanations.append("Activity contains known threat indicators")
        
        if activity_data.get('off_hours_activity', False):
            explanations.append("Activity occurred outside normal business hours")
        
        if activity_data.get('weekend_activity', False):
            explanations.append("Activity occurred during weekend")
        
        if activity_data.get('large_file_indicator', False):
            explanations.append("File transfer size exceeds normal user patterns")
        
        if activity_data.get('high_network_indicator', False):
            explanations.append("Network usage exceeds normal user patterns")
        
        # File size checks
        file_size = activity_data.get('file_size', 0)
        if file_size > 100 * 1024 * 1024:  # 100MB
            explanations.append(f"Large file transfer detected ({file_size / (1024*1024):.1f} MB)")
        
        # External access checks
        destination = str(activity_data.get('destination', '')).lower()
        if 'external' in destination or 'internet' in destination:
            explanations.append("External data transfer detected")
        
        # If no specific risks identified
        if not explanations:
            if risk_score < 30:
                explanations.append("Activity appears normal based on behavioral patterns")
            else:
                explanations.append("Activity flagged for review based on combined risk factors")
        
        return explanations
    
    def save_models(self, model_path: str) -> None:
        """Save all trained models to disk"""
        if not self.is_trained:
            print("⚠️ No trained models to save")
            return
        
        os.makedirs(model_path, exist_ok=True)
        
        print(f"💾 Saving models to {model_path}...")
        
        # Save sklearn models
        joblib.dump(self.models['isolation_forest'], f"{model_path}/isolation_forest.pkl")
        
        if self.models.get('xgboost') is not None:
            joblib.dump(self.models['xgboost'], f"{model_path}/xgboost_model.pkl")
        
        # Save Keras model in new format
        self.models['autoencoder'].save(f"{model_path}/autoencoder.keras")
        
        # Save preprocessors
        joblib.dump(self.scaler, f"{model_path}/scaler.pkl")
        joblib.dump(self.encoders, f"{model_path}/encoders.pkl")
        
        # Save configuration
        config_data = {
            'feature_columns': self.feature_columns,
            'autoencoder_threshold': float(self.autoencoder_threshold),
            'is_trained': self.is_trained,
            'model_config': self.config,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(f"{model_path}/config.json", 'w') as f:
            json.dump(config_data, f, indent=2)
        
        print(f"✅ Models saved successfully to {model_path}")
    
    def load_models(self, model_path: str) -> bool:
        """Load trained models from disk"""
        config_file = f"{model_path}/config.json"
        
        if not os.path.exists(config_file):
            print(f"⚠️ No trained models found at {model_path}")
            print("   Please train models first using train_models()")
            return False
        
        print(f"📂 Loading models from {model_path}...")
        
        try:
            # Load configuration
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            self.feature_columns = config_data['feature_columns']
            self.autoencoder_threshold = config_data['autoencoder_threshold']
            self.is_trained = config_data['is_trained']
            
            # Load models
            self.models['isolation_forest'] = joblib.load(f"{model_path}/isolation_forest.pkl")
            
            # Load XGBoost if exists
            xgb_path = f"{model_path}/xgboost_model.pkl"
            if os.path.exists(xgb_path):
                self.models['xgboost'] = joblib.load(xgb_path)
            else:
                self.models['xgboost'] = None
            
            # Load Keras model
            self.models['autoencoder'] = tf.keras.models.load_model(f"{model_path}/autoencoder.keras")
            
            # Load preprocessors
            self.scaler = joblib.load(f"{model_path}/scaler.pkl")
            self.encoders = joblib.load(f"{model_path}/encoders.pkl")
            
            print("✅ Models loaded successfully!")
            print(f"   - Loaded at: {config_data.get('saved_at', 'Unknown')}")
            print(f"   - Features: {len(self.feature_columns)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main function for model training"""
    print("\n" + "="*60)
    print("IGNISYL Anomaly Detection Training")
    print("="*60 + "\n")
    
    # Initialize detector
    detector = BehavioralAnomalyDetector()
    
    # Ensure data and model directories exist
    data_path = os.path.join(settings.DATA_PATH, "synthetic")
    model_path = settings.MODEL_PATH
    
    os.makedirs(data_path, exist_ok=True)
    os.makedirs(model_path, exist_ok=True)
    
    # Train models
    try:
        detector.train_models(data_path)
        
        # Save models
        detector.save_models(model_path)
        
        print("\n" + "="*60)
        print("✅ Training Complete!")
        print("="*60)
        print(f"\n📁 Models saved to: {model_path}")
        print("🚀 Models ready for deployment\n")
        
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)