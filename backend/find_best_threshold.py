"""Find optimal threshold for best F1 score"""
import sys
import json
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import pickle

def test_thresholds():
    # Load data
    data_file = Path(__file__).parent.parent / 'data' / 'synthetic' / 'training_data.json'
    with open(data_file, 'r') as f:
        all_data = json.load(f)
    
    # Extract features
    X_all = []
    y_all = []
    for sample in all_data:
        features = [
            sample['hour'],
            sample['day_of_week'],
            sample.get('file_size', 0),
            np.log1p(sample.get('file_size', 0)),
            sample['bytes_transferred'],
            np.log1p(sample['bytes_transferred']),
            int(sample['is_weekend']),
            int(sample.get('is_business_hours', 0)),
            sample.get('confidence_score', 0.2)
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
    scaler = pickle.load(open(models_dir / 'scaler.pkl', 'rb'))
    xgboost_model = pickle.load(open(models_dir / 'xgboost.pkl', 'rb'))
    
    # Get predictions
    X_test_scaled = scaler.transform(X_test)
    y_pred_proba = xgboost_model.predict_proba(X_test_scaled)[:, 1]
    
    print("="*70)
    print("🎯 THRESHOLD OPTIMIZATION")
    print("="*70)
    
    # Test many thresholds
    thresholds = np.arange(0.05, 0.95, 0.05)
    results = []
    
    for thresh in thresholds:
        y_pred = (y_pred_proba >= thresh).astype(int)
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        tp = sum((y_pred == 1) & (y_test == 1))
        fp = sum((y_pred == 1) & (y_test == 0))
        fn = sum((y_pred == 0) & (y_test == 1))
        
        results.append({
            'threshold': thresh,
            'accuracy': acc,
            'precision': prec,
            'recall': rec,
            'f1': f1,
            'tp': tp,
            'fp': fp,
            'fn': fn
        })
    
    # Sort by F1
    results.sort(key=lambda x: x['f1'], reverse=True)
    
    print("\n📊 TOP 5 THRESHOLDS BY F1-SCORE:")
    print("-"*70)
    print(f"{'Thresh':<8} {'Acc':<7} {'Prec':<7} {'Rec':<7} {'F1':<7} {'TP':<5} {'FP':<5} {'FN':<5}")
    print("-"*70)
    
    for i, r in enumerate(results[:5]):
        print(f"{r['threshold']:.2f}     {r['accuracy']*100:5.1f}%  {r['precision']*100:5.1f}%  {r['recall']*100:5.1f}%  {r['f1']*100:5.1f}%  {r['tp']:3d}   {r['fp']:3d}   {r['fn']:3d}")
    
    print("="*70)
    
    # Best F1
    best = results[0]
    print(f"\n✅ BEST THRESHOLD: {best['threshold']:.2f}")
    print(f"   Accuracy:  {best['accuracy']*100:.1f}%")
    print(f"   Precision: {best['precision']*100:.1f}%")
    print(f"   Recall:    {best['recall']*100:.1f}%")
    print(f"   F1-Score:  {best['f1']*100:.1f}%")
    print("="*70)

if __name__ == "__main__":
    test_thresholds()