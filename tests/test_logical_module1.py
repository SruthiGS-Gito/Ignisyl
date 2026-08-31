"""
Phase 2 Logical Tests — Module 1: Data Ingestion & Preprocessing
=================================================================
Verifies *behavioural correctness* rather than structural correctness:
  1. Anomalous inputs score higher than normal inputs
  2. Correct patterns detected for each threat type
  3. Time-window filtering at boundaries
  4. Anomaly injection produces correct threat types and field values
  5. User risk-flagging threshold logic

Modules under test:
  backend/services/log_processor.py   (LogProcessor)
  backend/ml_engine/data_generator.py (BehavioralDataGenerator)

Run with:
    python -m unittest tests/test_logical_module1.py -v
"""

import sys
import os
import unittest
import re
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# ── Project root on path ──────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ── Stub config before data_generator imports it ─────────────────────────────
_cfg = MagicMock()
_cfg.settings.DATA_PATH = "/tmp/ignisyl_test"
_cfg.ACTIVITY_TYPES = [
    "login", "logout", "file_access", "network_access", "email_sent",
    "file_download", "file_upload", "database_query", "system_command",
    "application_launch", "usb_access",
]
_cfg.MONITORED_PROTOCOLS = ["HTTP", "HTTPS", "FTP", "SSH", "DNS"]
sys.modules.setdefault("config",        _cfg)
sys.modules.setdefault("config.config", _cfg)

from backend.services.log_processor import LogProcessor              # noqa: E402
from backend.ml_engine.data_generator import BehavioralDataGenerator  # noqa: E402


# ══════════════════════════════════════════════════════════════════════════════
# Shared helpers
# ══════════════════════════════════════════════════════════════════════════════

def _recent(seconds_ago=30):
    return (datetime.now() - timedelta(seconds=seconds_ago)).isoformat()


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 1 — Anomalous vs Normal scoring + Pattern specificity (tests 1-5)
# ══════════════════════════════════════════════════════════════════════════════

class TestAnomalousVsNormalScoring(unittest.TestCase):
    """
    Logical invariant: anomalous activities must carry higher suspicion signals
    than normal activities, both in the LogProcessor and in BehavioralDataGenerator.
    """

    # 1
    def test_suspicious_log_has_higher_signal_than_benign_log(self):
        """
        A log matching a threat pattern must set is_suspicious=True while a
        benign log must remain is_suspicious=False — confirming the binary
        scoring separates the two populations.
        """
        lp = LogProcessor()
        benign    = lp.process_log_entry({"message": "User session started normally"})
        malicious = lp.process_log_entry({"message": "Failed login attempt user: eve"})

        self.assertFalse(benign["is_suspicious"],
                         "Benign log incorrectly flagged as suspicious")
        self.assertTrue(malicious["is_suspicious"],
                        "Threat-matching log not flagged as suspicious")

    # 2
    def test_normal_activity_confidence_score_below_anomalous(self):
        """
        data_generator assigns confidence_score in [0.1, 0.3] for normal
        activities and ≥ 0.5 for all anomaly types.  The maximum normal score
        must be strictly less than the minimum anomalous score.
        """
        gen = BehavioralDataGenerator(num_users=10, num_days=1)
        gen.generate_user_profiles()
        user = gen.users[0]
        ts   = datetime(2024, 6, 10, 10, 0, 0)

        # Sample 50 normal activities
        normal_scores = [
            gen._create_activity(user, "file_access", ts)["confidence_score"]
            for _ in range(50)
        ]

        # Anomaly scores come directly from the creator methods
        exfil_score     = gen._create_exfiltration_anomaly(user, [])["confidence_score"]
        privilege_score = gen._create_privilege_anomaly(user, [])["confidence_score"]
        compromise_score = gen._create_compromise_anomaly(user, [])["confidence_score"]

        self.assertLessEqual(max(normal_scores), 0.35,
                             "Normal activity confidence_score exceeded expected ceiling")
        self.assertGreaterEqual(exfil_score,      0.5)
        self.assertGreaterEqual(privilege_score,  0.5)
        self.assertGreaterEqual(compromise_score, 0.5)

    # 3
    def test_multiple_pattern_matches_increase_suspicion_signal(self):
        """
        A message triggering MORE patterns must produce a longer
        detected_patterns list — confirming that richer threat signals
        accumulate correctly.
        """
        lp = LogProcessor()

        # Triggers only failed_login
        single = lp.process_log_entry(
            {"message": "Failed login attempt for user: alice"}
        )
        # Triggers both failed_login AND firewall_block
        double = lp.process_log_entry(
            {"message": "Failed login attempt for user: bob. "
                        "Firewall rule blocked user: bob"}
        )

        self.assertEqual(len(single["detected_patterns"]), 1)
        self.assertGreater(len(double["detected_patterns"]),
                           len(single["detected_patterns"]),
                           "Multi-pattern message should have more detected patterns")

    # 4
    def test_failed_login_pattern_rejects_successful_login_message(self):
        """
        The failed_login regex must NOT fire on a successful-login message —
        confirming pattern specificity (no false positives on opposite event).
        """
        lp      = LogProcessor()
        pattern = lp.log_patterns["failed_login"]

        self.assertIsNone(pattern.search("Successful login for user: alice"),
                          "failed_login pattern incorrectly matched a success message")
        self.assertIsNone(pattern.search("User alice logged in successfully"),
                          "failed_login pattern incorrectly matched a success message")

    # 5
    def test_each_pattern_matches_only_its_intended_threat_class(self):
        """
        Each of the five patterns must match its own canonical message and
        must NOT match the canonical messages of the other four — confirming
        non-overlapping threat classification.
        """
        lp = LogProcessor()
        canonical = {
            "failed_login":         "Failed login attempt user: alice",
            "data_access":          "Data access recorded file: report.xlsx",
            "privilege_escalation": "Privilege escalation: elevated to admin",
            "network_anomaly":      "Network anomaly detected 192.168.1.1",
            "firewall_block":       "Firewall rule blocked user: mallory",
        }

        for owner, message in canonical.items():
            # Must match its own pattern
            self.assertIsNotNone(
                lp.log_patterns[owner].search(message),
                f"Pattern '{owner}' failed to match its own canonical message",
            )
            # Must NOT match the other patterns' canonical messages
            for other, other_msg in canonical.items():
                if other == owner:
                    continue
                # A cross-match is only a problem if it's a full false positive;
                # we verify the owner pattern doesn't fire on the other's message.
                # (Some patterns are intentionally narrow; cross-matches indicate a bug.)
                # We only assert non-match where the messages are clearly disjoint.
                if not any(kw in other_msg for kw in message.split()[:2]):
                    result = lp.log_patterns[owner].search(other_msg)
                    self.assertIsNone(
                        result,
                        f"Pattern '{owner}' incorrectly matched message for '{other}': "
                        f"'{other_msg}'",
                    )


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 2 — Time-window filtering at boundaries (tests 6-10)
# ══════════════════════════════════════════════════════════════════════════════

def _make_log(lp, message="test", minutes_ago=5, suspicious=False):
    """Helper: ingest one log with a controlled timestamp."""
    ts    = (datetime.now() - timedelta(minutes=minutes_ago)).isoformat()
    entry = {"message": message, "timestamp": ts}
    return lp.process_log_entry(entry)


class TestTimeWindowBoundaries(unittest.TestCase):
    """
    Logical invariant: only logs whose timestamps fall STRICTLY INSIDE the
    requested window are returned.  The comparison used is `>` (not `>=`),
    so the exact boundary moment is excluded.

    To avoid flakiness from clock drift we use margins ≥ 5 minutes around
    every boundary.  The one exception (test 10) avoids real timestamps
    entirely by using time_window = 0.
    """

    # 6
    def test_log_well_inside_window_counted_by_analyze_logs(self):
        """A log from 10 min ago must appear in a 60-min analysis window."""
        lp = LogProcessor()
        _make_log(lp, minutes_ago=10)

        result = lp.analyze_logs(time_window=3600)   # 60-min window
        self.assertEqual(result["total_logs"], 1,
                         "Log inside the window was not counted")

    # 7
    def test_log_well_outside_window_excluded_by_analyze_logs(self):
        """A log from 2 hours ago must be absent from a 60-min analysis window."""
        lp = LogProcessor()
        _make_log(lp, minutes_ago=120)

        result = lp.analyze_logs(time_window=3600)
        self.assertEqual(result["total_logs"], 0,
                         "Log outside the window was incorrectly counted")

    # 8
    def test_log_just_inside_boundary_is_included(self):
        """
        A log from 55 min ago sits clearly inside a 3600-second (60-min)
        window and must be returned — confirming logs before the cutoff
        are captured.
        """
        lp = LogProcessor()
        _make_log(lp, "Failed login attempt user: x", minutes_ago=55)

        matched = lp.detect_patterns("failed_login", time_window=3600)
        self.assertEqual(len(matched), 1,
                         "Log 55 min ago should be inside the 60-min window")

    # 9
    def test_log_just_outside_boundary_is_excluded(self):
        """
        A log from 65 min ago sits clearly outside a 3600-second (60-min)
        window and must NOT be returned — confirming the cutoff is enforced.
        """
        lp = LogProcessor()
        _make_log(lp, "Failed login attempt user: y", minutes_ago=65)

        matched = lp.detect_patterns("failed_login", time_window=3600)
        self.assertEqual(len(matched), 0,
                         "Log 65 min ago should be outside the 60-min window")

    # 10
    def test_zero_second_window_excludes_all_past_logs(self):
        """
        With time_window=0 the cutoff equals datetime.now().  Every stored
        log has a timestamp in the past (timestamp < now), so the strict
        `>` comparison excludes all of them — confirming the boundary
        semantics: 'strictly after cutoff'.
        """
        lp = LogProcessor()
        for i in range(3):
            _make_log(lp, minutes_ago=1)   # 1 minute in the past

        result = lp.analyze_logs(time_window=0)
        self.assertEqual(result["total_logs"], 0,
                         "time_window=0 should exclude every past log")


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 3 — Anomaly injection: correct threat types & field values (tests 11-15)
# ══════════════════════════════════════════════════════════════════════════════

def _gen_with_users(n=5):
    gen = BehavioralDataGenerator(num_users=n, num_days=1)
    gen.generate_user_profiles()
    return gen


class TestAnomalyInjectionFieldValues(unittest.TestCase):
    """
    Logical invariant: each anomaly creator must produce field values that
    are *qualitatively distinct* from normal activity — not just structurally
    present but semantically meaningful for the threat scenario.
    """

    def setUp(self):
        self.gen  = _gen_with_users()
        self.user = self.gen.users[0]

    # 11
    def test_exfiltration_anomaly_always_routes_to_external_server(self):
        """
        Data exfiltration must always target an external destination.
        Sending large volumes internally is a different (and less severe) risk.
        Run 20 times to confirm the field is hardcoded, not random.
        """
        for _ in range(20):
            anomaly = self.gen._create_exfiltration_anomaly(self.user, [])
            self.assertEqual(
                anomaly["destination"], "external_server",
                "Exfiltration anomaly destination must always be 'external_server'",
            )

    # 12
    def test_exfiltration_file_count_far_exceeds_normal_transfer(self):
        """
        Normal file transfers move 1-10 files; exfiltration moves 50-500.
        Every generated exfil anomaly must have file_count >= 50.
        """
        NORMAL_MAX   = 10
        EXFIL_MIN    = 50
        for _ in range(20):
            anomaly = self.gen._create_exfiltration_anomaly(self.user, [])
            self.assertGreaterEqual(
                anomaly["file_count"], EXFIL_MIN,
                f"Exfiltration file_count {anomaly['file_count']} "
                f"is not above normal ceiling of {NORMAL_MAX}",
            )

    # 13
    def test_exfiltration_risk_factors_include_all_three_indicators(self):
        """
        The exfiltration risk narrative requires exactly these three signals:
        'large_transfer', 'off_hours', 'external_destination'.
        Missing any one of them weakens the detection rationale.
        """
        expected_flags = {"large_transfer", "off_hours", "external_destination"}
        for _ in range(10):
            anomaly  = self.gen._create_exfiltration_anomaly(self.user, [])
            got_flags = set(anomaly["risk_factors"])
            self.assertTrue(
                expected_flags.issubset(got_flags),
                f"Exfiltration risk_factors missing: "
                f"{expected_flags - got_flags}",
            )

    # 14
    def test_privilege_anomaly_always_targets_hr_database(self):
        """
        Privilege-abuse simulation accesses HR data from a non-HR user —
        the database_name must always be 'hr_db' to represent this
        cross-department violation scenario.
        """
        for _ in range(20):
            anomaly = self.gen._create_privilege_anomaly(self.user, [])
            self.assertEqual(
                anomaly["database_name"], "hr_db",
                "Privilege anomaly must target 'hr_db' to simulate "
                "cross-department data access",
            )

    # 15
    def test_compromise_anomaly_risk_factors_include_all_three_indicators(self):
        """
        A credential-compromise event is characterised by three concurrent
        signals: unusual location, new device, and multiple login attempts.
        All three must be present in every generated anomaly.
        """
        expected_flags = {"unusual_location", "new_device", "multiple_attempts"}
        for _ in range(10):
            anomaly   = self.gen._create_compromise_anomaly(self.user, [])
            got_flags = set(anomaly["risk_factors"])
            self.assertTrue(
                expected_flags.issubset(got_flags),
                f"Compromise risk_factors missing: "
                f"{expected_flags - got_flags}",
            )


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 4 — User risk-flagging threshold logic (tests 16-20)
# ══════════════════════════════════════════════════════════════════════════════

def _ingest_n_logs(lp, user_id, n, minutes_ago=5):
    """Ingest exactly n logs for user_id inside the default analysis window."""
    ts = (datetime.now() - timedelta(minutes=minutes_ago)).isoformat()
    for _ in range(n):
        lp.process_log_entry({
            "message":   "Normal system event",
            "user_id":   user_id,
            "timestamp": ts,
        })


class TestUserRiskFlaggingThreshold(unittest.TestCase):
    """
    Logical invariant: the suspicious-user threshold is STRICTLY GREATER
    THAN 50.  The code reads:  `if count > 50`
      - exactly 50 logs  →  NOT flagged  (50 is not > 50)
      - exactly 51 logs  →  flagged      (51 > 50)
    These tests confirm the boundary is enforced correctly and that
    users are evaluated independently of one another.
    """

    # 16
    def test_user_with_exactly_50_logs_is_not_flagged(self):
        """At-threshold: 50 logs must NOT trigger a suspicious-user flag."""
        lp = LogProcessor()
        _ingest_n_logs(lp, "alice", 50)
        result = lp.analyze_logs()
        self.assertNotIn(
            "alice", result["suspicious_users"],
            "User with exactly 50 logs should not be flagged (threshold is >50)",
        )

    # 17
    def test_user_with_exactly_51_logs_is_flagged(self):
        """One-above-threshold: 51 logs must trigger a suspicious-user flag."""
        lp = LogProcessor()
        _ingest_n_logs(lp, "bob", 51)
        result = lp.analyze_logs()
        self.assertIn(
            "bob", result["suspicious_users"],
            "User with 51 logs should be flagged (51 > 50)",
        )

    # 18
    def test_user_with_49_logs_is_not_flagged(self):
        """Well-below-threshold: 49 logs must NOT trigger a suspicious-user flag."""
        lp = LogProcessor()
        _ingest_n_logs(lp, "carol", 49)
        result = lp.analyze_logs()
        self.assertNotIn(
            "carol", result["suspicious_users"],
            "User with 49 logs should not be flagged",
        )

    # 19
    def test_multiple_high_volume_users_all_flagged_independently(self):
        """
        Two separate users both exceeding the threshold must both appear
        in suspicious_users — confirming the check is per-user, not global.
        """
        lp = LogProcessor()
        _ingest_n_logs(lp, "eve",   55)
        _ingest_n_logs(lp, "frank", 60)
        result = lp.analyze_logs()
        self.assertIn("eve",   result["suspicious_users"])
        self.assertIn("frank", result["suspicious_users"])

    # 20
    def test_low_volume_user_not_flagged_alongside_high_volume_user(self):
        """
        A low-volume user must NOT be flagged simply because another user
        in the same window is above the threshold — confirming isolation
        between users in the flagging logic.
        """
        lp = LogProcessor()
        _ingest_n_logs(lp, "grace",  55)   # above threshold → should be flagged
        _ingest_n_logs(lp, "henry",  10)   # below threshold → must NOT be flagged

        result = lp.analyze_logs()
        self.assertIn(
            "grace", result["suspicious_users"],
            "High-volume user 'grace' should be flagged",
        )
        self.assertNotIn(
            "henry", result["suspicious_users"],
            "Low-volume user 'henry' must not be flagged by association",
        )


# ══════════════════════════════════════════════════════════════════════════════
# BATCH 5 — Cross-cutting logical invariants (tests 21-25)
# ══════════════════════════════════════════════════════════════════════════════

class TestCrossCuttingInvariants(unittest.TestCase):
    """
    Deeper logical checks that span multiple behaviours or confirm that
    independent filters compose correctly.
    """

    # 21
    def test_privilege_anomaly_rows_affected_always_in_bulk_range(self):
        """
        A privilege-abuse query is characterised by mass data extraction
        (10 000–100 000 rows).  Every generated anomaly must stay within
        that range — confirming it is meaningfully different from a normal
        query (1–10 000 rows) and from an unbounded value.
        """
        gen = _gen_with_users()
        user = gen.users[0]
        for _ in range(20):
            anomaly = gen._create_privilege_anomaly(user, [])
            self.assertGreaterEqual(anomaly["rows_affected"], 10_000,
                                    "Privilege anomaly rows_affected below expected minimum")
            self.assertLessEqual(anomaly["rows_affected"],  100_000,
                                 "Privilege anomaly rows_affected above expected maximum")

    # 22
    def test_normal_activities_remain_unmodified_after_anomaly_injection(self):
        """
        inject_anomalies() appends anomalous records; it must not alter
        any pre-existing activity object.  Verify that every activity that
        was normal before injection is still normal (is_suspicious=False)
        after injection, regardless of which new anomalies were added.
        """
        gen = _gen_with_users(n=20)
        start  = datetime(2024, 6, 10)
        end    = datetime(2024, 6, 11)
        normal = gen.generate_normal_activities(start, end)

        # Capture the suspicious flag of every original activity before injection
        pre_flags = [a["is_suspicious"] for a in normal]

        with patch("backend.ml_engine.data_generator.random.random",
                   return_value=0.1):          # force anomaly injection
            gen.inject_anomalies(normal)

        # Original activity objects must be unchanged
        post_flags = [a["is_suspicious"] for a in normal]
        self.assertEqual(pre_flags, post_flags,
                         "inject_anomalies() modified existing activity objects")

    # 23
    def test_get_suspicious_logs_applies_both_suspicion_and_time_filter(self):
        """
        get_suspicious_logs() must satisfy TWO conditions simultaneously:
          (a) is_suspicious = True
          (b) timestamp within the requested hours window
        A suspicious log outside the window and a benign log inside the
        window must both be absent from the result.
        """
        lp  = LogProcessor()
        now = datetime.now()

        # Recent suspicious — must appear
        e1 = {"message": "Failed login attempt user: x",
              "timestamp": (now - timedelta(minutes=10)).isoformat()}
        lp.process_log_entry(e1)

        # Old suspicious — must be excluded by time filter
        e2 = {"message": "Failed login attempt user: y",
              "timestamp": (now - timedelta(hours=5)).isoformat()}
        lp.process_log_entry(e2)

        # Recent benign — must be excluded by suspicion filter
        e3 = {"message": "Normal health check",
              "timestamp": (now - timedelta(minutes=5)).isoformat()}
        lp.process_log_entry(e3)

        result = lp.get_suspicious_logs(hours=1)

        self.assertEqual(len(result), 1,
                         "Expected exactly 1 log: recent+suspicious only")
        self.assertTrue(result[0]["is_suspicious"])

    # 24
    def test_analyze_logs_suspicious_count_excludes_old_suspicious_logs(self):
        """
        suspicious_log_count in analyze_logs() must only reflect logs that
        are BOTH suspicious AND within the time window — confirming the two
        independent criteria are applied together, not separately.
        """
        lp  = LogProcessor()
        now = datetime.now()

        # Old suspicious (outside 1-hour window)
        old = {"message": "Firewall rule blocked user: z",
               "timestamp": (now - timedelta(hours=3)).isoformat()}
        lp.process_log_entry(old)

        # Recent suspicious (inside 1-hour window)
        new = {"message": "Failed login attempt user: z",
               "timestamp": (now - timedelta(minutes=5)).isoformat()}
        lp.process_log_entry(new)

        result = lp.analyze_logs(time_window=3600)
        self.assertEqual(result["suspicious_log_count"], 1,
                         "Only the recent suspicious log should be counted")
        self.assertEqual(result["total_logs"], 1,
                         "Old log must be outside the analysis window entirely")

    # 25
    def test_user_id_filter_is_exact_match_not_substring(self):
        """
        get_user_logs("alice") must return ONLY logs whose user_id is the
        string "alice" — not "alice_admin" or any other user whose id
        happens to contain "alice" as a substring.
        This confirms the filter uses equality, not containment.
        """
        lp  = LogProcessor()
        ts  = (datetime.now() - timedelta(minutes=5)).isoformat()

        lp.process_log_entry({"message": "evt", "user_id": "alice",       "timestamp": ts})
        lp.process_log_entry({"message": "evt", "user_id": "alice_admin", "timestamp": ts})
        lp.process_log_entry({"message": "evt", "user_id": "bob_alice",   "timestamp": ts})

        result = lp.get_user_logs("alice")

        self.assertEqual(len(result), 1,
                         "get_user_logs should match exact user_id, not substrings")
        self.assertEqual(result[0]["user_id"], "alice")


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
