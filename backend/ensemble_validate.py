"""Validate with ensemble voting (IF + AE + XGBoost)"""
import sys
import json
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import pickle
from tensorflow import keras

def validate_ensemble():
    # Load data
    data_file = Path(__file__).parent.parent / 'data' / 'synthetic' / 'training_data.json'
    with open(data_file, 'r') as f:
        all_data = json.load(f)
    
    # Extract features
    X_all = []
    y_all = []
    for sample in all_data:
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
            sample.get('failed_login_count', 0),               # 10
            sample.get('access_frequency', 1.0),               # 11
            int(sample.get('unusual_location', False)),        # 12
            sample.get('file_type_risk', 0),                   # 13
            sample.get('time_since_last', 60)                  # 14
        ]
        X_all.append(features)
        y_all.append(1 if sample['is_malicious'] else 0)
    
    X_all = np.array(X_all)
    y_all = np.array(y_all)
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X_all, y_all, test_size=0.2, random_state=42, stratify=y_all
    )
    
    # Load models
    models_dir = Path(__file__).parent.parent / 'data' / 'models'
    
    isolation_forest = pickle.load(open(models_dir / 'isolation_forest.pkl', 'rb'))
    autoencoder = keras.models.load_model(models_dir / 'autoencoder.h5', compile=False)
    autoencoder.compile(optimizer='adam', loss='mse')
    scaler = pickle.load(open(models_dir / 'scaler.pkl', 'rb'))
    xgboost_model = pickle.load(open(models_dir / 'xgboost.pkl', 'rb'))
    
    # Scale
    X_test_scaled = scaler.transform(X_test)
    
    print("="*70)
    print("🎯 ENSEMBLE VOTING VALIDATION (2/3 Agreement)")
    print("="*70)
    
    # Get individual predictions
    
    # 1. Isolation Forest
    if_scores = isolation_forest.score_samples(X_test_scaled)
    if_scores_norm = (if_scores - if_scores.min()) / (if_scores.max() - if_scores.min() + 1e-10)
    if_anomaly = (if_scores_norm < 0.3).astype(int)  # Lower scores = more anomalous
    
    # 2. Autoencoder
    ae_reconstructed = autoencoder.predict(X_test_scaled, verbose=0)
    ae_errors = np.mean(np.square(X_test_scaled - ae_reconstructed), axis=1)
    ae_errors_norm = (ae_errors - ae_errors.min()) / (ae_errors.max() - ae_errors.min() + 1e-10)
    ae_anomaly = (ae_errors_norm > 0.7).astype(int)  # High error = anomaly
    
    # 3. XGBoost
    xgb_proba = xgboost_model.predict_proba(X_test_scaled)[:, 1]
    xgb_anomaly = (xgb_proba > 0.05).astype(int)
    
    # Ensemble voting (at least 2 out of 3 agree)
    votes = if_anomaly + ae_anomaly + xgb_anomaly
    y_pred_ensemble = (votes >= 2).astype(int)
    
    # Calculate metrics
    acc = accuracy_score(y_test, y_pred_ensemble)
    prec = precision_score(y_test, y_pred_ensemble, zero_division=0)
    rec = recall_score(y_test, y_pred_ensemble, zero_division=0)
    f1 = f1_score(y_test, y_pred_ensemble, zero_division=0)
    
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred_ensemble).ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    
    print(f"\n📊 ENSEMBLE RESULTS:")
    print(f"   Accuracy:  {acc*100:.1f}%")
    print(f"   Precision: {prec*100:.1f}%")
    print(f"   Recall:    {rec*100:.1f}%")
    print(f"   F1-Score:  {f1*100:.1f}%")
    print(f"   FPR:       {fpr*100:.1f}%")
    
    print(f"\n📋 Confusion Matrix:")
    print(f"   TN: {tn}, FP: {fp}, FN: {fn}, TP: {tp}")
    
    print("\n🔍 Individual Model Votes:")
    print(f"   IF detected:  {sum(if_anomaly)} anomalies")
    print(f"   AE detected:  {sum(ae_anomaly)} anomalies")
    print(f"   XGB detected: {sum(xgb_anomaly)} anomalies")
    
    print("="*70)

if __name__ == "__main__":
    validate_ensemble()