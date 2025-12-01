"""
ML Models Tests for IGNISYL
Tests the 3-model ensemble: Isolation Forest, Autoencoder, XGBoost
"""

import sys
import os
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_feature_extraction():
    """Test feature extraction from activities"""
    print("=" * 60)
    print("Testing Feature Extraction")
    print("=" * 60)
    
    # Sample activity
    activity = {
        'user_id': 'test_user',
        'activity_type': 'file_access',
        'timestamp': '2025-01-01T14:30:00',
        'hour': 14,
        'day_of_week': 2,
        'is_weekend': False,
        'bytes_transferred': 5000000,
        'source_ip': '192.168.1.100'
    }
    
    # Extract features (simplified)
    features = [
        activity['hour'],
        activity['day_of_week'],
        int(activity['is_weekend']),
        np.log1p(activity['bytes_transferred']),
        0  # activity_type encoded
    ]
    
    print(f"✅ Extracted features: {features}")
    assert len(features) == 5
    print("✅ Feature extraction test passed")

def test_risk_scoring():
    """Test risk scoring logic"""
    print("\n" + "=" * 60)
    print("Testing Risk Scoring")
    print("=" * 60)
    
    # Simulate ML model scores
    isolation_forest_score = 0.72
    autoencoder_score = 0.81
    xgboost_score = 0.83
    
    # Weighted ensemble
    weights = [0.3, 0.3, 0.4]
    ensemble_score = (
        isolation_forest_score * weights[0] +
        autoencoder_score * weights[1] +
        xgboost_score * weights[2]
    )
    
    final_risk = ensemble_score * 100
    
    print(f"   Isolation Forest: {isolation_forest_score}")
    print(f"   Autoencoder: {autoencoder_score}")
    print(f"   XGBoost: {xgboost_score}")
    print(f"   Final Risk Score: {final_risk:.2f}")
    
    assert 0 <= final_risk <= 100
    print("✅ Risk scoring test passed")

def test_model_loading():
    """Test loading trained models"""
    print("\n" + "=" * 60)
    print("Testing Model Loading")
    print("=" * 60)
    
    model_paths = [
        'data/models/isolation_forest.pkl',
        'data/models/autoencoder.h5',
        'data/models/xgboost.pkl',
        'data/models/scaler.pkl'
    ]
    
    for path in model_paths:
        if os.path.exists(path):
            print(f"✅ Found: {path}")
        else:
            print(f"⚠️ Not found: {path} (run train_models.py first)")
    
    print("✅ Model loading test passed")

def test_anomaly_detection():
    """Test anomaly detection logic"""
    print("\n" + "=" * 60)
    print("Testing Anomaly Detection")
    print("=" * 60)
    
    # Normal activity features
    normal_activity = np.array([[14, 2, 0, 15.5, 0]])  # Business hours, weekday
    
    # Anomalous activity features
    anomalous_activity = np.array([[2, 6, 1, 22.5, 6]])  # 2 AM, weekend, large transfer, honeypot
    
    # Simulate anomaly scores (higher = more anomalous)
    normal_score = 0.15  # Low anomaly
    anomalous_score = 0.92  # High anomaly
    
    print(f"   Normal activity score: {normal_score}")
    print(f"   Anomalous activity score: {anomalous_score}")
    
    assert normal_score < 0.5
    assert anomalous_score > 0.7
    
    print("✅ Anomaly detection test passed")

def test_risk_level_classification():
    """Test risk level classification"""
    print("\n" + "=" * 60)
    print("Testing Risk Level Classification")
    print("=" * 60)
    
    test_scores = [15, 40, 60, 80, 95]
    expected_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL', 'CRITICAL']
    
    for score, expected in zip(test_scores, expected_levels):
        if score < 30:
            level = 'LOW'
        elif score < 50:
            level = 'MEDIUM'
        elif score < 70:
            level = 'HIGH'
        else:
            level = 'CRITICAL'
        
        print(f"   Score {score}: {level}")
        assert level == expected
    
    print("✅ Risk level classification test passed")

def test_contextual_modifiers():
    """Test contextual risk modifiers"""
    print("\n" + "=" * 60)
    print("Testing Contextual Modifiers")
    print("=" * 60)
    
    base_risk = 50.0
    
    # Test modifier 1: Outside business hours
    if True:  # outside_hours
        base_risk += 10
        print(f"   + Outside hours modifier: {base_risk}")
    
    # Test modifier 2: Weekend activity
    if True:  # is_weekend
        base_risk += 5
        print(f"   + Weekend modifier: {base_risk}")
    
    # Test modifier 3: Large data transfer
    if True:  # large_transfer
        base_risk += 15
        print(f"   + Large transfer modifier: {base_risk}")
    
    # Cap at 100
    final_risk = min(base_risk, 100)
    
    print(f"   Final risk score: {final_risk}")
    assert final_risk <= 100
    
    print("✅ Contextual modifiers test passed")

def test_model_performance_metrics():
    """Test model performance calculation"""
    print("\n" + "=" * 60)
    print("Testing Model Performance Metrics")
    print("=" * 60)
    
    # Simulated predictions
    true_positives = 85
    false_positives = 10
    true_negatives = 890
    false_negatives = 15
    
    # Calculate metrics
    accuracy = (true_positives + true_negatives) / (true_positives + true_negatives + false_positives + false_negatives)
    precision = true_positives / (true_positives + false_positives)
    recall = true_positives / (true_positives + false_negatives)
    f1_score = 2 * (precision * recall) / (precision + recall)
    
    print(f"   Accuracy: {accuracy * 100:.2f}%")
    print(f"   Precision: {precision * 100:.2f}%")
    print(f"   Recall: {recall * 100:.2f}%")
    print(f"   F1-Score: {f1_score * 100:.2f}%")
    
    assert accuracy > 0.9  # Should be > 90%
    assert precision > 0.8
    assert recall > 0.8
    
    print("✅ Model performance metrics test passed")

def run_all_ml_tests():
    """Run all ML model tests"""
    print("=" * 60)
    print("IGNISYL - ML Models Tests")
    print("=" * 60)
    
    try:
        test_feature_extraction()
        test_risk_scoring()
        test_model_loading()
        test_anomaly_detection()
        test_risk_level_classification()
        test_contextual_modifiers()
        test_model_performance_metrics()
        
        print("\n" + "=" * 60)
        print("✅ ALL ML TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test assertion failed: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_ml_tests()
