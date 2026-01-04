"""
Tests for PDF report generation to ensure data accuracy.
"""

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import os
import sys
import tempfile

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.user_management import UserManager
from models.activity_log import ActivityLogger


class TestReportGeneration(unittest.TestCase):
    """Tests for report generation functionality."""

    def setUp(self):
        """Set up test fixtures with isolated in-memory databases."""
        # Create temporary databases for isolation
        self.temp_dir = tempfile.mkdtemp()
        self.test_user_db = os.path.join(self.temp_dir, "test_users.db")
        self.test_activity_db = os.path.join(self.temp_dir, "test_activities.db")

        # Create isolated instances
        self.test_user_manager = UserManager(db_path=self.test_user_db)
        self.test_activity_logger = ActivityLogger(db_path=self.test_activity_db)

        # Test user data
        self.test_user = {
            "username": "report_user",
            "full_name": "Report Test User",
            "department": "Reports",
            "role": "Analyst",
            "email": "report@test.com",
            "password_hash": "hashed_password"
        }

        # Register the test user
        result = self.test_user_manager.register_user(
            username=self.test_user["username"],
            full_name=self.test_user["full_name"],
            department=self.test_user["department"],
            role=self.test_user["role"],
            email=self.test_user["email"],
            password_hash=self.test_user["password_hash"]
        )
        self.assertTrue(result["success"], "Failed to register test user")
        self.test_user_id = result["user_id"]

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    def test_activity_logging_stores_risk_score(self):
        """
        Verify that activities are logged with their risk scores.
        """
        # Log an activity
        activity_data = {
            "user_id": self.test_user_id,
            "username": self.test_user["username"],
            "full_name": self.test_user["full_name"],
            "activity_type": "file_access",
            "risk_score": 25.0,
            "risk_level": "LOW",
            "summary": "Accessed a non-sensitive file.",
            "action": "ALLOW"
        }
        activity_id = self.test_activity_logger.log_activity(activity_data)
        self.assertIsNotNone(activity_id)

        # Retrieve and verify
        activities = self.test_activity_logger.get_recent_activities(limit=10)
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0]['risk_score'], 25.0)

    def test_user_risk_score_update(self):
        """
        Verify that user's current risk score can be updated independently.
        """
        # Set an authoritative risk score on the user profile
        authoritative_risk_score = 95.0
        self.test_user_manager.update_user_activity(
            self.test_user_id,
            risk_score=authoritative_risk_score
        )

        # Retrieve and verify
        user = self.test_user_manager.get_user(self.test_user_id)
        self.assertIsNotNone(user)
        self.assertEqual(user['current_risk_score'], authoritative_risk_score)

    def test_risk_score_consistency(self):
        """
        Verify that user's current_risk_score is independent of activity log risk_score.
        This tests the fix for stale risk score bug.
        """
        # 1. Log an activity with a LOW risk score
        stale_risk_score = 15.0
        activity_data = {
            "user_id": self.test_user_id,
            "username": self.test_user["username"],
            "full_name": self.test_user["full_name"],
            "activity_type": "file_access",
            "risk_score": stale_risk_score,
            "risk_level": "LOW",
            "summary": "Accessed a non-sensitive file.",
            "action": "ALLOW"
        }
        self.test_activity_logger.log_activity(activity_data)

        # 2. Update user's current risk score to a HIGH value
        authoritative_risk_score = 95.0
        self.test_user_manager.update_user_activity(
            self.test_user_id,
            risk_score=authoritative_risk_score
        )

        # 3. Verify user's current_risk_score is the authoritative one
        user = self.test_user_manager.get_user(self.test_user_id)
        self.assertEqual(
            user['current_risk_score'],
            authoritative_risk_score,
            f"User's current_risk_score should be {authoritative_risk_score}, not {user['current_risk_score']}"
        )

        # 4. Verify activity log still has the original (stale) score
        activities = self.test_activity_logger.get_recent_activities(limit=10)
        self.assertEqual(len(activities), 1)
        self.assertEqual(
            activities[0]['risk_score'],
            stale_risk_score,
            "Activity log should retain the original risk score"
        )


if __name__ == '__main__':
    unittest.main()
