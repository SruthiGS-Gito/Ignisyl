"""
IGNISYL Demo Runner
Runs a complete demo of the system with simulated threats
"""

import asyncio
import random
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def simulate_normal_activity():
    """Simulate normal user activity"""
    print("✅ Simulating normal activity...")
    print("   Risk Score: 15 - File access during business hours")
    await asyncio.sleep(2)

async def simulate_medium_threat():
    """Simulate medium-risk threat"""
    print("⚠️ Simulating MEDIUM threat...")
    print("   Risk Score: 45 - Large file transfer outside normal hours")
    await asyncio.sleep(2)

async def simulate_high_threat():
    """Simulate high-risk threat requiring analyst decision"""
    print("🚨 Simulating HIGH threat...")
    print("   Risk Score: 62 - Multiple anomalies detected")
    print("   → Sent to Analyst Decision Queue")
    await asyncio.sleep(3)

async def simulate_critical_threat():
    """Simulate critical threat"""
    print("🔴 Simulating CRITICAL threat...")
    print("   Risk Score: 95 - Honeypot file accessed!")
    print("   → AUTO-BLOCKED")
    print("   → Security team notified")
    await asyncio.sleep(3)

async def run_demo():
    """Run complete demo"""
    
    print("=" * 60)
    print("IGNISYL - Live Demo")
    print("=" * 60)
    print("\nThis demo simulates various threat scenarios\n")
    
    # Scenario 1: Normal Activity
    print("\n📊 Scenario 1: Normal Business Activity")
    print("-" * 60)
    await simulate_normal_activity()
    
    # Scenario 2: Medium Threat
    print("\n📊 Scenario 2: Unusual But Not Critical")
    print("-" * 60)
    await simulate_medium_threat()
    
    # Scenario 3: High Threat (Analyst Decision)
    print("\n📊 Scenario 3: Analyst Decision Required")
    print("-" * 60)
    await simulate_high_threat()
    print("\n   Analyst Options:")
    print("   • ALLOW - Mark as false positive")
    print("   • RESTRICT - Block external internet")
    print("   • ISOLATE - Full quarantine")
    print("   • ESCALATE - Forward to manager")
    
    # Scenario 4: Critical Threat
    print("\n📊 Scenario 4: Confirmed Insider Threat")
    print("-" * 60)
    await simulate_critical_threat()
    
    # Summary
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print("\n📋 Key Features Demonstrated:")
    print("   ✅ 5-Level Graduated Response")
    print("   ✅ Human-in-the-Loop Decision Making")
    print("   ✅ Automatic Threat Blocking")
    print("   ✅ Analyst Control Panel")
    print("\n💡 To see the full system:")
    print("   1. Start backend: cd backend && python main.py")
    print("   2. Start frontend: cd frontend && npm start")
    print("   3. Login at: http://localhost:3000")
    print("=" * 60)

if __name__ == '__main__':
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted")
