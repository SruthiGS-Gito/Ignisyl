"""
Phase 1 Technical Tests — Module 3: Autoencoder (BehavioralAnomalyDetector)
=============================================================================
Verifies the autoencoder-specific surfaces of BehavioralAnomalyDetector:

  • train_autoencoder  — architecture config, normal-only training, threshold
  • Reconstruction error calculation — MSE formula, perfect/worst-case cases
  • AE score normalisation and clipping in predict_anomaly_scores

Module under test:
  backend/ml_engine/anomaly_detector.py  (BehavioralAnomalyDetector)

Run with:
    python -m unittest tests/test_autoencoder.py -v
"""

import sys
import os
import unittest
import numpy as np
from unittest.mock import MagicMock, patch, call

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

RNG = np.random.default_rng(0)
N_FEAT = 5


def _make_Xy(n_normal=100, n_anom=20, n_features=N_FEAT, fill_normal=0.0, fill_anom=999.0):
    """
    Return (X, y) where normal rows are fill_normal and anomalous rows
    are fill_anom — making it easy to verify which rows were used.
    """
    X_n = np.full((n_normal, n_features), fill_normal, dtype=np.float64)
    X_a = np.full((n_anom,   n_features), fill_anom,   dtype=np.float64)
    X   = np.vstack([X_n, X_a])
    y   = np.array([0] * n_normal + [1] * n_anom, dtype=int)
    return X, y


def _ae_mock(reconstruction="perfect", threshold=1.0):
    """
    Return (det, ae_mock) where the detector has a trained IF stub,
    a stubbed XGB, and an AE mock whose prediction strategy is controlled.

    reconstruction='perfect'  → predict returns X.copy()  (zero MSE)
    reconstruction='zeros'    → predict returns zeros      (maximum MSE)
    """
    det = BehavioralAnomalyDetector()

    # ── Real IF (trained on tight normal data) ────────────────────────────────
    from sklearn.ensemble import IsolationForest
    X_normal = RNG.standard_normal((100, N_FEAT))
    y_normal = np.zeros(100, dtype=int)
    det.train_isolation_forest(X_normal, y_normal)

    # ── AE mock ───────────────────────────────────────────────────────────────
    ae = MagicMock()
    if reconstruction == "perfect":
        ae.predict.side_effect = lambda X, **kw: X.copy()
    else:
        ae.predict.side_effect = lambda X, **kw: np.zeros_like(X)
    det.models["autoencoder"] = ae
    det.autoencoder_threshold = threshold

    # ── XGB mock ─────────────────────────────────────────────────────────────
    xgb = MagicMock()
    xgb.predict_proba.side_effect = lambda X: np.full((len(X), 2), 0.5)
    det.models["xgboost"] = xgb

    det.is_trained = True
    return det, ae


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 1 — Config, training surface, reconstruction math (tests 1-5)
# ══════════════════════════════════════════════════════════════════════════════

class TestAutoencoderConfigAndTraining(unittest.TestCase):
    """
    Tests covering:
      1. Default configuration values stored in det.config['autoencoder']
      2. train_autoencoder trains only on normal rows (y == 0)
      3. autoencoder_threshold set to 95th-percentile of training MSE
      4. Perfect reconstruction produces AE score of 0 in predict_anomaly_scores
      5. Extreme reconstruction error (predictions = 0, tiny threshold) clips to 1
    """

    # 1
    def test_autoencoder_config_default_values(self):
        """
        The autoencoder sub-config must carry the exact hyperparameter defaults
        used to build and train the model so that architecture and training
        behaviour are reproducible without external configuration.
        """
        det = BehavioralAnomalyDetector()
        cfg = det.config["autoencoder"]
        self.assertEqual(cfg["encoding_dim"],  32)
        self.assertEqual(cfg["epochs"],       100)
        self.assertEqual(cfg["batch_size"],    32)
        self.assertAlmostEqual(cfg["learning_rate"], 0.001, places=6,
                               msg="Default learning rate must be 0.001")

    # 2
    def test_train_autoencoder_fits_only_on_normal_samples(self):
        """
        train_autoencoder must split X into normal (y==0) rows before
        calling model.fit — anomalous rows (y==1) must never be included
        in the training set, because the AE learns the normal distribution
        and measures deviation from it.

        We use fill_anom=999 so any anomalous row that leaked into fit
        would show up as a value of 999 in the argument matrix.
        """
        det = BehavioralAnomalyDetector()
        X, y = _make_Xy(n_normal=100, n_anom=20, fill_normal=1.0, fill_anom=999.0)

        mock_ae = MagicMock()
        # predict must return an ndarray so the MSE calculation doesn't crash
        mock_ae.predict.side_effect = lambda X, **kw: np.zeros_like(X)

        with patch("backend.ml_engine.anomaly_detector.Model", return_value=mock_ae):
            det.train_autoencoder(X, y)

        # First positional arg of fit() is X_train
        fit_X = mock_ae.fit.call_args[0][0]

        # No anomalous row (999.0) must appear in X_train
        self.assertFalse(
            np.any(fit_X == 999.0),
            "Anomalous rows (fill value 999) must not appear in the autoencoder fit call",
        )
        # Training rows must be a subset of the normal rows (≤ 100)
        self.assertLessEqual(fit_X.shape[0], 100,
                             "Fit arg row count must not exceed the number of normal samples")
        self.assertGreater(fit_X.shape[0], 0,
                           "Fit arg must be non-empty")

    # 3
    def test_autoencoder_threshold_is_95th_percentile_of_training_mse(self):
        """
        After training, autoencoder_threshold must equal the 95th percentile
        of per-sample reconstruction MSE on X_train.

        We control the reconstruction by returning zeros from predict(),
        so MSE per sample = mean(X_train^2, axis=1).
        With X_normal = 3.0 everywhere, MSE = 9.0 for every sample,
        giving percentile(..., 95) = 9.0.
        """
        det = BehavioralAnomalyDetector()
        n_normal, n_anom = 50, 10
        X, y = _make_Xy(n_normal=n_normal, n_anom=n_anom,
                         fill_normal=3.0, fill_anom=0.0)

        mock_ae = MagicMock()
        # Predict zeros → reconstruction error = input^2 per element = 9.0 mean per row
        mock_ae.predict.side_effect = lambda X, **kw: np.zeros_like(X)

        with patch("backend.ml_engine.anomaly_detector.Model", return_value=mock_ae):
            det.train_autoencoder(X, y)

        # Every X_train row is 3.0, predictions are 0.0
        # MSE per sample = mean((3-0)^2 across N_FEAT) = 9.0
        # 95th percentile of a constant array = 9.0
        self.assertAlmostEqual(
            det.autoencoder_threshold, 9.0, places=6,
            msg="autoencoder_threshold must be the 95th percentile of training MSE",
        )

    # 4
    def test_perfect_reconstruction_yields_zero_ae_score(self):
        """
        When the autoencoder reproduces its input exactly (predictions == X),
        the per-sample MSE is 0, giving an AE anomaly score of 0/threshold = 0.
        This confirms the lower-bound behaviour: normal activity → no AE signal.
        """
        det, _ = _ae_mock(reconstruction="perfect", threshold=1.0)
        X_test  = RNG.standard_normal((20, N_FEAT))
        scores  = det.predict_anomaly_scores(X_test)

        np.testing.assert_allclose(
            scores["autoencoder"], 0.0, atol=1e-10,
            err_msg="Perfect reconstruction must produce AE score of exactly 0",
        )

    # 5
    def test_extreme_reconstruction_error_clips_ae_score_to_one(self):
        """
        When predictions are all zeros and the threshold is near zero,
        the raw score (MSE / threshold) greatly exceeds 1 — the clip
        in predict_anomaly_scores must cap it at 1.0.
        This confirms the upper-bound behaviour: catastrophic deviation
        → maximum AE anomaly score of 1.0.
        """
        det, _ = _ae_mock(reconstruction="zeros", threshold=1e-9)
        # X with non-zero values → large MSE relative to tiny threshold
        X_test = np.ones((10, N_FEAT), dtype=np.float64) * 5.0
        scores = det.predict_anomaly_scores(X_test)

        np.testing.assert_array_equal(
            scores["autoencoder"],
            np.ones(10),
            err_msg="AE scores must be clipped to 1.0 when raw score >> 1",
        )


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 2 — Architecture wiring, training split, and per-sample scoring (6-10)
# ══════════════════════════════════════════════════════════════════════════════

class TestAutoencoderArchitectureAndScoring(unittest.TestCase):
    """
    Tests covering:
      6. Compiled model is stored in det.models['autoencoder'] after training
      7. EarlyStopping is configured with the correct parameters
      8. 80/20 train/val split is applied to the normal-only data
      9. Known reconstruction offset produces a mathematically exact AE score
     10. Per-sample MSE: each row in a batch receives its own independent score
    """

    # 6
    def test_trained_model_stored_in_models_dict(self):
        """
        After train_autoencoder completes, the compiled Keras model must be
        accessible as det.models['autoencoder'] — confirming that the model
        reference is persisted for later use in predict_anomaly_scores.
        """
        det = BehavioralAnomalyDetector()
        X, y = _make_Xy(n_normal=50, n_anom=10)

        mock_ae = MagicMock()
        mock_ae.predict.side_effect = lambda X, **kw: np.zeros_like(X)

        with patch("backend.ml_engine.anomaly_detector.Model", return_value=mock_ae):
            det.train_autoencoder(X, y)

        self.assertIn("autoencoder", det.models,
                      "det.models must contain 'autoencoder' key after training")
        self.assertIs(det.models["autoencoder"], mock_ae,
                      "Stored model must be the compiled Keras model returned by Model()")

    # 7
    def test_early_stopping_configured_with_correct_parameters(self):
        """
        train_autoencoder must create an EarlyStopping callback that monitors
        'val_loss' with patience=10 and restore_best_weights=True — matching
        the architectural specification and preventing over-fitting.
        """
        det = BehavioralAnomalyDetector()
        X, y = _make_Xy(n_normal=50, n_anom=10)

        mock_ae = MagicMock()
        mock_ae.predict.side_effect = lambda X, **kw: np.zeros_like(X)

        with patch("backend.ml_engine.anomaly_detector.Model", return_value=mock_ae), \
             patch("backend.ml_engine.anomaly_detector.EarlyStopping") as mock_es:
            det.train_autoencoder(X, y)

        mock_es.assert_called_once_with(
            monitor="val_loss",
            patience=10,
            restore_best_weights=True,
        )

    # 8
    def test_train_autoencoder_uses_80_20_train_val_split(self):
        """
        train_autoencoder must split the normal data with test_size=0.2,
        giving 80 % to training and 20 % to validation.  With 100 normal
        samples the fit() call receives 80 rows (X_train) and the
        validation_data kwarg receives the remaining 20 (X_val).
        """
        det = BehavioralAnomalyDetector()
        n_normal = 100
        X, y = _make_Xy(n_normal=n_normal, n_anom=20)

        mock_ae = MagicMock()
        mock_ae.predict.side_effect = lambda X, **kw: np.zeros_like(X)

        with patch("backend.ml_engine.anomaly_detector.Model", return_value=mock_ae):
            det.train_autoencoder(X, y)

        kwargs    = mock_ae.fit.call_args[1]
        X_train   = mock_ae.fit.call_args[0][0]
        X_val     = kwargs["validation_data"][0]

        expected_train = int(n_normal * 0.8)   # 80
        expected_val   = n_normal - expected_train  # 20

        self.assertEqual(X_train.shape[0], expected_train,
                         f"X_train must have {expected_train} rows (80 % of {n_normal} normal)")
        self.assertEqual(X_val.shape[0], expected_val,
                         f"X_val must have {expected_val} rows (20 % of {n_normal} normal)")

    # 9
    def test_known_offset_produces_exact_ae_score(self):
        """
        With predictions = X + 0.5 and threshold = 1.0, the reconstruction
        MSE per sample is mean(0.5^2, ...) = 0.25, giving an AE score of
        0.25 / 1.0 = 0.25.  This pins down the exact arithmetic of the
        normalised reconstruction-error formula.
        """
        det, ae = _ae_mock(reconstruction="perfect", threshold=1.0)
        ae.predict.side_effect  = lambda X, **kw: X + 0.5   # constant offset
        det.autoencoder_threshold = 1.0

        X_test = np.ones((6, N_FEAT))
        scores = det.predict_anomaly_scores(X_test)

        # ae_mse  = mean((X - (X+0.5))^2, axis=1) = mean(0.25 per feature) = 0.25
        # ae_norm = clip(0.25 / 1.0, 0, 1)        = 0.25
        np.testing.assert_allclose(
            scores["autoencoder"], 0.25, atol=1e-10,
            err_msg="AE score must equal mean(offset^2) / threshold = 0.25",
        )

    # 10
    def test_ae_score_is_computed_independently_per_sample(self):
        """
        Each row in the input batch must receive its own AE score based solely
        on its own reconstruction error — confirming the mean is taken across
        features (axis=1), not globally across the batch.

        Row 0: X = [1, …]  → MSE = 1.0  → score = 1.0 / 4.0 = 0.25
        Row 1: X = [2, …]  → MSE = 4.0  → score = 4.0 / 4.0 = 1.0
        (predictions = 0 for all; threshold = 4.0)
        """
        det, ae = _ae_mock(reconstruction="zeros", threshold=4.0)
        det.autoencoder_threshold = 4.0

        X_test        = np.zeros((2, N_FEAT))
        X_test[0, :]  = 1.0   # MSE = 1.0 → score = 0.25
        X_test[1, :]  = 2.0   # MSE = 4.0 → score = 1.0

        scores = det.predict_anomaly_scores(X_test)
        ae_scores = scores["autoencoder"]

        self.assertAlmostEqual(float(ae_scores[0]), 0.25, places=10,
                               msg="Row-0 score must reflect its own MSE (0.25)")
        self.assertAlmostEqual(float(ae_scores[1]), 1.0,  places=10,
                               msg="Row-1 score must reflect its own MSE (clipped to 1.0)")


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 3 — Training call contract and score linearity (tests 11-15)
# ══════════════════════════════════════════════════════════════════════════════

class TestAutoencoderTrainingCallContract(unittest.TestCase):
    """
    Tests covering the exact call signature of model.fit() and the
    linear relationship between reconstruction error and AE score:

     11. fit() receives X_train as BOTH input and target (autoencoder pattern)
     12. fit() is called with the epochs and batch_size from det.config
     13. fit() is called with the EarlyStopping instance in callbacks
     14. MSE exactly equal to threshold → AE score = 1.0 (boundary)
     15. MSE exactly half the threshold  → AE score = 0.5 (linear midpoint)
    """

    def _train_with_mock(self, n_normal=100, n_anom=20):
        """
        Return (det, mock_ae) with train_autoencoder already called.
        mock_ae.predict returns zeros so threshold arithmetic stays simple.
        """
        det   = BehavioralAnomalyDetector()
        X, y  = _make_Xy(n_normal=n_normal, n_anom=n_anom)
        mock_ae = MagicMock()
        mock_ae.predict.side_effect = lambda X, **kw: np.zeros_like(X)
        with patch("backend.ml_engine.anomaly_detector.Model", return_value=mock_ae):
            det.train_autoencoder(X, y)
        return det, mock_ae

    # 11
    def test_fit_receives_x_train_as_both_input_and_target(self):
        """
        Autoencoders are trained to reconstruct their own input, so fit()
        must be called as fit(X_train, X_train, ...) — input and target are
        the same array.  If a different target were passed the model would
        not learn a reconstruction mapping.
        """
        _, mock_ae = self._train_with_mock()

        fit_args = mock_ae.fit.call_args[0]
        X_input  = fit_args[0]
        X_target = fit_args[1]

        np.testing.assert_array_equal(
            X_input, X_target,
            err_msg="fit() first arg (input) must equal second arg (target) "
                    "for autoencoder training",
        )

    # 12
    def test_fit_called_with_config_epochs_and_batch_size(self):
        """
        The epochs and batch_size passed to fit() must match the values in
        det.config['autoencoder'] — confirming that the config dict drives
        training hyper-parameters rather than hard-coded literals.
        """
        det, mock_ae = self._train_with_mock()

        fit_kwargs = mock_ae.fit.call_args[1]
        self.assertEqual(
            fit_kwargs["epochs"],     det.config["autoencoder"]["epochs"],
            "fit() epochs must equal config['autoencoder']['epochs']",
        )
        self.assertEqual(
            fit_kwargs["batch_size"], det.config["autoencoder"]["batch_size"],
            "fit() batch_size must equal config['autoencoder']['batch_size']",
        )

    # 13
    def test_fit_includes_early_stopping_in_callbacks(self):
        """
        The EarlyStopping instance created inside train_autoencoder must be
        passed to fit() via the callbacks kwarg — confirming that training
        can halt early when validation loss stops improving.
        """
        det = BehavioralAnomalyDetector()
        X, y = _make_Xy(n_normal=50, n_anom=10)

        mock_ae = MagicMock()
        mock_ae.predict.side_effect = lambda X, **kw: np.zeros_like(X)
        sentinel_es = MagicMock(name="EarlyStopping_instance")

        with patch("backend.ml_engine.anomaly_detector.Model",       return_value=mock_ae), \
             patch("backend.ml_engine.anomaly_detector.EarlyStopping", return_value=sentinel_es):
            det.train_autoencoder(X, y)

        callbacks = mock_ae.fit.call_args[1]["callbacks"]
        self.assertIn(
            sentinel_es, callbacks,
            "The EarlyStopping instance must appear in fit()'s callbacks list",
        )

    # 14
    def test_ae_score_is_one_when_mse_equals_threshold(self):
        """
        When per-sample MSE exactly equals the threshold, the normalised score
        is MSE/threshold = 1.0 — the highest score before clipping would apply.
        This pins the upper natural boundary of the linear scaling.
        """
        threshold = 4.0
        det, ae   = _ae_mock(reconstruction="zeros", threshold=threshold)
        det.autoencoder_threshold = threshold

        # With predictions = 0 and X = sqrt(threshold), MSE = threshold
        # mean(sqrt(4)^2 per feature) = mean(4.0, ...) = 4.0
        X_test = np.full((5, N_FEAT), np.sqrt(threshold))
        scores = det.predict_anomaly_scores(X_test)

        np.testing.assert_allclose(
            scores["autoencoder"], 1.0, atol=1e-10,
            err_msg="AE score must equal 1.0 when MSE == threshold",
        )

    # 15
    def test_ae_score_is_half_when_mse_is_half_the_threshold(self):
        """
        The mapping from reconstruction error to AE score is linear:
        score = clip(MSE / threshold, 0, 1).  At MSE = threshold/2 the
        score must be exactly 0.5 — confirming the proportional scaling.
        """
        threshold = 4.0
        det, ae   = _ae_mock(reconstruction="zeros", threshold=threshold)
        det.autoencoder_threshold = threshold

        # With predictions = 0 and X = sqrt(threshold/2), MSE = threshold/2
        # mean(sqrt(2)^2 per feature) = mean(2.0, ...) = 2.0 = threshold/2
        X_test = np.full((5, N_FEAT), np.sqrt(threshold / 2))
        scores = det.predict_anomaly_scores(X_test)

        np.testing.assert_allclose(
            scores["autoencoder"], 0.5, atol=1e-10,
            err_msg="AE score must equal 0.5 when MSE == threshold / 2",
        )


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 4 — fit() call details, threshold type, score invariants (tests 16-20)
# ══════════════════════════════════════════════════════════════════════════════

class TestAutoencoderFitDetailsAndInvariants(unittest.TestCase):
    """
    Tests covering lower-level fit() call details and mathematical invariants
    of the AE score that must hold regardless of input content:

     16. fit() is called with verbose=0 (silent training)
     17. validation_data uses X_val as both input and target
     18. autoencoder_threshold is a non-negative scalar after training
     19. AE scores are always non-negative (MSE ≥ 0 → clip lower-bound is never active)
     20. Threshold >> MSE drives score toward zero (asymptotic lower boundary)
    """

    def _train_with_mock(self, n_normal=100, n_anom=20):
        det    = BehavioralAnomalyDetector()
        X, y   = _make_Xy(n_normal=n_normal, n_anom=n_anom)
        mock_ae = MagicMock()
        mock_ae.predict.side_effect = lambda X, **kw: np.zeros_like(X)
        with patch("backend.ml_engine.anomaly_detector.Model", return_value=mock_ae):
            det.train_autoencoder(X, y)
        return det, mock_ae

    # 16
    def test_fit_called_with_verbose_zero(self):
        """
        fit() must be called with verbose=0 so that training produces no
        console output — keeping the production log clean during batch runs.
        """
        _, mock_ae = self._train_with_mock()
        fit_kwargs = mock_ae.fit.call_args[1]
        self.assertEqual(
            fit_kwargs["verbose"], 0,
            "fit() must receive verbose=0 to suppress training output",
        )

    # 17
    def test_validation_data_uses_x_val_as_both_input_and_target(self):
        """
        The validation split passed to fit() must be (X_val, X_val) — the
        same reconstruction-target convention as the training data — so that
        validation loss measures reconstruction quality, not a different task.
        """
        _, mock_ae = self._train_with_mock()
        val_input, val_target = mock_ae.fit.call_args[1]["validation_data"]
        np.testing.assert_array_equal(
            val_input, val_target,
            err_msg="validation_data must be (X_val, X_val): "
                    "input and target must be identical",
        )

    # 18
    def test_autoencoder_threshold_is_non_negative_scalar_after_training(self):
        """
        autoencoder_threshold must be a non-negative scalar (not an array)
        after training — a negative or array-valued threshold would cause
        incorrect score normalisation in predict_anomaly_scores.
        """
        det, _ = self._train_with_mock()
        threshold = det.autoencoder_threshold

        self.assertTrue(
            np.isscalar(threshold) or isinstance(threshold, np.floating),
            f"autoencoder_threshold must be scalar, got {type(threshold)}",
        )
        self.assertGreaterEqual(
            float(threshold), 0.0,
            "autoencoder_threshold must be non-negative (MSE is always ≥ 0)",
        )

    # 19
    def test_ae_scores_are_always_non_negative(self):
        """
        Because MSE = mean((X - pred)^2) ≥ 0, the raw AE score is ≥ 0
        before clipping.  The lower clip bound (0) should therefore never
        activate — but the output must still be ≥ 0 regardless of input.
        Tested with predictions = −X (sign flip), which maximises MSE.
        """
        det, ae = _ae_mock(reconstruction="perfect", threshold=1.0)
        # predictions = −X → MSE = mean((X−(−X))^2) = mean(4X^2) ≥ 0
        ae.predict.side_effect = lambda X, **kw: -X.copy()

        X_test = RNG.standard_normal((30, N_FEAT))
        scores = det.predict_anomaly_scores(X_test)

        self.assertTrue(
            np.all(scores["autoencoder"] >= 0.0),
            "AE scores must be non-negative for any input",
        )

    # 20
    def test_very_large_threshold_drives_ae_score_toward_zero(self):
        """
        When the threshold is orders of magnitude larger than the actual
        reconstruction error, the normalised score MSE/threshold approaches
        zero — confirming the denominator scaling behaves correctly at the
        low end of the anomaly range.
        """
        threshold = 1e12
        det, ae   = _ae_mock(reconstruction="zeros", threshold=threshold)
        det.autoencoder_threshold = threshold

        # X = ones → MSE = 1.0; score = 1.0 / 1e12 ≈ 0
        X_test = np.ones((5, N_FEAT))
        scores = det.predict_anomaly_scores(X_test)

        np.testing.assert_allclose(
            scores["autoencoder"], 0.0, atol=1e-6,
            err_msg="AE score must approach 0 when threshold >> MSE",
        )


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 5 — Output invariants, monotonicity, and edge cases (tests 21-25)
# ══════════════════════════════════════════════════════════════════════════════

class TestAutoencoderEdgeCasesAndInvariants(unittest.TestCase):
    """
    Tests covering hard output guarantees and boundary inputs:

     21. All AE scores lie within [0, 1] regardless of input magnitude
     22. Higher reconstruction error monotonically yields a higher AE score
     23. predict_anomaly_scores always includes 'autoencoder' key with correct length
     24. fit() is called exactly once per train_autoencoder invocation
     25. train_autoencoder succeeds when all samples are normal (y all zeros)
    """

    def _train_with_mock(self, n_normal=100, n_anom=20):
        det    = BehavioralAnomalyDetector()
        X, y   = _make_Xy(n_normal=n_normal, n_anom=n_anom)
        mock_ae = MagicMock()
        mock_ae.predict.side_effect = lambda X, **kw: np.zeros_like(X)
        with patch("backend.ml_engine.anomaly_detector.Model", return_value=mock_ae):
            det.train_autoencoder(X, y)
        return det, mock_ae

    # 21
    def test_ae_scores_always_within_zero_one_range(self):
        """
        np.clip enforces [0, 1] on the normalised scores, so regardless of
        how small or large the reconstruction error is, every AE score in
        the returned array must satisfy 0 ≤ score ≤ 1.
        Tested with a batch that includes both perfect rows (score → 0) and
        rows whose MSE far exceeds the threshold (score → 1).
        """
        det, ae = _ae_mock(reconstruction="zeros", threshold=1.0)
        det.autoencoder_threshold = 1.0

        # Row 0-4: X = 0 → MSE = 0 → score = 0
        # Row 5-9: X = 100 → MSE = 10 000 >> threshold → clipped to 1
        X_test = np.zeros((10, N_FEAT))
        X_test[5:] = 100.0
        scores = det.predict_anomaly_scores(X_test)["autoencoder"]

        self.assertTrue(np.all(scores >= 0.0),
                        "Every AE score must be ≥ 0")
        self.assertTrue(np.all(scores <= 1.0),
                        "Every AE score must be ≤ 1")

    # 22
    def test_higher_reconstruction_error_yields_higher_ae_score(self):
        """
        The AE score is a monotone function of reconstruction MSE
        (score = clip(MSE / threshold, 0, 1)).  Three samples with
        increasing values (and predictions = 0) must produce strictly
        increasing scores — confirming the ordering is preserved end-to-end.

        X_low=1  → MSE=1   → score=0.10
        X_mid=2  → MSE=4   → score=0.40
        X_high=3 → MSE=9   → score=0.90   (threshold=10)
        """
        det, ae = _ae_mock(reconstruction="zeros", threshold=10.0)
        det.autoencoder_threshold = 10.0

        X_test = np.vstack([
            np.full((1, N_FEAT), 1.0),   # MSE = 1 → 0.10
            np.full((1, N_FEAT), 2.0),   # MSE = 4 → 0.40
            np.full((1, N_FEAT), 3.0),   # MSE = 9 → 0.90
        ])
        scores = det.predict_anomaly_scores(X_test)["autoencoder"]

        self.assertLess(float(scores[0]), float(scores[1]),
                        "score(X=1) must be less than score(X=2)")
        self.assertLess(float(scores[1]), float(scores[2]),
                        "score(X=2) must be less than score(X=3)")

    # 23
    def test_predict_anomaly_scores_always_includes_autoencoder_key(self):
        """
        predict_anomaly_scores must return a dict that contains the key
        'autoencoder', and the associated array must have one entry per
        input sample — confirming the AE branch is always executed and
        its output is correctly structured.
        """
        n_samples = 7
        det, _    = _ae_mock(reconstruction="perfect", threshold=1.0)
        scores    = det.predict_anomaly_scores(RNG.standard_normal((n_samples, N_FEAT)))

        self.assertIn("autoencoder", scores,
                      "predict_anomaly_scores must include 'autoencoder' key")
        self.assertEqual(
            len(scores["autoencoder"]), n_samples,
            "AE score array length must equal the number of input samples",
        )

    # 24
    def test_fit_called_exactly_once_per_train_autoencoder_call(self):
        """
        train_autoencoder must call model.fit() exactly once — not zero
        times (which would skip training) and not more than once (which
        would waste compute or indicate a loop bug).
        """
        _, mock_ae = self._train_with_mock()
        self.assertEqual(
            mock_ae.fit.call_count, 1,
            "fit() must be called exactly once during train_autoencoder",
        )

    # 25
    def test_train_autoencoder_succeeds_when_all_samples_are_normal(self):
        """
        When the dataset contains no anomalous rows (y = all zeros),
        train_autoencoder must complete without error and store the model —
        confirming the normal-filtering step does not break with a 100 %
        normal dataset.
        """
        det = BehavioralAnomalyDetector()
        n   = 60
        X   = RNG.standard_normal((n, N_FEAT))
        y   = np.zeros(n, dtype=int)   # every sample is normal

        mock_ae = MagicMock()
        mock_ae.predict.side_effect = lambda X, **kw: np.zeros_like(X)

        with patch("backend.ml_engine.anomaly_detector.Model", return_value=mock_ae):
            try:
                det.train_autoencoder(X, y)
            except Exception as exc:
                self.fail(
                    f"train_autoencoder raised {type(exc).__name__} "
                    f"with an all-normal dataset: {exc}"
                )

        self.assertIn("autoencoder", det.models,
                      "Model must be stored even when all samples are normal")


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
