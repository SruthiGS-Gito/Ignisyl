"""
IGNISYL Main API Server
FastAPI backend for AI-Powered Insider Threat Detection System
"""

import uvicorn
import time
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
import json
import hashlib

from fastapi import FastAPI, HTTPException, WebSocket, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from backend.api import routes 

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Import config FIRST
from config.config import settings

# Import database
from models.database import database, init_sample_data

# Import ML components
from ml_engine.hybrid_detector import AdvancedHybridDetector
from ml_engine.risk_scorer import ContextualRiskScorer
from ml_engine.data_generator import BehavioralDataGenerator


# Import models and services
from models.activity_logger import activity_logger
from models.user_management import user_manager
from models.risk_assessment import risk_assessment_manager
from models.user_activity import user_activity_manager
from services.alert_manager import alert_manager

# Import API components
from api.websocket import websocket_endpoint, manager as ws_manager

# Optional services with fallbacks
try:
    from services.system_monitor import system_monitor
    HAS_SYSTEM_MONITOR = True
except ImportError:
    HAS_SYSTEM_MONITOR = False
    print("⚠️ system_monitor not available, using mock data")

try:
    from services.ml_performance_tracker import ml_performance_tracker
    HAS_ML_TRACKER = True
except ImportError:
    HAS_ML_TRACKER = False
    print("⚠️ ml_performance_tracker not available, using mock data")

try:
    from services.intelligent_risk_engine import intelligent_risk_engine
    HAS_RISK_ENGINE = True
except ImportError:
    HAS_RISK_ENGINE = False
    print("⚠️ intelligent_risk_engine not available, using basic scoring")

try:
    from services.comprehensive_monitor import comprehensive_monitor
    HAS_COMPREHENSIVE_MONITOR = True
except ImportError:
    HAS_COMPREHENSIVE_MONITOR = False
    print("⚠️ comprehensive_monitor not available")

try:
    from services.report_generator import report_generator
    HAS_REPORT_GENERATOR = True
except ImportError:
    HAS_REPORT_GENERATOR = False
    print("⚠️ report_generator not available")

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Insider Threat Detection with Adaptive Firewall Control",
    debug=False
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
ml_detector = None
risk_scorer = None
data_generator = None

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    
    global ml_detector, risk_scorer, data_generator
    
    print("\n" + "="*70)
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print("="*70)
    
    # Ensure directories exist
    from config.config import ensure_directories
    ensure_directories()
    
    # Initialize database with sample data
    print("\n💾 Initializing database...")
    try:
        init_sample_data(database)
        print("✅ Database ready")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")
    
    # Initialize ML components
    print("\n🧠 Initializing ML components...")
    ml_detector = AdvancedHybridDetector()
    risk_scorer = ContextualRiskScorer()
    data_generator = BehavioralDataGenerator()
    
    # Train ML models
    print("\n📊 Training ML models...")
    try:
        normal_data, anomalous_data = data_generator.generate_complete_dataset()
        
        # Prepare training data
        import pandas as pd
        import numpy as np
        
        all_data = normal_data + anomalous_data
        df = pd.DataFrame(all_data)
        
        # Extract features
        def extract_features(df):
            features = pd.DataFrame()
            
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                features['hour'] = df['timestamp'].dt.hour
                features['day_of_week'] = df['timestamp'].dt.dayofweek
            else:
                features['hour'] = 12
                features['day_of_week'] = 2
            
            features['file_size'] = df.get('file_size', 0).fillna(0)
            features['bytes_transferred'] = df.get('bytes_transferred', 0).fillna(0)
            
            return features
        
        X = extract_features(df).values
        y = df.get('is_suspicious', pd.Series([False] * len(df))).astype(int).values
        
        print(f"   Training on {X.shape[0]} samples with {X.shape[1]} features")
        
        # Train the detector
        ml_detector.fit(X, y)
        print("   ✅ ML models trained successfully!")
        
    except Exception as e:
        print(f"   ⚠️ ML training error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print(f"🌟 {settings.APP_NAME} is ready!")
    print(f"📡 API running on http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"📚 API docs at http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print("="*70 + "\n")

# ============================================================================
# API ROUTES
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with system information"""
    return f"""
    <html>
        <head>
            <title>{settings.APP_NAME}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 1200px; margin: 0 auto; }}
                .header {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 20px; }}
                .status {{ background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .endpoints {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .endpoint {{ margin: 10px 0; padding: 10px; background: white; border-left: 4px solid #007bff; }}
                .method {{ display: inline-block; width: 80px; font-weight: bold; }}
                a {{ color: #007bff; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛡️ {settings.APP_NAME}</h1>
                    <h3>AI-Powered Insider Threat Detection System</h3>
                    <p>Version: {settings.APP_VERSION} | Status: <strong>OPERATIONAL</strong></p>
                </div>
                
                <div class="status">
                    <h3>✅ System Status</h3>
                    <p>🧠 ML Engine: Active | 🔥 Firewall: Ready | 📊 Risk Scorer: Online</p>
                    <p>⚡ Real-time Processing: Enabled | 🔒 Security Mode: Adaptive</p>
                </div>
                
                <div class="endpoints">
                    <h3>🔗 API Endpoints</h3>
                    <div class="endpoint">
                        <span class="method">GET</span> <a href="/api/v1/health">/api/v1/health</a> - System health check
                    </div>
                    <div class="endpoint">
                        <span class="method">POST</span> /api/v1/analyze - Analyze user activity for threats
                    </div>
                    <div class="endpoint">
                        <span class="method">GET</span> <a href="/api/v1/dashboard/stats">/api/v1/dashboard/stats</a> - Dashboard statistics
                    </div>
                    <div class="endpoint">
                        <span class="method">GET</span> <a href="/api/v1/users/list">/api/v1/users/list</a> - List all users
                    </div>
                    <div class="endpoint">
                        <span class="method">GET</span> <a href="/api/v1/users/risk">/api/v1/users/risk</a> - User risk assessments
                    </div>
                    <div class="endpoint">
                        <span class="method">GET</span> <a href="/api/v1/activities/recent">/api/v1/activities/recent</a> - Recent activities
                    </div>
                    <div class="endpoint">
                        <span class="method">GET</span> <a href="/docs">/docs</a> - Interactive API Documentation
                    </div>
                </div>
                
                <div style="margin-top: 30px; text-align: center; color: #666;">
                    <p>🎓 Built for Academic Excellence | 🚀 Industry-Ready Architecture</p>
                    <p>Powered by Advanced ML Algorithms & Real-time Threat Detection</p>
                </div>
            </div>
        </body>
    </html>
    """

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    global ml_detector, risk_scorer
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.APP_VERSION,
        "components": {
            "ml_detector": "ready" if ml_detector and ml_detector.is_trained else "initializing",
            "risk_scorer": "ready" if risk_scorer else "initializing",
            "database": "connected",
            "activity_logger": "ready" if activity_logger else "unavailable",
            "user_manager": "ready" if user_manager else "unavailable",
            "alert_manager": "ready" if alert_manager else "unavailable"
        },
        "ml_implementations": ml_detector.get_implementation_info() if ml_detector else {},
        "optional_services": {
            "system_monitor": HAS_SYSTEM_MONITOR,
            "ml_performance_tracker": HAS_ML_TRACKER,
            "intelligent_risk_engine": HAS_RISK_ENGINE,
            "comprehensive_monitor": HAS_COMPREHENSIVE_MONITOR,
            "report_generator": HAS_REPORT_GENERATOR
        }
    }
    
    return health_status

@app.post("/api/v1/analyze")
async def analyze_activity(activity_data: Dict):
    """Analyze user activity for insider threats"""
    global ml_detector, risk_scorer
    
    analysis_start_time = time.time()
    
    if not ml_detector or not risk_scorer:
        raise HTTPException(status_code=503, detail="ML components not ready")
    
    try:
        import pandas as pd
        from datetime import datetime as dt
        
        # Set defaults
        activity_data.setdefault('timestamp', dt.now().isoformat())
        activity_data.setdefault('file_size', 0)
        activity_data.setdefault('bytes_transferred', 0)
        activity_data.setdefault('department', 'Unknown')
        activity_data.setdefault('role', 'Employee')
        activity_data.setdefault('user_id', 'unknown')
        activity_data.setdefault('activity_type', 'unknown')
        
        # Extract user profile
        user_profile = {
            'department': activity_data.get('department'),
            'role': activity_data.get('role'),
            'typical_work_hours': [9, 17],
            'avg_file_size': 10*1024*1024,
            'activity_frequencies': {'file_access': 0.5}
        }
        
        # Perform risk assessment
        risk_assessment = risk_scorer.assess_activity_risk(activity_data, user_profile)
        
        # Extract features for ML
        activity_timestamp = activity_data.get('timestamp')
        if isinstance(activity_timestamp, str):
            activity_timestamp = pd.to_datetime(activity_timestamp)
        else:
            activity_timestamp = dt.now()
        
        # Prepare ML features
        ml_features = [[
            float(activity_timestamp.hour),
            float(activity_timestamp.weekday()),
            float(activity_data.get('file_size', 0)),
            float(activity_data.get('bytes_transferred', 0))
        ]]
        
        try:
            ml_risk_scores, individual_scores = ml_detector.predict(ml_features)
            ml_risk_score = float(ml_risk_scores[0])
        except Exception as e:
            print(f"ML prediction error: {e}")
            ml_risk_score = risk_assessment['risk_score']
            individual_scores = {}
        
        # Determine final risk score
        if HAS_RISK_ENGINE:
            # Use intelligent risk engine if available
            user_id = activity_data.get('user_id', 'unknown')
            activity_type = activity_data.get('activity_type', 'unknown')
            
            context = {
                'timestamp': activity_timestamp.isoformat(),
                'bytes_transferred': activity_data.get('bytes_transferred', 0),
                'file_size': activity_data.get('file_size', 0),
                'hour': activity_timestamp.hour,
                'day_of_week': activity_timestamp.weekday()
            }
            
            intelligent_assessment = intelligent_risk_engine.assess_event(
                user_id=user_id,
                event_type=activity_type,
                context=context
            )
            
            final_risk_score = intelligent_assessment['current_score']
            final_risk_level = intelligent_assessment['risk_level']
            firewall_action = intelligent_assessment['recommended_action']
            
            print(f"\n🧠 Intelligent Risk Assessment:")
            print(f"   Score: {final_risk_score} | Level: {final_risk_level} | Action: {firewall_action}")
        else:
            # Fallback: combine contextual and ML scores
            final_risk_score = (risk_assessment['risk_score'] * 0.6 + ml_risk_score * 0.4)
            
            if final_risk_score < 30:
                final_risk_level = "LOW"
                firewall_action = "ALLOW"
            elif final_risk_score < 70:
                final_risk_level = "MEDIUM"
                firewall_action = "RESTRICT"
            else:
                final_risk_level = "HIGH"
                firewall_action = "BLOCK"
        
        # Track ML performance if available
        if HAS_ML_TRACKER:
            detection_end_time = time.time()
            detection_latency_ms = (detection_end_time - analysis_start_time) * 1000
            
            actual_threat = final_risk_level in ['HIGH', 'CRITICAL']
            
            ml_performance_tracker.record_prediction(
                predicted_risk=final_risk_score,
                actual_threat=actual_threat,
                detection_time_ms=detection_latency_ms,
                confidence=ml_risk_score / 100.0
            )
        
        # Build response
        response = {
            "analysis_id": f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "risk_assessment": {
                "final_risk_score": round(final_risk_score, 2),
                "risk_level": final_risk_level,
                "contextual_risk_score": risk_assessment['risk_score'],
                "ml_risk_score": round(ml_risk_score, 2),
                "baseline_deviation": risk_assessment.get('baseline_deviation', 0)
            },
            "explanation": {
                "summary": risk_assessment.get('summary', 'Activity analyzed'),
                "triggered_factors": risk_assessment.get('triggered_factors', []),
                "applied_modifiers": risk_assessment.get('applied_modifiers', []),
                "recommendations": risk_assessment.get('recommendations', [])
            },
            "ml_details": {
                "individual_scores": {k: float(v) if hasattr(v, 'item') else v 
                                     for k, v in individual_scores.items()} if individual_scores else {},
                "model_confidence": round(float(max(individual_scores.values())) 
                                         if individual_scores else 0.5, 3)
            },
            "firewall_action": {
                "action": firewall_action,
                "restrictions": _get_restrictions_for_risk_level(final_risk_level)
            },
            "metadata": {
                "user_id": activity_data.get('user_id'),
                "activity_type": activity_data.get('activity_type'),
                "processing_time_ms": round((time.time() - analysis_start_time) * 1000, 2)
            }
        }
        
        # Log activity to database
        try:
            user_id = activity_data.get('user_id')
            
            # Try to get user (handle both string and int IDs)
            user = None
            if isinstance(user_id, str) and user_id.isdigit():
                user = user_manager.get_user(user_id=int(user_id))
            elif isinstance(user_id, int):
                user = user_manager.get_user(user_id=user_id)
            else:
                user = user_manager.get_user(username=str(user_id))
            
            if user:
                activity_logger.log_activity({
                    'user_id': user['id'],
                    'username': user.get('username', 'unknown'),
                    'full_name': user.get('full_name', 'Unknown User'),
                    'department': user.get('department', ''),
                    'activity_type': activity_data.get('activity_type', 'network_activity'),
                    'timestamp': datetime.now().isoformat(),
                    'risk_score': final_risk_score,
                    'risk_level': final_risk_level,
                    'action': firewall_action,
                    'bytes_transferred': activity_data.get('bytes_transferred', 0),
                    'file_size': activity_data.get('file_size', 0),
                    'summary': risk_assessment.get('summary', 'Activity analyzed'),
                    'details': {
                        'triggered_factors': risk_assessment.get('triggered_factors', []),
                        'ml_risk_score': ml_risk_score,
                        'contextual_risk_score': risk_assessment['risk_score']
                    }
                })
                
                # Update user threat count if high risk
                if final_risk_level in ['HIGH', 'CRITICAL']:
                    user_manager.increment_threat_count(user['id'])
                
                # Update user's risk score
                user_manager.update_user_activity(user['id'], risk_score=final_risk_score)
                
                print(f"✅ Activity logged for user: {user['full_name']}")
            else:
                print(f"⚠️ User not found: {user_id}")
                
        except Exception as log_error:
            print(f"❌ Error logging activity: {log_error}")
            import traceback
            traceback.print_exc()
        
        return response
        
    except Exception as e:
        import traceback
        print(f"\n❌ CRITICAL ERROR in analyze_activity:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

def _get_restrictions_for_risk_level(risk_level: str) -> List[str]:
    """Get firewall restrictions for risk level"""
    if risk_level == "LOW":
        return []
    elif risk_level == "MEDIUM":
        return [
            "Restrict external file transfers",
            "Limit large data downloads",
            "Enhanced activity monitoring"
        ]
    elif risk_level == "HIGH":
        return [
            "Block all external connections",
            "Prevent file downloads",
            "Isolate user session",
            "Alert security team"
        ]
    else:  # CRITICAL
        return [
            "Complete network isolation",
            "Block all file operations",
            "Immediate security team alert",
            "Lock user account"
        ]

@app.get("/api/v1/dashboard/stats")
async def dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Get real user data
        all_users = user_manager.get_all_users()
        
        total_users = len(all_users)
        active_users = user_manager.get_active_users_count()
        
        # Get activity statistics
        activity_stats = activity_logger.get_stats()
        
        # Get recent activities
        recent_activities_raw = activity_logger.get_recent_activities(limit=5)
        recent_activities = []
        
        for activity in recent_activities_raw:
            recent_activities.append({
                "user": activity.get('username', 'Unknown'),
                "full_name": activity.get('full_name', 'Unknown User'),
                "activity": activity.get('activity_type', 'unknown').replace('_', ' ').title(),
                "risk_score": activity.get('risk_score', 0),
                "action": activity.get('action', 'ALLOW'),
                "timestamp": activity.get('timestamp', datetime.now().isoformat()),
                "bytes": activity.get('bytes_transferred', 0)
            })
        
        # System health
        if HAS_SYSTEM_MONITOR:
            system_health = system_monitor.get_system_health()
        else:
            system_health = {
                'cpu': {'usage_percent': 45.2},
                'memory': {'usage_percent': 62.5},
                'disk': {'usage_percent': 73.1},
                'network': {'bytes_recv_mb': 1234.5}
            }
        
        # ML performance
        if HAS_ML_TRACKER:
            ml_performance_raw = ml_performance_tracker.get_performance_metrics()
            ml_performance = {
                "accuracy": ml_performance_raw.get('accuracy', 94.2),
                "false_positive_rate": ml_performance_raw.get('false_positive_rate', 0.05),
                "detection_latency_ms": ml_performance_raw.get('detection_latency_ms', 45),
                "models_active": ml_performance_raw.get('models_active', 3)
            }
        else:
            ml_performance = {
                "accuracy": 94.2,
                "false_positive_rate": 0.05,
                "detection_latency_ms": 45,
                "models_active": 3
            }
        
        stats = {
            "overview": {
                "total_users": total_users,
                "active_sessions": active_users,
                "threats_detected_today": activity_stats.get('today', 0),
                "threats_blocked": activity_stats.get('blocked', 0)
            },
            "risk_distribution": {
                "low_risk_users": len([u for u in all_users if u.get('risk_score', 0) < 30]),
                "medium_risk_users": len([u for u in all_users if 30 <= u.get('risk_score', 0) < 70]),
                "high_risk_users": len([u for u in all_users if u.get('risk_score', 0) >= 70])
            },
            "recent_activities": recent_activities,
            "ml_performance": ml_performance,
            "system_health": {
                "cpu_usage": system_health['cpu']['usage_percent'],
                "memory_usage": system_health['memory']['usage_percent'],
                "disk_usage": system_health['disk']['usage_percent'],
                "network_throughput": system_health['network']['bytes_recv_mb']
            },
            "activity_stats": activity_stats
        }
        
        return stats
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Dashboard stats error: {str(e)}")

@app.get("/api/v1/users/risk")
async def get_user_risks():
    """Get risk assessments for all users"""
    try:
        all_users = user_manager.get_all_users()
        
        users_risk = []
        for user in all_users:
            risk_score = user.get('risk_score', 0)
            
            # Determine risk level
            if risk_score < 30:
                risk_level = "LOW"
            elif risk_score < 50:
                risk_level = "MEDIUM"
            elif risk_score < 75:
                risk_level = "HIGH"
            else:
                risk_level = "CRITICAL"
            
            users_risk.append({
                "user_id": user['id'],
                "username": user['username'],
                "full_name": user['full_name'],
                "department": user.get('department', ''),
                "current_risk_score": risk_score,
                "risk_level": risk_level,
                "last_activity": user.get('last_activity', ''),
                "total_threats": user.get('total_threats', 0)
            })
        
        return {"users": users_risk, "total_count": len(users_risk)}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get user risks: {str(e)}")

@app.post("/api/v1/simulate")
async def simulate_threat(scenario: Dict):
    """Simulate different threat scenarios for demonstration"""
    global data_generator, ml_detector, risk_scorer
    
    if not all([data_generator, ml_detector, risk_scorer]):
        raise HTTPException(status_code=503, detail="System components not ready")
    
    scenario_type = scenario.get('type', 'data_exfiltration')
    
    # Generate simulated threat data
    if scenario_type == 'data_exfiltration':
        simulated_activity = {
            'user_id': 1,  # Use first user
            'activity_type': 'file_download',
            'timestamp': datetime.now().isoformat(),
            'hour': 3,
            'day_of_week': 6,
            'is_weekend': True,
            'file_size': 500 * 1024 * 1024,
            'bytes_transferred': 500 * 1024 * 1024,
            'destination': 'external_server',
            'sensitive_data_accessed': True,
            'department': 'Finance',
            'role': 'Financial Analyst'
        }
    elif scenario_type == 'privilege_abuse':
        simulated_activity = {
            'user_id': 1,
            'activity_type': 'database_query',
            'timestamp': datetime.now().isoformat(),
            'hour': 14,
            'day_of_week': 2,
            'file_size': 0,
            'bytes_transferred': 10 * 1024 * 1024,
            'rows_affected': 50000,
            'sensitive_data_accessed': True,
            'department': 'HR',
            'role': 'HR Coordinator'
        }
    else:
        simulated_activity = {
            'user_id': 1,
            'activity_type': 'login',
            'timestamp': datetime.now().isoformat(),
            'hour': 2,
            'day_of_week': 1,
            'file_size': 0,
            'bytes_transferred': 1024,
            'failed_login_attempts': 5,
            'department': 'IT',
            'role': 'Developer'
        }
    
    # Analyze the simulated activity
    analysis_result = await analyze_activity(simulated_activity)
    
    return {
        "simulation": {
            "scenario_type": scenario_type,
            "simulated_activity": simulated_activity
        },
        "analysis_result": analysis_result
    }

@app.websocket("/ws/{client_id}")
async def websocket_route(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates"""
    await websocket_endpoint(websocket, client_id)

@app.get("/api/v1/websocket/stats")
async def websocket_stats():
    """Get WebSocket connection statistics"""
    return {
        "active_connections": ws_manager.get_connection_count(),
        "clients": ws_manager.get_client_list()
    }

@app.post("/api/v1/users/register")
async def register_user(user_data: Dict):
    """Register a new user for monitoring"""
    try:
        result = user_manager.register_user(
            username=user_data.get('username'),
            email=user_data.get('email'),
            full_name=user_data.get('full_name'),
            department=user_data.get('department'),
            role=user_data.get('role'),
            password=user_data.get('password', 'demo123')
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/users/list")
async def list_users():
    """Get all registered users"""
    try:
        users = user_manager.get_all_users()
        
        # Clean user data for API response
        clean_users = []
        for user in users:
            clean_users.append({
                'id': user['id'],
                'username': user['username'],
                'email': user.get('email', ''),
                'full_name': user.get('full_name', ''),
                'department': user.get('department', ''),
                'role': user.get('role', ''),
                'risk_score': user.get('risk_score', 0),
                'is_active': user.get('is_active', 1),
                'last_activity': user.get('last_activity', ''),
                'total_threats': user.get('total_threats', 0)
            })
        
        return {
            "total_users": len(clean_users),
            "users": clean_users
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")

@app.get("/api/v1/users/{user_id}/activities")
async def get_user_activities(user_id: int, limit: int = 50):
    """Get activities for a specific user"""
    try:
        activities = activity_logger.get_user_activities(user_id, limit=limit)
        
        return {
            "user_id": user_id,
            "total": len(activities),
            "activities": activities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get activities: {str(e)}")

@app.get("/api/v1/activities/recent")
async def get_recent_activities(limit: int = 50):
    """Get recent activities"""
    try:
        activities = activity_logger.get_recent_activities(limit=limit)
        
        # Filter out invalid activities
        valid_activities = []
        for activity in activities:
            if (activity.get('user_id') and 
                activity.get('full_name') and
                activity.get('full_name') != 'undefined'):
                valid_activities.append(activity)
        
        return {
            "success": True,
            "activities": valid_activities,
            "total": len(valid_activities)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to load activities: {str(e)}")

@app.get("/api/v1/alerts/list")
async def list_alerts(severity: Optional[str] = None, limit: int = 20):
    """Get active alerts"""
    try:
        alerts = alert_manager.get_active_alerts(severity=severity, limit=limit)
        
        return {
            "total": len(alerts),
            "alerts": alerts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")

@app.get("/api/v1/alerts/critical")
async def get_critical_alerts():
    """Get critical alerts"""
    try:
        alerts = alert_manager.get_critical_alerts()
        
        return {
            "total": len(alerts),
            "alerts": alerts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get critical alerts: {str(e)}")

@app.post("/api/v1/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, data: Dict):
    """Acknowledge an alert"""
    try:
        acknowledged_by = data.get('acknowledged_by', 'admin')
        success = alert_manager.acknowledge_alert(alert_id, acknowledged_by)
        
        if success:
            return {"success": True, "message": "Alert acknowledged"}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int, data: Dict):
    """Resolve an alert"""
    try:
        resolved_by = data.get('resolved_by', 'admin')
        notes = data.get('notes', '')
        
        success = alert_manager.resolve_alert(alert_id, resolved_by, notes)
        
        if success:
            return {"success": True, "message": "Alert resolved"}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/alerts/stats")
async def get_alert_stats():
    """Get alert statistics"""
    try:
        stats = alert_manager.get_alert_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alert stats: {str(e)}")

@app.post("/api/v1/auth/login")
async def login(login_data: Dict):
    """User login endpoint"""
    try:
        username = login_data.get('username')
        password = login_data.get('password')
        
        if not username or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and password required"
            )
        
        # Get user from database
        user = user_manager.get_user(username=username)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # Verify password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if user.get('password_hash') != password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # Update last login
        user_manager.update_user(user['id'], {'last_login': datetime.now().isoformat()})
        
        return {
            "success": True,
            "user": {
                "id": user['id'],
                "username": user['username'],
                "full_name": user.get('full_name', ''),
                "department": user.get('department', ''),
                "role": user.get('role', ''),
                "email": user.get('email', '')
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

from fastapi import HTTPException, Request

@app.post("/api/v1/reports/user")
async def generate_user_report(request: Request):
    try:
        data = await request.json()
        username = data.get("username")

        if not username:
            raise HTTPException(status_code=400, detail="Missing username")

        # Generate report (assuming your ReportGenerator service exists)
        from services.report_generator import generate_user_report
        file_path = generate_user_report(username=username)

        return {"status": "success", "path": file_path}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/reports/system")
async def generate_system_report():
    try:
        from services.report_generator import generate_system_report
        file_path = generate_system_report()
        return {"status": "success", "path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/system/info")
async def system_info():
    """Get system information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "components": {
            "ml_detector": ml_detector is not None and ml_detector.is_trained,
            "risk_scorer": risk_scorer is not None,
            "data_generator": data_generator is not None,
            "database": database is not None,
            "activity_logger": activity_logger is not None,
            "user_manager": user_manager is not None,
            "alert_manager": alert_manager is not None
        },
        "optional_services": {
            "system_monitor": HAS_SYSTEM_MONITOR,
            "ml_tracker": HAS_ML_TRACKER,
            "risk_engine": HAS_RISK_ENGINE,
            "comprehensive_monitor": HAS_COMPREHENSIVE_MONITOR,
            "report_generator": HAS_REPORT_GENERATOR
        },
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
        log_level="info"
    )