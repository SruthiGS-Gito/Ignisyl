"""Compare IGNISYL against baseline ML models"""
import sys
import json
import time
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import pickle

# Fix Windows encoding for emojis
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.ml_engine.baseline_models import BaselineComparison


def extract_features(df):
    """Extract 14 features from activity data - same as validate_accuracy.py

    Args:
        df: DataFrame with activity data

    Returns:
        DataFrame with 14 engineered features (NaN-safe)
    """
    features = pd.DataFrame()

    # Time-based features (use existing fields from training_data.json)
    if 'hour' in df.columns:
        features['hour'] = df['hour'].fillna(12)
    elif 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        features['hour'] = df['timestamp'].dt.hour.fillna(12)
    else:
        features['hour'] = 12

    if 'day_of_week' in df.columns:
        features['day_of_week'] = df['day_of_week'].fillna(2)
    elif 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        features['day_of_week'] = df['timestamp'].dt.dayofweek.fillna(2)
    else:
        features['day_of_week'] = 2

    # File size features (raw + log)
    if 'file_size' in df.columns:
        file_size = df['file_size'].fillna(0)
    else:
        file_size = pd.Series([0] * len(df))

    features['file_size'] = file_size
    features['file_size_log'] = np.log1p(file_size)

    # Network bytes features (raw + log)
    if 'bytes_transferred' in df.columns:
        bytes_transferred = df['bytes_transferred'].fillna(0)
    else:
        bytes_transferred = pd.Series([0] * len(df))

    features['bytes_transferred'] = bytes_transferred
    features['network_bytes_log'] = np.log1p(bytes_transferred)

    # Boolean features
    if 'is_weekend' in df.columns:
        features['is_weekend'] = df['is_weekend'].fillna(False).astype(int)
    elif 'timestamp' in df.columns:
        features['is_weekend'] = df['timestamp'].dt.dayofweek.isin([5, 6]).fillna(False).astype(int)
    else:
        features['is_weekend'] = 0

    if 'is_business_hours' in df.columns:
        features['is_business_hours'] = df['is_business_hours'].fillna(True).astype(int)
    elif 'timestamp' in df.columns:
        features['is_business_hours'] = df['timestamp'].dt.hour.between(9, 17).fillna(True).astype(int)
    else:
        features['is_business_hours'] = 1

    # Risk indicators
    features['confidence_score'] = df.get('confidence_score', pd.Series([0.2] * len(df))).fillna(0.2)
    features['failed_login_count'] = df.get('failed_login_count', pd.Series([0] * len(df))).fillna(0)
    features['access_frequency'] = df.get('access_frequency', pd.Series([1.0] * len(df))).fillna(1.0)
    features['unusual_location'] = df.get('unusual_location', pd.Series([0] * len(df))).fillna(0).astype(int)
    features['file_type_risk'] = df.get('file_type_risk', pd.Series([0] * len(df))).fillna(0)
    features['time_since_last'] = df.get('time_since_last', pd.Series([60] * len(df))).fillna(60)

    # Final NaN check and replacement
    features = features.fillna(0)

    return features


def load_data():
    """Load training data from JSON file

    Returns:
        Tuple of (X, y) - features and labels
    """
    print("\n" + "="*70)
    print("📂 Loading Training Data")
    print("="*70)

    data_file = Path(__file__).parent.parent / 'data' / 'synthetic' / 'training_data.json'

    if not data_file.exists():
        raise FileNotFoundError(f"Training data not found: {data_file}")

    with open(data_file, 'r') as f:
        all_data = json.load(f)

    print(f"✅ Loaded {len(all_data)} samples from {data_file.name}")

    # Convert to DataFrame
    df = pd.DataFrame(all_data)

    # Extract features
    print("\n🔧 Extracting 14 features...")
    X = extract_features(df).values

    # Use 'is_malicious' field (correct field name in training_data.json)
    y = df['is_malicious'].astype(int).values

    print(f"✅ Features shape: {X.shape}")
    print(f"✅ Labels shape: {y.shape}")
    print(f"✅ Malicious samples: {sum(y)} ({sum(y)/len(y)*100:.1f}%)")
    print(f"✅ Normal samples: {len(y)-sum(y)} ({(len(y)-sum(y))/len(y)*100:.1f}%)")

    # Check for NaN values
    nan_count = np.isnan(X).sum()
    if nan_count > 0:
        print(f"⚠️ WARNING: Found {nan_count} NaN values in features")
        print("🔧 Cleaning NaN values...")
        # Replace NaN with 0
        X = np.nan_to_num(X, nan=0.0)
        print(f"✅ NaN values replaced with 0")

    return X, y


def train_ignisyl_models(X_train, y_train, X_test, y_test):
    """Train IGNISYL models for comparison

    Args:
        X_train: Training features
        y_train: Training labels
        X_test: Test features
        y_test: Test labels

    Returns:
        Dictionary with IGNISYL results
    """
    print("\n" + "="*70)
    print("🧠 Training IGNISYL Models")
    print("="*70)

    # Try different Keras imports for compatibility
    try:
        import keras
        print("✅ Using standalone Keras")
    except ImportError:
        try:
            from tensorflow import keras
            print("✅ Using TensorFlow Keras")
        except ImportError:
            try:
                import tf_keras as keras
                print("✅ Using tf_keras")
            except ImportError:
                raise ImportError("No Keras installation found. Install with: pip install keras")

    from sklearn.ensemble import IsolationForest
    import xgboost as xgb

    # Scale data
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    ignisyl_results = {}

    # 1. Isolation Forest
    print("\n🌲 Training Isolation Forest...", end=" ", flush=True)
    start_time = time.time()
    iso_forest = IsolationForest(
        n_estimators=100,
        contamination=0.1,
        random_state=42,
        n_jobs=-1
    )
    iso_forest.fit(X_train_scaled)
    if_train_time = time.time() - start_time
    print(f"✅ Done ({if_train_time:.2f}s)")

    # Predict
    if_scores = iso_forest.score_samples(X_test_scaled)
    if_scores_norm = (if_scores - if_scores.min()) / (if_scores.max() - if_scores.min() + 1e-10)
    if_pred = (if_scores_norm < 0.3).astype(int)

    # 2. Autoencoder
    print("🧬 Training Autoencoder...", end=" ", flush=True)
    start_time = time.time()

    input_dim = X_train_scaled.shape[1]
    autoencoder = keras.Sequential([
        keras.layers.Dense(32, activation='relu', input_shape=(input_dim,)),
        keras.layers.Dense(16, activation='relu'),
        keras.layers.Dense(8, activation='relu'),
        keras.layers.Dense(16, activation='relu'),
        keras.layers.Dense(32, activation='relu'),
        keras.layers.Dense(input_dim, activation='linear')
    ])

    autoencoder.compile(optimizer='adam', loss='mse')
    autoencoder.fit(
        X_train_scaled, X_train_scaled,
        epochs=50,
        batch_size=32,
        validation_split=0.1,
        verbose=0
    )
    ae_train_time = time.time() - start_time
    print(f"✅ Done ({ae_train_time:.2f}s)")

    # Predict
    ae_reconstructed = autoencoder.predict(X_test_scaled, verbose=0)
    ae_errors = np.mean(np.square(X_test_scaled - ae_reconstructed), axis=1)
    ae_errors_norm = (ae_errors - ae_errors.min()) / (ae_errors.max() - ae_errors.min() + 1e-10)
    ae_pred = (ae_errors_norm > 0.7).astype(int)

    # 3. XGBoost
    print("🚀 Training XGBoost...", end=" ", flush=True)
    start_time = time.time()
    xgb_model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        eval_metric='logloss',
        use_label_encoder=False
    )
    xgb_model.fit(X_train_scaled, y_train)
    xgb_train_time = time.time() - start_time
    print(f"✅ Done ({xgb_train_time:.2f}s)")

    # Predict
    xgb_pred_proba = xgb_model.predict_proba(X_test_scaled)[:, 1]
    xgb_pred = (xgb_pred_proba > 0.5).astype(int)

    # Evaluate XGBoost
    acc = accuracy_score(y_test, xgb_pred)
    prec = precision_score(y_test, xgb_pred, zero_division=0)
    rec = recall_score(y_test, xgb_pred, zero_division=0)
    f1 = f1_score(y_test, xgb_pred, zero_division=0)
    tn, fp, fn, tp = confusion_matrix(y_test, xgb_pred).ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0

    ignisyl_results['IGNISYL (XGBoost)'] = {
        'accuracy': acc,
        'precision': prec,
        'recall': rec,
        'f1_score': f1,
        'fpr': fpr,
        'training_time': xgb_train_time
    }

    # 4. Ensemble (2/3 voting)
    print("\n🎯 Creating Ensemble (2/3 voting)...", end=" ", flush=True)
    votes = if_pred + ae_pred + xgb_pred
    ensemble_pred = (votes >= 2).astype(int)

    acc = accuracy_score(y_test, ensemble_pred)
    prec = precision_score(y_test, ensemble_pred, zero_division=0)
    rec = recall_score(y_test, ensemble_pred, zero_division=0)
    f1 = f1_score(y_test, ensemble_pred, zero_division=0)
    tn, fp, fn, tp = confusion_matrix(y_test, ensemble_pred).ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0

    total_train_time = if_train_time + ae_train_time + xgb_train_time

    ignisyl_results['IGNISYL (Ensemble)'] = {
        'accuracy': acc,
        'precision': prec,
        'recall': rec,
        'f1_score': f1,
        'fpr': fpr,
        'training_time': total_train_time
    }

    print(f"✅ Done")

    return ignisyl_results


def save_results(baseline_results, ignisyl_results, summary):
    """Save comparison results to JSON

    Args:
        baseline_results: Results from baseline models
        ignisyl_results: Results from IGNISYL models
        summary: Summary statistics
    """
    output_file = Path(__file__).parent / 'baseline_comparison_results.json'

    results = {
        'baseline_models': baseline_results,
        'ignisyl_models': ignisyl_results,
        'summary': summary,
        'timestamp': pd.Timestamp.now().isoformat()
    }

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")


def main():
    """Main comparison function"""
    print("\n" + "="*70)
    print("🏆 IGNISYL vs BASELINE MODELS COMPARISON")
    print("="*70)

    # Load data
    X, y = load_data()

    # Split data
    print("\n📊 Splitting data (80% train, 20% test)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"✅ Train set: {X_train.shape[0]} samples")
    print(f"✅ Test set: {X_test.shape[0]} samples")

    # Scale data for baselines
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train baseline models
    baseline_comparison = BaselineComparison()
    baseline_comparison.train_all_baselines(X_train_scaled, y_train, verbose=True)

    # Evaluate baselines
    baseline_results = baseline_comparison.compare_all_models(X_test_scaled, y_test, verbose=True)

    # Train IGNISYL models (skip if tensorflow not working)
    try:
        ignisyl_results = train_ignisyl_models(X_train, y_train, X_test, y_test)
        # Print comparison table
        baseline_comparison.print_comparison_table(include_ignisyl=ignisyl_results)
    except ImportError as e:
        print(f"\n⚠️ Skipping IGNISYL models (TensorFlow not available): {e}")
        ignisyl_results = {}
        # Print comparison table without IGNISYL
        baseline_comparison.print_comparison_table()

    # Calculate improvement (only if IGNISYL results available)
    if ignisyl_results and 'IGNISYL (Ensemble)' in ignisyl_results:
        ensemble_accuracy = ignisyl_results['IGNISYL (Ensemble)']['accuracy']
        best_baseline_name, best_baseline_acc = baseline_comparison.get_best_baseline()

        improvement_pct = ((ensemble_accuracy - best_baseline_acc) / best_baseline_acc) * 100
        absolute_improvement = (ensemble_accuracy - best_baseline_acc) * 100

        # Print summary
        print("\n" + "="*70)
        print("📈 PERFORMANCE SUMMARY")
        print("="*70)
        print(f"\n🥇 Best Baseline: {best_baseline_name}")
        print(f"   Accuracy: {best_baseline_acc*100:.1f}%")
        print(f"\n🏆 IGNISYL Ensemble")
        print(f"   Accuracy: {ensemble_accuracy*100:.1f}%")
        print(f"\n✅ IGNISYL Improvement:")
        print(f"   Absolute: +{absolute_improvement:.1f}% accuracy points")
        print(f"   Relative: {improvement_pct:.1f}% better than best baseline")
        print("="*70)

        # Summary statistics
        summary_stats = baseline_comparison.get_summary_statistics()
        summary_stats['ignisyl_ensemble_accuracy'] = ensemble_accuracy
        summary_stats['best_baseline_accuracy'] = best_baseline_acc
        summary_stats['improvement_absolute'] = absolute_improvement
        summary_stats['improvement_relative'] = improvement_pct
    else:
        # Just show baseline summary
        best_baseline_name, best_baseline_acc = baseline_comparison.get_best_baseline()
        print("\n" + "="*70)
        print("📈 BASELINE PERFORMANCE SUMMARY")
        print("="*70)
        print(f"\n🥇 Best Baseline Model: {best_baseline_name}")
        print(f"   Accuracy: {best_baseline_acc*100:.1f}%")
        print("="*70)

        summary_stats = baseline_comparison.get_summary_statistics()

    # Save results
    save_results(baseline_results, ignisyl_results, summary_stats)

    print("\n✅ Comparison complete!")


if __name__ == "__main__":
    main()
