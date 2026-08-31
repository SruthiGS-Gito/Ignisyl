"""
Phase 2 Logical Tests — Module 2: Isolation Forest (BehavioralAnomalyDetector)
===============================================================================
Verifies *behavioural correctness*:
  1. Anomalous inputs produce higher risk scores than normal inputs
  2. Ensemble weights correctly influence the final score
  3. Risk-level thresholds (LOW / MEDIUM / HIGH) trigger at correct boundaries
  4. Explanation flags correctly identify the right threat indicators
  5. Feature preparation correctly transforms raw input before scoring

Module under test:
  backend/ml_engine/anomaly_detector.py  (BehavioralAnomalyDetector)

Run with:
    python -m unittest tests/test_logical_module2.py -v
"""

import sys
import os
import unittest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch

# ── Project root on path ──────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ── Stub heavy imports before module loads them ───────────────────────────────
_tf_stub = MagicMock()
for _mod in [
    "tensorflow", "tensorflow.keras", "tensorflow.keras.models",
    "tensorflow.keras.layers", "tensorflow.keras.optimizers",
    "tensorflow.keras.callbacks",
]:
    sys.modules.setdefault(_mod, _tf_stub)
sys.modules.setdefault("xgboost", MagicMock())

_cfg = MagicMock()
_cfg.settings.LOW_RISK_THRESHOLD    = 30
_cfg.settings.MEDIUM_RISK_THRESHOLD = 70
sys.modules.setdefault("config",        _cfg)
sys.modules.setdefault("config.config", _cfg)

from backend.ml_engine.anomaly_detector import BehavioralAnomalyDetector  # noqa: E402


# ══════════════════════════════════════════════════════════════════════════════
# Shared fixtures
# ══════════════════════════════════════════════════════════════════════════════

RNG = np.random.default_rng(42)

def _normal_data(n=300, n_features=10):
    """Tight Gaussian cluster — normal behaviour."""
    return RNG.standard_normal((n, n_features)).astype(np.float64)

def _outlier_data(n=30, n_features=10, magnitude=10.0):
    """Points far from the origin — clear statistical outliers."""
    return (RNG.standard_normal((n, n_features)) + magnitude).astype(np.float64)

def _trained_if_detector(n_normal=300, n_features=10):
    """
    Detector with only the real IsolationForest trained.
    AE and XGB are stubbed so predict_anomaly_scores() can run end-to-end.
    """
    det = BehavioralAnomalyDetector()
    X_normal = _normal_data(n=n_normal, n_features=n_features)
    y        = np.zeros(n_normal, dtype=int)
    det.train_isolation_forest(X_normal, y)

    n_total = n_normal
    ae_mock = MagicMock()
    ae_mock.predict.side_effect = lambda X, **kw: X.copy()   # zero reconstruction error
    det.models["autoencoder"]   = ae_mock
    det.autoencoder_threshold   = 1.0

    xgb_mock = MagicMock()
    xgb_mock.predict_proba.side_effect = lambda X: np.full((len(X), 2), 0.5)
    det.models["xgboost"] = xgb_mock

    det.is_trained = True
    return det


def _if_scores(det, X_batch):
    """Return the isolation-forest slice of predict_anomaly_scores."""
    return det.predict_anomaly_scores(X_batch)["isolation_forest"]


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 1 — Anomalous inputs produce higher risk scores (tests 1-5)
# ══════════════════════════════════════════════════════════════════════════════

class TestAnomalousInputsScoreHigher(unittest.TestCase):
    """
    Logical invariant: statistical outliers must receive higher anomaly
    scores than inliers when the Isolation Forest is correctly trained
    on normal data only.
    """

    def setUp(self):
        self.det      = _trained_if_detector()
        self.n_feat   = 10
        self.X_normal = _normal_data(n=100, n_features=self.n_feat)
        self.X_outlier = _outlier_data(n=30,  n_features=self.n_feat)
        # Score a mixed batch so normalisation uses the full range
        self.X_mixed   = np.vstack([self.X_normal, self.X_outlier])
        self.scores    = _if_scores(self.det, self.X_mixed)
        self.s_normal  = self.scores[:100]
        self.s_outlier = self.scores[100:]

    # 1
    def test_mean_outlier_if_score_exceeds_mean_normal_score(self):
        """
        On average, statistical outliers must score higher than inliers.
        This is the primary logical guarantee of the Isolation Forest.
        """
        self.assertGreater(
            self.s_outlier.mean(), self.s_normal.mean(),
            f"Mean outlier IF score ({self.s_outlier.mean():.4f}) should exceed "
            f"mean normal score ({self.s_normal.mean():.4f})",
        )

    # 2
    def test_raw_decision_function_lower_for_outliers(self):
        """
        IsolationForest.decision_function() returns LOWER values for
        anomalies (shorter average path length = more isolated).
        The inversion in predict_anomaly_scores() should flip this
        — so this test confirms the raw signal direction is correct
        before inversion.
        """
        raw_normal  = self.det.models["isolation_forest"].decision_function(self.X_normal)
        raw_outlier = self.det.models["isolation_forest"].decision_function(self.X_outlier)
        self.assertLess(
            raw_outlier.mean(), raw_normal.mean(),
            "Raw decision_function should be lower for outliers (shorter isolation path)",
        )

    # 3
    def test_if_scores_are_not_constant_across_varied_inputs(self):
        """
        A correctly-trained IF must assign different scores to different
        inputs — confirming the model has learned a meaningful decision
        boundary and is not degenerate.
        """
        score_variance = self.scores.var()
        self.assertGreater(
            score_variance, 1e-6,
            "IF scores have near-zero variance — model may be degenerate",
        )

    # 4
    def test_majority_of_outliers_outrank_majority_of_normals(self):
        """
        At least 75 % of outlier scores must exceed the median normal
        score — a stricter ordering check than mean comparison alone.
        """
        median_normal = np.median(self.s_normal)
        frac_above    = (self.s_outlier > median_normal).mean()
        self.assertGreaterEqual(
            frac_above, 0.75,
            f"Only {frac_above:.0%} of outliers exceeded the normal median; "
            "expected ≥ 75 %",
        )

    # 5
    def test_ensemble_with_full_if_weight_orders_outliers_above_inliers(self):
        """
        When all ensemble weight is placed on the Isolation Forest
        (weights = {IF: 1.0, AE: 0.0, XGB: 0.0}), the mean risk score
        for outliers must exceed the mean risk score for inliers —
        confirming that higher IF scores propagate correctly through
        the ensemble to the final risk score.
        """
        weights = {"isolation_forest": 1.0, "autoencoder": 0.0, "xgboost": 0.0}

        risk_normal, _  = self.det.ensemble_prediction(self.X_mixed, weights=weights)
        r_normal  = risk_normal[:100]
        r_outlier = risk_normal[100:]

        self.assertGreater(
            r_outlier.mean(), r_normal.mean(),
            "Outlier risk scores should exceed normal risk scores "
            "when IF carries 100 % of ensemble weight",
        )


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 2 — Ensemble weights correctly influence the final score (tests 6-10)
# ══════════════════════════════════════════════════════════════════════════════

class TestEnsembleWeightInfluence(unittest.TestCase):
    """
    Logical invariant: the weight assigned to each model must
    proportionally determine its contribution to the final risk score.
    Doubling a model's weight should increase that model's influence;
    zeroing it should remove it entirely.
    """

    def setUp(self):
        self.det    = _trained_if_detector()
        self.n_feat = 10
        X_normal    = _normal_data(n=100, n_features=self.n_feat)
        X_outlier   = _outlier_data(n=30,  n_features=self.n_feat)
        self.X_mixed = np.vstack([X_normal, X_outlier])

    # 6
    def test_increasing_if_weight_widens_gap_between_outlier_and_normal_scores(self):
        """
        As the IF weight increases (and other weights decrease proportionally),
        the difference between mean outlier and mean normal risk scores must grow —
        confirming that IF weight controls the strength of the IF signal.
        """
        def gap(if_w):
            other = (1.0 - if_w) / 2
            w = {"isolation_forest": if_w, "autoencoder": other, "xgboost": other}
            scores, _ = self.det.ensemble_prediction(self.X_mixed, weights=w)
            return scores[100:].mean() - scores[:100].mean()   # outlier - normal

        gap_low  = gap(0.1)
        gap_high = gap(0.9)
        self.assertGreater(
            gap_high, gap_low,
            f"Higher IF weight ({gap_high:.2f}) should widen the outlier-normal gap "
            f"compared with lower IF weight ({gap_low:.2f})",
        )

    # 7
    def test_zero_if_weight_makes_if_contribution_invisible(self):
        """
        With IF weight = 0 and both AE and XGB returning identical constant
        scores for every sample, all risk scores in the batch must be equal —
        confirming that IF's discriminative power is completely suppressed.
        """
        det = _trained_if_detector()

        # Force AE and XGB to return the same constant for every sample
        const_score = 0.4
        det.models["autoencoder"].predict.side_effect  = lambda X, **kw: X.copy()
        det.autoencoder_threshold = 1e9        # drives AE score ≈ 0
        det.models["xgboost"].predict_proba.side_effect = (
            lambda X: np.full((len(X), 2), const_score)
        )

        weights = {"isolation_forest": 0.0, "autoencoder": 0.0, "xgboost": 1.0}
        scores, _ = det.ensemble_prediction(self.X_mixed, weights=weights)

        # All scores should be identical (XGB always returns const_score)
        self.assertAlmostEqual(
            scores.max() - scores.min(), 0.0, places=6,
            msg="With IF weight=0 and constant XGB, all risk scores must be equal",
        )

    # 8
    def test_weighted_sum_math_with_fully_controlled_individual_scores(self):
        """
        Given precisely known individual model scores, the ensemble output
        must equal the exact weighted sum — verifying the arithmetic is correct.

        IF=0.6, AE=0.3, XGB=0.5 with weights 0.5 / 0.3 / 0.2:
        expected = 0.5×0.6 + 0.3×0.3 + 0.2×0.5 = 0.30 + 0.09 + 0.10 = 0.49
        risk_score = 0.49 × 100 = 49.0
        """
        det = _trained_if_detector()
        fixed = {
            "isolation_forest": np.array([0.6]),
            "autoencoder":      np.array([0.3]),
            "xgboost":          np.array([0.5]),
        }
        weights = {"isolation_forest": 0.5, "autoencoder": 0.3, "xgboost": 0.2}
        expected_risk = (0.5*0.6 + 0.3*0.3 + 0.2*0.5) * 100   # 49.0

        with patch.object(det, "predict_anomaly_scores", return_value=fixed):
            risk, _ = det.ensemble_prediction(np.zeros((1, self.n_feat)), weights=weights)

        self.assertAlmostEqual(float(risk[0]), expected_risk, places=5,
                               msg=f"Expected risk {expected_risk}, got {float(risk[0]):.5f}")

    # 9
    def test_dominant_weight_determines_ordering_when_models_disagree(self):
        """
        When IF says a sample is highly anomalous (0.9) and XGB says it
        is normal (0.1), the model with the larger weight must determine
        which direction the final score falls.
        """
        det = _trained_if_detector()
        # One sample where IF disagrees with XGB
        disagreement = {
            "isolation_forest": np.array([0.9]),
            "autoencoder":      np.array([0.5]),
            "xgboost":          np.array([0.1]),
        }

        with patch.object(det, "predict_anomaly_scores", return_value=disagreement):
            # IF dominates → high risk
            risk_if_dom, _ = det.ensemble_prediction(
                np.zeros((1, self.n_feat)),
                weights={"isolation_forest": 0.8, "autoencoder": 0.1, "xgboost": 0.1},
            )
            # XGB dominates → low risk
            risk_xgb_dom, _ = det.ensemble_prediction(
                np.zeros((1, self.n_feat)),
                weights={"isolation_forest": 0.1, "autoencoder": 0.1, "xgboost": 0.8},
            )

        self.assertGreater(
            float(risk_if_dom[0]), float(risk_xgb_dom[0]),
            "IF-dominant weighting should yield higher risk than XGB-dominant "
            "when IF and XGB disagree on the same sample",
        )

    # 10
    def test_equal_weights_produce_score_between_individual_extremes(self):
        """
        With equal weights and known individual scores IF=0.8, AE=0.2, XGB=0.5,
        the ensemble result (0.5 × 100 = 50) must lie strictly between
        the lowest individual score (20) and the highest (80) — confirming
        that no single model dominates when weights are balanced.
        """
        det = _trained_if_detector()
        fixed = {
            "isolation_forest": np.array([0.8]),
            "autoencoder":      np.array([0.2]),
            "xgboost":          np.array([0.5]),
        }
        equal_w = {"isolation_forest": 1/3, "autoencoder": 1/3, "xgboost": 1/3}

        with patch.object(det, "predict_anomaly_scores", return_value=fixed):
            risk, _ = det.ensemble_prediction(np.zeros((1, self.n_feat)), weights=equal_w)

        score = float(risk[0])
        self.assertGreater(score, 0.2 * 100,
                           "Ensemble score should exceed lowest individual (20)")
        self.assertLess(score,    0.8 * 100,
                        "Ensemble score should be below highest individual (80)")


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 3 — Risk-level thresholds trigger at correct boundaries (tests 11-15)
# ══════════════════════════════════════════════════════════════════════════════

class TestRiskLevelThresholds(unittest.TestCase):
    """
    Logical invariant: _get_risk_level() must map risk scores to the
    correct label at and around each threshold boundary.

    Config stubs (set at module level):
        LOW_RISK_THRESHOLD    = 30
        MEDIUM_RISK_THRESHOLD = 70

    Expected mapping (strict less-than comparisons in the implementation):
        score <  30  → "LOW"
        30 <= score < 70  → "MEDIUM"
        score >= 70  → "HIGH"
    """

    def setUp(self):
        # _get_risk_level() is stateless — no training needed
        self.det = BehavioralAnomalyDetector()

    # 11
    def test_score_well_below_low_threshold_returns_low(self):
        """
        A score comfortably below 30 (e.g. 10) must be classified LOW —
        confirming the LOW branch fires for clearly non-anomalous activity.
        """
        self.assertEqual(self.det._get_risk_level(10.0), "LOW")

    # 12
    def test_score_just_below_low_threshold_returns_low(self):
        """
        A score of 29.9 — one tenth of a point below the LOW boundary —
        must still return "LOW", verifying the strict-less-than boundary.
        """
        self.assertEqual(self.det._get_risk_level(29.9), "LOW")

    # 13
    def test_score_exactly_at_low_threshold_returns_medium(self):
        """
        A score of exactly 30.0 must return "MEDIUM" because the LOW
        branch uses strict less-than (<), so 30 is not LOW.
        This is the most critical boundary: off-by-one here would
        mis-classify borderline activity.
        """
        self.assertEqual(self.det._get_risk_level(30.0), "MEDIUM")

    # 14
    def test_score_exactly_at_medium_threshold_returns_high(self):
        """
        A score of exactly 70.0 must return "HIGH" because the MEDIUM
        branch uses strict less-than (<), so 70 is not MEDIUM.
        Symmetrically critical to test 13 for the upper boundary.
        """
        self.assertEqual(self.det._get_risk_level(70.0), "HIGH")

    # 15
    def test_score_well_above_medium_threshold_returns_high(self):
        """
        A score of 95 — well above 70 — must return "HIGH", confirming
        the HIGH fallback branch is reached and no upper bound clips it.
        """
        self.assertEqual(self.det._get_risk_level(95.0), "HIGH")


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 4 — Explanation flags correctly identify threat indicators (tests 16-20)
# ══════════════════════════════════════════════════════════════════════════════

class TestExplanationFlags(unittest.TestCase):
    """
    Logical invariant: _generate_explanation() must include the right
    human-readable string for each threat indicator that is present,
    and must NOT include spurious explanations for conditions that are absent.

    The method signature is:
        _generate_explanation(activity_data: Dict,
                              individual_scores: Dict[str, np.ndarray],
                              risk_score: float) -> List[str]

    Each individual_scores value is indexed as scores[model][0], so we
    supply single-element numpy arrays.
    """

    def setUp(self):
        # No training needed — method is purely logic-driven
        self.det = BehavioralAnomalyDetector()
        # Neutral scores below every threshold
        self.low_scores = {
            "isolation_forest": np.array([0.3]),
            "autoencoder":      np.array([0.3]),
            "xgboost":          np.array([0.3]),
        }

    def _explain(self, activity_data, scores=None, risk=50.0):
        return self.det._generate_explanation(
            activity_data, scores or self.low_scores, risk
        )

    # 16
    def test_high_if_score_triggers_deviation_explanation(self):
        """
        When the Isolation Forest score exceeds 0.7, the explanation must
        include the string about deviating from normal behavior — confirming
        that the IF signal is surfaced in the human-readable output.
        """
        high_if_scores = {
            "isolation_forest": np.array([0.85]),
            "autoencoder":      np.array([0.3]),
            "xgboost":          np.array([0.3]),
        }
        result = self._explain({}, scores=high_if_scores)
        self.assertIn(
            "Activity pattern significantly deviates from normal behavior",
            result,
            "High IF score (>0.7) must add the deviation explanation",
        )

    # 17
    def test_all_low_scores_and_no_flags_yields_normal_explanation(self):
        """
        When every model score is below 0.7 and no risk flags are set in
        activity_data, the explanation list must contain exactly one entry
        stating the activity appears normal — confirming the fallback branch
        fires and no spurious flags are appended.
        """
        result = self._explain({"is_suspicious": False,
                                "off_hours_activity": False,
                                "file_size": 0})
        self.assertEqual(len(result), 1,
                         "Only the fallback explanation expected; got extra flags")
        self.assertIn("Activity appears normal based on behavioral patterns",
                      result)

    # 18
    def test_is_suspicious_flag_triggers_threat_indicator_explanation(self):
        """
        When activity_data['is_suspicious'] is True, the explanation must
        contain the 'known threat indicators' string — confirming that the
        log-processor's suspicion flag propagates correctly into the explanation.
        """
        result = self._explain({"is_suspicious": True})
        self.assertIn(
            "Activity contains known threat indicators",
            result,
            "is_suspicious=True must add the threat-indicator explanation",
        )

    # 19
    def test_large_file_size_triggers_large_transfer_explanation(self):
        """
        A file_size above 100 MB (104 857 601 bytes) must produce the
        'Large file transfer detected' explanation — verifying the 100 MB
        threshold check fires at the correct byte boundary.
        """
        over_100mb = 100 * 1024 * 1024 + 1        # 1 byte over 100 MB
        result = self._explain({"file_size": over_100mb})
        self.assertIn(
            "Large file transfer detected",
            result,
            "file_size just over 100 MB must trigger the large-transfer explanation",
        )
        # Also confirm a file just under the threshold does NOT trigger it
        under_100mb = 100 * 1024 * 1024 - 1
        result_under = self._explain({"file_size": under_100mb})
        self.assertNotIn(
            "Large file transfer detected",
            result_under,
            "file_size just under 100 MB must NOT trigger the large-transfer explanation",
        )

    # 20
    def test_external_destination_triggers_external_transfer_explanation(self):
        """
        When 'external' appears anywhere in the destination string (case-
        insensitive), the explanation must include 'External data transfer
        detected' — confirming the substring check is applied correctly.
        An internal destination must not trigger the flag.
        """
        result_ext = self._explain({"destination": "external_server_42"})
        self.assertIn(
            "External data transfer detected",
            result_ext,
            "destination containing 'external' must flag an external transfer",
        )

        result_int = self._explain({"destination": "internal_share"})
        self.assertNotIn(
            "External data transfer detected",
            result_int,
            "Internal destination must NOT trigger the external-transfer explanation",
        )


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 5 — Feature preparation correctly transforms raw input (tests 21-25)
# ══════════════════════════════════════════════════════════════════════════════

class TestFeaturePreparation(unittest.TestCase):
    """
    Logical invariant: the feature-preparation pipeline must consistently
    transform raw activity data into a correctly shaped, scaled numeric matrix.

    Pipeline under test (called in sequence):
        _process_nested_fields(df) → fills NaN, casts bool columns
        _engineer_features(df)     → adds cyclical time, log, risk columns
        prepare_features(df)       → encodes categoricals, scales, returns ndarray

    All tests use a minimal DataFrame with just the columns each step needs.
    """

    # ── shared helpers ────────────────────────────────────────────────────────

    def _make_df(self, n=5, hour=10, day=1,
                 activity_type="file_access", file_size=1024.0, user_id="u1"):
        """Minimal DataFrame covering every column the pipeline touches."""
        base_ts = pd.Timestamp("2024-01-15 10:00:00")
        return pd.DataFrame({
            "user_id":           [user_id] * n,
            "timestamp":         pd.date_range(base_ts, periods=n, freq="1min"),
            "hour":              [float(hour)] * n,
            "day_of_week":       [float(day)] * n,
            "is_weekend":        [False] * n,
            "is_business_hours": [True] * n,
            "activity_type":     [activity_type] * n,
            "department":        ["engineering"] * n,
            "protocol":          ["https"] * n,
            "file_size":         [float(file_size)] * n,
            "network_bytes":     [2048.0] * n,
            "confidence_score":  [0.2] * n,
        })

    def _run_pipeline(self, det, df):
        """Run the two pre-steps that must precede prepare_features."""
        df = det._process_nested_fields(df.copy())
        df = det._engineer_features(df)
        return df

    def setUp(self):
        self.det = BehavioralAnomalyDetector()

    # 21
    def test_engineer_features_creates_cyclical_and_log_columns(self):
        """
        _engineer_features must add the four cyclical time columns
        (hour_sin/cos, day_sin/cos) and two log-transform columns
        (file_size_log, network_bytes_log) with mathematically correct values.
        """
        df = self._make_df(hour=12, day=3)
        df = self.det._process_nested_fields(df.copy())
        result = self.det._engineer_features(df)

        for col in ["hour_sin", "hour_cos", "day_sin", "day_cos",
                    "file_size_log", "network_bytes_log"]:
            self.assertIn(col, result.columns,
                          f"Expected column '{col}' in _engineer_features output")

        # Verify the cyclical math is applied correctly for hour=12
        expected_hour_sin = np.sin(2 * np.pi * 12 / 24)
        self.assertAlmostEqual(
            float(result["hour_sin"].iloc[0]), expected_hour_sin, places=10,
            msg="hour_sin must equal sin(2π × hour / 24)",
        )

        # Verify log1p transform for file_size=1024
        expected_log = np.log1p(1024.0)
        self.assertAlmostEqual(
            float(result["file_size_log"].iloc[0]), expected_log, places=10,
            msg="file_size_log must equal log1p(file_size)",
        )

    # 22
    def test_prepare_features_populates_feature_columns_and_correct_shape(self):
        """
        After calling prepare_features, det.feature_columns must be a
        non-empty list and the returned array's column count must match it —
        confirming the feature registry is kept in sync with the output matrix.
        """
        df = self._make_df(n=8)
        df = self._run_pipeline(self.det, df)
        X = self.det.prepare_features(df)

        self.assertGreater(len(self.det.feature_columns), 0,
                           "feature_columns must be populated after prepare_features")
        self.assertIsInstance(X, np.ndarray)
        self.assertEqual(
            X.shape, (8, len(self.det.feature_columns)),
            "Output row count must equal n; column count must equal feature_columns length",
        )

    # 23
    def test_scaler_is_fitted_after_first_prepare_features_call(self):
        """
        Before the first call det.scaler is absent; after the first call it
        must exist and be a fitted StandardScaler (with mean_ attribute) —
        confirming that fit_transform fires on the initial call.
        """
        det = BehavioralAnomalyDetector()
        # scaler must not exist yet
        self.assertFalse(
            hasattr(det, "scaler") and det.scaler is not None,
            "scaler should not be fitted before the first prepare_features call",
        )

        df = self._run_pipeline(det, self._make_df(n=5))
        det.prepare_features(df)

        self.assertTrue(hasattr(det, "scaler") and det.scaler is not None,
                        "scaler must be set after first prepare_features call")
        self.assertTrue(hasattr(det.scaler, "mean_"),
                        "scaler must be fitted (have mean_ attribute)")

    # 24
    def test_scaler_not_refitted_on_second_prepare_features_call(self):
        """
        The scaler must be fitted exactly once (on the first call) and then
        reused via transform on all subsequent calls.  Calling prepare_features
        a second time with different data must leave scaler.mean_ unchanged —
        confirming the 'if not hasattr scaler' guard works correctly.
        """
        det = BehavioralAnomalyDetector()

        # First call: fit the scaler on modest file sizes
        df1 = self._run_pipeline(det, self._make_df(n=6, file_size=100.0))
        det.prepare_features(df1)
        mean_after_first = det.scaler.mean_.copy()

        # Second call: very different file sizes — should NOT re-fit
        df2 = self._run_pipeline(det, self._make_df(n=6, file_size=9_999_999.0))
        det.prepare_features(df2)

        np.testing.assert_array_equal(
            det.scaler.mean_, mean_after_first,
            err_msg="Scaler mean must remain from the first fit; "
                    "second call must use transform only",
        )

    # 25
    def test_unseen_categorical_value_handled_without_error(self):
        """
        When prepare_features is called a second time with a categorical
        value not seen during the first (fitting) call, it must map the
        unknown value to 'unknown' and return a valid numpy array rather
        than raising a LabelEncoder error — verifying the unseen-category
        guard in the encoding logic.
        """
        det = BehavioralAnomalyDetector()

        # First call: fit encoder on a known activity type
        df1 = self._run_pipeline(det, self._make_df(n=5, activity_type="file_access"))
        det.prepare_features(df1)

        # Second call: category the encoder has never seen
        df2 = self._run_pipeline(
            det, self._make_df(n=3, activity_type="completely_unknown_type_xyz")
        )
        try:
            X = det.prepare_features(df2)
        except Exception as exc:
            self.fail(
                f"prepare_features raised {type(exc).__name__} on an unseen "
                f"categorical value: {exc}"
            )

        self.assertIsInstance(X, np.ndarray,
                              "Output must be a numpy array even for unseen categories")
        self.assertEqual(X.shape[0], 3,
                         "Row count must match the input DataFrame size")


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
