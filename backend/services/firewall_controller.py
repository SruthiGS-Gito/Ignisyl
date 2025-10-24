"""
Firewall Controller for IGNISYL
Manages adaptive firewall rules based on threat detection
NOTE: This is a SIMULATION for demonstration - actual firewall commands are not executed
"""

import subprocess
import platform
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
import logging

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)

from config.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirewallController:
    """
    Controls firewall rules to block/restrict suspicious users
    
    IMPORTANT: This is a SIMULATION for academic demonstration.
    In production, this would execute actual OS-specific firewall commands.
    For safety, no actual firewall commands are executed.
    """
    
    def __init__(self):
        self.active_rules = {}  # user_id: rule_data
        self.rule_history = []
        self.os_type = platform.system()  # Windows, Linux, Darwin (macOS)
        self.simulation_mode = True  # Always True for safety
        
        logger.info(f"🛡️ Firewall Controller initialized (OS: {self.os_type}, Mode: SIMULATION)")
    
    def apply_block(self, user_id: str, ip_address: str, 
                    duration_minutes: int = 60, reason: str = "") -> Dict:
        """
        Block all network access for a user
        
        Args:
            user_id: User identifier
            ip_address: User's IP address to block
            duration_minutes: How long to maintain the block
            reason: Reason for blocking
            
        Returns:
            Dict with action details
        """
        expiry_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        rule = {
            "rule_id": f"block_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "user_id": user_id,
            "ip_address": ip_address,
            "action": "BLOCK",
            "reason": reason,
            "applied_at": datetime.now().isoformat(),
            "expires_at": expiry_time.isoformat(),
            "duration_minutes": duration_minutes,
            "status": "active"
        }
        
        # Generate firewall command (NOT executed for safety)
        firewall_command = self._get_block_command(ip_address)
        
        # Store active rule
        self.active_rules[user_id] = rule
        self.rule_history.append(rule)
        
        logger.warning(f"🚫 BLOCKED user {user_id} at {ip_address} for {duration_minutes} minutes")
        logger.info(f"   Reason: {reason}")
        logger.info(f"   Simulated command: {firewall_command}")
        
        return {
            "success": True,
            "rule": rule,
            "simulated_command": firewall_command,
            "message": f"User {user_id} blocked until {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}",
            "note": "SIMULATION - No actual firewall commands executed"
        }
    
    def apply_restriction(self, user_id: str, ip_address: str, 
                         restrictions: List[str], duration_minutes: int = 30,
                         reason: str = "") -> Dict:
        """
        Apply limited restrictions (rate limiting, port blocking, etc.)
        
        Args:
            user_id: User identifier
            ip_address: User's IP address
            restrictions: List of restriction types
            duration_minutes: How long to maintain restrictions
            reason: Reason for restrictions
            
        Returns:
            Dict with action details
        """
        expiry_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        rule = {
            "rule_id": f"restrict_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "user_id": user_id,
            "ip_address": ip_address,
            "action": "RESTRICT",
            "restrictions": restrictions,
            "reason": reason,
            "applied_at": datetime.now().isoformat(),
            "expires_at": expiry_time.isoformat(),
            "duration_minutes": duration_minutes,
            "status": "active"
        }
        
        # Generate restriction commands (NOT executed)
        commands = []
        if "block_external" in restrictions:
            commands.append(self._get_restrict_external_command(ip_address))
        if "rate_limit" in restrictions:
            commands.append(self._get_rate_limit_command(ip_address))
        if "block_file_transfer" in restrictions:
            commands.append(self._get_block_ports_command(ip_address, [21, 22, 445]))
        
        self.active_rules[user_id] = rule
        self.rule_history.append(rule)
        
        logger.warning(f"⚠️ RESTRICTED user {user_id} at {ip_address}")
        logger.info(f"   Restrictions: {', '.join(restrictions)}")
        logger.info(f"   Reason: {reason}")
        
        return {
            "success": True,
            "rule": rule,
            "simulated_commands": commands,
            "message": f"User {user_id} restricted until {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}",
            "note": "SIMULATION - No actual firewall commands executed"
        }
    
    def allow_user(self, user_id: str) -> Dict:
        """
        Allow normal access for a user (remove restrictions)
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict with action details
        """
        if user_id in self.active_rules:
            return self.remove_rule(user_id)
        
        logger.info(f"✅ User {user_id} has normal access (no active rules)")
        
        return {
            "success": True,
            "message": f"User {user_id} has normal access",
            "action": "ALLOW"
        }
    
    def remove_rule(self, user_id: str) -> Dict:
        """Remove firewall rule for a user"""
        if user_id not in self.active_rules:
            return {
                "success": False, 
                "message": f"No active rule for user {user_id}"
            }
        
        rule = self.active_rules[user_id]
        rule["status"] = "removed"
        rule["removed_at"] = datetime.now().isoformat()
        
        # Generate removal command (NOT executed)
        removal_command = self._get_remove_command(rule["ip_address"])
        
        del self.active_rules[user_id]
        
        logger.info(f"✅ REMOVED firewall rule for user {user_id}")
        logger.info(f"   Simulated command: {removal_command}")
        
        return {
            "success": True,
            "message": f"Firewall rule removed for user {user_id}",
            "simulated_command": removal_command,
            "note": "SIMULATION - No actual firewall commands executed"
        }
    
    def get_active_rules(self) -> List[Dict]:
        """Get all currently active firewall rules"""
        return list(self.active_rules.values())
    
    def get_rule_for_user(self, user_id: str) -> Optional[Dict]:
        """Get active rule for a specific user"""
        return self.active_rules.get(user_id)
    
    def get_rule_history(self, limit: int = 100) -> List[Dict]:
        """Get firewall rule history"""
        return self.rule_history[-limit:]
    
    def cleanup_expired_rules(self) -> int:
        """Remove expired firewall rules"""
        now = datetime.now()
        expired_count = 0
        expired_users = []
        
        for user_id, rule in self.active_rules.items():
            try:
                expiry = datetime.fromisoformat(rule["expires_at"])
                if now > expiry:
                    expired_users.append(user_id)
                    expired_count += 1
            except Exception as e:
                logger.error(f"Error checking expiry for rule {user_id}: {e}")
        
        for user_id in expired_users:
            self.remove_rule(user_id)
        
        if expired_count > 0:
            logger.info(f"🧹 Cleaned up {expired_count} expired firewall rules")
        
        return expired_count
    
    def get_stats(self) -> Dict:
        """Get firewall statistics"""
        active_blocks = len([r for r in self.active_rules.values() if r['action'] == 'BLOCK'])
        active_restrictions = len([r for r in self.active_rules.values() if r['action'] == 'RESTRICT'])
        
        total_blocks = len([r for r in self.rule_history if r['action'] == 'BLOCK'])
        total_restrictions = len([r for r in self.rule_history if r['action'] == 'RESTRICT'])
        
        return {
            'active_rules': len(self.active_rules),
            'active_blocks': active_blocks,
            'active_restrictions': active_restrictions,
            'total_blocks_all_time': total_blocks,
            'total_restrictions_all_time': total_restrictions,
            'total_rules_all_time': len(self.rule_history),
            'os_type': self.os_type,
            'simulation_mode': self.simulation_mode
        }
    
    # ========================================================================
    # OS-SPECIFIC COMMAND GENERATORS (SIMULATED - NOT EXECUTED)
    # ========================================================================
    
    def _get_block_command(self, ip_address: str) -> str:
        """Generate OS-specific block command"""
        if self.os_type == "Windows":
            return f'netsh advfirewall firewall add rule name="IGNISYL_Block_{ip_address}" dir=in action=block remoteip={ip_address}'
        elif self.os_type == "Linux":
            return f'iptables -A INPUT -s {ip_address} -j DROP'
        elif self.os_type == "Darwin":  # macOS
            return f'pfctl -t blocklist -T add {ip_address}'
        else:
            return f'# Unsupported OS: {self.os_type}'
    
    def _get_restrict_external_command(self, ip_address: str) -> str:
        """Block external connections for an IP"""
        if self.os_type == "Windows":
            return f'netsh advfirewall firewall add rule name="IGNISYL_Restrict_{ip_address}" dir=out action=block remoteip=!192.168.0.0/16 localip={ip_address}'
        elif self.os_type == "Linux":
            return f'iptables -A OUTPUT -s {ip_address} ! -d 192.168.0.0/16,10.0.0.0/8 -j DROP'
        else:
            return f'# Restrict external for {ip_address}'
    
    def _get_rate_limit_command(self, ip_address: str, limit_mbps: int = 1) -> str:
        """Apply bandwidth rate limiting"""
        if self.os_type == "Linux":
            return f'tc qdisc add dev eth0 root handle 1: htb default 10 && tc class add dev eth0 parent 1: classid 1:1 htb rate {limit_mbps}mbit'
        elif self.os_type == "Windows":
            return f'# Rate limit not directly supported - would use QoS policies'
        else:
            return f'# Rate limit {ip_address} to {limit_mbps}Mbps'
    
    def _get_block_ports_command(self, ip_address: str, ports: List[int]) -> str:
        """Block specific ports for an IP"""
        port_list = ','.join(map(str, ports))
        
        if self.os_type == "Windows":
            return f'netsh advfirewall firewall add rule name="IGNISYL_BlockPorts_{ip_address}" dir=out protocol=TCP remoteport={port_list} localip={ip_address} action=block'
        elif self.os_type == "Linux":
            return f'iptables -A OUTPUT -s {ip_address} -p tcp -m multiport --dports {port_list} -j DROP'
        else:
            return f'# Block ports {port_list} for {ip_address}'
    
    def _get_remove_command(self, ip_address: str) -> str:
        """Generate command to remove firewall rule"""
        if self.os_type == "Windows":
            return f'netsh advfirewall firewall delete rule name="IGNISYL_Block_{ip_address}"'
        elif self.os_type == "Linux":
            return f'iptables -D INPUT -s {ip_address} -j DROP'
        elif self.os_type == "Darwin":
            return f'pfctl -t blocklist -T delete {ip_address}'
        else:
            return f'# Remove rule for {ip_address}'
    
    async def auto_cleanup_loop(self):
        """Background task to automatically cleanup expired rules"""
        logger.info("🔄 Starting auto-cleanup loop")
        
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                self.cleanup_expired_rules()
            except Exception as e:
                logger.error(f"Error in auto-cleanup loop: {e}")

# Global firewall controller instance
try:
    firewall = FirewallController()
except Exception as e:
    logger.error(f"Failed to initialize firewall controller: {e}")
    firewall = None

# ============================================================================
# UTILITY FUNCTIONS FOR EASY ACCESS
# ============================================================================

def block_user(user_id: str, ip_address: str, duration_minutes: int = 60, reason: str = "") -> Dict:
    """Block a user's network access"""
    if firewall:
        return firewall.apply_block(user_id, ip_address, duration_minutes, reason)
    return {"success": False, "message": "Firewall controller not available"}

def restrict_user(user_id: str, ip_address: str, restrictions: List[str], 
                 duration_minutes: int = 30, reason: str = "") -> Dict:
    """Apply restrictions to a user"""
    if firewall:
        return firewall.apply_restriction(user_id, ip_address, restrictions, duration_minutes, reason)
    return {"success": False, "message": "Firewall controller not available"}

def allow_user(user_id: str) -> Dict:
    """Allow normal access for a user"""
    if firewall:
        return firewall.allow_user(user_id)
    return {"success": False, "message": "Firewall controller not available"}

def unblock_user(user_id: str) -> Dict:
    """Remove firewall rules for a user"""
    if firewall:
        return firewall.remove_rule(user_id)
    return {"success": False, "message": "Firewall controller not available"}

def get_blocked_users() -> List[Dict]:
    """Get list of currently blocked/restricted users"""
    if firewall:
        return firewall.get_active_rules()
    return []

def get_firewall_stats() -> Dict:
    """Get firewall statistics"""
    if firewall:
        return firewall.get_stats()
    return {}

def main():
    """Test firewall controller"""
    print("\n" + "="*60)
    print("IGNISYL Firewall Controller Test")
    print("="*60 + "\n")
    
    fw = FirewallController()
    
    # Test block
    print("Testing BLOCK action...")
    result = fw.apply_block("test_user_1", "192.168.1.100", duration_minutes=5, reason="High risk activity detected")
    print(f"   Result: {result['message']}")
    
    # Test restriction
    print("\nTesting RESTRICT action...")
    result = fw.apply_restriction("test_user_2", "192.168.1.101", 
                                  ["block_external", "rate_limit"], 
                                  duration_minutes=10,
                                  reason="Medium risk activity detected")
    print(f"   Result: {result['message']}")
    
    # Get active rules
    print(f"\n📊 Active rules: {len(fw.get_active_rules())}")
    
    # Get stats
    stats = fw.get_stats()
    print(f"\n📈 Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Firewall controller test complete!")
    print("⚠️  Note: All commands are SIMULATED for safety")

if __name__ == "__main__":
    main()