"""
Firewall Controller for IGNISYL
Manages adaptive firewall rules based on threat detection

SIMULATION MODE (Default):
- Commands are generated and logged but NOT executed
- Safe for demo/academic use
- Actions are recorded in memory and activity database

PRODUCTION MODE (Requires Agent):
- For real OS-level enforcement, deploy IGNISYL Agent on workstations
- Agent runs with elevated privileges (SYSTEM/root)
- Central server sends commands, agents execute locally
- See docs/FIREWALL_SYSTEM_DOCUMENTATION.md for architecture
"""

import subprocess
import platform
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
import logging

logger = logging.getLogger("ignisyl.firewall")


class FirewallController:
    """
    Controls firewall rules to block/restrict suspicious users.

    By default, operates in SIMULATION MODE where commands are logged
    but not executed. This is safe for demos and development.

    For production deployment, integrate with IGNISYL Agent or
    enterprise security tools (Active Directory, Cisco ISE, etc.)
    """

    # Simulation mode flag - set to False only if running with proper privileges
    SIMULATION_MODE = True

    def __init__(self, simulation_mode: bool = True):
        """
        Initialize the firewall controller.

        Args:
            simulation_mode: If True (default), commands are logged but not executed.
                           If False, will attempt to execute OS commands (requires privileges).
        """
        self.simulation_mode = simulation_mode
        self.active_rules: Dict[str, Dict] = {}  # user_id: rule_data
        self.rule_history: List[Dict] = []
        self.action_log: List[Dict] = []  # Persistent action log
        self.os_type = platform.system()  # Windows, Linux, Darwin (macOS)

        if self.simulation_mode:
            logger.info("[FIREWALL] Initialized in SIMULATION MODE - commands will be logged but not executed")
        else:
            logger.warning("[FIREWALL] Initialized in PRODUCTION MODE - commands WILL be executed!")
            logger.warning("[FIREWALL] Ensure process has appropriate privileges (Administrator/root)")
        
        # Load active rules from database on startup
        self._load_active_rules_from_db()
        
    def apply_block(self, user_id: str, ip_address: str, duration_minutes: int = 60) -> Dict:
        """
        Block all network access for a user.

        In simulation mode: Logs the command but does not execute it.
        In production mode: Executes the actual OS firewall command.

        Args:
            user_id: User identifier
            ip_address: User's IP address to block
            duration_minutes: How long to maintain the block (0 = indefinite)

        Returns:
            Dict with action details and simulation status
        """
        expiry_time = datetime.now() + timedelta(minutes=duration_minutes) if duration_minutes > 0 else None

        rule = {
            "rule_id": f"block_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "user_id": user_id,
            "ip_address": ip_address,
            "action": "BLOCK",
            "applied_at": datetime.now().isoformat(),
            "expires_at": expiry_time.isoformat() if expiry_time else "indefinite",
            "status": "active",
            "simulation_mode": self.simulation_mode
        }

        # Generate OS-specific firewall command
        firewall_command = self._get_block_command(ip_address)

        # Execute or simulate
        execution_result = self._execute_command(firewall_command, "BLOCK", user_id)

        # Store active rule
        self.active_rules[user_id] = rule
        self.rule_history.append(rule)

        # Log to action log
        self._log_action("BLOCK", user_id, ip_address, firewall_command, execution_result)

        logger.info(f"[FIREWALL] BLOCK applied to {user_id} at {ip_address}")
        logger.info(f"[FIREWALL] Command: {firewall_command}")
        logger.info(f"[FIREWALL] Mode: {'SIMULATION' if self.simulation_mode else 'PRODUCTION'}")

        return {
            "success": True,
            "simulation_mode": self.simulation_mode,
            "rule": rule,
            "command": firewall_command,
            "execution_result": execution_result,
            "message": f"User {user_id} blocked" + (f" until {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}" if expiry_time else " indefinitely")
        }
    
    def apply_restriction(self, user_id: str, ip_address: str, restrictions: List[str], duration_minutes: int = 30) -> Dict:
        """
        Apply limited restrictions (rate limiting, port blocking, etc.)
        
        Args:
            user_id: User identifier
            ip_address: User's IP address
            restrictions: List of restriction types
            duration_minutes: How long to maintain restrictions
        """
        expiry_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        rule = {
            "rule_id": f"restrict_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "user_id": user_id,
            "ip_address": ip_address,
            "action": "RESTRICT",
            "restrictions": restrictions,
            "applied_at": datetime.now().isoformat(),
            "expires_at": expiry_time.isoformat(),
            "status": "active"
        }
        
        # Generate restriction commands
        commands = []
        if "block_external" in restrictions:
            commands.append(self._get_restrict_external_command(ip_address))
        if "rate_limit" in restrictions:
            commands.append(self._get_rate_limit_command(ip_address))
        if "block_file_transfer" in restrictions:
            commands.append(self._get_block_ports_command(ip_address, [21, 22, 445]))
        
        self.active_rules[user_id] = rule
        self.rule_history.append(rule)
        
        print(f"[WARN] RESTRICTED user {user_id} at {ip_address}")
        print(f"   Restrictions: {', '.join(restrictions)}")
        
        return {
            "success": True,
            "rule": rule,
            "simulated_commands": commands,
            "message": f"User {user_id} restricted until {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}"
        }
    
    def remove_rule(self, user_id: str) -> Dict:
        """Remove firewall rule for a user"""
        if user_id not in self.active_rules:
            return {"success": False, "message": f"No active rule for user {user_id}"}
        
        rule = self.active_rules[user_id]
        rule["status"] = "removed"
        rule["removed_at"] = datetime.now().isoformat()
        
        # Generate removal command
        removal_command = self._get_remove_command(rule["ip_address"])
        
        del self.active_rules[user_id]
        
        print(f"[OK] REMOVED firewall rule for user {user_id}")
        
        return {
            "success": True,
            "message": f"Firewall rule removed for user {user_id}",
            "simulated_command": removal_command
        }
    
    def get_active_rules(self) -> List[Dict]:
        """Get all currently active firewall rules"""
        return list(self.active_rules.values())
    
    def get_rule_history(self, limit: int = 100) -> List[Dict]:
        """Get firewall rule history"""
        return self.rule_history[-limit:]
    
    def cleanup_expired_rules(self) -> int:
        """Remove expired firewall rules"""
        now = datetime.now()
        expired_count = 0
        expired_users = []
        
        for user_id, rule in self.active_rules.items():
            expiry = datetime.fromisoformat(rule["expires_at"])
            if now > expiry:
                expired_users.append(user_id)
                expired_count += 1
        
        for user_id in expired_users:
            self.remove_rule(user_id)
        
        if expired_count > 0:
            print(f"[*] Cleaned up {expired_count} expired firewall rules")
        
        return expired_count
    
    # OS-specific command generators (simulated)
    
    def _get_block_command(self, ip_address: str) -> str:
        """Generate OS-specific block command"""
        if self.os_type == "Windows":
            return f'netsh advfirewall firewall add rule name="Block_{ip_address}" dir=in action=block remoteip={ip_address}'
        elif self.os_type == "Linux":
            return f'iptables -A INPUT -s {ip_address} -j DROP'
        elif self.os_type == "Darwin":  # macOS
            return f'pfctl -t blocklist -T add {ip_address}'
        else:
            return f'# Unsupported OS: {self.os_type}'
    
    def _get_restrict_external_command(self, ip_address: str) -> str:
        """Block external connections for an IP"""
        if self.os_type == "Windows":
            return f'netsh advfirewall firewall add rule name="Restrict_External_{ip_address}" dir=out action=block remoteip={ip_address}'
        elif self.os_type == "Linux":
            return f'iptables -A OUTPUT -s {ip_address} ! -d 192.168.0.0/16 -j DROP'
        else:
            return f'# Restrict external for {ip_address}'
    
    def _get_rate_limit_command(self, ip_address: str, limit_mbps: int = 1) -> str:
        """Apply bandwidth rate limiting"""
        if self.os_type == "Linux":
            return f'tc qdisc add dev eth0 root tbf rate {limit_mbps}mbit burst 32kbit latency 400ms'
        else:
            return f'# Rate limit {ip_address} to {limit_mbps}Mbps'
    
    def _get_block_ports_command(self, ip_address: str, ports: List[int]) -> str:
        """Block specific ports for an IP"""
        port_list = ','.join(map(str, ports))
        if self.os_type == "Windows":
            return f'netsh advfirewall firewall add rule name="Block_Ports_{ip_address}" dir=out protocol=TCP remoteport={port_list} remoteip={ip_address} action=block'
        elif self.os_type == "Linux":
            return f'iptables -A OUTPUT -s {ip_address} -p tcp -m multiport --dports {port_list} -j DROP'
        else:
            return f'# Block ports {port_list} for {ip_address}'

    # ============================================================================
    # COMMAND EXECUTION AND LOGGING HELPERS
    # ============================================================================

    def _execute_command(self, command: str, action_type: str, user_id: str) -> Dict[str, Any]:
        """
        Execute or simulate a firewall command.

        In simulation mode: Returns success without executing.
        In production mode: Attempts to execute the command.

        Args:
            command: The OS command to execute
            action_type: Type of action (BLOCK, RESTRICT, etc.)
            user_id: Target user ID

        Returns:
            Dict with execution status and details
        """
        if self.simulation_mode:
            return {
                "executed": False,
                "simulated": True,
                "command": command,
                "status": "success",
                "message": f"Command logged (simulation mode)"
            }

        # Production mode - attempt actual execution
        try:
            # Check for admin/root privileges
            if self.os_type == "Windows":
                import ctypes
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                is_admin = os.geteuid() == 0

            if not is_admin:
                return {
                    "executed": False,
                    "simulated": False,
                    "command": command,
                    "status": "failed",
                    "error": "Insufficient privileges - requires Administrator/root"
                }

            # Execute the command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            return {
                "executed": True,
                "simulated": False,
                "command": command,
                "status": "success" if result.returncode == 0 else "failed",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        except subprocess.TimeoutExpired:
            return {
                "executed": False,
                "simulated": False,
                "command": command,
                "status": "failed",
                "error": "Command timed out after 30 seconds"
            }
        except Exception as e:
            return {
                "executed": False,
                "simulated": False,
                "command": command,
                "status": "failed",
                "error": str(e)
            }

    def _log_action(self, action_type: str, user_id: str, ip_address: Optional[str],
                    command: str, execution_result: Dict) -> None:
        """
        Log a firewall action to the action log.

        Args:
            action_type: Type of action (BLOCK, RESTRICT, ISOLATE, ALLOW)
            user_id: Target user ID
            ip_address: Target IP address (if known)
            command: The command that was/would be executed
            execution_result: Result of execution or simulation
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "command": command,
            "simulation_mode": self.simulation_mode,
            "execution_result": execution_result,
            "os_type": self.os_type
        }

        self.action_log.append(log_entry)

        # Keep only the last 1000 entries to prevent memory issues
        if len(self.action_log) > 1000:
            self.action_log = self.action_log[-1000:]

        logger.debug(f"[FIREWALL] Action logged: {action_type} for {user_id}")

    def get_action_log(self, limit: int = 100) -> List[Dict]:
        """
        Get recent firewall action log entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of action log entries, most recent first
        """
        return list(reversed(self.action_log[-limit:]))

    def get_simulation_status(self) -> Dict[str, Any]:
        """
        Get current simulation mode status and statistics.

        Returns:
            Dict with simulation status and action statistics
        """
        return {
            "simulation_mode": self.simulation_mode,
            "os_type": self.os_type,
            "active_rules_count": len(self.active_rules),
            "total_actions_logged": len(self.action_log),
            "rule_history_count": len(self.rule_history),
            "message": "Commands are logged but NOT executed" if self.simulation_mode else "Commands ARE being executed"
        }
    
    def _get_remove_command(self, ip_address: str) -> str:
        """Generate command to remove firewall rule"""
        if self.os_type == "Windows":
            return f'netsh advfirewall firewall delete rule name="Block_{ip_address}"'
        elif self.os_type == "Linux":
            return f'iptables -D INPUT -s {ip_address} -j DROP'
        elif self.os_type == "Darwin":
            return f'pfctl -t blocklist -T delete {ip_address}'
        else:
            return f'# Remove rule for {ip_address}'

    # ============================================================================
    # GRADUATED RESPONSE FRAMEWORK - NEW FUNCTIONS
    # ============================================================================
    
    def apply_graduated_response(self, user_id: str, risk_score: float, 
                                 analyst_override: bool = False):
        """
        Apply graduated response based on risk score and analyst decision
        
        Args:
            user_id: User identifier
            risk_score: Risk score (0-100)
            analyst_override: If True, wait for analyst decision on RESTRICT level
            
        Returns:
            dict: Action taken and restrictions applied
        """
        logger.info(f"Applying graduated response for {user_id} - Risk: {risk_score}")
        
        if risk_score < 30:
            return self._allow(user_id)
        elif risk_score < 50:
            return self._monitor(user_id)
        elif risk_score < 70:
            if analyst_override:
                return self._wait_for_analyst_decision(user_id, risk_score)
            return self._auto_restrict(user_id)
        elif risk_score < 90:
            self._auto_isolate(user_id)
            return self._alert_analyst_urgent(user_id)
        else:
            return self._critical_block_shutdown(user_id)
    
    def _allow(self, user_id: str):
        """Level 1: Normal operations with logging"""
        logger.info(f"ALLOW action for {user_id}")
        return {
            "action": "ALLOW",
            "level": 1,
            "log_level": "NORMAL",
            "restrictions": None,
            "analyst_required": False
        }
    
    def _monitor(self, user_id: str):
        """Level 2: Enhanced monitoring"""
        logger.info(f"MONITOR action for {user_id}")
        
        # Increase logging detail
        monitoring_config = {
            "detailed_logging": True,
            "screenshot_capture": False,  # Optional: enable if needed
            "keystroke_logging": False,   # Optional: enable if needed
            "network_packet_capture": True
        }
        
        return {
            "action": "MONITOR",
            "level": 2,
            "log_level": "DETAILED",
            "analyst_notification": True,
            "restrictions": None,
            "monitoring_config": monitoring_config
        }
    
    def _auto_restrict(self, user_id: str):
        """Level 3: Automatic restriction with analyst notification"""
        logger.warning(f"RESTRICT action for {user_id}")
        
        restrictions = {
            "block_external_internet": True,
            "rate_limit_mbps": 1,
            "block_ports": [21, 22, 445, 3389],  # FTP, SSH, SMB, RDP
            "allow_internal_network": True,
            "duration_minutes": 60,
            "notify_user": True
        }
        
        # Apply restrictions via existing methods
        ip_address = self._get_user_ip(user_id)
        if ip_address:
            self._apply_network_restrictions(ip_address, restrictions)
        
        # Send to analyst queue for review
        self._send_to_analyst_queue(user_id, "RESTRICT", restrictions)
        
        return {
            "action": "RESTRICT",
            "level": 3,
            "restrictions": restrictions,
            "analyst_review_required": True,
            "auto_expire": True
        }
    
    def _wait_for_analyst_decision(self, user_id: str, risk_score: float):
        """Hold threat in queue waiting for analyst decision"""
        logger.info(f"Waiting for analyst decision: {user_id} - Risk: {risk_score}")
        
        # Create pending decision record
        pending_decision = {
            "user_id": user_id,
            "risk_score": risk_score,
            "timestamp": datetime.now().isoformat(),
            "status": "PENDING_ANALYST",
            "recommended_action": "RESTRICT"
        }
        
        # Store in database (you'll need to create this table)
        self._store_pending_decision(pending_decision)
        
        # Send urgent notification to analysts
        self._notify_analysts_decision_needed(user_id, risk_score)
        
        return {
            "action": "PENDING",
            "level": 3,
            "status": "WAITING_FOR_ANALYST",
            "risk_score": risk_score,
            "timeout_minutes": 15  # Auto-escalate if no decision in 15 min
        }
    
    def _auto_isolate(self, user_id: str):
        """Level 4: Network isolation"""
        logger.error(f"ISOLATE action for {user_id}")
        
        restrictions = {
            "block_all_external": True,
            "allow_internal_only": True,
            "disconnect_vpn": True,
            "disable_usb": True,
            "force_local_logging": True,
            "require_admin_unlock": True
        }
        
        # Immediate isolation
        ip_address = self._get_user_ip(user_id)
        if ip_address:
            self._apply_full_isolation(ip_address, restrictions)
        
        # Alert analysts urgently
        self._alert_analyst_urgent(user_id, "ISOLATION_APPLIED")
        
        return {
            "action": "ISOLATE",
            "level": 4,
            "restrictions": restrictions,
            "analyst_intervention": "REQUIRED",
            "auto_expire": False
        }
    
    def _critical_block_shutdown(self, user_id: str):
        """Level 5: Critical threat response"""
        logger.critical(f"CRITICAL BLOCK for {user_id}")
        
        restrictions = {
            "complete_network_disconnect": True,
            "system_lock": True,
            "optional_shutdown": False,  # Set True for automatic shutdown
            "require_admin_unlock": True,
            "forensics_capture": True
        }
        
        # Immediate action
        ip_address = self._get_user_ip(user_id)
        if ip_address:
            self.block_user(user_id, ip_address, duration_minutes=0)  # Indefinite
        
        # Alert entire security team
        self._alert_security_team_critical(user_id)
        self._activate_incident_response(user_id)
        
        return {
            "action": "BLOCK",
            "level": 5,
            "restrictions": restrictions,
            "incident_response": "ACTIVATED",
            "require_admin_review": True
        }
    
    def analyst_override_action(self, user_id: str, action: str, 
                                custom_restrictions: dict, 
                                analyst_id: str, reason: str):
        """
        Allow analyst to manually control firewall actions
        
        Args:
            user_id: Target user
            action: One of ALLOW, RESTRICT, ISOLATE, BLOCK
            custom_restrictions: Custom restriction settings
            analyst_id: Analyst making the decision
            reason: Justification for action
            
        Returns:
            dict: Result of action
        """
        valid_actions = ["ALLOW", "RESTRICT", "ISOLATE", "BLOCK"]
        
        if action not in valid_actions:
            raise ValueError(f"Invalid action. Must be one of {valid_actions}")
        
        logger.info(f"Analyst {analyst_id} taking action {action} on {user_id}: {reason}")
        
        # Log analyst decision to database
        self._log_analyst_action(
            user_id=user_id,
            analyst_id=analyst_id,
            action=action,
            reason=reason,
            restrictions=custom_restrictions,
            timestamp=datetime.now()
        )
        
        # Apply analyst's custom restrictions
        ip_address = self._get_user_ip(user_id)
        
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
        
        # Persist rule to database for recovery on restart
        duration_minutes = custom_restrictions.get('duration_minutes', 60)
        expires_at = datetime.now() + timedelta(minutes=duration_minutes)
        self._persist_rule_to_db(
            user_id=user_id,
            action=action,
            restrictions=custom_restrictions,
            analyst_id=analyst_id,
            reason=reason,
            expires_at=expires_at
        )
        
        return result
    
    # ============================================================================
    # HELPER METHODS FOR GRADUATED RESPONSE
    # ============================================================================
    
    def _persist_rule_to_db(self, user_id: str, action: str, restrictions: dict,
                            analyst_id: str, reason: str, expires_at):
        """Store firewall rule in database for persistence across restarts"""
        import sqlite3
        try:
            conn = sqlite3.connect('data/sessions.db')
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS firewall_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    action TEXT,
                    restrictions TEXT,
                    analyst_id TEXT,
                    reason TEXT,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            # Deactivate any existing rules for this user
            cursor.execute('''
                UPDATE firewall_rules SET status='superseded' 
                WHERE user_id=? AND status='active'
            ''', (user_id,))
            
            cursor.execute('''
                INSERT INTO firewall_rules 
                (user_id, action, restrictions, analyst_id, reason, 
                 created_at, expires_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
            ''', (
                user_id, action, json.dumps(restrictions), 
                analyst_id, reason, datetime.now(), expires_at
            ))
            conn.commit()
            conn.close()
            logger.info(f"[FIREWALL] Persisted rule for {user_id}: {action}")
        except Exception as e:
            logger.error(f"Failed to persist firewall rule: {e}")
    
    def _load_active_rules_from_db(self):
        """Load unexpired rules from database on startup"""
        import sqlite3
        try:
            conn = sqlite3.connect('data/sessions.db')
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='firewall_rules'
            ''')
            if not cursor.fetchone():
                conn.close()
                return
            
            # Get active rules that haven't expired
            # Use strftime format to match SQLite datetime format (space separator)
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                SELECT user_id, action, restrictions, expires_at
                FROM firewall_rules
                WHERE status='active'
                AND expires_at > ?
            ''', (now_str,))
            
            loaded_count = 0
            for row in cursor.fetchall():
                user_id, action, restrictions_json, expires_at = row
                self.active_rules[user_id] = {
                    'action': action,
                    'restrictions': json.loads(restrictions_json) if restrictions_json else {},
                    'expires_at': expires_at
                }
                loaded_count += 1
                logger.info(f"[FIREWALL] Restored rule for {user_id}: {action}")
            
            if loaded_count > 0:
                logger.info(f"[FIREWALL] Loaded {loaded_count} active rules from database")
            
            conn.close()
        except Exception as e:
            logger.error(f"Failed to load rules from DB: {e}")
    
    def _get_user_ip(self, user_id: str) -> str:
        """Get user's current IP address from activity logs"""
        # Query recent activity to get IP
        # You'll need to implement this based on your database
        try:
            from models.user_activity import UserActivity
            recent = UserActivity.query.filter_by(user_id=user_id)\
                .order_by(UserActivity.timestamp.desc()).first()
            return recent.source_ip if recent else None
        except Exception as e:
            logger.error(f"Error getting user IP: {e}")
            return None
    
    def _apply_network_restrictions(self, ip_address: str, restrictions: dict):
        """Apply custom network restrictions"""
        if restrictions.get("block_external_internet"):
            # Block all external traffic, allow internal only
            self._block_external_for_ip(ip_address)
        
        if restrictions.get("rate_limit_mbps"):
            # Apply rate limiting
            rate_limit = restrictions["rate_limit_mbps"]
            self._apply_rate_limit(ip_address, rate_limit)
        
        if restrictions.get("block_ports"):
            # Block specific ports
            for port in restrictions["block_ports"]:
                self._block_port_for_ip(ip_address, port)
    
    def _apply_full_isolation(self, ip_address: str, restrictions: dict):
        """Apply complete network isolation"""
        # Block all external
        self._block_external_for_ip(ip_address)
        
        # Keep internal network access
        if not restrictions.get("block_all_internal"):
            self._allow_internal_for_ip(ip_address)
    
    def _send_to_analyst_queue(self, user_id: str, action: str, restrictions: dict):
        """Add threat to analyst decision queue"""
        # This should store to database table for analysts to review
        logger.info(f"Sending {user_id} to analyst queue: {action}")
        # Implementation depends on your database structure
        pass
    
    def _notify_analysts_decision_needed(self, user_id: str, risk_score: float):
        """Send notification to analysts that decision is needed"""
        logger.warning(f"Analyst decision needed for {user_id} - Risk: {risk_score}")
        # Implement notification system (email, Slack, etc.)
        pass
    
    def _alert_analyst_urgent(self, user_id: str, message: str = ""):
        """Send urgent alert to analysts"""
        logger.warning(f"URGENT: Analyst attention needed for {user_id} - {message}")
        # Implement urgent notification
        return {"alert_sent": True, "level": "URGENT"}
    
    def _alert_security_team_critical(self, user_id: str):
        """Alert entire security team of critical incident"""
        logger.critical(f"CRITICAL INCIDENT: {user_id}")
        # Implement team-wide alert
        pass
    
    def _activate_incident_response(self, user_id: str):
        """Activate incident response protocol"""
        logger.critical(f"Activating incident response for {user_id}")
        # Trigger incident response workflow
        pass
    
    def _log_analyst_action(self, user_id: str, analyst_id: str, action: str, 
                           reason: str, restrictions: dict, timestamp: datetime):
        """Log analyst decision to audit trail"""
        log_entry = {
            "user_id": user_id,
            "analyst_id": analyst_id,
            "action": action,
            "reason": reason,
            "restrictions": json.dumps(restrictions),
            "timestamp": timestamp.isoformat()
        }
        logger.info(f"Analyst action logged: {log_entry}")
        # Store to database
        pass
    
    def _clear_restrictions(self, user_id: str, ip_address: str):
        """Clear all restrictions for user"""
        if ip_address:
            self._get_remove_command(ip_address)
        logger.info(f"Cleared all restrictions for {user_id}")
    
    def _apply_custom_restrictions(self, user_id: str, ip_address: str, restrictions: dict):
        """Apply analyst's custom restrictions"""
        if ip_address:
            self._apply_network_restrictions(ip_address, restrictions)
        logger.info(f"Applied custom restrictions for {user_id}: {restrictions}")
    
    def _apply_isolation(self, user_id: str, ip_address: str, restrictions: dict):
        """Apply isolation with custom settings"""
        if ip_address:
            self._apply_full_isolation(ip_address, restrictions)
        logger.info(f"Applied isolation for {user_id}")
    
    def _apply_full_block(self, user_id: str, ip_address: str, restrictions: dict):
        """Apply complete block"""
        if ip_address:
            duration = restrictions.get("duration_minutes", 0)
            self.block_user(user_id, ip_address, duration)
        logger.info(f"Applied full block for {user_id}")
    
    def _send_user_notification(self, user_id: str, action: str, reason: str):
        """Send notification to user about action taken"""
        logger.info(f"Sending notification to {user_id}: {action} - {reason}")
        # Implement user notification
        pass
    
    def _store_pending_decision(self, pending_decision: dict):
        """Store pending decision in database"""
        # Store to pending_analyst_decisions table
        logger.info(f"Stored pending decision: {pending_decision}")
        pass

    # ============================================================================
    # NETWORK OPERATION HELPER METHODS
    # ============================================================================
    
    def _block_external_for_ip(self, ip_address: str):
        """Block external internet for specific IP"""
        command = self._get_restrict_external_command(ip_address)
        logger.info(f"Blocking external access for {ip_address}: {command}")
        # In production, execute the actual command, IMPORTANT !
        pass
    
    def _apply_rate_limit(self, ip_address: str, rate_limit_mbps: int):
        """Apply bandwidth rate limiting"""
        command = self._get_rate_limit_command(ip_address, rate_limit_mbps)
        logger.info(f"Applying rate limit for {ip_address}: {command}")
        # In production, execute the actual command
        pass
    
    def _block_port_for_ip(self, ip_address: str, port: int):
        """Block specific port for IP"""
        command = self._get_block_ports_command(ip_address, [port])
        logger.info(f"Blocking port {port} for {ip_address}: {command}")
        # In production, execute the actual command
        pass
    
    def _allow_internal_for_ip(self, ip_address: str):
        """Allow internal network access"""
        # This would use OS-specific commands to allow internal subnet
        logger.info(f"Allowing internal network for {ip_address}")
        pass
    
    def block_user(self, user_id: str, ip_address: str, duration_minutes: int = 60):
        """Wrapper for apply_block to maintain compatibility"""
        return self.apply_block(user_id, ip_address, duration_minutes)
    
    async def auto_cleanup_loop(self):
        """Background task to automatically cleanup expired rules"""
        while True:
            await asyncio.sleep(60)  # Check every minute
            self.cleanup_expired_rules()

# Global firewall controller instance
firewall = FirewallController()

# Utility functions for easy access

def block_user(user_id: str, ip_address: str, duration_minutes: int = 60) -> Dict:
    """Block a user's network access"""
    return firewall.apply_block(user_id, ip_address, duration_minutes)

def restrict_user(user_id: str, ip_address: str, restrictions: List[str], duration_minutes: int = 30) -> Dict:
    """Apply restrictions to a user"""
    return firewall.apply_restriction(user_id, ip_address, restrictions, duration_minutes)

def unblock_user(user_id: str) -> Dict:
    """Remove firewall rules for a user"""
    return firewall.remove_rule(user_id)

def get_blocked_users() -> List[Dict]:
    """Get list of currently blocked/restricted users"""
    return firewall.get_active_rules()
