"""
Phase 1 Technical Tests — Data Ingestion & Preprocessing
=========================================================
Unit tests for individual functions and component tests for the pipeline.

Modules under test:
  - backend/services/log_processor.py   (LogProcessor)
  - backend/ml_engine/data_generator.py (BehavioralDataGenerator)

Run with:
    python -m pytest tests/test_data_ingestion_preprocessing.py -v
"""

import sys
import os
import json
import re
import unittest
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# ── Project root on path ──────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ── Stub config.config before data_generator imports it at module level ───────
_cfg = MagicMock()
_cfg.settings.DATA_PATH             = "/tmp/ignisyl_test"
_cfg.settings.LOW_RISK_THRESHOLD    = 30
_cfg.settings.MEDIUM_RISK_THRESHOLD = 70
_cfg.ACTIVITY_TYPES = [
    "login", "logout", "file_access", "network_access", "email_sent",
    "file_download", "file_upload", "database_query", "system_command",
    "application_launch", "usb_access",
]
_cfg.MONITORED_PROTOCOLS = ["HTTP", "HTTPS", "FTP", "SSH", "DNS"]
sys.modules.setdefault("config", _cfg)
sys.modules.setdefault("config.config", _cfg)

from backend.services.log_processor import LogProcessor          # noqa: E402
from backend.ml_engine.data_generator import BehavioralDataGenerator  # noqa: E402


# ══════════════════════════════════════════════════════════════════════════════
# Helper factories
# ══════════════════════════════════════════════════════════════════════════════

def make_raw_log(message="Normal system event", level="INFO",
                 source="system", user_id=None, timestamp=None):
    entry = {"message": message, "level": level, "source": source}
    if user_id is not None:
        entry["user_id"] = user_id
    if timestamp is not None:
        entry["timestamp"] = timestamp
    return entry


_SUSPICIOUS_MESSAGES = {
    "failed_login":         "Failed login attempt for user: alice",
    "data_access":          "Data access recorded for file: secrets.xlsx",
    "privilege_escalation": "Privilege escalation: elevated to admin",
    "network_anomaly":      "Network anomaly detected from 10.0.0.1",
    "firewall_block":       "Firewall rule blocked user: mallory",
}


def make_suspicious_raw_log(pattern, **overrides):
    entry = make_raw_log(message=_SUSPICIOUS_MESSAGES[pattern])
    entry.update(overrides)
    return entry


# ══════════════════════════════════════════════════════════════════════════════
# LogProcessor — Unit Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestLogProcessorInit(unittest.TestCase):
    """LogProcessor.__init__ and _initialize_patterns"""

    def setUp(self):
        self.lp = LogProcessor()

    def test_log_buffer_starts_empty(self):
        self.assertEqual(self.lp.log_buffer, [])

    def test_processed_logs_starts_empty(self):
        self.assertEqual(self.lp.processed_logs, [])

    def test_patterns_dict_has_five_keys(self):
        expected = {
            "failed_login", "data_access", "privilege_escalation",
            "network_anomaly", "firewall_block",
        }
        self.assertEqual(set(self.lp.log_patterns.keys()), expected)

    def test_patterns_are_compiled_regex(self):
        compiled_type = type(re.compile(""))
        for name, pat in self.lp.log_patterns.items():
            self.assertIsInstance(pat, compiled_type,
                                  f"Pattern '{name}' is not a compiled regex")


# ─────────────────────────────────────────────────────────────────────────────

class TestProcessLogEntry(unittest.TestCase):
    """LogProcessor.process_log_entry — defaults, keys, patterns, flags, state"""

    def setUp(self):
        self.lp = LogProcessor()

    # Required output keys
    def test_returns_all_required_keys(self):
        result = self.lp.process_log_entry(make_raw_log())
        required = {
            "log_id", "timestamp", "level", "source", "message",
            "user_id", "raw_data", "detected_patterns", "is_suspicious",
        }
        self.assertTrue(required.issubset(result.keys()))

    # Defaults
    def test_level_defaults_to_info(self):
        result = self.lp.process_log_entry({"message": "test"})
        self.assertEqual(result["level"], "INFO")

    def test_source_defaults_to_system(self):
        result = self.lp.process_log_entry({"message": "test"})
        self.assertEqual(result["source"], "system")

    def test_message_defaults_to_empty_string(self):
        result = self.lp.process_log_entry({})
        self.assertEqual(result["message"], "")

    def test_user_id_defaults_to_none(self):
        result = self.lp.process_log_entry({"message": "no user"})
        self.assertIsNone(result["user_id"])

    def test_provided_user_id_preserved(self):
        result = self.lp.process_log_entry(make_raw_log(user_id="alice"))
        self.assertEqual(result["user_id"], "alice")

    def test_raw_data_preserved_verbatim(self):
        raw = make_raw_log(user_id="u1")
        result = self.lp.process_log_entry(raw)
        self.assertEqual(result["raw_data"], raw)

    def test_custom_timestamp_preserved(self):
        ts = "2024-01-15T10:00:00"
        result = self.lp.process_log_entry(make_raw_log(timestamp=ts))
        self.assertEqual(result["timestamp"], ts)

    # Pattern detection — one test per pattern
    def test_detects_failed_login(self):
        result = self.lp.process_log_entry(make_suspicious_raw_log("failed_login"))
        self.assertIn("failed_login", result["detected_patterns"])

    def test_detects_data_access(self):
        result = self.lp.process_log_entry(make_suspicious_raw_log("data_access"))
        self.assertIn("data_access", result["detected_patterns"])

    def test_detects_privilege_escalation(self):
        result = self.lp.process_log_entry(make_suspicious_raw_log("privilege_escalation"))
        self.assertIn("privilege_escalation", result["detected_patterns"])

    def test_detects_network_anomaly(self):
        result = self.lp.process_log_entry(make_suspicious_raw_log("network_anomaly"))
        self.assertIn("network_anomaly", result["detected_patterns"])

    def test_detects_firewall_block(self):
        result = self.lp.process_log_entry(make_suspicious_raw_log("firewall_block"))
        self.assertIn("firewall_block", result["detected_patterns"])

    def test_benign_message_yields_empty_patterns(self):
        result = self.lp.process_log_entry(make_raw_log("User authenticated successfully"))
        self.assertEqual(result["detected_patterns"], [])

    # is_suspicious flag
    def test_is_suspicious_true_when_pattern_detected(self):
        result = self.lp.process_log_entry(make_suspicious_raw_log("failed_login"))
        self.assertTrue(result["is_suspicious"])

    def test_is_suspicious_false_for_benign_message(self):
        result = self.lp.process_log_entry(make_raw_log("Routine health check"))
        self.assertFalse(result["is_suspicious"])

    # State mutations
    def test_entry_appended_to_log_buffer(self):
        self.lp.process_log_entry(make_raw_log())
        self.assertEqual(len(self.lp.log_buffer), 1)

    def test_entry_appended_to_processed_logs(self):
        self.lp.process_log_entry(make_raw_log())
        self.assertEqual(len(self.lp.processed_logs), 1)

    def test_multiple_entries_accumulate(self):
        for _ in range(5):
            self.lp.process_log_entry(make_raw_log())
        self.assertEqual(len(self.lp.processed_logs), 5)

    def test_log_id_starts_with_log_prefix(self):
        result = self.lp.process_log_entry(make_raw_log())
        self.assertTrue(result["log_id"].startswith("log_"))

    def test_log_id_format_is_correct(self):
        # log_id is built from datetime; format check is more reliable than
        # uniqueness because rapid calls may share the same microsecond.
        import re as _re
        pattern = _re.compile(r"^log_\d{8}_\d{6}_\d+$")
        for _ in range(5):
            log_id = self.lp.process_log_entry(make_raw_log())["log_id"]
            self.assertRegex(log_id, pattern, f"Unexpected log_id format: {log_id}")


# ─────────────────────────────────────────────────────────────────────────────

class TestGetUserLogs(unittest.TestCase):
    """LogProcessor.get_user_logs"""

    def setUp(self):
        self.lp = LogProcessor()
        now = datetime.now()
        # 5 logs for alice, most-recent first when sorted
        for i in range(5):
            ts = (now - timedelta(minutes=i)).isoformat()
            self.lp.process_log_entry(make_raw_log(user_id="alice", timestamp=ts))
        # 3 logs for bob
        for i in range(3):
            ts = (now - timedelta(minutes=i + 10)).isoformat()
            self.lp.process_log_entry(make_raw_log(user_id="bob", timestamp=ts))

    def test_returns_only_requested_user(self):
        logs = self.lp.get_user_logs("alice")
        self.assertTrue(all(l["user_id"] == "alice" for l in logs))

    def test_returns_correct_count(self):
        self.assertEqual(len(self.lp.get_user_logs("alice")), 5)
        self.assertEqual(len(self.lp.get_user_logs("bob")), 3)

    def test_limit_is_honoured(self):
        self.assertEqual(len(self.lp.get_user_logs("alice", limit=2)), 2)

    def test_sorted_most_recent_first(self):
        logs = self.lp.get_user_logs("alice")
        for i in range(len(logs) - 1):
            self.assertGreaterEqual(logs[i]["timestamp"], logs[i + 1]["timestamp"])

    def test_unknown_user_returns_empty_list(self):
        self.assertEqual(self.lp.get_user_logs("nobody"), [])


# ─────────────────────────────────────────────────────────────────────────────

class TestGetSuspiciousLogs(unittest.TestCase):
    """LogProcessor.get_suspicious_logs"""

    def setUp(self):
        self.lp = LogProcessor()
        now = datetime.now()

        # Recent suspicious log (10 min ago)
        entry = make_suspicious_raw_log("failed_login")
        entry["timestamp"] = (now - timedelta(minutes=10)).isoformat()
        self.lp.process_log_entry(entry)

        # Recent benign log
        self.lp.process_log_entry(
            make_raw_log(timestamp=(now - timedelta(minutes=5)).isoformat())
        )

        # Old suspicious log (49 hours ago — outside default 24-hour window)
        entry2 = make_suspicious_raw_log("firewall_block")
        entry2["timestamp"] = (now - timedelta(hours=49)).isoformat()
        self.lp.process_log_entry(entry2)

    def test_returns_only_suspicious_entries(self):
        logs = self.lp.get_suspicious_logs(hours=24)
        self.assertTrue(all(l["is_suspicious"] for l in logs))

    def test_time_window_excludes_old_logs(self):
        logs = self.lp.get_suspicious_logs(hours=24)
        self.assertEqual(len(logs), 1)

    def test_wider_window_includes_old_suspicious_logs(self):
        logs = self.lp.get_suspicious_logs(hours=50)
        self.assertEqual(len(logs), 2)

    def test_benign_logs_never_returned(self):
        logs = self.lp.get_suspicious_logs(hours=50)
        messages = [l["message"] for l in logs]
        self.assertNotIn("Normal system event", messages)


# ─────────────────────────────────────────────────────────────────────────────

class TestDetectPatterns(unittest.TestCase):
    """LogProcessor.detect_patterns"""

    def setUp(self):
        self.lp = LogProcessor()
        now = datetime.now()
        recent = (now - timedelta(minutes=30)).isoformat()
        old    = (now - timedelta(minutes=90)).isoformat()  # 1.5 h ago

        # 2 recent failed_login
        for _ in range(2):
            entry = make_suspicious_raw_log("failed_login")
            entry["timestamp"] = recent
            self.lp.process_log_entry(entry)

        # 1 recent data_access
        entry = make_suspicious_raw_log("data_access")
        entry["timestamp"] = recent
        self.lp.process_log_entry(entry)

        # 1 old failed_login (outside 1-hour window)
        entry = make_suspicious_raw_log("failed_login")
        entry["timestamp"] = old
        self.lp.process_log_entry(entry)

    def test_returns_only_matching_pattern(self):
        logs = self.lp.detect_patterns("failed_login")
        self.assertTrue(
            all("failed_login" in l["detected_patterns"] for l in logs)
        )

    def test_default_window_excludes_old_log(self):
        # time_window=3600 s (1 h) → old log (1.5 h ago) excluded
        logs = self.lp.detect_patterns("failed_login", time_window=3600)
        self.assertEqual(len(logs), 2)

    def test_wider_window_includes_old_log(self):
        # time_window=7200 s (2 h) → old log (1.5 h ago) included
        logs = self.lp.detect_patterns("failed_login", time_window=7200)
        self.assertEqual(len(logs), 3)

    def test_non_existent_pattern_returns_empty(self):
        self.assertEqual(self.lp.detect_patterns("no_such_pattern"), [])

    def test_different_pattern_not_cross_contaminated(self):
        logs = self.lp.detect_patterns("firewall_block")
        self.assertEqual(logs, [])


# ─────────────────────────────────────────────────────────────────────────────

class TestAnalyzeLogs(unittest.TestCase):
    """LogProcessor.analyze_logs"""

    def setUp(self):
        self.lp = LogProcessor()
        now = datetime.now()
        ts = (now - timedelta(minutes=10)).isoformat()

        # 3 INFO logs for alice
        for _ in range(3):
            self.lp.process_log_entry(
                make_raw_log(level="INFO", user_id="alice", timestamp=ts)
            )
        # 2 WARNING logs for bob
        for _ in range(2):
            self.lp.process_log_entry(
                make_raw_log(level="WARNING", user_id="bob", timestamp=ts)
            )
        # 1 suspicious log for alice
        entry = make_suspicious_raw_log("failed_login")
        entry.update({"timestamp": ts, "user_id": "alice"})
        self.lp.process_log_entry(entry)

    def test_total_log_count(self):
        self.assertEqual(self.lp.analyze_logs()["total_logs"], 6)

    def test_level_distribution_info(self):
        # 3 explicit INFO logs + the suspicious log (also INFO by default) = 4
        self.assertEqual(self.lp.analyze_logs()["level_distribution"]["INFO"], 4)

    def test_level_distribution_warning(self):
        self.assertEqual(self.lp.analyze_logs()["level_distribution"]["WARNING"], 2)

    def test_suspicious_log_count(self):
        self.assertEqual(self.lp.analyze_logs()["suspicious_log_count"], 1)

    def test_user_activity_counts(self):
        result = self.lp.analyze_logs()
        self.assertEqual(result["user_activity"]["alice"], 4)
        self.assertEqual(result["user_activity"]["bob"], 2)

    def test_pattern_distribution_includes_detected_pattern(self):
        self.assertIn("failed_login", self.lp.analyze_logs()["pattern_distribution"])

    def test_suspicious_users_flagged_above_threshold(self):
        now = datetime.now()
        ts = (now - timedelta(minutes=5)).isoformat()
        for _ in range(51):
            self.lp.process_log_entry(make_raw_log(user_id="charlie", timestamp=ts))
        self.assertIn("charlie", self.lp.analyze_logs()["suspicious_users"])

    def test_users_below_threshold_not_flagged(self):
        result = self.lp.analyze_logs()
        self.assertNotIn("alice", result["suspicious_users"])
        self.assertNotIn("bob",   result["suspicious_users"])

    def test_time_window_excludes_old_logs(self):
        old_ts = (datetime.now() - timedelta(hours=2)).isoformat()
        self.lp.process_log_entry(make_raw_log(level="ERROR", timestamp=old_ts))
        # Default window = 3600 s → old log excluded
        self.assertEqual(self.lp.analyze_logs(time_window=3600)["total_logs"], 6)

    def test_result_includes_time_window_key(self):
        result = self.lp.analyze_logs(time_window=1800)
        self.assertEqual(result["time_window_seconds"], 1800)


# ─────────────────────────────────────────────────────────────────────────────

class TestAggregateByTime(unittest.TestCase):
    """LogProcessor.aggregate_by_time"""

    def setUp(self):
        self.lp = LogProcessor()
        # 2 logs in same hour (10:xx on June 15)
        self.lp.process_log_entry(make_raw_log(timestamp="2024-06-15T10:00:00"))
        self.lp.process_log_entry(make_raw_log(timestamp="2024-06-15T10:30:00"))
        # 1 log in a different hour same day
        self.lp.process_log_entry(make_raw_log(timestamp="2024-06-15T14:00:00"))
        # 1 log on the following day
        self.lp.process_log_entry(make_raw_log(timestamp="2024-06-16T09:00:00"))

    def test_hour_groups_same_hour(self):
        result = self.lp.aggregate_by_time("hour")
        self.assertEqual(result["2024-06-15 10:00"], 2)

    def test_hour_separates_different_hours(self):
        result = self.lp.aggregate_by_time("hour")
        self.assertEqual(result.get("2024-06-15 14:00"), 1)

    def test_day_groups_same_day(self):
        result = self.lp.aggregate_by_time("day")
        self.assertEqual(result["2024-06-15"], 3)

    def test_day_separates_different_days(self):
        result = self.lp.aggregate_by_time("day")
        self.assertEqual(result["2024-06-16"], 1)

    def test_week_groups_same_iso_week(self):
        result = self.lp.aggregate_by_time("week")
        # June 15 and 16, 2024 are both ISO week 24
        self.assertEqual(result.get("2024-W24"), 4)

    def test_unknown_interval_falls_back_to_day(self):
        result = self.lp.aggregate_by_time("minute")   # unsupported
        # Should produce day-level keys
        self.assertIn("2024-06-15", result)


# ─────────────────────────────────────────────────────────────────────────────

class TestExportLogs(unittest.TestCase):
    """LogProcessor.export_logs"""

    def setUp(self):
        self.lp = LogProcessor()
        self.lp.process_log_entry(make_raw_log(timestamp="2024-06-01T10:00:00"))
        self.lp.process_log_entry(make_raw_log(timestamp="2024-06-15T10:00:00"))
        self.lp.process_log_entry(make_raw_log(timestamp="2024-06-30T10:00:00"))

    def _tmp(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        return path

    def test_creates_valid_json_file(self):
        path = self._tmp()
        try:
            self.lp.export_logs(path)
            with open(path) as f:
                data = json.load(f)
            self.assertIsInstance(data, list)
        finally:
            os.unlink(path)

    def test_returns_total_log_count(self):
        path = self._tmp()
        try:
            self.assertEqual(self.lp.export_logs(path), 3)
        finally:
            os.unlink(path)

    def test_start_time_filter_excludes_earlier_logs(self):
        path = self._tmp()
        try:
            count = self.lp.export_logs(path, start_time="2024-06-10T00:00:00")
            self.assertEqual(count, 2)   # June 15 + June 30
        finally:
            os.unlink(path)

    def test_end_time_filter_excludes_later_logs(self):
        path = self._tmp()
        try:
            count = self.lp.export_logs(path, end_time="2024-06-15T23:59:59")
            self.assertEqual(count, 2)   # June 1 + June 15
        finally:
            os.unlink(path)

    def test_combined_start_and_end_filter(self):
        path = self._tmp()
        try:
            count = self.lp.export_logs(
                path,
                start_time="2024-06-10T00:00:00",
                end_time="2024-06-20T00:00:00",
            )
            self.assertEqual(count, 1)   # Only June 15
        finally:
            os.unlink(path)

    def test_exported_content_matches_count(self):
        path = self._tmp()
        try:
            count = self.lp.export_logs(path, start_time="2024-06-10T00:00:00")
            with open(path) as f:
                data = json.load(f)
            self.assertEqual(len(data), count)
        finally:
            os.unlink(path)


# ─────────────────────────────────────────────────────────────────────────────

class TestClearOldLogs(unittest.TestCase):
    """LogProcessor.clear_old_logs"""

    def setUp(self):
        self.lp = LogProcessor()
        now = datetime.now()
        # 2 recent logs
        self.lp.process_log_entry(
            make_raw_log(timestamp=(now - timedelta(days=10)).isoformat())
        )
        self.lp.process_log_entry(
            make_raw_log(timestamp=(now - timedelta(days=20)).isoformat())
        )
        # 2 old logs (>90 days)
        self.lp.process_log_entry(
            make_raw_log(timestamp=(now - timedelta(days=100)).isoformat())
        )
        self.lp.process_log_entry(
            make_raw_log(timestamp=(now - timedelta(days=120)).isoformat())
        )

    def test_removes_old_logs(self):
        self.lp.clear_old_logs(days_old=90)
        self.assertEqual(len(self.lp.processed_logs), 2)

    def test_preserves_recent_logs(self):
        self.lp.clear_old_logs(days_old=90)
        for log in self.lp.processed_logs:
            age = datetime.now() - datetime.fromisoformat(log["timestamp"])
            self.assertLess(age.days, 90)

    def test_returns_count_of_cleared_logs(self):
        self.assertEqual(self.lp.clear_old_logs(days_old=90), 2)

    def test_returns_zero_when_nothing_cleared(self):
        self.assertEqual(self.lp.clear_old_logs(days_old=200), 0)

    def test_clears_all_when_threshold_is_zero(self):
        count = self.lp.clear_old_logs(days_old=0)
        self.assertEqual(count, 4)
        self.assertEqual(len(self.lp.processed_logs), 0)


# ══════════════════════════════════════════════════════════════════════════════
# BehavioralDataGenerator — Unit Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestBehavioralDataGeneratorInit(unittest.TestCase):
    """BehavioralDataGenerator.__init__"""

    def test_default_num_users(self):
        self.assertEqual(BehavioralDataGenerator().num_users, 50)

    def test_default_num_days(self):
        self.assertEqual(BehavioralDataGenerator().num_days, 30)

    def test_custom_params_stored(self):
        gen = BehavioralDataGenerator(num_users=10, num_days=7)
        self.assertEqual(gen.num_users, 10)
        self.assertEqual(gen.num_days, 7)

    def test_users_list_starts_empty(self):
        self.assertEqual(BehavioralDataGenerator(num_users=5).users, [])

    def test_user_profiles_dict_starts_empty(self):
        self.assertEqual(BehavioralDataGenerator(num_users=5).user_profiles, {})

    def test_threat_scenarios_keys(self):
        gen = BehavioralDataGenerator()
        expected = {
            "data_exfiltration", "privilege_abuse",
            "credential_compromise", "insider_sabotage",
        }
        self.assertEqual(set(gen.threat_scenarios.keys()), expected)

    def test_threat_scenario_values_are_floats_between_0_and_1(self):
        for key, val in BehavioralDataGenerator().threat_scenarios.items():
            self.assertIsInstance(val, float, f"{key} value is not float")
            self.assertGreater(val, 0.0)
            self.assertLess(val, 1.0)


# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateUserProfiles(unittest.TestCase):
    """BehavioralDataGenerator.generate_user_profiles"""

    def setUp(self):
        self.gen = BehavioralDataGenerator(num_users=5, num_days=1)
        self.profiles = self.gen.generate_user_profiles()

    def test_generates_correct_count(self):
        self.assertEqual(len(self.profiles), 5)

    def test_users_list_populated(self):
        self.assertEqual(len(self.gen.users), 5)

    def test_user_profiles_dict_populated(self):
        self.assertEqual(len(self.gen.user_profiles), 5)

    def test_user_profiles_keyed_by_user_id(self):
        for user in self.profiles:
            self.assertIn(user["user_id"], self.gen.user_profiles)

    def test_required_keys_present_on_each_profile(self):
        required = {
            "user_id", "username", "email", "full_name", "department", "role",
            "seniority_level", "start_date", "work_hours", "device_preferences",
            "network_patterns", "file_access_patterns", "is_high_privilege",
            "risk_factors",
        }
        for user in self.profiles:
            missing = required - user.keys()
            self.assertFalse(missing, f"Profile missing keys: {missing}")

    def test_user_ids_are_sequential_from_one(self):
        ids = [u["user_id"] for u in self.profiles]
        self.assertEqual(ids, list(range(1, 6)))

    def test_email_domain_is_ignisyl_demo(self):
        for user in self.profiles:
            self.assertTrue(user["email"].endswith("@ignisyl.demo"))

    def test_is_high_privilege_is_boolean(self):
        for user in self.profiles:
            self.assertIsInstance(user["is_high_privilege"], bool)


# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateWorkPattern(unittest.TestCase):
    """BehavioralDataGenerator._generate_work_pattern"""

    def setUp(self):
        self.gen = BehavioralDataGenerator()

    def test_returns_required_keys(self):
        result = self.gen._generate_work_pattern("IT", "Software Engineer")
        for key in ("start", "end", "flexibility", "weekend_work"):
            self.assertIn(key, result)

    def test_executive_role_has_earlier_start(self):
        base = self.gen._generate_work_pattern("Finance", "Accountant")
        exec_ = self.gen._generate_work_pattern("Finance", "CFO")
        self.assertLess(exec_["start"], base["start"])

    def test_executive_role_has_later_end(self):
        base = self.gen._generate_work_pattern("Finance", "Accountant")
        exec_ = self.gen._generate_work_pattern("Finance", "CFO")
        self.assertGreater(exec_["end"], base["end"])

    def test_executive_role_has_higher_weekend_work(self):
        base = self.gen._generate_work_pattern("Sales", "Sales Rep")
        exec_ = self.gen._generate_work_pattern("Sales", "VP Sales")
        self.assertGreater(exec_["weekend_work"], base["weekend_work"])

    def test_non_executive_matches_base_pattern_start(self):
        result = self.gen._generate_work_pattern("HR", "HR Coordinator")
        # Base for HR is start=9; non-exec should not be adjusted
        self.assertEqual(result["start"], 9)


# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateDeviceProfile(unittest.TestCase):
    """BehavioralDataGenerator._generate_device_profile"""

    def setUp(self):
        self.gen = BehavioralDataGenerator()

    def test_returns_required_keys(self):
        result = self.gen._generate_device_profile()
        for key in ("primary_device", "secondary_devices", "os_preference",
                    "browser_preference", "mobile_usage"):
            self.assertIn(key, result)

    def test_mobile_usage_within_valid_range(self):
        for _ in range(30):
            val = self.gen._generate_device_profile()["mobile_usage"]
            self.assertGreaterEqual(val, 0.1)
            self.assertLessEqual(val, 0.4)

    def test_secondary_devices_is_list(self):
        self.assertIsInstance(self.gen._generate_device_profile()["secondary_devices"], list)


# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateNetworkProfile(unittest.TestCase):
    """BehavioralDataGenerator._generate_network_profile"""

    def setUp(self):
        self.gen = BehavioralDataGenerator()

    def test_returns_required_keys(self):
        result = self.gen._generate_network_profile("IT")
        for key in ("avg_daily_bandwidth_mb", "peak_hours",
                    "external_sites_accessed", "vpn_usage", "cloud_service_usage"):
            self.assertIn(key, result)

    def test_it_higher_avg_bandwidth_than_hr(self):
        it_vals = [self.gen._generate_network_profile("IT")["avg_daily_bandwidth_mb"]
                   for _ in range(10)]
        hr_vals = [self.gen._generate_network_profile("HR")["avg_daily_bandwidth_mb"]
                   for _ in range(10)]
        self.assertGreater(sum(it_vals) / 10, sum(hr_vals) / 10)


# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateFilePatterns(unittest.TestCase):
    """BehavioralDataGenerator._generate_file_patterns"""

    def setUp(self):
        self.gen = BehavioralDataGenerator()

    def test_returns_required_keys(self):
        result = self.gen._generate_file_patterns("IT", "Software Engineer")
        for key in ("file_types", "avg_files_per_day", "large_file_frequency",
                    "sensitive_file_access", "external_shares"):
            self.assertIn(key, result)

    def test_file_types_is_non_empty_list(self):
        result = self.gen._generate_file_patterns("Finance", "Accountant")
        self.assertIsInstance(result["file_types"], list)
        self.assertGreater(len(result["file_types"]), 0)

    def test_senior_role_has_higher_sensitive_access_than_junior(self):
        senior = self.gen._generate_file_patterns("IT", "Senior Engineer")
        junior = self.gen._generate_file_patterns("IT", "Engineer")
        self.assertGreater(
            senior["sensitive_file_access"],
            junior["sensitive_file_access"],
        )


# ─────────────────────────────────────────────────────────────────────────────

class TestAssignRiskFactors(unittest.TestCase):
    """BehavioralDataGenerator._assign_risk_factors"""

    def setUp(self):
        self.gen = BehavioralDataGenerator()

    def test_returns_all_five_keys(self):
        result = self.gen._assign_risk_factors()
        expected = {
            "financial_stress", "job_dissatisfaction",
            "recent_performance_issues", "external_relationships", "access_creep",
        }
        self.assertEqual(set(result.keys()), expected)

    def test_all_values_are_boolean(self):
        result = self.gen._assign_risk_factors()
        for key, val in result.items():
            self.assertIsInstance(val, bool, f"Risk factor '{key}' is not bool")


# ─────────────────────────────────────────────────────────────────────────────

class TestCreateActivity(unittest.TestCase):
    """BehavioralDataGenerator._create_activity — base and per-type keys"""

    def setUp(self):
        self.gen = BehavioralDataGenerator(num_users=3, num_days=1)
        self.gen.generate_user_profiles()
        self.user = self.gen.users[0]
        self.ts   = datetime(2024, 6, 15, 10, 0, 0)

    def _activity(self, activity_type, extra=None):
        return self.gen._create_activity(self.user, activity_type, self.ts, extra)

    # Base fields
    def test_base_keys_present(self):
        result = self._activity("login")
        for key in ("user_id", "username", "activity_type", "timestamp",
                    "source_ip", "user_agent", "device_info",
                    "is_suspicious", "confidence_score"):
            self.assertIn(key, result)

    def test_user_id_matches_user(self):
        self.assertEqual(self._activity("login")["user_id"], self.user["user_id"])

    def test_activity_type_is_set(self):
        self.assertEqual(self._activity("login")["activity_type"], "login")

    def test_timestamp_is_set(self):
        self.assertEqual(self._activity("login")["timestamp"], self.ts)

    def test_is_suspicious_defaults_to_false(self):
        self.assertFalse(self._activity("login")["is_suspicious"])

    def test_extra_data_is_merged(self):
        result = self._activity("login", {"success": True, "mfa_used": False})
        self.assertTrue(result["success"])
        self.assertFalse(result["mfa_used"])

    def test_extra_data_can_override_base_field(self):
        result = self._activity("login", {"is_suspicious": True})
        self.assertTrue(result["is_suspicious"])

    # Per-type key checks
    def _assert_keys(self, activity_type, keys):
        result = self._activity(activity_type)
        for key in keys:
            self.assertIn(key, result, f"Key '{key}' missing from '{activity_type}' activity")

    def test_file_access_keys(self):
        self._assert_keys("file_access", ["file_path", "file_size", "action", "permission_level"])

    def test_network_access_keys(self):
        self._assert_keys("network_access",
                          ["destination_ip", "destination_domain", "protocol",
                           "port", "bytes_transferred", "duration_seconds"])

    def test_email_sent_keys(self):
        self._assert_keys("email_sent",
                          ["recipient_count", "external_recipients",
                           "attachment_count", "sender_reputation"])

    def test_file_download_keys(self):
        self._assert_keys("file_download",
                          ["file_count", "total_size", "destination",
                           "transfer_speed_mbps", "transfer_method"])

    def test_file_upload_keys(self):
        self._assert_keys("file_upload",
                          ["file_count", "total_size", "destination",
                           "transfer_speed_mbps", "transfer_method"])

    def test_database_query_keys(self):
        self._assert_keys("database_query",
                          ["database_name", "query_type", "rows_affected",
                           "execution_time_ms", "sensitive_data_accessed"])

    def test_system_command_keys(self):
        self._assert_keys("system_command",
                          ["command", "arguments", "exit_code",
                           "execution_time_ms", "privilege_level"])

    def test_application_launch_keys(self):
        self._assert_keys("application_launch",
                          ["application_name", "version",
                           "session_duration_minutes", "memory_usage_mb"])

    def test_usb_access_keys(self):
        self._assert_keys("usb_access",
                          ["device_type", "device_id", "vendor",
                           "files_transferred", "data_transferred_mb"])


# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateIpAddress(unittest.TestCase):
    """BehavioralDataGenerator._generate_ip_address"""

    _IP_RE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")

    def setUp(self):
        self.gen = BehavioralDataGenerator(num_users=1, num_days=1)
        self.gen.generate_user_profiles()
        self.user = self.gen.users[0]

    def test_returns_valid_ipv4(self):
        for _ in range(20):
            ip = self.gen._generate_ip_address(self.user)
            self.assertRegex(ip, self._IP_RE, f"Invalid IP: {ip}")

    @patch("backend.ml_engine.data_generator.random.random", return_value=0.5)
    def test_internal_ip_when_random_below_threshold(self, _):
        # random.random() = 0.5 < 0.8  → internal range 192.168.1.x
        ip = self.gen._generate_ip_address(self.user)
        self.assertTrue(ip.startswith("192.168.1."), f"Expected internal IP, got {ip}")


# ─────────────────────────────────────────────────────────────────────────────

class TestChooseActivityType(unittest.TestCase):
    """BehavioralDataGenerator._choose_activity_type"""

    def setUp(self):
        self.gen = BehavioralDataGenerator(num_users=1, num_days=1)
        self.gen.generate_user_profiles()
        self.ts = datetime(2024, 6, 15, 10, 0, 0)

    def _run(self, dept):
        return self.gen._choose_activity_type({"department": dept}, self.ts)

    def test_it_returns_valid_activity(self):
        valid = {"file_access", "system_command", "database_query",
                 "network_access", "application_launch"}
        for _ in range(20):
            self.assertIn(self._run("IT"), valid)

    def test_finance_returns_valid_activity(self):
        valid = {"file_access", "database_query", "email_sent",
                 "application_launch", "file_download"}
        for _ in range(20):
            self.assertIn(self._run("Finance"), valid)

    def test_legal_returns_valid_activity(self):
        valid = {"file_access", "email_sent", "database_query", "application_launch"}
        for _ in range(20):
            self.assertIn(self._run("Legal"), valid)


# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateDailyActivities(unittest.TestCase):
    """BehavioralDataGenerator._generate_daily_activities"""

    def setUp(self):
        self.gen = BehavioralDataGenerator(num_users=5, num_days=1)
        self.gen.generate_user_profiles()
        self.user = self.gen.users[0]

    def test_weekday_produces_login_and_logout(self):
        monday = datetime(2024, 6, 10)
        types = [a["activity_type"]
                 for a in self.gen._generate_daily_activities(self.user, monday)]
        self.assertIn("login",  types)
        self.assertIn("logout", types)

    def test_weekday_produces_at_least_two_activities(self):
        monday = datetime(2024, 6, 10)
        activities = self.gen._generate_daily_activities(self.user, monday)
        self.assertGreaterEqual(len(activities), 2)

    @patch("backend.ml_engine.data_generator.random.random", return_value=0.99)
    def test_saturday_returns_empty_when_random_exceeds_weekend_work(self, _):
        # All dept weekend_work values ≤ 0.25 < 0.99 → always skip
        saturday = datetime(2024, 6, 15)
        self.assertEqual(
            self.gen._generate_daily_activities(self.user, saturday), []
        )

    def test_all_activities_have_correct_user_id(self):
        monday = datetime(2024, 6, 10)
        for a in self.gen._generate_daily_activities(self.user, monday):
            self.assertEqual(a["user_id"], self.user["user_id"])


# ══════════════════════════════════════════════════════════════════════════════
# BehavioralDataGenerator — Component Tests (Preprocessing Pipeline)
# ══════════════════════════════════════════════════════════════════════════════

class TestInjectAnomalies(unittest.TestCase):
    """Component: anomaly injection stage of the preprocessing pipeline"""

    def setUp(self):
        self.gen = BehavioralDataGenerator(num_users=20, num_days=1)
        self.gen.generate_user_profiles()
        start = datetime(2024, 6, 10)   # Monday
        end   = datetime(2024, 6, 11)
        self.normal = self.gen.generate_normal_activities(start, end)

    @patch("backend.ml_engine.data_generator.random.random", return_value=0.1)
    def test_injection_increases_total_count(self, _):
        # random.random()=0.1 is below every injection threshold (0.2-0.3)
        all_acts = self.gen.inject_anomalies(self.normal)
        self.assertGreater(len(all_acts), len(self.normal))

    def test_original_activities_preserved_in_output(self):
        all_acts = self.gen.inject_anomalies(self.normal)
        self.assertGreaterEqual(len(all_acts), len(self.normal))

    @patch("backend.ml_engine.data_generator.random.random", return_value=0.1)
    def test_anomalous_entries_are_marked_suspicious(self, _):
        # Guaranteed injection: random.random()=0.1 fires all probability checks
        all_acts = self.gen.inject_anomalies(self.normal)
        suspicious = [a for a in all_acts if a.get("is_suspicious")]
        self.assertGreater(len(suspicious), 0)
        for a in suspicious:
            self.assertTrue(a["is_suspicious"])

    def test_normal_input_activities_are_not_suspicious(self):
        for a in self.normal:
            self.assertFalse(a.get("is_suspicious", False))

    # Exfiltration anomaly structure
    def test_exfiltration_anomaly_required_fields(self):
        anomaly = self.gen._create_exfiltration_anomaly(self.gen.users[0], [])
        for key in ("is_suspicious", "confidence_score", "total_size",
                    "destination", "file_count", "anomaly_type", "risk_factors"):
            self.assertIn(key, anomaly)

    def test_exfiltration_anomaly_type_value(self):
        anomaly = self.gen._create_exfiltration_anomaly(self.gen.users[0], [])
        self.assertEqual(anomaly["anomaly_type"], "data_exfiltration")

    def test_exfiltration_anomaly_high_confidence_score(self):
        anomaly = self.gen._create_exfiltration_anomaly(self.gen.users[0], [])
        self.assertGreaterEqual(anomaly["confidence_score"], 0.7)

    def test_exfiltration_anomaly_large_file_size(self):
        anomaly = self.gen._create_exfiltration_anomaly(self.gen.users[0], [])
        self.assertGreaterEqual(anomaly["total_size"], 500 * 1024 * 1024)

    # Privilege anomaly structure
    def test_privilege_anomaly_required_fields(self):
        anomaly = self.gen._create_privilege_anomaly(self.gen.users[0], [])
        for key in ("is_suspicious", "confidence_score", "query_type",
                    "rows_affected", "tables_accessed", "anomaly_type"):
            self.assertIn(key, anomaly)

    def test_privilege_anomaly_type_value(self):
        anomaly = self.gen._create_privilege_anomaly(self.gen.users[0], [])
        self.assertEqual(anomaly["anomaly_type"], "privilege_abuse")

    def test_privilege_anomaly_large_row_count(self):
        anomaly = self.gen._create_privilege_anomaly(self.gen.users[0], [])
        self.assertGreaterEqual(anomaly["rows_affected"], 10_000)

    def test_privilege_anomaly_accesses_sensitive_data(self):
        anomaly = self.gen._create_privilege_anomaly(self.gen.users[0], [])
        self.assertTrue(anomaly["sensitive_data_accessed"])

    # Compromise anomaly structure
    def test_compromise_anomaly_required_fields(self):
        anomaly = self.gen._create_compromise_anomaly(self.gen.users[0], [])
        for key in ("is_suspicious", "confidence_score", "source_ip",
                    "device_info", "location", "login_attempts", "anomaly_type"):
            self.assertIn(key, anomaly)

    def test_compromise_anomaly_type_value(self):
        anomaly = self.gen._create_compromise_anomaly(self.gen.users[0], [])
        self.assertEqual(anomaly["anomaly_type"], "credential_compromise")

    def test_compromise_anomaly_multiple_login_attempts(self):
        anomaly = self.gen._create_compromise_anomaly(self.gen.users[0], [])
        self.assertGreaterEqual(anomaly["login_attempts"], 3)

    def test_compromise_anomaly_unknown_device(self):
        anomaly = self.gen._create_compromise_anomaly(self.gen.users[0], [])
        self.assertIn("Unknown_Device_", anomaly["device_info"])


# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateNormalActivities(unittest.TestCase):
    """Component: normal activity generation stage"""

    def setUp(self):
        self.gen = BehavioralDataGenerator(num_users=5, num_days=3)
        self.gen.generate_user_profiles()
        self.start = datetime(2024, 6, 10)   # Monday
        self.end   = datetime(2024, 6, 12)   # Wednesday

    def test_returns_non_empty_list(self):
        self.assertGreater(
            len(self.gen.generate_normal_activities(self.start, self.end)), 0
        )

    def test_all_activities_are_not_suspicious(self):
        for a in self.gen.generate_normal_activities(self.start, self.end):
            self.assertFalse(
                a.get("is_suspicious", True),
                "Normal activity generation produced a suspicious entry",
            )

    def test_all_user_ids_belong_to_known_users(self):
        valid_ids = {u["user_id"] for u in self.gen.users}
        for a in self.gen.generate_normal_activities(self.start, self.end):
            self.assertIn(a["user_id"], valid_ids)

    def test_timestamps_are_datetime_objects(self):
        for a in self.gen.generate_normal_activities(self.start, self.end):
            self.assertIsInstance(a["timestamp"], datetime)

    def test_timestamps_within_date_range(self):
        end_inclusive = datetime(2024, 6, 12, 23, 59, 59)
        for a in self.gen.generate_normal_activities(self.start, end_inclusive):
            self.assertGreaterEqual(a["timestamp"], self.start)
            self.assertLessEqual(a["timestamp"], end_inclusive)


# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateCompleteDataset(unittest.TestCase):
    """Component: end-to-end dataset generation pipeline"""

    def setUp(self):
        self.gen = BehavioralDataGenerator(num_users=10, num_days=2)

    def test_returns_tuple_of_two_lists(self):
        normal, anomalous = self.gen.generate_complete_dataset()
        self.assertIsInstance(normal,    list)
        self.assertIsInstance(anomalous, list)

    def test_normal_list_contains_no_suspicious_entries(self):
        normal, _ = self.gen.generate_complete_dataset()
        for a in normal:
            self.assertFalse(a.get("is_suspicious", False),
                             "Normal list contains a suspicious activity")

    def test_anomalous_list_contains_only_suspicious_entries(self):
        _, anomalous = self.gen.generate_complete_dataset()
        for a in anomalous:
            self.assertTrue(a.get("is_suspicious"),
                            "Anomalous list contains a non-suspicious entry")

    def test_normal_list_is_non_empty(self):
        normal, _ = self.gen.generate_complete_dataset()
        self.assertGreater(len(normal), 0)

    @patch("backend.ml_engine.data_generator.random.random", return_value=0.1)
    def test_anomalous_list_non_empty_with_guaranteed_injection(self, _):
        # random.random()=0.1 ensures all probability thresholds fire
        _, anomalous = self.gen.generate_complete_dataset()
        self.assertGreater(len(anomalous), 0)

    def test_users_populated_after_generation(self):
        self.gen.generate_complete_dataset()
        self.assertEqual(len(self.gen.users), 10)

    def test_normal_and_anomalous_are_disjoint_by_flag(self):
        normal, anomalous = self.gen.generate_complete_dataset()
        normal_ids    = {id(a) for a in normal}
        anomalous_ids = {id(a) for a in anomalous}
        # No object should appear in both lists
        self.assertEqual(len(normal_ids & anomalous_ids), 0)


# ══════════════════════════════════════════════════════════════════════════════
# LogProcessor — Component / Pipeline Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestLogProcessorPipeline(unittest.TestCase):
    """Component: multi-step ingest → analyze → filter pipeline"""

    def test_ingest_then_analyze_counts_all_entries(self):
        lp  = LogProcessor()
        now = datetime.now()
        ts  = (now - timedelta(minutes=5)).isoformat()

        lp.process_log_entry(make_raw_log(level="INFO",    user_id="u1", timestamp=ts))
        lp.process_log_entry(make_raw_log(level="WARNING", user_id="u1", timestamp=ts))
        entry = make_suspicious_raw_log("failed_login")
        entry.update({"timestamp": ts, "user_id": "u2"})
        lp.process_log_entry(entry)

        result = lp.analyze_logs()
        self.assertEqual(result["total_logs"], 3)
        self.assertEqual(result["suspicious_log_count"], 1)
        self.assertIn("u1", result["user_activity"])
        self.assertIn("u2", result["user_activity"])

    def test_process_then_filter_returns_correct_suspicious_subset(self):
        lp  = LogProcessor()
        now = datetime.now()
        ts  = (now - timedelta(minutes=5)).isoformat()

        lp.process_log_entry(make_raw_log(timestamp=ts))

        e1 = make_suspicious_raw_log("privilege_escalation")
        e1["timestamp"] = ts
        lp.process_log_entry(e1)

        e2 = make_suspicious_raw_log("network_anomaly")
        e2["timestamp"] = ts
        lp.process_log_entry(e2)

        suspicious = lp.get_suspicious_logs(hours=1)
        self.assertEqual(len(suspicious), 2)
        self.assertTrue(all(l["is_suspicious"] for l in suspicious))

    def test_bulk_ingest_then_pattern_detect(self):
        lp  = LogProcessor()
        now = datetime.now()
        ts  = (now - timedelta(minutes=30)).isoformat()

        for _ in range(10):
            e = make_suspicious_raw_log("failed_login")
            e["timestamp"] = ts
            lp.process_log_entry(e)

        for _ in range(5):
            lp.process_log_entry(make_raw_log(timestamp=ts))

        matched = lp.detect_patterns("failed_login")
        self.assertEqual(len(matched), 10)

    def test_multi_day_ingest_then_aggregate(self):
        lp = LogProcessor()
        for day in range(1, 4):
            for _ in range(3):
                lp.process_log_entry(
                    make_raw_log(timestamp=f"2024-06-{day:02d}T10:00:00")
                )

        result = lp.aggregate_by_time("day")
        self.assertEqual(result["2024-06-01"], 3)
        self.assertEqual(result["2024-06-02"], 3)
        self.assertEqual(result["2024-06-03"], 3)

    def test_clear_then_reanalyze_shows_reduced_count(self):
        lp  = LogProcessor()
        now = datetime.now()

        for _ in range(2):
            lp.process_log_entry(
                make_raw_log(timestamp=(now - timedelta(days=5)).isoformat())
            )
        lp.process_log_entry(
            make_raw_log(timestamp=(now - timedelta(days=100)).isoformat())
        )

        cleared = lp.clear_old_logs(days_old=90)
        self.assertEqual(cleared, 1)
        self.assertEqual(len(lp.processed_logs), 2)

    def test_export_then_reload_preserves_log_count(self):
        lp = LogProcessor()
        now = datetime.now()
        ts  = (now - timedelta(minutes=1)).isoformat()

        for _ in range(4):
            lp.process_log_entry(make_raw_log(timestamp=ts))

        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            lp.export_logs(path)
            with open(path) as f:
                reloaded = json.load(f)
            self.assertEqual(len(reloaded), 4)
        finally:
            os.unlink(path)


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
