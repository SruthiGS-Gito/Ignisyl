# IGNISYL Firewall Action System Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Current Implementation Analysis](#current-implementation-analysis)
3. [Workflow Diagram](#workflow-diagram)
4. [Code Walkthrough](#code-walkthrough)
5. [Why Actions "Fail"](#why-actions-fail)
6. [Simulation Mode Design](#simulation-mode-design)
7. [Real-World Implementation Guide](#real-world-implementation-guide)

---

## System Overview

The IGNISYL Firewall Action System provides automated and analyst-driven threat response based on risk scores. It implements a **graduated response framework** aligned with IEEE standards:

| Risk Score | Action | Response Level |
|------------|--------|----------------|
| 0-30 | ALLOW | Normal operations with logging |
| 31-50 | MONITOR | Enhanced monitoring, detailed logging |
| 51-75 | RESTRICT | Analyst review required, limited access |
| 76-89 | ISOLATE | Network isolation, urgent analyst alert |
| 90-100 | BLOCK | Complete block, incident response activated |

---

## Current Implementation Analysis

### Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                         │
├──────────────────────────────────────────────────────────────────┤
│  AnalystControl.js        │  ActiveThreats.js                    │
│  - View pending threats   │  - View active threats               │
│  - Apply ALLOW/RESTRICT/  │  - Quick block action                │
│    ISOLATE/BLOCK          │                                      │
│  - Contact user           │                                      │
│  - Escalate threat        │                                      │
└────────────┬─────────────────────────────┬───────────────────────┘
             │                             │
             ▼                             ▼
┌────────────────────────────────────────────────────────────────┐
│                      api.js (API Client)                        │
├────────────────────────────────────────────────────────────────┤
│  analystAPI.takeAction(threatId, actionData)                   │
│  analystAPI.getPendingDecisions()                              │
│  analystAPI.contactUser(threatId, message, method)             │
│  analystAPI.escalateThreat(threatId, escalateTo, notes)        │
│  firewallAPI.blockUser(userId, ipAddress, duration)            │
│  firewallAPI.restrictUser(userId, ipAddress, restrictions)     │
└────────────────────────────────┬───────────────────────────────┘
                                 │ HTTP POST
                                 ▼
┌────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                            │
├────────────────────────────────────────────────────────────────┤
│  routes.py                                                      │
│  ├── POST /api/v1/analyst/threat/{id}/action                   │
│  ├── GET  /api/v1/analyst/pending-decisions                    │
│  ├── POST /api/v1/analyst/threat/{id}/contact-user             │
│  ├── POST /api/v1/analyst/threat/{id}/escalate                 │
│  └── POST /api/v1/firewall/action                              │
└────────────────────────────────┬───────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────┐
│                   FirewallController                            │
│                   (firewall_controller.py)                      │
├────────────────────────────────────────────────────────────────┤
│  Methods:                                                       │
│  ├── apply_block(user_id, ip, duration)                        │
│  ├── apply_restriction(user_id, ip, restrictions, duration)    │
│  ├── remove_rule(user_id)                                      │
│  ├── apply_graduated_response(user_id, risk_score)             │
│  └── analyst_override_action(user_id, action, restrictions)    │
│                                                                 │
│  OS Command Generators (SIMULATED):                             │
│  ├── _get_block_command(ip) → netsh/iptables/pfctl             │
│  ├── _get_restrict_external_command(ip)                        │
│  ├── _get_rate_limit_command(ip, limit_mbps)                   │
│  └── _get_block_ports_command(ip, ports)                       │
└────────────────────────────────────────────────────────────────┘
```

### Key Files

| File | Purpose |
|------|---------|
| `backend/services/firewall_controller.py` | Core firewall logic, command generation |
| `backend/api/routes.py` | API endpoints for analyst actions |
| `frontend/src/services/api.js` | Frontend API client |
| `frontend/src/components/AnalystControl/AnalystControl.js` | Analyst UI |
| `frontend/src/components/Pages/ActiveThreats.js` | Threat display with block button |

---

## Workflow Diagram

```
User Performs Suspicious Activity (e.g., file_deletion)
                    │
                    ▼
┌─────────────────────────────────────┐
│   ML Detector Calculates Risk       │
│   risk_score = 73 (HIGH)            │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│   Activity Logged to Database       │
│   action = "RESTRICT"               │
│   (51-75 range = analyst review)    │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│   Analyst Views Dashboard           │
│   Sees threat in pending queue      │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│   Analyst Reviews Details           │
│   ┌─────────────────────────────┐   │
│   │ Type: file_deletion         │   │
│   │ User: john.doe              │   │
│   │ Risk: 73 (HIGH)             │   │
│   │ Time: Dec 29, 04:37 PM      │   │
│   └─────────────────────────────┘   │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│   Analyst Selects Action            │
│   ○ ALLOW - False positive          │
│   ○ RESTRICT - Limit access         │
│   ● ISOLATE - Quarantine ← SELECTED │
│   ○ BLOCK - Complete block          │
│                                     │
│   Reason: "Accessed file deletion"  │
│   Duration: 1 hour                  │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│   Frontend Calls API                │
│                                     │
│   analystAPI.takeAction(            │
│     "user_john_doe",                │
│     {                               │
│       action: "ISOLATE",            │
│       custom_restrictions: {...},   │
│       reason: "Accessed file...",   │
│       duration_minutes: 60          │
│     }                               │
│   )                                 │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│   Backend Processes Request         │
│                                     │
│   1. Verify admin/analyst role      │
│   2. Get user from database         │
│   3. Call firewall.analyst_override │
│   4. Log action to activity DB      │
│   5. Return success response        │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│   FirewallController                │
│                                     │
│   analyst_override_action():        │
│   - Logs action to audit trail      │
│   - Generates OS commands (simulated)│
│   - Updates active_rules dict       │
│   - Returns result to API           │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│   Result Returned to Frontend       │
│                                     │
│   { success: true,                  │
│     result: { status: "ISOLATED" }, │
│     message: "Action applied..." }  │
└─────────────────────────────────────┘
```

---

## Code Walkthrough

### 1. Frontend: AnalystControl.js

```javascript
// frontend/src/components/AnalystControl/AnalystControl.js:73-98

const handleApplyAction = async () => {
  if (!reason.trim()) {
    alert('Please provide a reason for this action');
    return;
  }

  setSubmitting(true);
  try {
    // Call the analyst API to apply the action
    await analystAPI.takeAction(selectedThreat.user_id, {
      action,                    // ALLOW, RESTRICT, ISOLATE, or BLOCK
      custom_restrictions: customRestrictions,
      reason,
      duration_minutes: duration,
    });

    alert(`Action ${action} applied successfully!`);
    setShowModal(false);
    fetchData();  // Refresh the pending threats list
    resetForm();
  } catch (error) {
    console.error('Error applying action:', error);
    alert('Failed to apply action. Please try again.');  // ← Error shown to user
  } finally {
    setSubmitting(false);
  }
};
```

### 2. API Client: api.js

```javascript
// frontend/src/services/api.js:63-77

export const analystAPI = {
  getPendingDecisions: () => api.get('/api/v1/analyst/pending-decisions'),

  takeAction: (threatId, actionData) =>
    api.post(`/api/v1/analyst/threat/${threatId}/action`, actionData),
    // POST body: { action, custom_restrictions, reason, duration_minutes }

  contactUser: (threatId, message, method = 'notification') =>
    api.post(`/api/v1/analyst/threat/${threatId}/contact-user`, { message, method }),

  escalateThreat: (threatId, escalateTo, notes) =>
    api.post(`/api/v1/analyst/threat/${threatId}/escalate`, { escalate_to: escalateTo, notes }),

  getMyActions: (limit = 50) =>
    api.get(`/api/v1/analyst/my-actions?limit=${limit}`),
};
```

### 3. Backend Endpoint: routes.py

```python
# backend/api/routes.py:630-698

@router.post("/analyst/threat/{threat_id}/action")
async def analyst_take_action(
    threat_id: str,
    action: str,
    custom_restrictions: dict,
    reason: str,
    duration_minutes: int = 60,
    current_user: dict = Depends(get_current_user)
):
    try:
        from services.firewall_controller import firewall

        # Step 1: Verify analyst has permission
        if current_user.get('role') not in ['admin', 'analyst']:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Step 2: Verify user exists
        user = user_manager.get_user(threat_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Step 3: Add duration to restrictions
        custom_restrictions["duration_minutes"] = duration_minutes

        # Step 4: Apply firewall action ← This is where the "magic" happens
        result = firewall.analyst_override_action(
            user_id=threat_id,
            action=action,
            custom_restrictions=custom_restrictions,
            analyst_id=current_user.get('username'),
            reason=reason
        )

        # Step 5: Log the analyst action to database
        activity_logger.log_activity({
            "user_id": current_user.get('username'),
            "activity_type": "analyst_action",
            "target_user": threat_id,
            "action": action,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })

        # Step 6: Return success response
        return {
            "success": True,
            "result": result,
            "message": f"Action {action} applied successfully"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in analyst action: {e}")
        raise HTTPException(status_code=500, detail="Failed to apply action")  # ← Generic error
```

### 4. Firewall Controller: firewall_controller.py

```python
# backend/services/firewall_controller.py:392-455

def analyst_override_action(self, user_id: str, action: str,
                            custom_restrictions: dict,
                            analyst_id: str, reason: str):
    """Allow analyst to manually control firewall actions"""
    valid_actions = ["ALLOW", "RESTRICT", "ISOLATE", "BLOCK"]

    if action not in valid_actions:
        raise ValueError(f"Invalid action. Must be one of {valid_actions}")

    logger.info(f"Analyst {analyst_id} taking action {action} on {user_id}: {reason}")

    # Log analyst decision to database (for audit trail)
    self._log_analyst_action(
        user_id=user_id,
        analyst_id=analyst_id,
        action=action,
        reason=reason,
        restrictions=custom_restrictions,
        timestamp=datetime.now()
    )

    # Get user's IP address
    ip_address = self._get_user_ip(user_id)

    # Apply action based on type
    if action == "ALLOW":
        self._clear_restrictions(user_id, ip_address)
        result = {"status": "CLEARED", "message": "All restrictions removed"}

    elif action == "RESTRICT":
        self._apply_custom_restrictions(user_id, ip_address, custom_restrictions)
        result = {"status": "RESTRICTED", "restrictions": custom_restrictions}

    elif action == "ISOLATE":
        self._apply_isolation(user_id, ip_address, custom_restrictions)
        result = {"status": "ISOLATED", "restrictions": custom_restrictions}

    elif action == "BLOCK":
        self._apply_full_block(user_id, ip_address, custom_restrictions)
        result = {"status": "BLOCKED", "restrictions": custom_restrictions}

    # Notify user if configured
    if custom_restrictions.get("notify_user"):
        self._send_user_notification(user_id, action, reason)

    result.update({
        "action_applied": action,
        "analyst": analyst_id,
        "timestamp": datetime.now().isoformat(),
        "reason": reason
    })

    return result
```

---

## Why Actions "Fail"

### Current System Status: SIMULATION MODE

The current IGNISYL firewall system operates in **simulation mode**. This is **intentional and correct** for a demo/academic project.

### What "Simulation Mode" Means

```python
# backend/services/firewall_controller.py:586-591

def _block_external_for_ip(self, ip_address: str):
    """Block external internet for specific IP"""
    command = self._get_restrict_external_command(ip_address)
    logger.info(f"Blocking external access for {ip_address}: {command}")
    # In production, execute the actual command  ← NOTE: Command NOT executed
    pass  # ← Does nothing except log
```

The firewall controller:
1. **Generates** OS-specific commands (correct for Windows/Linux/macOS)
2. **Logs** what would happen
3. **Stores** the action in memory (`active_rules` dictionary)
4. **Does NOT execute** the actual system commands

### Why This Is Correct for Demo

| Real Execution Would Require | Problem |
|------------------------------|---------|
| Administrator/root privileges | Backend runs as normal user |
| Same machine as user | Backend is a server, user is on different machine |
| OS-level access | Web app sandboxed from system |
| Network infrastructure control | Would need router/switch access |

### The "Failed to apply action" Error

This error message appears when an exception occurs in the endpoint. In the current codebase, actions should **NOT fail** because:

1. The simulation mode doesn't execute actual commands
2. All operations are in-memory or database logging
3. The `pass` statements prevent real failures

If you're seeing this error, check:
- Database connection issues (`activity_logger.log_activity()` might fail)
- User not found in database
- Invalid action type (not ALLOW/RESTRICT/ISOLATE/BLOCK)
- Permission issues (non-admin trying to access)

---

## Simulation Mode Design

### Current Behavior (Already Implemented)

```python
# When analyst applies ISOLATE action:

1. Frontend sends: POST /api/v1/analyst/threat/user123/action
   Body: { action: "ISOLATE", reason: "Suspicious activity", duration: 60 }

2. Backend logs action to database ✓

3. FirewallController.analyst_override_action() called:
   - Generates isolation command (not executed)
   - Stores rule in self.active_rules dictionary
   - Returns success result

4. Response: { success: true, result: { status: "ISOLATED" } }

5. Frontend shows: "Action ISOLATE applied successfully!"
```

### What Gets Recorded

| Storage | Data |
|---------|------|
| `active_rules` dict | Current active rules (in-memory, lost on restart) |
| `rule_history` list | All rules ever applied (in-memory) |
| Activity database | Analyst actions logged permanently |
| Console logs | Command that would be executed |

### Recommended Enhancement: Persistent Simulation State

For a more robust demo, actions should persist across restarts:

```python
# Enhanced simulation mode stores to database

class ActionLog(SQLiteModel):
    id: int
    user_id: str
    action: str  # ALLOW, RESTRICT, ISOLATE, BLOCK
    applied_by: str  # analyst username
    applied_at: datetime
    expires_at: datetime
    reason: str
    restrictions: dict  # JSON
    status: str  # active, expired, cleared
    simulated_command: str  # What would be executed
```

---

## Real-World Implementation Guide

### Enterprise Deployment Architecture

For actual OS-level enforcement in production:

```
┌─────────────────────────────────────────────────────────────────┐
│                    IGNISYL CENTRAL SERVER                       │
│                    (Your FastAPI Backend)                       │
│                                                                 │
│  - Threat Detection (ML models)                                 │
│  - Policy Management                                            │
│  - Action Coordination                                          │
│  - Stores pending actions for agents                            │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              │ Agent API
                              │ (polling every 30s)
                              ▼
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ IGNISYL AGENT │    │ IGNISYL AGENT │    │ IGNISYL AGENT │
│ (Workstation) │    │ (Workstation) │    │ (Workstation) │
│               │    │               │    │               │
│ Runs as:      │    │ Runs as:      │    │ Runs as:      │
│ - SYSTEM (Win)│    │ - root (Linux)│    │ - root (Mac)  │
│               │    │               │    │               │
│ Can execute:  │    │ Can execute:  │    │ Can execute:  │
│ - netsh       │    │ - iptables    │    │ - pfctl       │
│ - PowerShell  │    │ - tc          │    │ - dscl        │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
   User: john.doe       User: jane.smith      User: bob.wilson
```

### Agent Implementation Example

```python
# agent/ignisyl_agent.py (Runs on each workstation)

import os
import platform
import subprocess
import requests
import time
from typing import Dict, List

class IGNISYLAgent:
    """
    IGNISYL Agent - Runs on each user's computer
    Communicates with central server to enforce actions
    """

    def __init__(self, server_url: str, api_key: str):
        self.server_url = server_url
        self.api_key = api_key
        self.os_type = platform.system()
        self.username = os.getlogin()
        self.hostname = platform.node()

    def run(self):
        """Main agent loop - poll for actions"""
        print(f"[IGNISYL Agent] Started on {self.hostname} ({self.os_type})")
        print(f"[IGNISYL Agent] Monitoring user: {self.username}")

        while True:
            try:
                self.poll_for_actions()
            except Exception as e:
                print(f"[ERROR] Poll failed: {e}")

            time.sleep(30)  # Poll every 30 seconds

    def poll_for_actions(self):
        """Check server for pending actions"""
        response = requests.get(
            f"{self.server_url}/api/v1/agent/actions",
            headers={"X-API-Key": self.api_key},
            params={
                "username": self.username,
                "hostname": self.hostname
            },
            timeout=10
        )

        if response.status_code == 200:
            actions = response.json().get("pending_actions", [])
            for action in actions:
                self.execute_action(action)
                self.report_result(action["id"], "completed")

    def execute_action(self, action: Dict):
        """Execute firewall action on local machine"""
        action_type = action["type"]
        duration = action.get("duration_seconds", 3600)

        print(f"[ACTION] Executing {action_type} for {duration}s")

        if action_type == "ISOLATE":
            self.isolate_network(duration)
        elif action_type == "BLOCK":
            self.block_all_network()
        elif action_type == "RESTRICT":
            self.apply_restrictions(action.get("restrictions", {}))
        elif action_type == "ALLOW":
            self.clear_all_rules()

    def isolate_network(self, duration: int):
        """Block external network, keep internal"""
        if self.os_type == "Windows":
            # Block all outbound except internal subnet
            subprocess.run([
                "netsh", "advfirewall", "firewall", "add", "rule",
                "name=IGNISYL_ISOLATE",
                "dir=out",
                "action=block",
                "enable=yes"
            ], check=True)

            # Allow internal network
            subprocess.run([
                "netsh", "advfirewall", "firewall", "add", "rule",
                "name=IGNISYL_ALLOW_INTERNAL",
                "dir=out",
                "action=allow",
                "remoteip=192.168.0.0/16,10.0.0.0/8,172.16.0.0/12"
            ], check=True)

            # Schedule removal
            remove_time = time.strftime(
                "%H:%M",
                time.localtime(time.time() + duration)
            )
            subprocess.run([
                "schtasks", "/create", "/tn", "IGNISYL_REMOVE",
                "/tr", "netsh advfirewall firewall delete rule name=IGNISYL_ISOLATE",
                "/sc", "once", "/st", remove_time, "/f"
            ])

        elif self.os_type == "Linux":
            # Get current user UID
            uid = os.getuid()

            # Block all output for this user
            subprocess.run([
                "sudo", "iptables", "-A", "OUTPUT",
                "-m", "owner", "--uid-owner", str(uid),
                "-j", "DROP"
            ], check=True)

            # Allow internal
            subprocess.run([
                "sudo", "iptables", "-I", "OUTPUT",
                "-m", "owner", "--uid-owner", str(uid),
                "-d", "192.168.0.0/16",
                "-j", "ACCEPT"
            ], check=True)

    def report_result(self, action_id: str, status: str):
        """Report action result back to server"""
        requests.post(
            f"{self.server_url}/api/v1/agent/report",
            headers={"X-API-Key": self.api_key},
            json={
                "action_id": action_id,
                "status": status,
                "hostname": self.hostname,
                "timestamp": time.time()
            }
        )
```

### Server-Side Agent Endpoints

```python
# backend/api/agent_routes.py (New file)

from fastapi import APIRouter, Header, HTTPException
from typing import List, Optional

router = APIRouter(prefix="/api/v1/agent", tags=["Agent API"])

# In-memory pending actions (use database in production)
pending_actions = {}

@router.get("/actions")
async def get_pending_actions(
    username: str,
    hostname: str,
    api_key: str = Header(..., alias="X-API-Key")
):
    """
    Called by agents to check for pending actions.
    Returns list of actions to execute on the workstation.
    """
    # Verify API key
    if not verify_agent_api_key(api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")

    # Get pending actions for this user/host
    key = f"{username}@{hostname}"
    actions = pending_actions.get(key, [])

    # Mark as dispatched
    pending_actions[key] = []

    return {"pending_actions": actions}

@router.post("/report")
async def report_action_result(
    action_id: str,
    status: str,
    hostname: str,
    timestamp: float,
    api_key: str = Header(..., alias="X-API-Key")
):
    """
    Called by agents after executing an action.
    Updates the action status in the database.
    """
    # Verify API key
    if not verify_agent_api_key(api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")

    # Update action status in database
    # ... implementation ...

    return {"success": True}

def queue_action_for_user(username: str, hostname: str, action: dict):
    """Queue an action for an agent to pick up"""
    key = f"{username}@{hostname}"
    if key not in pending_actions:
        pending_actions[key] = []
    pending_actions[key].append(action)
```

### Integration with Enterprise Security Tools

For cloud/enterprise environments, integrate with existing tools:

```python
# backend/services/enterprise_integrations.py

class EnterpriseIntegrations:
    """Integrate with enterprise security tools for real enforcement"""

    def block_via_active_directory(self, username: str):
        """Disable user account in Active Directory"""
        from ldap3 import Server, Connection, MODIFY_REPLACE

        conn = Connection(
            Server('ldap://company-ad.com'),
            user='ignisyl-service@company.com',
            password=os.environ['AD_SERVICE_PASSWORD']
        )
        conn.bind()

        # Disable the account (userAccountControl = 514)
        conn.modify(
            f'CN={username},OU=Users,DC=company,DC=com',
            {'userAccountControl': [(MODIFY_REPLACE, [514])]}
        )

    def isolate_via_cisco_ise(self, username: str):
        """Put user in quarantine VLAN via Cisco ISE"""
        import requests

        requests.post(
            'https://ise.company.com/api/v1/quarantine',
            auth=('ignisyl', os.environ['ISE_PASSWORD']),
            json={'username': username, 'vlan': 'QUARANTINE'}
        )

    def revoke_okta_sessions(self, username: str):
        """Revoke all active sessions in Okta"""
        import requests

        # Get user ID
        user_resp = requests.get(
            f'https://company.okta.com/api/v1/users/{username}',
            headers={'Authorization': f'SSWS {os.environ["OKTA_TOKEN"]}'}
        )
        user_id = user_resp.json()['id']

        # Clear all sessions
        requests.delete(
            f'https://company.okta.com/api/v1/users/{user_id}/sessions',
            headers={'Authorization': f'SSWS {os.environ["OKTA_TOKEN"]}'}
        )

    def block_aws_access(self, username: str):
        """Revoke AWS access via IAM"""
        import boto3

        iam = boto3.client('iam')

        # Attach deny-all policy
        iam.attach_user_policy(
            UserName=username,
            PolicyArn='arn:aws:iam::aws:policy/AWSDenyAll'
        )
```

---

## Summary

| Aspect | Current State | Production Requirement |
|--------|---------------|------------------------|
| Action Logging | Works (database) | Works |
| Risk Scoring | Works (ML models) | Works |
| Analyst UI | Works (React) | Works |
| Firewall Commands | Generated but not executed | Agent on each workstation |
| OS-Level Enforcement | Simulated | Requires elevated privileges |
| Network Scope | Local simulation | Enterprise network integration |

### Recommendations

1. **For Demo/Academic**: Current simulation mode is perfect
2. **For Proof of Concept**: Add persistent action logging to database
3. **For Enterprise**: Implement agent architecture or integrate with existing tools

The current IGNISYL system correctly implements the **intelligence and decision layer**. Real enforcement requires the **execution layer** (agents or integrations) which is outside the scope of a web application.

---

## API Reference

### POST /api/v1/analyst/threat/{threat_id}/action

Apply firewall action to a user.

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

**Request Body:**
```json
{
  "action": "ISOLATE",
  "reason": "Suspicious file access detected",
  "duration_minutes": 60,
  "custom_restrictions": {
    "block_external_internet": true,
    "allow_internal_network": true,
    "notify_user": true
  }
}
```

**Success Response (200):**
```json
{
  "success": true,
  "simulation_mode": true,
  "action_applied": "ISOLATE",
  "target_user": "user_123",
  "applied_by": "admin",
  "duration_minutes": 60,
  "message": "Action ISOLATE applied successfully (simulation mode)",
  "note": "Commands logged but not executed. For real enforcement, deploy IGNISYL Agent.",
  "result": {
    "status": "ISOLATED",
    "restrictions": {
      "block_external_internet": true,
      "allow_internal_network": true,
      "duration_minutes": 60
    }
  }
}
```

**Error Responses:**

| Code | Cause | Response |
|------|-------|----------|
| 400 | Invalid action type | `{"detail": "Invalid action 'QUARANTINE'. Must be one of: ['ALLOW', 'RESTRICT', 'ISOLATE', 'BLOCK']"}` |
| 401 | Missing/invalid JWT | `{"detail": "Not authenticated"}` |
| 403 | Insufficient permissions | `{"detail": "Insufficient permissions. Role 'User' cannot apply firewall actions."}` |
| 404 | User not found | `{"detail": "User not found"}` |
| 500 | Server error | `{"detail": "Failed to apply action: <error details>"}` |

### GET /api/v1/analyst/pending-decisions

Get threats waiting for analyst review (risk score 51-75).

**Success Response (200):**
```json
{
  "success": true,
  "count": 5,
  "pending_decisions": [
    {
      "id": "act_12345",
      "user_id": "user_john",
      "username": "john.doe",
      "full_name": "John Doe",
      "activity_type": "file_deletion",
      "risk_score": 65,
      "risk_level": "HIGH",
      "timestamp": "2024-01-03T14:30:00Z",
      "summary": "john.doe - File Deletion",
      "action": "RESTRICT",
      "recommended_action": "RESTRICT",
      "details": {
        "file_path": "/sensitive/data.xlsx",
        "file_size": 1048576
      }
    }
  ]
}
```

### POST /api/v1/analyst/threat/{threat_id}/contact-user

Send message to user about suspicious activity.

**Request:**
```json
{
  "message": "Please verify the file deletion activity on your account",
  "method": "notification"
}
```

**Response:**
```json
{
  "success": true,
  "simulation_mode": true,
  "status": "message_logged",
  "method": "notification",
  "target_user": "john.doe",
  "timestamp": "2024-01-03T14:35:00Z",
  "message": "Message to John Doe logged (simulation mode)",
  "note": "In production, message would be sent via configured notification service."
}
```

### POST /api/v1/analyst/threat/{threat_id}/escalate

Escalate threat to higher authority.

**Request:**
```json
{
  "escalate_to": "incident_team",
  "notes": "User has deleted multiple sensitive files in the last hour"
}
```

**Valid escalation targets:** `admin`, `manager`, `incident_team`, `security_lead`, `ciso`

**Response:**
```json
{
  "success": true,
  "simulation_mode": true,
  "escalated_to": "incident_team",
  "target_user": "john.doe",
  "analyst": "admin",
  "timestamp": "2024-01-03T14:40:00Z",
  "message": "Threat escalated to incident_team (simulation mode)",
  "note": "In production, notifications would be sent to the escalation target."
}
```

### GET /api/v1/analyst/my-actions

Get analyst's action history for audit trail.

**Query Parameters:**
- `limit` (optional): Number of actions to return (default: 50, max: 200)

**Response:**
```json
{
  "success": true,
  "analyst": "admin",
  "count": 3,
  "actions": [
    {
      "action_id": "act_67890",
      "action_type": "analyst_action",
      "target_user": "john.doe",
      "timestamp": "2024-01-03T14:30:00Z",
      "summary": "Analyst admin applied ISOLATE: Suspicious file access",
      "details": {
        "action": "ISOLATE",
        "reason": "Suspicious file access",
        "duration_minutes": 60
      }
    }
  ]
}
```

---

## Troubleshooting

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "Failed to apply action" | Network error | Check if backend is running on port 8000 |
| 401 Unauthorized | Token expired | Re-login to get fresh JWT token |
| 403 Forbidden | Wrong role | Login as admin or security analyst |
| "Invalid action" | Wrong action type | Use ALLOW, RESTRICT, ISOLATE, or BLOCK |
| No activities showing | Empty database | Run `/debug/simulate-activity` endpoint |

### Checking System Status

1. **Verify backend is running:**
   ```bash
   curl http://localhost:8000/api/v1/debug/auth-check
   ```

2. **Check user database:**
   ```bash
   curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/debug/users
   ```

3. **View firewall controller status:**
   ```python
   from services.firewall_controller import firewall
   print(firewall.get_simulation_status())
   # Output: {"simulation_mode": true, "active_rules_count": 0, ...}
   ```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-01-03 | Initial documentation |
| 1.1 | 2024-01-03 | Added API reference, troubleshooting |

---

*IGNISYL Threat Detection System*
*Document maintained by the IGNISYL development team*
