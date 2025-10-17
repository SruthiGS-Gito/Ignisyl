"""
WebSocket Handler for Real-time Updates
Provides live threat detection updates to connected clients
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict
import asyncio
import json
from datetime import datetime

class ConnectionManager:
    """Manages WebSocket connections and broadcasts"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.client_info: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str = None):
        """Accept and register new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.client_info[websocket] = {
            "client_id": client_id or f"client_{len(self.active_connections)}",
            "connected_at": datetime.now().isoformat()
        }
        print(f"WebSocket client connected: {self.client_info[websocket]['client_id']}")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection",
            "status": "connected",
            "client_id": self.client_info[websocket]["client_id"],
            "message": "Connected to IGNISYL real-time updates"
        }, websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove disconnected client"""
        if websocket in self.active_connections:
            client_id = self.client_info[websocket]["client_id"]
            self.active_connections.remove(websocket)
            del self.client_info[websocket]
            print(f"WebSocket client disconnected: {client_id}")
    
    async def send_personal_message(self, message: Dict, websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending message to client: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_threat_alert(self, threat_data: Dict):
        """Broadcast threat detection alert"""
        alert = {
            "type": "threat_alert",
            "timestamp": datetime.now().isoformat(),
            "threat": threat_data
        }
        await self.broadcast(alert)
        print(f"Broadcasted threat alert: {threat_data.get('threat_type', 'unknown')}")
    
    async def broadcast_system_update(self, update_data: Dict):
        """Broadcast system status update"""
        update = {
            "type": "system_update",
            "timestamp": datetime.now().isoformat(),
            "update": update_data
        }
        await self.broadcast(update)
    
    async def broadcast_user_risk_change(self, user_id: str, old_risk: float, new_risk: float):
        """Broadcast when user risk score changes significantly"""
        if abs(new_risk - old_risk) > 10:  # Only broadcast significant changes
            change = {
                "type": "risk_change",
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "old_risk_score": old_risk,
                "new_risk_score": new_risk,
                "change": new_risk - old_risk
            }
            await self.broadcast(change)
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)
    
    def get_client_list(self) -> List[Dict]:
        """Get list of connected clients"""
        return [
            {
                "client_id": info["client_id"],
                "connected_at": info["connected_at"]
            }
            for info in self.client_info.values()
        ]

# Global connection manager instance
manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, client_id: str = None):
    """
    Main WebSocket endpoint handler
    Usage: ws://localhost:8000/ws/{client_id}
    """
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                # Handle different message types
                if message_type == "ping":
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                
                elif message_type == "subscribe":
                    # Client subscribing to specific alerts
                    await manager.send_personal_message({
                        "type": "subscribed",
                        "subscription": message.get("subscription"),
                        "status": "success"
                    }, websocket)
                
                elif message_type == "request_status":
                    # Client requesting system status
                    await manager.send_personal_message({
                        "type": "status_response",
                        "active_connections": manager.get_connection_count(),
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                
                else:
                    # Echo unknown messages
                    await manager.send_personal_message({
                        "type": "echo",
                        "received": message
                    }, websocket)
                    
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Utility functions for broadcasting from other parts of the application

async def notify_threat_detected(threat_data: Dict):
    """Broadcast threat alert to all connected clients"""
    message = {
        "type": "threat_alert",  # ← THIS IS CRITICAL
        "threat": threat_data,
        "timestamp": datetime.now().isoformat()
    }
    
    await manager.broadcast(message)
    print(f"Broadcasted threat alert: {threat_data.get('threat_type')}")

async def notify_system_update(update_data: Dict):
    """Call this to broadcast system updates"""
    await manager.broadcast_system_update(update_data)

async def notify_risk_change(user_id: str, old_risk: float, new_risk: float):
    """Call this when user risk scores change"""
    await manager.broadcast_user_risk_change(user_id, old_risk, new_risk)