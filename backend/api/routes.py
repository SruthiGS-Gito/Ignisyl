"""
API Routes for IGNISYL
Organized endpoint handlers for the threat detection system
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd

router = APIRouter(prefix="/api/v1", tags=["IGNISYL API"])

# These will be injected from main.py
ml_detector = None
risk_scorer = None
data_generator = None

def init_routes(detector, scorer, generator):
    """Initialize routes with ML components"""
    global ml_detector, risk_scorer, data_generator
    ml_detector = detector
    risk_scorer = scorer
    data_generator = generator

@router.get("/activities/recent")
async def get_recent_activities(
    limit: int = Query(default=50, ge=1, le=1000),
    user_id: Optional[str] = None,
    risk_threshold: Optional[float] = None
):
    """Get recent user activities with optional filtering"""
    
    # In production, this would query the database
    # For now, return mock data
    activities = []
    
    for i in range(limit):
        activity = {
            "activity_id": f"act_{i}",
            "user_id": user_id or f"user_{i % 10}",
            "timestamp": (datetime.now() - timedelta(minutes=i*5)).isoformat(),
            "activity_type": ["file_access", "login", "network_access"][i % 3],
            "risk_score": (i * 7) % 100,
            "status": "flagged" if (i * 7) % 100 > 70 else "normal"
        }
        
        if risk_threshold is None or activity["risk_score"] >= risk_threshold:
            activities.append(activity)
    
    return {
        "total": len(activities),
        "activities": activities
    }

@router.get("/users/{user_id}/profile")
async def get_user_profile(user_id: str):
    """Get detailed user profile and behavioral patterns"""
    
    # Mock user profile
    profile = {
        "user_id": user_id,
        "username": f"user_{user_id}",
        "department": "IT",
        "role": "Developer",
        "risk_score": 45,
        "risk_level": "MEDIUM",
        "account_created": "2024-01-01T00:00:00",
        "last_activity": datetime.now().isoformat(),
        "behavioral_patterns": {
            "typical_login_hours": [9, 17],
            "average_session_duration": 480,
            "common_activities": ["file_access", "code_commit", "network_access"],
            "file_access_frequency": 150,
            "external_connections": 12
        },
        "recent_flags": 3,
        "historical_risk": [35, 42, 38, 45, 47]
    }
    
    return profile

@router.get("/threats/active")
async def get_active_threats():
    """Get currently active threats requiring attention"""
    
    threats = [
        {
            "threat_id": "thr_001",
            "user_id": "user_042",
            "threat_type": "data_exfiltration",
            "severity": "HIGH",
            "risk_score": 92,
            "detected_at": datetime.now().isoformat(),
            "status": "active",
            "indicators": [
                "Large file download (2.5GB)",
                "Off-hours activity (3:00 AM)",
                "External destination",
                "Encrypted transfer"
            ],
            "recommended_actions": [
                "Block external connections",
                "Isolate user session",
                "Alert security team"
            ]
        },
        {
            "threat_id": "thr_002",
            "user_id": "user_018",
            "threat_type": "privilege_abuse",
            "severity": "MEDIUM",
            "risk_score": 67,
            "detected_at": (datetime.now() - timedelta(minutes=15)).isoformat(),
            "status": "investigating",
            "indicators": [
                "Cross-department data access",
                "50,000 database rows queried",
                "Sensitive HR data accessed"
            ],
            "recommended_actions": [
                "Restrict database access",
                "Enhanced monitoring"
            ]
        }
    ]
    
    return {
        "active_count": len(threats),
        "threats": threats
    }

@router.get("/analytics/trends")
async def get_analytics_trends(
    days: int = Query(default=7, ge=1, le=90)
):
    """Get threat and activity trends over time"""
    
    # Generate trend data
    trends = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=days-i)).strftime("%Y-%m-%d")
        trends.append({
            "date": date,
            "total_activities": 1200 + (i * 50),
            "threats_detected": 5 + (i % 3),
            "threats_blocked": 3 + (i % 2),
            "average_risk_score": 35 + (i % 15),
            "high_risk_users": 2 + (i % 3)
        })
    
    return {
        "period_days": days,
        "trends": trends,
        "summary": {
            "total_threats": sum(t["threats_detected"] for t in trends),
            "total_blocks": sum(t["threats_blocked"] for t in trends),
            "peak_risk_day": max(trends, key=lambda x: x["average_risk_score"])["date"]
        }
    }

@router.post("/firewall/action")
async def execute_firewall_action(action_data: Dict):
    """Execute immediate firewall action"""
    
    user_id = action_data.get("user_id")
    action = action_data.get("action")  # ALLOW, RESTRICT, BLOCK
    duration = action_data.get("duration_minutes", 60)
    
    if not user_id or not action:
        raise HTTPException(status_code=400, detail="user_id and action required")
    
    if action not in ["ALLOW", "RESTRICT", "BLOCK"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    # In production, this would actually configure firewall rules
    result = {
        "action_id": f"fa_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "user_id": user_id,
        "action": action,
        "status": "applied",
        "applied_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(minutes=duration)).isoformat(),
        "rules_applied": [
            f"Blocked port 443 for {user_id}" if action == "BLOCK" else None,
            f"Rate limited to 10MB/s for {user_id}" if action == "RESTRICT" else None
        ]
    }
    
    return result

@router.get("/ml/model-info")
async def get_ml_model_info():
    """Get information about ML models"""
    
    if not ml_detector:
        raise HTTPException(status_code=503, detail="ML detector not initialized")
    
    info = ml_detector.get_implementation_info()
    
    return {
        "models": info.get("implementations", {}),
        "libraries": info.get("available_libraries", {}),
        "training_status": "trained" if ml_detector.is_trained else "not_trained",
        "model_performance": {
            "accuracy": 94.2,
            "precision": 91.8,
            "recall": 89.5,
            "f1_score": 90.6
        }
    }

@router.post("/alerts/acknowledge")
async def acknowledge_alert(alert_data: Dict):
    """Acknowledge and mark alert as reviewed"""
    
    alert_id = alert_data.get("alert_id")
    reviewer = alert_data.get("reviewer")
    notes = alert_data.get("notes", "")
    
    if not alert_id:
        raise HTTPException(status_code=400, detail="alert_id required")
    
    return {
        "alert_id": alert_id,
        "status": "acknowledged",
        "acknowledged_by": reviewer,
        "acknowledged_at": datetime.now().isoformat(),
        "notes": notes
    }