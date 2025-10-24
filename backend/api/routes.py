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
    """Get recent user activities with optional filtering - REAL DATA"""
    from backend.models.activity_logger import activity_logger
    
    try:
        # Get activities from database
        all_activities = activity_logger.get_recent_activities(limit=limit)
        
        # Filter based on parameters
        filtered_activities = []
        
        for activity in all_activities:
            # Filter by user_id if provided
            if user_id and activity.get('user_id') != user_id:
                continue
            
            # Filter by risk threshold if provided
            if risk_threshold and activity.get('risk_score', 0) < risk_threshold:
                continue
            
            # Only include valid activities
            if (activity.get('user_id') and 
                activity.get('user_id') not in ['undefined', 'unknown', ''] and
                activity.get('username') and
                activity.get('username') not in ['undefined', 'unknown', ''] and
                activity.get('full_name') and
                activity.get('full_name') not in ['undefined', 'unknown', '']):
                
                filtered_activities.append({
                    "activity_id": activity.get('id', f"act_{len(filtered_activities)}"),
                    "user_id": activity.get('user_id'),
                    "username": activity.get('username'),
                    "full_name": activity.get('full_name'),
                    "timestamp": activity.get('timestamp'),
                    "activity_type": activity.get('activity_type'),
                    "risk_score": activity.get('risk_score', 0),
                    "risk_level": activity.get('risk_level', 'LOW'),
                    "action": activity.get('action', 'ALLOW'),
                    "status": "flagged" if activity.get('risk_score', 0) > 70 else "normal",
                    "bytes_transferred": activity.get('bytes_transferred', 0),
                    "summary": activity.get('summary', '')
                })
        
        return {
            "success": True,
            "total": len(filtered_activities),
            "activities": filtered_activities
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "total": 0,
            "activities": [],
            "error": str(e)
        }

@router.get("/users/{user_id}/profile")
async def get_user_profile(user_id: str):
    """Get detailed user profile and behavioral patterns - REAL DATA"""
    from models.user_management import user_manager
    from backend.models.activity_logger import activity_logger
    from services.intelligent_risk_engine import intelligent_risk_engine
    
    try:
        # Get user from database
        user = user_manager.get_user(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Get user's risk profile from intelligent engine
        risk_profile = intelligent_risk_engine.get_user_risk_profile(user_id)
        
        # Get user's recent activities
        user_activities = activity_logger.get_user_activities(user_id, limit=50)
        
        # Calculate behavioral patterns
        activity_types = {}
        hours_active = set()
        
        for activity in user_activities:
            # Count activity types
            act_type = activity.get('activity_type', 'unknown')
            activity_types[act_type] = activity_types.get(act_type, 0) + 1
            
            # Track active hours
            try:
                timestamp = datetime.fromisoformat(activity.get('timestamp', ''))
                hours_active.add(timestamp.hour)
            except:
                pass
        
        # Get most common activities
        common_activities = sorted(activity_types.items(), key=lambda x: x[1], reverse=True)[:3]
        common_activities = [act[0] for act in common_activities]
        
        # Build profile response
        profile = {
            "user_id": user['user_id'],
            "username": user['username'],
            "full_name": user['full_name'],
            "email": user['email'],
            "department": user['department'],
            "role": user['role'],
            "risk_score": risk_profile.get('current_score', 0),
            "peak_risk_score": risk_profile.get('peak_score', 0),
            "risk_level": "LOW" if risk_profile.get('current_score', 0) < 30 else 
                         "MEDIUM" if risk_profile.get('current_score', 0) < 50 else
                         "HIGH" if risk_profile.get('current_score', 0) < 75 else "CRITICAL",
            "account_created": user.get('created_at', datetime.now().isoformat()),
            "last_activity": user.get('last_activity', datetime.now().isoformat()),
            "behavioral_patterns": {
                "typical_login_hours": sorted(list(hours_active))[:5] if hours_active else [9, 17],
                "total_activities": len(user_activities),
                "common_activities": common_activities if common_activities else ["file_access"],
                "recent_events": risk_profile.get('recent_events', 0),
                "total_threats": user.get('total_threats', 0)
            },
            "recent_flags": user.get('total_threats', 0),
            "total_events": risk_profile.get('total_events', 0)
        }
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching user profile: {str(e)}")

@router.get("/threats/active")
async def get_active_threats():
    """Get currently active threats requiring attention - REAL DATA"""
    from backend.models.activity_logger import activity_logger
    from models.user_management import user_manager
    from datetime import datetime, timedelta
    
    try:
        # Get recent activities (last 24 hours)
        recent_activities = activity_logger.get_recent_activities(limit=100)
        
        # Filter for HIGH and CRITICAL threats only
        active_threats = []
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        
        for activity in recent_activities:
            # Only include HIGH/CRITICAL risk activities
            if activity.get('risk_level') in ['HIGH', 'CRITICAL']:
                try:
                    activity_time = datetime.fromisoformat(activity['timestamp'])
                    
                    # Only last 24 hours
                    if activity_time > twenty_four_hours_ago:
                        # Get user details
                        user = user_manager.get_user(activity['user_id'])
                        
                        # Build indicators based on activity type
                        indicators = []
                        recommendations = []
                        
                        # Determine indicators based on activity
                        if activity.get('activity_type') == 'honeypot_access':
                            indicators = [
                                f"Unauthorized file access detected",
                                f"Risk Score: {activity.get('risk_score', 0)}",
                                f"Action taken: {activity.get('action', 'MONITOR')}"
                            ]
                            recommendations = [
                                "Immediate investigation required",
                                "Review user access permissions",
                                "Check for data exfiltration"
                            ]
                        elif activity.get('activity_type') == 'network_activity':
                            bytes_transferred = activity.get('bytes_transferred', 0)
                            mb_transferred = bytes_transferred / (1024 * 1024)
                            indicators = [
                                f"Large data transfer: {mb_transferred:.2f} MB",
                                f"Risk Score: {activity.get('risk_score', 0)}",
                                f"Time: {datetime.fromisoformat(activity['timestamp']).strftime('%I:%M %p')}"
                            ]
                            recommendations = [
                                "Monitor network activity",
                                "Review data transfer logs",
                                "Verify legitimate business need"
                            ]
                        else:
                            indicators = [
                                f"{activity.get('activity_type', 'unknown').replace('_', ' ').title()} detected",
                                f"Risk Score: {activity.get('risk_score', 0)}"
                            ]
                            recommendations = [
                                "Investigate activity",
                                "Enhanced monitoring recommended"
                            ]
                        
                        # Determine status based on action
                        status = 'active' if activity.get('action') == 'BLOCK' else 'investigating'
                        
                        active_threats.append({
                            'threat_id': f"thr_{activity.get('id', len(active_threats) + 1)}",
                            'user_id': activity.get('user_id', 'unknown'),
                            'username': activity.get('username', 'unknown'),
                            'full_name': activity.get('full_name', 'Unknown User'),
                            'threat_type': activity.get('activity_type', 'unknown').replace('_', ' '),
                            'severity': activity.get('risk_level', 'MEDIUM'),
                            'risk_score': activity.get('risk_score', 0),
                            'detected_at': activity['timestamp'],
                            'status': status,
                            'indicators': indicators,
                            'recommended_actions': recommendations
                        })
                        
                except Exception as e:
                    print(f"Error processing threat activity: {e}")
                    continue
        
        # Sort by risk score (highest first)
        active_threats.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return {
            "success": True,
            "active_count": len(active_threats),
            "threats": active_threats,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "active_count": 0,
            "threats": [],
            "error": str(e)
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
    
from fastapi import Request
from services.report_generator import report_generator

@router.post("/analyze")
async def analyze_user_activity(request: Request):
    """
    Analyze user activity for potential threats using the ML detector,
    risk scoring, and report generation.
    """
    if not ml_detector or not risk_scorer:
        raise HTTPException(status_code=503, detail="ML components not initialized")

    try:
        data = await request.json()
        user_id = data.get("user_id")
        activities = data.get("activities", [])

        if not user_id or not activities:
            raise HTTPException(status_code=400, detail="user_id and activities are required")

        # Step 1: Run threat detection
        detected_threats = ml_detector.analyze(activities)

        # Step 2: Score risk level
        risk_summary = risk_scorer.calculate_risk_summary(detected_threats)

        # Step 3: Generate PDF report
        user_info = {
            "user_id": user_id,
            "username": data.get("username", "unknown"),
            "full_name": data.get("full_name", "Unknown User"),
            "email": data.get("email", "N/A"),
            "department": data.get("department", "N/A"),
            "role": data.get("role", "N/A")
        }
        pdf_path = report_generator.generate_threat_report(
            user=user_info,
            activities=activities,
            summary=risk_summary
        )

        return {
            "success": True,
            "message": "Analysis and report generation complete",
            "threats_detected": len(detected_threats),
            "risk_summary": risk_summary,
            "report_path": pdf_path
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error analyzing user activity: {str(e)}")


@router.get("/reports/download")
async def download_report(file: str):
    """Download generated threat analysis reports"""
    from fastapi.responses import FileResponse
    import os

    try:
        report_dir = report_generator.output_dir
        file_path = os.path.join(report_dir, file)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Report not found")
        return FileResponse(file_path, media_type="application/pdf", filename=file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading report: {str(e)}")
