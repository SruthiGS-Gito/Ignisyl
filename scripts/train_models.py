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
    print(f"📂 Loading training data from {filepath}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    print(f"✅ Loaded {len(data)} training samples")
    return data

def prepare_features(data):
    """Prepare features for training"""
    print("🔧 Preparing features...")
    
    X = []
    y = []
    
    # Activity type encoding
    activity_types = {
        'file_access': 0, 'network_access': 1, 'login': 2,
        'data_transfer': 3, 'privilege_escalation': 4,
        'usb_device': 5, 'honeypot_access': 6
    }
    
    for sample in data:
        features = [
            sample['hour'],
            sample['day_of_week'],
            int(sample['is_weekend']),
            np.log1p(sample['bytes_transferred']),  # Log transform
            activity_types.get(sample['activity_type'], 0)
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
    print("\n🌲 Training Isolation Forest...")
    
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
    print("\n🧠 Training Autoencoder...")
    
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
    """Train XGBoost"""
    print("\n🚀 Training XGBoost...")
    
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42
    )
    
    model.fit(X, y)
    
    # Calculate accuracy
    train_acc = model.score(X, y)
    print(f"✅ XGBoost trained - Training Accuracy: {train_acc*100:.2f}%")
    
    return model

def save_models(isolation_forest, autoencoder, scaler, xgboost, output_dir='data/models'):
    """Save trained models"""
    print(f"\n💾 Saving models to {output_dir}...")
    
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
