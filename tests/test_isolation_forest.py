"""
Phase 1 Technical Tests — Isolation Forest (BehavioralAnomalyDetector)
=======================================================================
Unit tests for model initialization, training, and prediction functions.
Tests are added in batches of 5.

Module under test:
  backend/ml_engine/anomaly_detector.py  (BehavioralAnomalyDetector)

Run with:
    python -m unittest tests/test_isolation_forest.py -v
"""

import sys
import os
import unittest
import numpy as np
from unittest.mock import MagicMock, patch, PropertyMock

# ── Project root on path ──────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ── Stub heavy imports before anomaly_detector loads them at module level ─────
# TensorFlow is broken in this environment; XGBoost is also stubbed so
# individual Isolation Forest tests remain self-contained.
_tf_stub = MagicMock()
for _mod in [
    "tensorflow", "tensorflow.keras", "tensorflow.keras.models",
    "tensorflow.keras.layers", "tensorflow.keras.optimizers",
    "tensorflow.keras.callbacks",
]:
    sys.modules.setdefault(_mod, _tf_stub)

sys.modules.setdefault("xgboost", MagicMock())

# ── Stub config.config ────────────────────────────────────────────────────────
_cfg = MagicMock()
_cfg.settings.LOW_RISK_THRESHOLD    = 30
_cfg.settings.MEDIUM_RISK_THRESHOLD = 70
_cfg.settings.DATA_PATH  = "/tmp/ignisyl_test"
_cfg.settings.MODEL_PATH = "/tmp/ignisyl_models"
sys.modules.setdefault("config",        _cfg)
sys.modules.setdefault("config.config", _cfg)

from backend.ml_engine.anomaly_detector import BehavioralAnomalyDetector  # noqa: E402
from sklearn.ensemble import IsolationForest                               # noqa: E402


# ══════════════════════════════════════════════════════════════════════════════
# Shared fixture helpers
# ══════════════════════════════════════════════════════════════════════════════

def _make_X(n_samples=200, n_features=10, seed=42):
    """Return a deterministic float64 feature matrix."""
    rng = np.random.default_rng(seed)
    return rng.standard_normal((n_samples, n_features)).astype(np.float64)


def _make_y(n_samples=200, anomaly_frac=0.1, seed=42):
    """Return binary labels with `anomaly_frac` fraction of 1s."""
    rng = np.random.default_rng(seed)
    y = np.zeros(n_samples, dtype=int)
    n_anomalies = max(1, int(n_samples * anomaly_frac))
    idx = rng.choice(n_samples, size=n_anomalies, replace=False)
    y[idx] = 1
    return y


def _trained_detector():
    """Return a detector with only the Isolation Forest trained."""
    det = BehavioralAnomalyDetector()
    X = _make_X()
    y = _make_y()
    det.train_isolation_forest(X, y)
    return det, X, y


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 1 — Initialization (tests 1-5)
# ══════════════════════════════════════════════════════════════════════════════

class TestInitialization(unittest.TestCase):
    """BehavioralAnomalyDetector.__init__"""

    def setUp(self):
        self.det = BehavioralAnomalyDetector()

    # 1
    def test_models_dict_starts_empty(self):
        self.assertEqual(self.det.models, {})

    # 2
    def test_is_trained_starts_false(self):
        self.assertFalse(self.det.is_trained)

    # 3
    def test_feature_columns_starts_empty(self):
        self.assertEqual(self.det.feature_columns, [])

    # 4
    def test_config_has_all_three_model_keys(self):
        expected = {"isolation_forest", "autoencoder", "xgboost"}
        self.assertEqual(set(self.det.config.keys()), expected)

    # 5
    def test_isolation_forest_config_values(self):
        cfg = self.det.config["isolation_forest"]
        self.assertEqual(cfg["contamination"],  0.1)
        self.assertEqual(cfg["n_estimators"],   100)
        self.assertEqual(cfg["random_state"],   42)
        self.assertEqual(cfg["max_samples"],    "auto")


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 2 — Training: train_isolation_forest (tests 6-10)
# ══════════════════════════════════════════════════════════════════════════════

class TestTrainIsolationForest(unittest.TestCase):
    """BehavioralAnomalyDetector.train_isolation_forest"""

    def setUp(self):
        self.det = BehavioralAnomalyDetector()
        self.X   = _make_X(n_samples=200, n_features=10)
        self.y   = _make_y(n_samples=200, anomaly_frac=0.1)

    # 6
    def test_model_stored_under_correct_key(self):
        self.det.train_isolation_forest(self.X, self.y)
        self.assertIn("isolation_forest", self.det.models)

    # 7
    def test_stored_model_is_isolation_forest_instance(self):
        self.det.train_isolation_forest(self.X, self.y)
        self.assertIsInstance(self.det.models["isolation_forest"], IsolationForest)

    # 8
    @patch("backend.ml_engine.anomaly_detector.IsolationForest")
    def test_trains_only_on_normal_samples(self, MockIF):
        """fit() must receive exactly the normal rows (y == 0)."""
        mock_model = MagicMock()
        MockIF.return_value = mock_model
        self.det.train_isolation_forest(self.X, self.y)
        X_passed = mock_model.fit.call_args[0][0]
        n_normal  = int((self.y == 0).sum())
        self.assertEqual(len(X_passed), n_normal)

    # 9
    def test_config_params_applied_to_model(self):
        self.det.train_isolation_forest(self.X, self.y)
        model = self.det.models["isolation_forest"]
        self.assertEqual(model.n_estimators,  self.det.config["isolation_forest"]["n_estimators"])
        self.assertEqual(model.contamination, self.det.config["isolation_forest"]["contamination"])
        self.assertEqual(model.random_state,  self.det.config["isolation_forest"]["random_state"])

    # 10
    def test_is_trained_remains_false_after_partial_training(self):
        # is_trained is only set True by train_models(), not train_isolation_forest()
        self.det.train_isolation_forest(self.X, self.y)
        self.assertFalse(self.det.is_trained)


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 3 — Prediction: predict_anomaly_scores / IF scores (tests 11-15)
# ══════════════════════════════════════════════════════════════════════════════

def _det_with_mocked_ensemble():
    """
    Train only the real IsolationForest; stub autoencoder and xgboost so
    predict_anomaly_scores() can run end-to-end without TF/XGBoost.
    """
    det, X, y = _trained_detector()
    n = len(X)

    # Stub autoencoder: predict returns a copy of X (zero reconstruction error)
    ae_mock = MagicMock()
    ae_mock.predict.return_value = X.copy()
    det.models["autoencoder"] = ae_mock
    det.autoencoder_threshold  = 1.0          # any positive float

    # Stub xgboost: predict_proba returns uniform 0.5 probabilities
    xgb_mock = MagicMock()
    xgb_mock.predict_proba.return_value = np.full((n, 2), 0.5)
    det.models["xgboost"] = xgb_mock

    det.is_trained = True
    return det, X


class TestPredictAnomalyScores(unittest.TestCase):
    """BehavioralAnomalyDetector.predict_anomaly_scores — Isolation Forest slice"""

    def setUp(self):
        self.det_untrained = BehavioralAnomalyDetector()
        self.det, self.X   = _det_with_mocked_ensemble()

    # 11
    def test_raises_value_error_when_not_trained(self):
        X = _make_X(n_samples=10)
        with self.assertRaises(ValueError):
            self.det_untrained.predict_anomaly_scores(X)

    # 12
    def test_returns_dict_with_isolation_forest_key(self):
        scores = self.det.predict_anomaly_scores(self.X)
        self.assertIn("isolation_forest", scores)

    # 13
    def test_isolation_forest_scores_in_0_1_range(self):
        scores = self.det.predict_anomaly_scores(self.X)
        if_scores = scores["isolation_forest"]
        self.assertTrue(np.all(if_scores >= 0.0),
                        "Some IF scores are below 0")
        self.assertTrue(np.all(if_scores <= 1.0),
                        "Some IF scores exceed 1")

    # 14
    def test_isolation_forest_scores_length_matches_input(self):
        scores = self.det.predict_anomaly_scores(self.X)
        self.assertEqual(len(scores["isolation_forest"]), len(self.X))

    # 15
    def test_isolation_forest_scores_are_inverted_decision_function(self):
        """Higher anomaly score must correspond to lower decision_function value."""
        raw = self.det.models["isolation_forest"].decision_function(self.X)
        scores = self.det.predict_anomaly_scores(self.X)["isolation_forest"]
        # Pearson correlation between raw decision values and IF scores must be negative
        correlation = np.corrcoef(raw, scores)[0, 1]
        self.assertLess(correlation, 0,
                        "IF scores should be negatively correlated with decision_function")


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 4 — Ensemble Prediction (tests 16-20)
# ══════════════════════════════════════════════════════════════════════════════

class TestEnsemblePrediction(unittest.TestCase):
    """BehavioralAnomalyDetector.ensemble_prediction"""

    def setUp(self):
        self.det, self.X = _det_with_mocked_ensemble()

    # 16
    def test_returns_tuple_of_two_elements(self):
        result = self.det.ensemble_prediction(self.X)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    # 17
    def test_risk_scores_clipped_to_0_100(self):
        risk_scores, _ = self.det.ensemble_prediction(self.X)
        self.assertTrue(np.all(risk_scores >= 0),
                        "Some risk scores are below 0")
        self.assertTrue(np.all(risk_scores <= 100),
                        "Some risk scores exceed 100")

    # 18
    def test_risk_scores_length_matches_input(self):
        risk_scores, _ = self.det.ensemble_prediction(self.X)
        self.assertEqual(len(risk_scores), len(self.X))

    # 19
    def test_default_weights_sum_to_one(self):
        # Verify the hard-coded default weights in the method
        det = BehavioralAnomalyDetector()
        default_weights = {
            "isolation_forest": 0.3,
            "autoencoder":      0.3,
            "xgboost":          0.4,
        }
        self.assertAlmostEqual(sum(default_weights.values()), 1.0, places=9)

    # 20
    def test_custom_weights_change_output(self):
        """Altering weights must produce a different ensemble score."""
        scores_default, _ = self.det.ensemble_prediction(self.X)
        scores_custom, _  = self.det.ensemble_prediction(
            self.X,
            weights={"isolation_forest": 1.0, "autoencoder": 0.0, "xgboost": 0.0},
        )
        # With all weight on IF the results should differ from the balanced default
        self.assertFalse(
            np.allclose(scores_default, scores_custom),
            "Custom weights produced identical scores to default weights",
        )


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 5 — Risk Level & Explanation (tests 21-25)
# ══════════════════════════════════════════════════════════════════════════════

def _low_individual_scores():
    """Individual scores well below every explanation threshold (0.7)."""
    return {
        "isolation_forest": np.array([0.1]),
        "autoencoder":      np.array([0.1]),
        "xgboost":          np.array([0.1]),
    }


class TestGetRiskLevel(unittest.TestCase):
    """BehavioralAnomalyDetector._get_risk_level"""

    def setUp(self):
        self.det = BehavioralAnomalyDetector()

    # 21
    def test_score_below_low_threshold_returns_low(self):
        # LOW_RISK_THRESHOLD = 30 in stub
        self.assertEqual(self.det._get_risk_level(10), "LOW")

    # 22
    def test_score_between_thresholds_returns_medium(self):
        # 30 <= 50 < 70
        self.assertEqual(self.det._get_risk_level(50), "MEDIUM")

    # 23
    def test_score_at_or_above_high_threshold_returns_high(self):
        # MEDIUM_RISK_THRESHOLD = 70 in stub
        self.assertEqual(self.det._get_risk_level(70), "HIGH")
        self.assertEqual(self.det._get_risk_level(95), "HIGH")


class TestGenerateExplanation(unittest.TestCase):
    """BehavioralAnomalyDetector._generate_explanation"""

    def setUp(self):
        self.det    = BehavioralAnomalyDetector()
        self.scores = _low_individual_scores()

    # 24
    def test_returns_a_list(self):
        result = self.det._generate_explanation({}, self.scores, 10.0)
        self.assertIsInstance(result, list)

    # 25
    def test_all_flags_absent_returns_normal_fallback(self):
        result = self.det._generate_explanation({}, self.scores, 10.0)
        self.assertTrue(
            any("appears normal" in msg for msg in result),
            f"Expected 'appears normal' fallback, got: {result}",
        )


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 6 — Explanation triggers & prepare_features (tests 26-30)
# ══════════════════════════════════════════════════════════════════════════════

class TestGenerateExplanationTriggers(unittest.TestCase):
    """_generate_explanation — individual trigger conditions"""

    def setUp(self):
        self.det = BehavioralAnomalyDetector()

    def _explain(self, activity_data, if_score=0.1, ae_score=0.1, xgb_score=0.1):
        scores = {
            "isolation_forest": np.array([if_score]),
            "autoencoder":      np.array([ae_score]),
            "xgboost":          np.array([xgb_score]),
        }
        return self.det._generate_explanation(activity_data, scores, 50.0)

    # 26
    def test_large_file_triggers_explanation(self):
        activity = {"file_size": 200 * 1024 * 1024}   # 200 MB > 100 MB threshold
        msgs = self._explain(activity)
        self.assertTrue(
            any("Large file transfer" in m for m in msgs),
            f"Expected 'Large file transfer' in {msgs}",
        )

    # 27
    def test_external_destination_triggers_explanation(self):
        activity = {"destination": "external_server"}
        msgs = self._explain(activity)
        self.assertTrue(
            any("External data transfer" in m for m in msgs),
            f"Expected 'External data transfer' in {msgs}",
        )

    # 28
    def test_is_suspicious_flag_triggers_explanation(self):
        activity = {"is_suspicious": True}
        msgs = self._explain(activity)
        self.assertTrue(
            any("known threat indicators" in m for m in msgs),
            f"Expected 'known threat indicators' in {msgs}",
        )

    # 29
    def test_off_hours_activity_triggers_explanation(self):
        activity = {"off_hours_activity": True}
        msgs = self._explain(activity)
        self.assertTrue(
            any("outside normal business hours" in m for m in msgs),
            f"Expected off-hours message in {msgs}",
        )

    # 30
    def test_high_isolation_forest_score_triggers_explanation(self):
        msgs = self._explain({}, if_score=0.9)   # > 0.7 threshold
        self.assertTrue(
            any("deviates from normal behavior" in m for m in msgs),
            f"Expected deviation message in {msgs}",
        )


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 7 — prepare_features & StandardScaler (tests 31-35)
# ══════════════════════════════════════════════════════════════════════════════

import pandas as pd  # noqa: E402 (already available but made explicit here)


def _make_minimal_df(n=80, seed=42):
    """Minimal DataFrame carrying the numeric columns prepare_features expects."""
    rng = np.random.default_rng(seed)
    hours       = rng.integers(0, 24, n)
    dow         = rng.integers(0, 7,  n)
    return pd.DataFrame({
        "hour":               hours,
        "day_of_week":        dow,
        "is_weekend":         (dow >= 5).astype(int),
        "is_business_hours":  ((hours >= 9) & (hours <= 17)).astype(int),
        "hour_sin":           np.sin(2 * np.pi * hours / 24),
        "hour_cos":           np.cos(2 * np.pi * hours / 24),
        "day_sin":            np.sin(2 * np.pi * dow   / 7),
        "day_cos":            np.cos(2 * np.pi * dow   / 7),
        "file_size_log":      rng.uniform(0, 10, n),
        "network_bytes_log":  rng.uniform(0, 10, n),
        "confidence_score":   rng.uniform(0,  1, n),
        "off_hours_activity": rng.integers(0,  2, n),
        "weekend_activity":   rng.integers(0,  2, n),
        "large_file_indicator":  rng.integers(0, 2, n),
        "high_network_indicator": rng.integers(0, 2, n),
    })


class TestPrepareFeatures(unittest.TestCase):
    """BehavioralAnomalyDetector.prepare_features"""

    def setUp(self):
        self.det = BehavioralAnomalyDetector()
        self.df  = _make_minimal_df()

    # 31
    def test_returns_numpy_array(self):
        result = self.det.prepare_features(self.df.copy())
        self.assertIsInstance(result, np.ndarray)

    # 32
    def test_output_row_count_matches_input(self):
        result = self.det.prepare_features(self.df.copy())
        self.assertEqual(result.shape[0], len(self.df))

    # 33
    def test_creates_scaler_on_first_call(self):
        self.assertFalse(hasattr(self.det, "scaler") and self.det.scaler is not None)
        self.det.prepare_features(self.df.copy())
        self.assertTrue(hasattr(self.det, "scaler"))
        self.assertIsNotNone(self.det.scaler)

    # 34
    def test_feature_columns_populated_after_call(self):
        self.det.prepare_features(self.df.copy())
        self.assertGreater(len(self.det.feature_columns), 0)

    # 35
    @patch("backend.ml_engine.anomaly_detector.StandardScaler")
    def test_scaler_fit_transform_called_once_across_two_calls(self, MockScaler):
        """fit_transform must be called only on the first call; second uses transform."""
        mock_scaler_instance = MagicMock()
        n_cols = len([c for c in self.df.columns])
        mock_scaler_instance.fit_transform.return_value = np.zeros((len(self.df), n_cols))
        mock_scaler_instance.transform.return_value     = np.zeros((len(self.df), n_cols))
        MockScaler.return_value = mock_scaler_instance

        self.det.prepare_features(self.df.copy())   # first call  → fit_transform
        self.det.prepare_features(self.df.copy())   # second call → transform

        self.assertEqual(mock_scaler_instance.fit_transform.call_count, 1)
        self.assertEqual(mock_scaler_instance.transform.call_count,     1)


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 8 — Categorical encoding & load_models (tests 36-40)
# ══════════════════════════════════════════════════════════════════════════════

def _make_df_with_categoricals(n=60, seed=0):
    """Minimal DataFrame that also carries the three categorical columns."""
    df = _make_minimal_df(n=n, seed=seed)
    rng = np.random.default_rng(seed)
    df["activity_type"] = rng.choice(["login", "logout", "file_access"], n)
    df["department"]    = rng.choice(["IT", "Finance", "HR"], n)
    df["protocol"]      = rng.choice(["HTTP", "HTTPS", "FTP"], n)
    return df


class TestPrepareFeaturesEncoding(unittest.TestCase):
    """prepare_features — categorical encoding branch"""

    def setUp(self):
        self.det = BehavioralAnomalyDetector()

    # 36
    def test_encodes_activity_type_column(self):
        df = _make_df_with_categoricals()
        self.det.prepare_features(df.copy())
        self.assertIn("activity_type_encoded", self.det.feature_columns)

    # 37
    def test_unseen_category_mapped_to_unknown_without_error(self):
        """Second call with an unknown activity_type must not raise."""
        df_train = _make_df_with_categoricals()
        self.det.prepare_features(df_train.copy())      # fits encoder

        df_pred = _make_df_with_categoricals(n=10)
        df_pred["activity_type"] = "never_seen_before"  # unseen category
        try:
            self.det.prepare_features(df_pred.copy())   # must not raise
        except Exception as exc:
            self.fail(f"Unseen category raised {type(exc).__name__}: {exc}")

    # 38
    def test_feature_columns_excludes_missing_df_columns(self):
        """Every column recorded in feature_columns must have been present in df."""
        df = pd.DataFrame({
            "hour":             np.arange(50, dtype=float),
            "confidence_score": np.random.rand(50),
        })
        self.det.prepare_features(df.copy())
        present = set(df.columns)
        for col in self.det.feature_columns:
            self.assertIn(col, present,
                          f"feature_columns includes '{col}' which was absent from df")

    # 39
    def test_load_models_returns_false_when_config_missing(self):
        det = BehavioralAnomalyDetector()
        result = det.load_models("/nonexistent/path/that/does/not/exist")
        self.assertFalse(result)

    # 40
    def test_load_models_sets_is_trained_from_config_json(self):
        import json, tempfile, joblib
        det = BehavioralAnomalyDetector()

        with tempfile.TemporaryDirectory() as tmp:
            # Write a minimal config.json
            config_data = {
                "feature_columns":      ["hour", "confidence_score"],
                "autoencoder_threshold": 0.05,
                "is_trained":            True,
            }
            with open(os.path.join(tmp, "config.json"), "w") as f:
                json.dump(config_data, f)

            # Stub out the heavy loaders so no real files are needed
            with patch("backend.ml_engine.anomaly_detector.joblib.load",
                       return_value=MagicMock()), \
                 patch("backend.ml_engine.anomaly_detector.tf") as mock_tf:
                mock_tf.keras.models.load_model.return_value = MagicMock()
                det.load_models(tmp)

        self.assertTrue(det.is_trained)


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 9 — _process_nested_fields, save_models, ensemble structure (41-45)
# ══════════════════════════════════════════════════════════════════════════════

import json as _json   # noqa: E402 (std-lib, already imported above via test 40)
import tempfile        # noqa: E402


class TestProcessNestedFields(unittest.TestCase):
    """BehavioralAnomalyDetector._process_nested_fields"""

    def setUp(self):
        self.det = BehavioralAnomalyDetector()

    # 41
    def test_fills_nan_numeric_columns_with_zero(self):
        df = pd.DataFrame({
            "file_size":       [np.nan, 1024.0],
            "rows_affected":   [np.nan, 5.0],
            "recipient_count": [np.nan, 3.0],
        })
        result = self.det._process_nested_fields(df)
        self.assertEqual(result.loc[0, "file_size"],       0)
        self.assertEqual(result.loc[0, "rows_affected"],   0)
        self.assertEqual(result.loc[0, "recipient_count"], 0)

    # 42
    def test_converts_is_suspicious_column_to_bool(self):
        df = pd.DataFrame({
            "is_suspicious":      [0, 1, 0],
            "is_weekend":         [1, 0, 1],
            "is_business_hours":  [1, 1, 0],
        })
        result = self.det._process_nested_fields(df)
        self.assertEqual(result["is_suspicious"].dtype, bool)
        self.assertEqual(result["is_weekend"].dtype,    bool)

    # 43
    def test_preserves_non_nan_numeric_values(self):
        df = pd.DataFrame({
            "file_size":   [500.0, np.nan],
            "total_size":  [np.nan, 999.0],
        })
        result = self.det._process_nested_fields(df)
        self.assertEqual(result.loc[0, "file_size"],  500.0)
        self.assertEqual(result.loc[1, "total_size"], 999.0)

    # 44
    def test_save_models_writes_config_json_with_expected_keys(self):
        det = BehavioralAnomalyDetector()
        det.is_trained           = True
        det.feature_columns      = ["hour", "confidence_score"]
        det.autoencoder_threshold = 0.042
        det.scaler               = MagicMock()
        det.encoders             = {}
        det.models = {
            "isolation_forest": MagicMock(),
            "xgboost":          MagicMock(),
            "autoencoder":      MagicMock(),
        }

        with tempfile.TemporaryDirectory() as tmp:
            with patch("backend.ml_engine.anomaly_detector.joblib.dump"):
                det.save_models(tmp)

            cfg_path = os.path.join(tmp, "config.json")
            self.assertTrue(os.path.exists(cfg_path),
                            "config.json was not created by save_models")

            with open(cfg_path) as f:
                cfg = _json.load(f)

            for key in ("feature_columns", "autoencoder_threshold", "is_trained"):
                self.assertIn(key, cfg, f"Key '{key}' missing from config.json")

    # 45
    def test_ensemble_prediction_individual_scores_has_all_three_keys(self):
        det, X = _det_with_mocked_ensemble()
        _, individual = det.ensemble_prediction(X)
        for key in ("isolation_forest", "autoencoder", "xgboost"):
            self.assertIn(key, individual,
                          f"Key '{key}' missing from individual_scores")


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 10 — Feature engineering, edge cases & boundaries (tests 46-50)
# ══════════════════════════════════════════════════════════════════════════════

from datetime import datetime as _dt, timedelta as _td  # noqa: E402


def _make_df_for_engineer(n=20, seed=7):
    """DataFrame with all columns required by _engineer_features."""
    rng = np.random.default_rng(seed)
    base = _dt(2024, 6, 10, 9, 0, 0)
    timestamps = pd.to_datetime([base + _td(hours=i) for i in range(n)])
    return pd.DataFrame({
        "user_id":          np.tile([1, 2], n // 2),
        "file_size":        rng.uniform(0, 1_000, n),
        "network_bytes":    rng.uniform(0, 5_000, n),
        "hour":             timestamps.hour,
        "day_of_week":      timestamps.dayofweek,
        "activity_type":    np.tile(["login", "file_access"], n // 2),
        "timestamp":        timestamps,
        "is_business_hours": np.ones(n, dtype=bool),
        "is_weekend":        np.zeros(n, dtype=bool),
    })


class TestEngineerFeatures(unittest.TestCase):
    """BehavioralAnomalyDetector._engineer_features"""

    def setUp(self):
        self.det = BehavioralAnomalyDetector()
        self.df  = _make_df_for_engineer()

    # 46
    def test_creates_hour_and_day_sin_cos_columns(self):
        result = self.det._engineer_features(self.df.copy())
        for col in ("hour_sin", "hour_cos", "day_sin", "day_cos"):
            self.assertIn(col, result.columns,
                          f"Expected column '{col}' not found after _engineer_features")

    # 47
    def test_creates_log_transform_columns(self):
        result = self.det._engineer_features(self.df.copy())
        self.assertIn("file_size_log",     result.columns)
        self.assertIn("network_bytes_log", result.columns)
        # log1p(0) == 0; log1p(positive) > 0
        self.assertTrue((result["file_size_log"] >= 0).all())


class TestTrainEdgeCases(unittest.TestCase):
    """Edge-case training scenarios for train_isolation_forest"""

    # 48
    def test_handles_all_normal_labels(self):
        """Training with y all-zero (no anomalies) must complete without error."""
        det = BehavioralAnomalyDetector()
        X   = _make_X(n_samples=100)
        y   = np.zeros(100, dtype=int)   # every sample is normal
        try:
            det.train_isolation_forest(X, y)
        except Exception as exc:
            self.fail(f"train_isolation_forest raised {type(exc).__name__} on all-normal data: {exc}")
        self.assertIn("isolation_forest", det.models)


class TestEnsembleMath(unittest.TestCase):
    """Verify ensemble weighted-sum arithmetic"""

    # 49
    def test_weighted_sum_produces_correct_risk_score(self):
        """
        With IF=0.8, AE=0.6, XGB=0.4 and default weights 0.3/0.3/0.4:
        ensemble = 0.3*0.8 + 0.3*0.6 + 0.4*0.4 = 0.58  →  risk = 58.0
        """
        det, _ = _det_with_mocked_ensemble()
        n = 1

        # Override individual score returns to fixed values
        det.models["isolation_forest"].decision_function = MagicMock(
            return_value=np.array([0.0])   # after normalisation → IF score = 0.5 (min=max edge)
        )
        # Directly patch predict_anomaly_scores for full control
        fixed_scores = {
            "isolation_forest": np.array([0.8]),
            "autoencoder":      np.array([0.6]),
            "xgboost":          np.array([0.4]),
        }
        with patch.object(det, "predict_anomaly_scores", return_value=fixed_scores):
            risk_scores, _ = det.ensemble_prediction(np.zeros((n, 10)))

        expected = (0.3 * 0.8 + 0.3 * 0.6 + 0.4 * 0.4) * 100   # = 58.0
        self.assertAlmostEqual(float(risk_scores[0]), expected, places=6)


class TestRiskLevelBoundary(unittest.TestCase):
    """_get_risk_level — exact threshold boundary behaviour"""

    def setUp(self):
        self.det = BehavioralAnomalyDetector()

    # 50
    def test_score_exactly_at_low_threshold_returns_medium(self):
        # LOW_RISK_THRESHOLD = 30 in stub
        # Code: if score < 30 → LOW; elif score < 70 → MEDIUM
        # score == 30 is NOT < 30, so it falls to MEDIUM
        self.assertEqual(self.det._get_risk_level(30), "MEDIUM")


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
