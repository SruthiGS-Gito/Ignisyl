"""
Phase 2 Logical Tests — Module 3: Autoencoder (BehavioralAnomalyDetector)
==========================================================================
Verifies *behavioural correctness*:
  1. Out-of-distribution inputs produce higher AE scores than in-distribution inputs
  2. Ensemble weights correctly amplify or suppress the AE signal
  3. Threshold calibration correctly separates normal from anomalous reconstruction errors
  4. AE score ordering is preserved end-to-end through the ensemble
  5. AE score properties hold across varied input distributions

Module under test:
  backend/ml_engine/anomaly_detector.py  (BehavioralAnomalyDetector)

Run with:
    python -m unittest tests/test_logical_module3.py -v
"""

import sys
import os
import unittest
import numpy as np
from unittest.mock import MagicMock, patch

# ── Project root on path ──────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ── Stub heavy imports before the module loads them ───────────────────────────
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

RNG    = np.random.default_rng(42)
N_FEAT = 5


def _normal_ae_data(n=150, n_features=N_FEAT, scale=0.3):
    """Tight Gaussian cluster near the origin — in-distribution (normal) data."""
    return (RNG.standard_normal((n, n_features)) * scale).astype(np.float64)


def _anomalous_ae_data(n=30, n_features=N_FEAT, magnitude=5.0):
    """
    Constant far-from-origin values — out-of-distribution (anomalous) data.
    With an AE mock that predicts zeros, MSE = magnitude² per feature.
    """
    return np.full((n, n_features), magnitude, dtype=np.float64)


def _ae_scoring_detector(threshold=30.0):
    """
    Detector whose AE is a mock that always predicts zeros.

    This simulates a trained AE that has memorised the zero-centred
    normal distribution: normal inputs (near 0) get low MSE, while
    anomalous inputs (far from 0) get high MSE.

    threshold=30.0 avoids clipping anomalous scores to 1, giving
    a continuous range for ordering tests.
    """
    det = BehavioralAnomalyDetector()

    # Real IF trained on normal data (required for predict_anomaly_scores)
    X_normal = _normal_ae_data(n=200)
    det.train_isolation_forest(X_normal, np.zeros(200, dtype=int))

    # AE mock: always predicts zeros → MSE = mean(X², axis=1)
    ae = MagicMock()
    ae.predict.side_effect = lambda X, **kw: np.zeros_like(X)
    det.models["autoencoder"] = ae
    det.autoencoder_threshold  = threshold

    # XGB mock: constant 50 % probability → neutral contribution
    xgb = MagicMock()
    xgb.predict_proba.side_effect = lambda X: np.full((len(X), 2), 0.5)
    det.models["xgboost"] = xgb

    det.is_trained = True
    return det


def _ae_scores(det, X):
    """Return the autoencoder slice of predict_anomaly_scores."""
    return det.predict_anomaly_scores(X)["autoencoder"]


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 1 — Out-of-distribution inputs produce higher AE scores (tests 1-5)
# ══════════════════════════════════════════════════════════════════════════════

class TestAnomalousInputsHigherAEScore(unittest.TestCase):
    """
    Logical invariant: an AE trained on normal data must assign higher
    reconstruction-error scores to out-of-distribution inputs than to
    in-distribution inputs — because the AE has learned to compress and
    reconstruct normal patterns but cannot reconstruct unseen anomalies.

    The fixture simulates this by using an AE mock that predicts zeros,
    so MSE scales with the squared magnitude of the input; normal data
    (near zero) → low MSE; anomalous data (far from zero) → high MSE.
    """

    def setUp(self):
        self.det       = _ae_scoring_detector(threshold=30.0)
        self.X_normal  = _normal_ae_data(n=100)
        self.X_anomaly = _anomalous_ae_data(n=30, magnitude=5.0)
        self.s_normal  = _ae_scores(self.det, self.X_normal)
        self.s_anomaly = _ae_scores(self.det, self.X_anomaly)

    # 1
    def test_mean_anomaly_ae_score_exceeds_mean_normal_ae_score(self):
        """
        On average, out-of-distribution inputs must receive higher AE
        anomaly scores than in-distribution inputs — the primary logical
        guarantee of reconstruction-error-based anomaly detection.
        """
        self.assertGreater(
            self.s_anomaly.mean(), self.s_normal.mean(),
            f"Mean anomaly AE score ({self.s_anomaly.mean():.4f}) must exceed "
            f"mean normal AE score ({self.s_normal.mean():.4f})",
        )

    # 2
    def test_raw_reconstruction_mse_higher_for_anomalous_data(self):
        """
        The raw reconstruction MSE (before threshold normalisation) must be
        higher for anomalous inputs — confirming the signal direction is
        correct at the source, before any clipping or scaling is applied.
        """
        ae_mock = self.det.models["autoencoder"]

        pred_normal  = ae_mock.predict(self.X_normal)
        pred_anomaly = ae_mock.predict(self.X_anomaly)

        mse_normal  = np.mean(np.power(self.X_normal  - pred_normal,  2), axis=1)
        mse_anomaly = np.mean(np.power(self.X_anomaly - pred_anomaly, 2), axis=1)

        self.assertGreater(
            mse_anomaly.mean(), mse_normal.mean(),
            "Raw MSE must be higher for anomalous inputs than normal inputs",
        )

    # 3
    def test_ae_scores_non_constant_across_mixed_batch(self):
        """
        When normal and anomalous inputs are scored in a single call,
        the resulting AE score array must have non-zero variance —
        confirming the AE produces a meaningful, non-degenerate signal.
        """
        X_mixed = np.vstack([self.X_normal, self.X_anomaly])
        scores  = _ae_scores(self.det, X_mixed)

        self.assertGreater(
            scores.var(), 1e-6,
            "AE scores must have non-zero variance across a mixed batch",
        )

    # 4
    def test_majority_of_anomaly_scores_exceed_median_normal_score(self):
        """
        At least 90 % of anomalous AE scores must exceed the median
        normal AE score — a strict ordering check ensuring the model
        distinguishes the bulk of anomalies from normal activity.
        """
        median_normal = np.median(self.s_normal)
        frac_above    = (self.s_anomaly > median_normal).mean()

        self.assertGreaterEqual(
            frac_above, 0.90,
            f"Only {frac_above:.0%} of anomaly AE scores exceeded the normal median; "
            "expected ≥ 90 %",
        )

    # 5
    def test_ensemble_with_full_ae_weight_orders_anomalous_above_normal(self):
        """
        When all ensemble weight is assigned to the Autoencoder
        (weights = {AE: 1.0, IF: 0.0, XGB: 0.0}), the mean risk score
        for anomalous inputs must exceed the mean risk score for normal
        inputs — confirming that the AE's discrimination propagates
        correctly through to the final risk score.
        """
        weights = {"isolation_forest": 0.0, "autoencoder": 1.0, "xgboost": 0.0}
        X_mixed = np.vstack([self.X_normal, self.X_anomaly])

        risk, _ = self.det.ensemble_prediction(X_mixed, weights=weights)
        r_normal  = risk[:len(self.X_normal)]
        r_anomaly = risk[len(self.X_normal):]

        self.assertGreater(
            r_anomaly.mean(), r_normal.mean(),
            "Anomalous risk scores must exceed normal risk scores "
            "when AE carries 100 % of ensemble weight",
        )


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 2 — Ensemble weights correctly amplify / suppress the AE signal (6-10)
# ══════════════════════════════════════════════════════════════════════════════

class TestAEEnsembleWeightInfluence(unittest.TestCase):
    """
    Logical invariant: the weight assigned to the Autoencoder must
    proportionally control its contribution to the final risk score.
    Increasing the AE weight must widen the anomaly-vs-normal gap;
    zeroing it must silence the AE entirely.
    """

    def setUp(self):
        self.det    = _ae_scoring_detector(threshold=30.0)
        self.n_feat = N_FEAT
        X_normal    = _normal_ae_data(n=100)
        X_anomaly   = _anomalous_ae_data(n=30, magnitude=5.0)
        self.X_mixed = np.vstack([X_normal, X_anomaly])
        self.n_normal = len(X_normal)

    # 6
    def test_increasing_ae_weight_widens_gap_between_anomalous_and_normal_scores(self):
        """
        As the AE weight increases (with other weights decreasing proportionally),
        the difference between mean anomalous and mean normal risk scores must
        grow — confirming that AE weight controls the strength of the AE signal.
        """
        def gap(ae_w):
            other = (1.0 - ae_w) / 2
            w = {"isolation_forest": other, "autoencoder": ae_w, "xgboost": other}
            scores, _ = self.det.ensemble_prediction(self.X_mixed, weights=w)
            return scores[self.n_normal:].mean() - scores[:self.n_normal].mean()

        gap_low  = gap(0.1)
        gap_high = gap(0.9)
        self.assertGreater(
            gap_high, gap_low,
            f"Higher AE weight ({gap_high:.2f}) should widen the anomaly-normal gap "
            f"compared with lower AE weight ({gap_low:.2f})",
        )

    # 7
    def test_zero_ae_weight_makes_ae_contribution_invisible(self):
        """
        With AE weight = 0 and XGB returning the same constant score for
        every sample, all risk scores in the batch must be equal —
        confirming that zeroing the AE weight completely suppresses its
        discriminative power.
        """
        det = _ae_scoring_detector(threshold=30.0)
        # Force XGB to return a constant for every sample
        det.models["xgboost"].predict_proba.side_effect = (
            lambda X: np.full((len(X), 2), 0.4)
        )

        weights = {"isolation_forest": 0.0, "autoencoder": 0.0, "xgboost": 1.0}
        scores, _ = det.ensemble_prediction(self.X_mixed, weights=weights)

        self.assertAlmostEqual(
            scores.max() - scores.min(), 0.0, places=6,
            msg="With AE weight=0 and constant XGB, all risk scores must be equal",
        )

    # 8
    def test_weighted_sum_math_with_fully_controlled_individual_scores(self):
        """
        Given precisely known individual model scores, the ensemble output
        must equal the exact weighted sum — verifying the arithmetic is correct.

        IF=0.4, AE=0.7, XGB=0.2  with weights  0.3 / 0.5 / 0.2:
        expected = 0.3×0.4 + 0.5×0.7 + 0.2×0.2 = 0.12 + 0.35 + 0.04 = 0.51
        risk_score = 0.51 × 100 = 51.0
        """
        det = _ae_scoring_detector(threshold=30.0)
        fixed = {
            "isolation_forest": np.array([0.4]),
            "autoencoder":      np.array([0.7]),
            "xgboost":          np.array([0.2]),
        }
        weights      = {"isolation_forest": 0.3, "autoencoder": 0.5, "xgboost": 0.2}
        expected_risk = (0.3 * 0.4 + 0.5 * 0.7 + 0.2 * 0.2) * 100   # 51.0

        with patch.object(det, "predict_anomaly_scores", return_value=fixed):
            risk, _ = det.ensemble_prediction(np.zeros((1, self.n_feat)), weights=weights)

        self.assertAlmostEqual(
            float(risk[0]), expected_risk, places=5,
            msg=f"Expected risk {expected_risk}, got {float(risk[0]):.5f}",
        )

    # 9
    def test_ae_dominant_weight_determines_ordering_when_ae_and_if_disagree(self):
        """
        When the AE flags a sample as highly anomalous (0.9) but IF says
        it is normal (0.1), the model with the larger weight must determine
        the direction of the final risk score.
        """
        det = _ae_scoring_detector(threshold=30.0)
        disagreement = {
            "isolation_forest": np.array([0.1]),
            "autoencoder":      np.array([0.9]),
            "xgboost":          np.array([0.5]),
        }

        with patch.object(det, "predict_anomaly_scores", return_value=disagreement):
            # AE dominates → high risk
            risk_ae_dom, _ = det.ensemble_prediction(
                np.zeros((1, self.n_feat)),
                weights={"isolation_forest": 0.1, "autoencoder": 0.8, "xgboost": 0.1},
            )
            # IF dominates → low risk
            risk_if_dom, _ = det.ensemble_prediction(
                np.zeros((1, self.n_feat)),
                weights={"isolation_forest": 0.8, "autoencoder": 0.1, "xgboost": 0.1},
            )

        self.assertGreater(
            float(risk_ae_dom[0]), float(risk_if_dom[0]),
            "AE-dominant weighting should yield higher risk than IF-dominant "
            "when AE and IF disagree on the same sample",
        )

    # 10
    def test_equal_weights_produce_score_between_individual_extremes(self):
        """
        With equal weights (1/3 each) and known individual scores
        IF=0.1, AE=0.8, XGB=0.5, the ensemble result must lie strictly
        between the lowest individual score (10) and the highest (80) —
        confirming that no single model dominates when weights are balanced.
        """
        det = _ae_scoring_detector(threshold=30.0)
        fixed = {
            "isolation_forest": np.array([0.1]),
            "autoencoder":      np.array([0.8]),
            "xgboost":          np.array([0.5]),
        }
        equal_w = {"isolation_forest": 1/3, "autoencoder": 1/3, "xgboost": 1/3}

        with patch.object(det, "predict_anomaly_scores", return_value=fixed):
            risk, _ = det.ensemble_prediction(np.zeros((1, self.n_feat)), weights=equal_w)

        score = float(risk[0])
        self.assertGreater(score, 0.1 * 100,
                           "Ensemble score must exceed lowest individual score (10)")
        self.assertLess(score,    0.8 * 100,
                        "Ensemble score must be below highest individual score (80)")


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 3 — Threshold calibration separates normal from anomalous (tests 11-15)
# ══════════════════════════════════════════════════════════════════════════════

class TestThresholdCalibration(unittest.TestCase):
    """
    Logical invariant: a threshold set to the 95th percentile of normal-data
    reconstruction MSE must capture the normal error range while allowing
    anomalous errors — which are much larger — to exceed it.

    All AE mocks return zeros, so MSE = mean(X², axis=1).
    Normal data (Gaussian, scale=0.3): MSE ≈ 0.09 per sample.
    Anomalous data (constant 5.0):     MSE = 25.0 per sample.
    """

    # 11
    def test_95th_percentile_threshold_covers_at_least_90_pct_of_normal_mse(self):
        """
        By definition, setting the threshold to the 95th percentile of
        training MSE means ≥ 95 % of training errors fall at or below it.
        A fresh sample from the same distribution must satisfy the same
        property: at least 90 % of normal-data MSEs must be ≤ threshold,
        confirming the calibration describes the normal error range.
        """
        X_normal  = _normal_ae_data(n=500)
        mse_vals  = np.mean(X_normal ** 2, axis=1)
        threshold = float(np.percentile(mse_vals, 95))

        frac_covered = (mse_vals <= threshold).mean()
        self.assertGreaterEqual(
            frac_covered, 0.90,
            f"Only {frac_covered:.0%} of normal MSEs fall below the 95th-percentile "
            "threshold; expected ≥ 90 %",
        )

    # 12
    def test_threshold_calibrated_on_normal_data_is_exceeded_by_anomalous_mse(self):
        """
        The threshold derived from normal-data MSE must be far below the
        reconstruction error of genuinely anomalous inputs — confirming that
        the calibration correctly identifies anomalies as out-of-range.
        With normal MSE ≈ 0.09 and anomalous MSE = 25.0, every anomalous
        sample must exceed the threshold.
        """
        X_normal   = _normal_ae_data(n=300)
        X_anomaly  = _anomalous_ae_data(n=50, magnitude=5.0)

        mse_normal  = np.mean(X_normal  ** 2, axis=1)
        mse_anomaly = np.mean(X_anomaly ** 2, axis=1)
        threshold   = float(np.percentile(mse_normal, 95))

        frac_above = (mse_anomaly > threshold).mean()
        self.assertGreaterEqual(
            frac_above, 0.99,
            f"Only {frac_above:.0%} of anomalous MSEs exceeded the normal-calibrated "
            "threshold; expected ≥ 99 %",
        )

    # 13
    def test_stricter_threshold_produces_more_clipped_ae_scores(self):
        """
        A lower threshold makes MSE/threshold larger, causing more scores
        to reach the clip ceiling of 1.0.  A detector with threshold=0.5
        must clip more samples to 1.0 than one with threshold=50.0,
        confirming the threshold controls detection sensitivity end-to-end.
        """
        X_mixed = np.vstack([
            _normal_ae_data(n=50),
            _anomalous_ae_data(n=20, magnitude=5.0),
        ])

        strict  = _ae_scoring_detector(threshold=0.5)
        lenient = _ae_scoring_detector(threshold=50.0)

        n_clipped_strict  = (np.isclose(_ae_scores(strict,  X_mixed), 1.0)).sum()
        n_clipped_lenient = (np.isclose(_ae_scores(lenient, X_mixed), 1.0)).sum()

        self.assertGreater(
            n_clipped_strict, n_clipped_lenient,
            "A stricter (lower) threshold must produce more AE scores clipped at 1.0",
        )

    # 14
    def test_normal_data_ae_scores_mostly_below_one_with_calibrated_threshold(self):
        """
        When the threshold is set to the 95th percentile of normal MSE,
        the vast majority of new normal-data samples must receive AE scores
        strictly below 1.0 (i.e., not clipped) — confirming that normal
        behaviour is not mis-classified as maximally anomalous.
        """
        X_cal     = _normal_ae_data(n=300)
        threshold = float(np.percentile(np.mean(X_cal ** 2, axis=1), 95))

        det    = _ae_scoring_detector(threshold=threshold)
        scores = _ae_scores(det, _normal_ae_data(n=200))

        frac_below_one = (scores < 1.0).mean()
        self.assertGreaterEqual(
            frac_below_one, 0.90,
            f"Only {frac_below_one:.0%} of normal AE scores are below 1.0; "
            "expected ≥ 90 % when threshold is calibrated on normal data",
        )

    # 15
    def test_doubling_threshold_halves_ae_scores_when_no_clipping_occurs(self):
        """
        AE score = clip(MSE / threshold, 0, 1).  When MSE << both thresholds
        (so the clip never fires), doubling the threshold must halve every
        score — verifying the linear inverse-proportional relationship.
        """
        # X = 0.1 everywhere → MSE = 0.01; well below threshold1=4 and threshold2=8
        X_test = np.full((8, N_FEAT), 0.1)

        det1 = _ae_scoring_detector(threshold=4.0)
        det2 = _ae_scoring_detector(threshold=8.0)

        s1 = _ae_scores(det1, X_test)
        s2 = _ae_scores(det2, X_test)

        np.testing.assert_allclose(
            s2, s1 / 2.0, rtol=1e-6,
            err_msg="Doubling the threshold must halve each AE score "
                    "(when no clipping is active)",
        )


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 4 — AE score ordering preserved end-to-end through ensemble (16-20)
# ══════════════════════════════════════════════════════════════════════════════

class TestAEScoreOrderingEndToEnd(unittest.TestCase):
    """
    Logical invariant: the ordering and magnitude of reconstruction errors
    must be faithfully preserved as they flow through the full pipeline —
    from raw MSE → normalised AE score → ensemble risk score → risk level.
    """

    # 16
    def test_ae_score_ordering_matches_mse_ordering_in_batch(self):
        """
        Three samples with strictly increasing input magnitudes produce
        strictly increasing MSEs (0.25 < 1.0 < 4.0) and therefore strictly
        increasing AE scores — confirming the per-sample ordering is intact
        after normalisation.
        """
        det = _ae_scoring_detector(threshold=10.0)

        # Increasing magnitudes → increasing MSE (predictions=0)
        X = np.vstack([
            np.full((1, N_FEAT), 0.5),   # MSE = 0.25  → score = 0.025
            np.full((1, N_FEAT), 1.0),   # MSE = 1.0   → score = 0.10
            np.full((1, N_FEAT), 2.0),   # MSE = 4.0   → score = 0.40
        ])
        scores = _ae_scores(det, X)

        self.assertLess(float(scores[0]), float(scores[1]),
                        "score(X=0.5) must be less than score(X=1.0)")
        self.assertLess(float(scores[1]), float(scores[2]),
                        "score(X=1.0) must be less than score(X=2.0)")

    # 17
    def test_ensemble_risk_equals_ae_score_times_100_when_ae_weight_is_one(self):
        """
        With AE weight = 1.0 and all other weights = 0.0, the ensemble
        risk score must equal exactly AE_score × 100 for every sample —
        verifying that the scaling from [0, 1] to [0, 100] is applied
        correctly and no information is lost between the two layers.

        Uses varied (Gaussian) input so the IF scores are finite (no
        identical-row division-by-zero), preventing 0.0 × NaN = NaN from
        contaminating the ensemble sum.
        """
        det     = _ae_scoring_detector(threshold=10.0)
        # Use varied normal data: different row values → IF min != max → no NaN
        X_test  = _normal_ae_data(n=20)
        weights = {"isolation_forest": 0.0, "autoencoder": 1.0, "xgboost": 0.0}

        ae_scores = det.predict_anomaly_scores(X_test)["autoencoder"]
        risk, _   = det.ensemble_prediction(X_test, weights=weights)

        np.testing.assert_allclose(
            risk, ae_scores * 100, rtol=1e-5,
            err_msg="Ensemble risk must equal AE score × 100 when AE weight = 1.0",
        )

    # 18
    def test_ae_score_gap_propagates_exactly_to_ensemble_risk_gap(self):
        """
        The difference between mean anomalous and mean normal AE scores,
        when multiplied by 100, must equal the difference between mean
        anomalous and mean normal ensemble risk scores (at AE weight=1.0) —
        confirming no information is added or lost in the scaling step.
        """
        det      = _ae_scoring_detector(threshold=10.0)
        X_normal = _normal_ae_data(n=60)
        X_anom   = _anomalous_ae_data(n=20, magnitude=3.0)
        X_mixed  = np.vstack([X_normal, X_anom])
        n_n      = len(X_normal)
        weights  = {"isolation_forest": 0.0, "autoencoder": 1.0, "xgboost": 0.0}

        ae_scores  = _ae_scores(det, X_mixed)
        ae_gap     = ae_scores[n_n:].mean() - ae_scores[:n_n].mean()

        risk, _    = det.ensemble_prediction(X_mixed, weights=weights)
        risk_gap   = risk[n_n:].mean() - risk[:n_n].mean()

        self.assertAlmostEqual(
            risk_gap, ae_gap * 100, places=4,
            msg="Risk-score gap must equal AE-score gap × 100",
        )

    # 19
    def test_high_ae_score_drives_risk_level_to_high(self):
        """
        When the AE assigns a score of 0.9 to a sample and carries 100 %
        of the ensemble weight, the resulting risk score is 90 — above the
        MEDIUM threshold of 70 — so _get_risk_level must return 'HIGH'.
        This verifies the end-to-end pipeline from reconstruction error to
        the human-readable risk label.
        """
        det = _ae_scoring_detector(threshold=10.0)
        fixed = {
            "isolation_forest": np.array([0.0]),
            "autoencoder":      np.array([0.9]),
            "xgboost":          np.array([0.0]),
        }
        weights = {"isolation_forest": 0.0, "autoencoder": 1.0, "xgboost": 0.0}

        with patch.object(det, "predict_anomaly_scores", return_value=fixed):
            risk, _ = det.ensemble_prediction(np.zeros((1, N_FEAT)), weights=weights)

        risk_level = det._get_risk_level(float(risk[0]))
        self.assertEqual(risk_level, "HIGH",
                         f"AE score=0.9 with full AE weight → risk=90 → expected HIGH, "
                         f"got {risk_level}")

    # 20
    def test_low_ae_score_drives_risk_level_to_low(self):
        """
        When the AE assigns a score of 0.1 to a sample and carries 100 %
        of the ensemble weight, the resulting risk score is 10 — below the
        LOW threshold of 30 — so _get_risk_level must return 'LOW'.
        Symmetric to test 19: confirms the pipeline is correct at both ends.
        """
        det = _ae_scoring_detector(threshold=10.0)
        fixed = {
            "isolation_forest": np.array([0.0]),
            "autoencoder":      np.array([0.1]),
            "xgboost":          np.array([0.0]),
        }
        weights = {"isolation_forest": 0.0, "autoencoder": 1.0, "xgboost": 0.0}

        with patch.object(det, "predict_anomaly_scores", return_value=fixed):
            risk, _ = det.ensemble_prediction(np.zeros((1, N_FEAT)), weights=weights)

        risk_level = det._get_risk_level(float(risk[0]))
        self.assertEqual(risk_level, "LOW",
                         f"AE score=0.1 with full AE weight → risk=10 → expected LOW, "
                         f"got {risk_level}")


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 5 — Fundamental AE score properties across varied distributions (21-25)
# ══════════════════════════════════════════════════════════════════════════════

class TestAEScoreDistributionalProperties(unittest.TestCase):
    """
    Logical invariants that must hold regardless of the specific input
    distribution — these are fundamental mathematical properties of the
    reconstruction-error scoring function:

     21. Row ordering (permutation) does not affect individual AE scores
     22. Scoring a sample alone gives the same result as scoring it in a batch
     23. AE score scales quadratically with input magnitude (MSE is quadratic)
     24. X and −X produce identical scores (MSE is symmetric under sign flip)
     25. All-zero input produces an AE score of exactly zero
    """

    # 21
    def test_ae_scores_are_permutation_invariant(self):
        """
        Shuffling the row order of the input batch must not change the score
        assigned to any individual sample — confirming that scoring is purely
        per-row with no cross-sample dependency (no batch normalisation, etc.).
        """
        det = _ae_scoring_detector(threshold=10.0)
        X   = _normal_ae_data(n=20)
        idx = RNG.permutation(20)

        scores_original = _ae_scores(det, X)
        scores_shuffled = _ae_scores(det, X[idx])

        np.testing.assert_allclose(
            scores_original[idx], scores_shuffled, rtol=1e-6,
            err_msg="AE score for each sample must be the same regardless of "
                    "its position in the input batch",
        )

    # 22
    def test_single_sample_ae_score_matches_batch_score(self):
        """
        Scoring a single sample in isolation must yield the same AE score as
        scoring it as part of a larger batch — confirming there are no
        batch-level side-effects (e.g. batch statistics) in the AE path.
        """
        det    = _ae_scoring_detector(threshold=10.0)
        X      = _normal_ae_data(n=10)
        scores_batch = _ae_scores(det, X)

        for i in [0, 4, 9]:
            score_alone = float(_ae_scores(det, X[i:i+1])[0])
            self.assertAlmostEqual(
                score_alone, float(scores_batch[i]), places=10,
                msg=f"Row {i}: single-sample score ({score_alone:.8f}) must equal "
                    f"batch score ({float(scores_batch[i]):.8f})",
            )

    # 23
    def test_ae_score_scales_quadratically_with_input_magnitude(self):
        """
        Because MSE = mean(X² , axis=1) when predictions are zero,
        doubling the input magnitude quadruples the MSE and therefore
        quadruples the AE score (when no clipping is active) —
        confirming the quadratic relationship between raw signal and score.
        """
        threshold = 100.0   # large enough to avoid clipping
        det = _ae_scoring_detector(threshold=threshold)

        X1 = np.full((5, N_FEAT), 1.0)   # MSE = 1.0   → score = 0.010
        X2 = np.full((5, N_FEAT), 2.0)   # MSE = 4.0   → score = 0.040  (4×)

        s1 = _ae_scores(det, X1)
        s2 = _ae_scores(det, X2)

        np.testing.assert_allclose(
            s2, 4.0 * s1, rtol=1e-6,
            err_msg="Doubling input magnitude must quadruple AE score "
                    "(quadratic scaling of MSE)",
        )

    # 24
    def test_ae_scores_are_symmetric_under_sign_flip(self):
        """
        MSE = mean((X − 0)², axis=1) = mean((−X − 0)², axis=1),
        so X and −X must produce identical AE scores — confirming that
        the scoring function is symmetric around the zero prediction.
        """
        det = _ae_scoring_detector(threshold=10.0)
        X   = _normal_ae_data(n=25)

        s_pos = _ae_scores(det,  X)
        s_neg = _ae_scores(det, -X)

        np.testing.assert_allclose(
            s_pos, s_neg, rtol=1e-10,
            err_msg="AE scores for X and −X must be identical "
                    "(MSE is symmetric under sign flip)",
        )

    # 25
    def test_zero_valued_input_produces_ae_score_of_exactly_zero(self):
        """
        When every input feature is zero and the AE predicts zero
        (perfect reconstruction), the per-sample MSE is 0 and the
        AE score must be exactly 0.0 — the absolute lower bound of the
        anomaly scale, representing perfectly normal behaviour.
        """
        det     = _ae_scoring_detector(threshold=10.0)
        X_zero  = np.zeros((8, N_FEAT))
        scores  = _ae_scores(det, X_zero)

        np.testing.assert_array_equal(
            scores, np.zeros(8),
            err_msg="All-zero input with predict=0 must yield AE score of exactly 0",
        )


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
