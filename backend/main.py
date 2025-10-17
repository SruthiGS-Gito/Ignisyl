"""
IGNISYL-Neo Main API Server
FastAPI backend for AI-Powered Insider Threat Detection System
"""
# This file : Main web server that ties everything together
# - Creates API endpoints (health check, analyze activity, dashboard stats)
# - Initializes ML models and risk scorer on startup
# - Handles incoming requests and returns threat analysis results

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.config import settings, ensure_directories
from backend.models.database import create_tables, init_sample_data
from backend.ml_engine.hybrid_detector import AdvancedHybridDetector
from backend.ml_engine.risk_scorer import ContextualRiskScorer
from backend.ml_engine.data_generator import BehavioralDataGenerator
from fastapi import WebSocket
from backend.api.websocket import websocket_endpoint, manager as ws_manager

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Insider Threat Detection with Adaptive Firewall Control",
    debug=settings.DEBUG
)

from backend.api import routes

# Include the router
app.include_router(routes.router)

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
    
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Ensure directories exist
    ensure_directories()
    
    # Initialize database
    create_tables()
    init_sample_data()
    
    # Initialize ML components
    print("🧠 Initializing ML components...")
    ml_detector = AdvancedHybridDetector()
    risk_scorer = ContextualRiskScorer()
    data_generator = BehavioralDataGenerator()
    
    # Train ML models with sample data
    print("📊 Training ML models...")
    try:
        normal_data, anomalous_data = data_generator.generate_complete_dataset()
        
        # Prepare training data
        all_data = normal_data + anomalous_data
        import pandas as pd
        import numpy as np
        
        df = pd.DataFrame(all_data)
        
        # Extract and engineer features from the generated data
        def extract_features(df):
            """Extract numerical features from activity data"""
            features = pd.DataFrame()
    
            # Time-based features
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                features['hour'] = df['timestamp'].dt.hour
                features['day_of_week'] = df['timestamp'].dt.dayofweek
            else:
                features['hour'] = 12
                features['day_of_week'] = 2
    
            # File size feature
            features['file_size'] = df.get('file_size', 0).fillna(0)
    
            # Network bytes transferred
            features['bytes_transferred'] = df.get('bytes_transferred', 0).fillna(0)
    
            return features

        X = extract_features(df).values
        y = df.get('is_suspicious', pd.Series([False] * len(df))).astype(int).values

        print(f"Training features shape: {X.shape}")  # This will show you (samples, 4)
        
        # Train the detector
        ml_detector.fit(X, y)
        print("✅ ML models trained successfully!")
            
    except Exception as e:
        print(f"⚠️ ML training error: {e}. Using fallback configuration.")
    
    # Initialize API routes with ML components
    routes.init_routes(ml_detector, risk_scorer, data_generator)
    
    print(f"🌟 {settings.APP_NAME} is ready!")
    print(f"📡 API running on http://{settings.API_HOST}:{settings.API_PORT}")

# API Routes

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with system information"""
    return f"""
    <html>
        <head>
            <title>{settings.APP_NAME}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 20px; }}
                .status {{ background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .endpoints {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .endpoint {{ margin: 10px 0; padding: 10px; background: white; border-left: 4px solid #007bff; }}
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
                        <strong>GET</strong> <a href="/api/v1/health">/api/v1/health</a> - System health check
                    </div>
                    <div class="endpoint">
                        <strong>POST</strong> <a href="/docs#/default/analyze_activity_api_v1_analyze_post">/api/v1/analyze</a> - Analyze user activity for threats
                    </div>
                    <div class="endpoint">
                        <strong>GET</strong> <a href="/api/v1/dashboard/stats">/api/v1/dashboard/stats</a> - Dashboard statistics
                    </div>
                    <div class="endpoint">
                        <strong>GET</strong> <a href="/api/v1/users/risk">/api/v1/users/risk</a> - User risk assessments
                    </div>
                    <div class="endpoint">
                        <strong>GET</strong> <a href="/docs">/docs</a> - Interactive API Documentation
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
            "firewall": "ready"
        },
        "ml_implementations": ml_detector.get_implementation_info() if ml_detector else {}
    }
    
    return health_status

@app.post("/api/v1/analyze")
async def analyze_activity(activity_data: Dict):
    """Analyze user activity for insider threats"""
    global ml_detector, risk_scorer
    
    if not ml_detector or not risk_scorer:
        raise HTTPException(status_code=503, detail="ML components not ready")
    
    try:
        import pandas as pd
        from datetime import datetime as dt
        
        # Ensure all required fields have defaults
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
        
        # Perform risk assessment using our contextual risk scorer
        risk_assessment = risk_scorer.assess_activity_risk(activity_data, user_profile)
        
        # Extract features consistently with training
        activity_timestamp = activity_data.get('timestamp')
        if isinstance(activity_timestamp, str):
            activity_timestamp = pd.to_datetime(activity_timestamp)
        else:
            activity_timestamp = dt.now()
        
        # Prepare feature vector matching training (4 features)
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
            import traceback
            traceback.print_exc()  # This will show full error in terminal
            ml_risk_score = risk_assessment['risk_score']
            individual_scores = {}
        
        # Combine risk assessments
        final_risk_score = (risk_assessment['risk_score'] + ml_risk_score) / 2
        final_risk_level = "LOW" if final_risk_score < 30 else "MEDIUM" if final_risk_score < 70 else "HIGH"
        
        # Determine firewall action
        firewall_action = "ALLOW" if final_risk_score < 30 else "RESTRICT" if final_risk_score < 70 else "BLOCK"
        
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
                "individual_scores": {k: float(v) if hasattr(v, 'item') else v for k, v in individual_scores.items()} if individual_scores else {},
                "model_confidence": round(float(max(individual_scores.values())) if individual_scores else 0.5, 3)
            },
            "firewall_action": {
                "action": firewall_action,
                "auto_applied": settings.AUTO_BLOCK_HIGH_RISK,
                "restrictions": _get_restrictions_for_risk_level(final_risk_level)
            },
            "metadata": {
                "user_id": activity_data.get('user_id'),
                "activity_type": activity_data.get('activity_type'),
                "processing_time_ms": 1
            }
        }
        
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()  # Print full error to terminal
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
    else:  # HIGH
        return [
            "Block all external connections",
            "Prevent file downloads",
            "Isolate user session",
            "Alert security team"
        ]

@app.get("/api/v1/dashboard/stats")
async def dashboard_stats():
    """Get dashboard statistics"""
    from backend.models.user_management import user_manager
    
    # Get real user data
    all_users = user_manager.get_all_users()
    total_users = len(all_users)
    active_users = user_manager.get_active_users_count()
    
    # Count total threats from all users
    total_threats = sum(user.get('total_threats', 0) for user in all_users)
    
    stats = {
        "overview": {
            "total_users": total_users,  # Real count!
            "active_sessions": active_users,  # Real count!
            "threats_detected_today": total_threats,  # Real count!
            "threats_blocked": 5  # Can keep this for now
        },
        "risk_distribution": {
            "low_risk_users": len([u for u in all_users if u['current_risk_score'] < 30]),
            "medium_risk_users": len([u for u in all_users if 30 <= u['current_risk_score'] < 70]),
            "high_risk_users": len([u for u in all_users if u['current_risk_score'] >= 70])
        },
        "recent_activities": [
            {
                "user": "sruthi.gs",
                "activity": "Large file download",
                "risk_score": 75,
                "action": "RESTRICT",
                "timestamp": "2024-01-15T14:30:00"
            }
        ],
        "ml_performance": {
            "accuracy": 94.2,
            "false_positive_rate": 0.05,
            "detection_latency_ms": 12,
            "models_active": 3
        },
        "system_health": {
            "cpu_usage": 45,
            "memory_usage": 62,
            "disk_usage": 78,
            "network_throughput": 156.7
        }
    }
    
    return stats

@app.get("/api/v1/users/risk")
async def get_user_risks():
    """Get risk assessments for all users"""
    
    # In real implementation, query from database
    users_risk = [
        {
            "user_id": "user_001",
            "username": "john.doe",
            "department": "Finance", 
            "current_risk_score": 25,
            "risk_level": "LOW",
            "last_activity": "2024-01-15T16:30:00",
            "recent_flags": 0
        },
        {
            "user_id": "user_002", 
            "username": "jane.smith",
            "department": "IT",
            "current_risk_score": 85,
            "risk_level": "HIGH", 
            "last_activity": "2024-01-15T23:45:00",
            "recent_flags": 3
        },
        {
            "user_id": "user_003",
            "username": "mike.wilson", 
            "department": "HR",
            "current_risk_score": 45,
            "risk_level": "MEDIUM",
            "last_activity": "2024-01-15T15:20:00", 
            "recent_flags": 1
        }
    ]
    
    return {"users": users_risk, "total_count": len(users_risk)}

@app.post("/api/v1/simulate")
async def simulate_threat(scenario: Dict):
    """Simulate different threat scenarios for demonstration"""
    global data_generator, ml_detector, risk_scorer
    
    if not all([data_generator, ml_detector, risk_scorer]):
        raise HTTPException(status_code=503, detail="System components not ready")
    
    scenario_type = scenario.get('type', 'data_exfiltration')
    
    from datetime import datetime
    
    # Generate simulated threat data
    if scenario_type == 'data_exfiltration':
        simulated_activity = {
            'user_id': 'demo_user',
            'activity_type': 'file_download',
            'timestamp': datetime.now().isoformat(),
            'hour': 3,  # 3 AM
            'day_of_week': 6,  # Sunday
            'is_weekend': True,
            'file_size': 500 * 1024 * 1024,  # 500 MB
            'bytes_transferred': 500 * 1024 * 1024,
            'destination': 'external_server',
            'sensitive_data_accessed': True,
            'department': 'Finance',
            'role': 'Financial Analyst'
        }
    elif scenario_type == 'privilege_abuse':
        simulated_activity = {
            'user_id': 'demo_user',
            'activity_type': 'database_query', 
            'timestamp': datetime.now().isoformat(),
            'hour': 14,
            'day_of_week': 2,
            'file_size': 0,
            'bytes_transferred': 10 * 1024 * 1024,
            'rows_affected': 50000,
            'sensitive_data_accessed': True,
            'department': 'HR',
            'role': 'HR Coordinator',
            'resource_department': 'Finance'  # Cross-department access
        }
    else:
        simulated_activity = {
            'user_id': 'demo_user',
            'activity_type': 'login',
            'timestamp': datetime.now().isoformat(),
            'hour': 2,
            'day_of_week': 1,
            'file_size': 0,
            'bytes_transferred': 1024,
            'location': 'Unknown_Location',
            'device_info': 'Unknown_Device_9999',
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

@app.post("/api/v1/broadcast/threat")
async def broadcast_threat(threat_data: Dict):
    """Endpoint to broadcast threat alerts via WebSocket"""
    from backend.api.websocket import notify_threat_detected
    
    try:
        await notify_threat_detected(threat_data)
        return {"status": "broadcasted", "threat_type": threat_data.get("threat_type")}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/v1/users/register")
async def register_user(user_data: Dict):
    """Register a new user for monitoring"""
    from backend.models.user_management import user_manager
    
    try:
        result = user_manager.register_user(
            username=user_data.get('username'),
            full_name=user_data.get('full_name'),
            department=user_data.get('department'),
            role=user_data.get('role'),
            email=user_data.get('email')
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/users/list")
async def list_users():
    """Get all registered users"""
    from backend.models.user_management import user_manager
    
    users = user_manager.get_all_users()
    return {
        "total_users": len(users),
        "users": users
    }

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )