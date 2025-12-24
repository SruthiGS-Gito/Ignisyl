"""
Train ML Models for IGNISYL
Trains the 3-model ensemble: Isolation Forest, Autoencoder, XGBoost
"""

import json
import pickle
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
from tensorflow import keras
from tensorflow.keras import layers
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_training_data(filepath='data/synthetic/training_data.json'):
    """Load training data"""
    print(f"[*] Loading training data from {filepath}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    print(f"✅ Loaded {len(data)} training samples")
    return data

def prepare_features(data):
    """Prepare features for training"""
    print("[*] Preparing features...")
    
    X = []
    y = []
    
    # Activity type encoding
    activity_types = {
        'file_access': 0, 'network_access': 1, 'login': 2,
        'data_transfer': 3, 'privilege_escalation': 4,
        'usb_device': 5, 'honeypot_access': 6
    }
    
    for sample in data:
        # Extract 9 features matching prediction pipeline
        features = [
            sample['hour'],                                      # 1
            sample['day_of_week'],                              # 2
            sample.get('file_size', 0),                         # 3
            np.log1p(sample.get('file_size', 0)),              # 4
            sample['bytes_transferred'],                        # 5
            np.log1p(sample['bytes_transferred']),             # 6
            int(sample['is_weekend']),                         # 7
            int(sample.get('is_business_hours', 0)),          # 8
            sample.get('confidence_score', 0.2),               # 9
            sample.get('failed_login_count', 0),               # 10 NEW
            sample.get('access_frequency', 1.0),               # 11 NEW
            int(sample.get('unusual_location', False)),        # 12 NEW
            sample.get('file_type_risk', 0),                   # 13 NEW
            sample.get('time_since_last', 60)                  # 14 NEW
        ]
        X.append(features)
        y.append(int(sample['is_malicious']))
    
    X = np.array(X)
    y = np.array(y)
    
    print(f"✅ Feature matrix shape: {X.shape}")
    print(f"   Malicious samples: {sum(y)} ({sum(y)/len(y)*100:.1f}%)")
    
    return X, y

def train_isolation_forest(X):
    """Train Isolation Forest"""
    print("\n[*] Training Isolation Forest...")
    
    model = IsolationForest(
        contamination=0.1,
        random_state=42,
        n_estimators=100
    )
    
    model.fit(X)
    print("✅ Isolation Forest trained")
    
    return model

def train_autoencoder(X):
    """Train Autoencoder"""
    print("\n[*] Training Autoencoder...")
    
    # Normalize data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Build autoencoder
    input_dim = X.shape[1]
    encoding_dim = 3
    
    model = keras.Sequential([
        layers.Dense(8, activation='relu', input_shape=(input_dim,)),
        layers.Dense(encoding_dim, activation='relu'),
        layers.Dense(8, activation='relu'),
        layers.Dense(input_dim, activation='sigmoid')
    ])
    
    model.compile(optimizer='adam', loss='mse')
    
    # Train
    model.fit(
        X_scaled, X_scaled,
        epochs=50,
        batch_size=32,
        validation_split=0.2,
        verbose=0
    )
    
    print("✅ Autoencoder trained")
    
    return model, scaler

def train_xgboost(X, y):
    """Train XGBoost with class balancing"""
    print("[*] Training XGBoost...")
    
    # Calculate class weights for imbalanced data
    n_samples = len(y)
    n_positive = int(sum(y))
    n_negative = n_samples - n_positive
    scale_pos_weight = n_negative / n_positive if n_positive > 0 else 1.0
    
    print(f"   Total samples: {n_samples}")
    print(f"   Normal (0): {n_negative} ({n_negative/n_samples*100:.1f}%)")
    print(f"   Malicious (1): {n_positive} ({n_positive/n_samples*100:.1f}%)")
    print(f"   Scale pos weight: {scale_pos_weight:.2f}")
    
    # Train XGBoost with class balancing
    xgb_model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        use_label_encoder=False,
        eval_metric='logloss'
    )
    
    xgb_model.fit(X, y)
    
    # Calculate training accuracy
    train_acc = xgb_model.score(X, y)
    print(f"✅ XGBoost trained - Training Accuracy: {train_acc*100:.2f}%")
    
    return xgb_model

def save_models(isolation_forest, autoencoder, scaler, xgboost, output_dir='data/models'):
    """Save trained models"""
    print(f"\n[*] Saving models to {output_dir}...")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Save Isolation Forest
    with open(os.path.join(output_dir, 'isolation_forest.pkl'), 'wb') as f:
        pickle.dump(isolation_forest, f)
    print("   ✅ Saved isolation_forest.pkl")
    
    # Save Autoencoder
    autoencoder.save(os.path.join(output_dir, 'autoencoder.h5'))
    print("   ✅ Saved autoencoder.h5")
    
    # Save Scaler
    with open(os.path.join(output_dir, 'scaler.pkl'), 'wb') as f:
        pickle.dump(scaler, f)
    print("   ✅ Saved scaler.pkl")
    
    # Save XGBoost
    with open(os.path.join(output_dir, 'xgboost.pkl'), 'wb') as f:
        pickle.dump(xgboost, f)
    print("   ✅ Saved xgboost.pkl")

if __name__ == '__main__':
    print("=" * 60)
    print("IGNISYL - ML Model Trainer")
    print("=" * 60)
    
    # Load data
    data = load_training_data()
    
    # Prepare features
    X, y = prepare_features(data)
    
    # Train models
    isolation_forest = train_isolation_forest(X)
    autoencoder, scaler = train_autoencoder(X)
    xgboost_model = train_xgboost(X, y)
    
    # Save models
    save_models(isolation_forest, autoencoder, scaler, xgboost_model)
    
    print("\n✅ Model training complete!")
    print("=" * 60)
