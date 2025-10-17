"""
Firewall Controller for IGNISYL
Manages adaptive firewall rules based on threat detection
"""

import subprocess
import platform
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio

class FirewallController:
    """
    Controls firewall rules to block/restrict suspicious users
    Simulates firewall actions for demonstration (actual implementation would use OS-specific commands)
    """
    
    def __init__(self):
        self.active_rules = {}  # user_id: rule_data
        self.rule_history = []
        self.os_type = platform.system()  # Windows, Linux, Darwin (macOS)
        
    def apply_block(self, user_id: str, ip_address: str, duration_minutes: int = 60) -> Dict:
        """
        Block all network access for a user
        
        Args:
            user_id: User identifier
            ip_address: User's IP address to block
            duration_minutes: How long to maintain the block
            
        Returns:
            Dict with action details
        """
        expiry_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        rule = {
            "rule_id": f"block_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "user_id": user_id,
            "ip_address": ip_address,
            "action": "BLOCK",
            "applied_at": datetime.now().isoformat(),
            "expires_at": expiry_time.isoformat(),
            "status": "active"
        }
        
        # Simulate firewall command (in production, this would execute actual commands)
        firewall_command = self._get_block_command(ip_address)
        
        # Store active rule
        self.active_rules[user_id] = rule
        self.rule_history.append(rule)
        
        print(f"🚫 BLOCKED user {user_id} at {ip_address}")
        print(f"   Command: {firewall_command}")
        
        return {
            "success": True,
            "rule": rule,
            "simulated_command": firewall_command,
            "message": f"User {user_id} blocked until {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}"
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
        
        print(f"⚠️ RESTRICTED user {user_id} at {ip_address}")
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
        
        print(f"✅ REMOVED firewall rule for user {user_id}")
        
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
            print(f"🧹 Cleaned up {expired_count} expired firewall rules")
        
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