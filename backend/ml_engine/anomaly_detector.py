"""
Advanced Anomaly Detection Engine for IGNISYL-Neo
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
        self.feature_columns = []
        self.is_trained = False
        
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
        if os.path.exists(f"{data_path}/combined_activities.csv"):
            df = pd.read_csv(f"{data_path}/combined_activities.csv")
        else:
            print("No training data found. Generating synthetic data...")
            from .data_generator import BehavioralDataGenerator
            generator = BehavioralDataGenerator()
            normal, anomalous = generator.generate_complete_dataset()
            df = pd.DataFrame(normal + anomalous)
        
        print(f"Loaded {len(df)} activity records")
        
        # Convert timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
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
        
        # Handle missing values
        df = df.fillna({
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
            'files_transferred': 0
        })
        
        # Convert boolean fields
        bool_columns = ['is_suspicious', 'is_weekend', 'is_business_hours', 'encryption_used', 'sensitive_data_accessed']
        for col in bool_columns:
            if col in df.columns:
                df[col] = df[col].astype(bool)
        
        return df
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer additional features for better anomaly detection"""
        
        # User-based aggregation features
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
        
        # Activity frequency features
        df['activities_per_day'] = df.groupby(['user_id', df['timestamp'].dt.date])['activity_type'].transform('count')
        
        # Time-based features
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        # Size ratios and anomaly indicators
        df['file_size_log'] = np.log1p(df['file_size'])
        df['network_bytes_log'] = np.log1p(df['network_bytes'])
        
        # Risk indicators
        df['off_hours_activity'] = ~df['is_business_hours']
        df['weekend_activity'] = df['is_weekend']
        df['large_file_indicator'] = df['file_size'] > df['user_file_size_mean'] + 2 * df['user_file_size_std']
        df['high_network_indicator'] = df['network_bytes'] > df['user_network_bytes_mean'] + 2 * df['user_network_bytes_std']
        
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
                    known_categories = self.encoders[col].classes_
                    df[col] = df[col].astype(str)
                    df[col] = df[col].apply(lambda x: x if x in known_categories else 'unknown')
                    
                    if 'unknown' not in known_categories:
                        # Add unknown category
                        self.encoders[col].classes_ = np.append(known_categories, 'unknown')
                    
                    df[f'{col}_encoded'] = self.encoders[col].transform(df[col])
                
                feature_columns.append(f'{col}_encoded')
        
        # Filter available columns
        available_columns = [col for col in feature_columns if col in df.columns]
        self.feature_columns = available_columns
        
        # Extract feature matrix
        X = df[available_columns].fillna(0)
        
        # Scale features
        if not hasattr(self, 'scaler') or self.scaler is None:
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)
        
        return X_scaled
    
    def train_isolation_forest(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train Isolation Forest model"""
        print("Training Isolation Forest...")
        
        # Isolation Forest works on unlabeled data (unsupervised)
        # We train on normal data only
        X_normal = X[y == 0]
        
        model = IsolationForest(**self.config['isolation_forest'])
        model.fit(X_normal)
        
        self.models['isolation_forest'] = model
        print(f"Isolation Forest trained on {len(X_normal)} normal samples")
    
    def train_autoencoder(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train Autoencoder for anomaly detection"""
        print("Training Autoencoder...")
        
        # Train autoencoder on normal data only
        X_normal = X[y == 0]
        
        input_dim = X.shape[1]
        encoding_dim = self.config['autoencoder']['encoding_dim']
        
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
        autoencoder.compile(optimizer=Adam(learning_rate=self.config['autoencoder']['learning_rate']),
                          loss='mse')
        
        # Train the autoencoder
        early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
        
        X_train, X_val = train_test_split(X_normal, test_size=0.2, random_state=42)
        
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
        train_predictions = autoencoder.predict(X_train)
        train_mse = np.mean(np.power(X_train - train_predictions, 2), axis=1)
        self.autoencoder_threshold = np.percentile(train_mse, 95)  # 95th percentile
        
        print(f"Autoencoder trained. Reconstruction threshold: {self.autoencoder_threshold:.4f}")
    
    def train_xgboost(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train XGBoost classifier"""
        print("Training XGBoost...")
        
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
    
    def train_models(self, data_path: str) -> None:
        """Train all anomaly detection models"""
        print("Starting model training...")
        
        # Load and preprocess data
        df = self.load_and_preprocess_data(data_path)
        
        # Prepare features
        X = self.prepare_features(df)
        y = df['is_suspicious'].astype(int).values
        
        print(f"Training on {len(X)} samples with {X.shape[1]} features")
        print(f"Class distribution: {np.bincount(y)}")
        
        # Train individual models
        self.train_isolation_forest(X, y)
        self.train_autoencoder(X, y)
        self.train_xgboost(X, y)
        
        self.is_trained = True
        print("All models trained successfully!")
    
    def predict_anomaly_scores(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """Get anomaly scores from all models"""
        if not self.is_trained:
            raise ValueError("Models must be trained before prediction")
        
        scores = {}
        
        # Isolation Forest scores
        if_scores = self.models['isolation_forest'].decision_function(X)
        # Convert to 0-1 scale (lower scores = more anomalous)
        if_scores_normalized = (if_scores - if_scores.min()) / (if_scores.max() - if_scores.min())
        scores['isolation_forest'] = 1 - if_scores_normalized  # Invert so higher = more anomalous
        
        # Autoencoder reconstruction error
        ae_predictions = self.models['autoencoder'].predict(X, verbose=0)
        ae_mse = np.mean(np.power(X - ae_predictions, 2), axis=1)
        # Normalize reconstruction error
        ae_scores_normalized = np.clip(ae_mse / self.autoencoder_threshold, 0, 1)
        scores['autoencoder'] = ae_scores_normalized
        
        # XGBoost probability scores
        xgb_proba = self.models['xgboost'].predict_proba(X)[:, 1]
        scores['xgboost'] = xgb_proba
        
        return scores
    
    def ensemble_prediction(self, X: np.ndarray, weights: Dict[str, float] = None) -> Tuple[np.ndarray, Dict]:
        """Combine predictions from multiple models"""
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
        
        # Convert to risk scores (0-100)
        risk_scores = np.clip(ensemble_scores * 100, 0, 100)
        
        return risk_scores, individual_scores
    
    def predict_single_activity(self, activity_data: Dict) -> Dict:
        """Predict anomaly for a single activity"""
        # Convert to DataFrame
        df = pd.DataFrame([activity_data])
        
        # Add timestamp features if not present
        if 'timestamp' in activity_data:
            if isinstance(activity_data['timestamp'], str):
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
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
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level"""
        if risk_score < settings.LOW_RISK_THRESHOLD:
            return "LOW"
        elif risk_score < settings.MEDIUM_RISK_THRESHOLD:
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
            explanations.append("Large file transfer detected")
        
        # External access checks
        if 'external' in str(activity_data.get('destination', '')).lower():
            explanations.append("External data transfer detected")
        
        if not explanations:
            explanations.append("Activity appears normal based on behavioral patterns")
        
        return explanations
    
    def save_models(self, model_path: str) -> None:
        """Save trained models to disk"""
        os.makedirs(model_path, exist_ok=True)
        
        # Save sklearn models
        joblib.dump(self.models['isolation_forest'], f"{model_path}/isolation_forest.pkl")
        joblib.dump(self.models['xgboost'], f"{model_path}/xgboost_model.pkl")
        
        # Save Keras model
        self.models['autoencoder'].save(f"{model_path}/autoencoder.h5")
        
        # Save preprocessors
        joblib.dump(self.scaler, f"{model_path}/scaler.pkl")
        joblib.dump(self.encoders, f"{model_path}/encoders.pkl")
        
        # Save configuration
        config_data = {
            'feature_columns': self.feature_columns,
            'autoencoder_threshold': self.autoencoder_threshold,
            'is_trained': self.is_trained
        }
        
        with open(f"{model_path}/config.json", 'w') as f:
            json.dump(config_data, f, indent=2)
        
        print(f"Models saved to {model_path}")
    
    def load_models(self, model_path: str) -> None:
        """Load trained models from disk"""
        if not os.path.exists(f"{model_path}/config.json"):
            print("No trained models found. Please train models first.")
            return False
        
        # Load configuration
        with open(f"{model_path}/config.json", 'r') as f:
            config_data = json.load(f)
        
        self.feature_columns = config_data['feature_columns']
        self.autoencoder_threshold = config_data['autoencoder_threshold']
        self.is_trained = config_data['is_trained']
        
        # Load models
        self.models['isolation_forest'] = joblib.load(f"{model_path}/isolation_forest.pkl")
        self.models['xgboost'] = joblib.load(f"{model_path}/xgboost_model.pkl")
        self.models['autoencoder'] = tf.keras.models.load_model(f"{model_path}/autoencoder.h5")
        
        # Load preprocessors
        self.scaler = joblib.load(f"{model_path}/scaler.pkl")
        self.encoders = joblib.load(f"{model_path}/encoders.pkl")
        
        print("Models loaded successfully!")
        return True

def main():
    """Main function for training models"""
    print("IGNISYL-Neo Anomaly Detection Training")
    print("=" * 50)
    
    # Initialize detector
    detector = BehavioralAnomalyDetector()
    
    # Train models
    data_path = settings.DATA_PATH + "/synthetic"
    detector.train_models(data_path)
    
    # Save models
    model_path = settings.MODEL_PATH
    detector.save_models(model_path)
    
    print("Training complete! Models ready for deployment.")

if __name__ == "__main__":
    main()