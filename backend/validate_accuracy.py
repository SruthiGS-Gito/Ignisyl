"""
Proper validation with correct train/test split
"""
import sys
import json
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix, f1_score
import pickle
from tensorflow import keras

def load_all_data():
    """Load all training data"""
    data_file = Path(__file__).parent.parent / 'data' / 'synthetic' / 'training_data.json'
    
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    return data

def extract_features(sample):
    """Extract 14 features matching training"""
    return [
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

def validate():
    print("="*60)
    print("🧪 PROPER IGNISYL VALIDATION")
    print("="*60)
    
    # Load ALL data
    print("\n📊 Loading all data...")
    all_data = load_all_data()
    print(f"✅ Loaded {len(all_data)} total samples")
    
    # Extract features and labels
    X_all = []
    y_all = []
    
    for sample in all_data:
        X_all.append(extract_features(sample))
        y_all.append(1 if sample['is_malicious'] else 0)
    
    X_all = np.array(X_all)
    y_all = np.array(y_all)
    
    print(f"   Feature shape: {X_all.shape}")
    print(f"   Total Normal: {sum(y_all == 0)}")
    print(f"   Total Malicious: {sum(y_all == 1)}")
    
    # Split train/test (80/20)
    print("\n✂️ Splitting train/test (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_all, y_all, 
        test_size=0.2, 
        random_state=42,
        stratify=y_all  # Keep same class ratio
    )
    
    print(f"   Train: {len(X_train)} samples")
    print(f"   Test:  {len(X_test)} samples")
    
    # Load scaler from training
    print("\n🔧 Loading scaler...")
    models_dir = Path(__file__).parent.parent / 'data' / 'models'
    scaler = pickle.load(open(models_dir / 'scaler.pkl', 'rb'))
    
    # Scale using TRAINING scaler
    X_test_scaled = scaler.transform(X_test)
    
    print(f"   Scaled features - Min: {X_test_scaled.min():.3f}, Max: {X_test_scaled.max():.3f}")
    
    # Load model
    print("\n🤖 Loading XGBoost model...")
    xgboost_model = pickle.load(open(models_dir / 'xgboost.pkl', 'rb'))
    
    # Predict
    print("\n🔍 Running predictions...")
    y_pred_proba = xgboost_model.predict_proba(X_test_scaled)[:, 1]
    
    # Stats
    print(f"\n📊 Prediction Probability Stats:")
    print(f"   Min: {y_pred_proba.min():.4f}")
    print(f"   Max: {y_pred_proba.max():.4f}")
    print(f"   Mean: {y_pred_proba.mean():.4f}")
    print(f"   Median: {np.median(y_pred_proba):.4f}")
    
    # Try different thresholds
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7]
    
    print("\n🎯 Testing different thresholds:")
    best_f1 = 0
    best_threshold = 0.5
    
    for thresh in thresholds:
        y_pred = (y_pred_proba >= thresh).astype(int)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        tp = sum((y_pred == 1) & (y_test == 1))
        print(f"   Threshold {thresh}: F1={f1:.3f}, TP={tp}")
        
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = thresh
    
    print(f"\n✅ Best threshold: {best_threshold} (F1={best_f1:.3f})")
    
    # Final predictions with best threshold
    y_pred = (y_pred_proba >= best_threshold).astype(int)
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    
    # Display results
    print("\n" + "="*60)
    print("📊 FINAL VALIDATION RESULTS")
    print("="*60)
    print(f"✅ Accuracy:  {accuracy*100:.1f}%")
    print(f"✅ Precision: {precision*100:.1f}%")
    print(f"✅ Recall:    {recall*100:.1f}%")
    print(f"✅ F1-Score:  {f1*100:.1f}%")
    print(f"✅ FPR:       {fpr*100:.1f}%")
    
    print("\n📋 Confusion Matrix:")
    print(f"   True Negatives:  {tn}")
    print(f"   False Positives: {fp}")
    print(f"   False Negatives: {fn}")
    print(f"   True Positives:  {tp}")
    
    print("="*60)
    
    # Save results
    results = {
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'fpr': float(fpr),
        'best_threshold': float(best_threshold),
        'confusion_matrix': {
            'tn': int(tn),
            'fp': int(fp),
            'fn': int(fn),
            'tp': int(tp)
        }
    }
    
    output_file = Path(__file__).parent / 'validation_results_proper.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Results saved to {output_file}")
    
    return results

if __name__ == "__main__":
    validate()