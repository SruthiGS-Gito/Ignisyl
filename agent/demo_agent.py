"""
IGNISYL Demo Agent - Safe Simulation Mode
For academic presentations and demonstrations
NO ACTUAL SYSTEM COMMANDS EXECUTED
"""

import time
import requests
import socket
import os
from datetime import datetime


class DemoAgent:
    def __init__(self, server_url):
        self.server_url = server_url
        self.username = os.getlogin()
        self.hostname = socket.gethostname()
        self.agent_id = f"demo_{self.hostname}_{int(time.time())}"
        self.running = False

        print("+" + "=" * 42 + "+")
        print("|  IGNISYL Demo Agent (SIMULATION)         |")
        print("+" + "=" * 42 + "+")
        print(f"[INFO] User: {self.username}")
        print(f"[INFO] Host: {self.hostname}")
        print(f"[INFO] Agent ID: {self.agent_id}")
        print(f"[DEMO] Simulation mode - no real commands")
        print()

    def execute_action(self, action):
        """SIMULATED execution - no real system changes"""
        action_type = action.get("type", "UNKNOWN")
        target = action.get("target", "N/A")

        print(f"\n[SIMULATION] Received: {action_type}")
        print(f"[SIMULATION] Target: {target}")
        print(f"[SIMULATION] What would happen in production:")

        if action_type == "BLOCK":
            print(f"  -> Would execute: netsh advfirewall firewall add rule ...")
            print(f"  -> Would block: All network traffic for user")
            print(f"  [OK] SIMULATED - No actual changes made")
            return {"status": "simulated", "action": "BLOCK", "message": "Firewall block simulated"}

        elif action_type == "RESTRICT":
            print(f"  -> Would execute: netsh advfirewall firewall add rule ...")
            print(f"  -> Would restrict: Limited bandwidth/ports")
            print(f"  [OK] SIMULATED - No actual changes made")
            return {"status": "simulated", "action": "RESTRICT", "message": "Network restriction simulated"}

        elif action_type == "ISOLATE":
            print(f"  -> Would execute: netsh advfirewall set allprofiles firewallpolicy blockinbound,blockoutbound")
            print(f"  -> Would isolate: Complete network isolation")
            print(f"  [OK] SIMULATED - No actual changes made")
            return {"status": "simulated", "action": "ISOLATE", "message": "Network isolation simulated"}

        elif action_type == "ALLOW":
            print(f"  -> Would execute: netsh advfirewall firewall delete rule ...")
            print(f"  -> Would allow: Restore full network access")
            print(f"  [OK] SIMULATED - No actual changes made")
            return {"status": "simulated", "action": "ALLOW", "message": "Access restoration simulated"}

        else:
            print(f"  -> Unknown action type: {action_type}")
            print(f"  [OK] SIMULATED - No changes made")
            return {"status": "simulated", "action": action_type, "message": "Unknown action simulated"}

    def register_with_server(self):
        """Register this demo agent with the IGNISYL server"""
        try:
            response = requests.post(
                f"{self.server_url}/api/v1/agent/register",
                json={
                    "agent_id": self.agent_id,
                    "hostname": self.hostname,
                    "username": self.username,
                    "mode": "demo",
                    "timestamp": datetime.now().isoformat()
                },
                timeout=10
            )
            if response.status_code == 200:
                print(f"[OK] Registered with server: {self.server_url}")
                return True
            else:
                print(f"[WARN] Server returned: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"[WARN] Could not connect to server: {self.server_url}")
            print(f"[INFO] Running in standalone demo mode")
            return False
        except Exception as e:
            print(f"[ERROR] Registration failed: {e}")
            return False

    def poll_for_actions(self):
        """Poll server for pending actions (demo mode)"""
        try:
            response = requests.get(
                f"{self.server_url}/api/v1/agent/{self.agent_id}/actions",
                timeout=5
            )
            if response.status_code == 200:
                actions = response.json().get("actions", [])
                return actions
            return []
        except:
            return []

    def send_status_update(self, action_result):
        """Send action result back to server"""
        try:
            requests.post(
                f"{self.server_url}/api/v1/agent/{self.agent_id}/status",
                json={
                    "agent_id": self.agent_id,
                    "result": action_result,
                    "timestamp": datetime.now().isoformat()
                },
                timeout=5
            )
        except:
            pass  # Non-critical in demo mode

    def run(self, poll_interval=5):
        """Main agent loop (demo mode)"""
        self.running = True
        print(f"\n[AGENT] Starting demo agent loop (poll interval: {poll_interval}s)")
        print(f"[AGENT] Press Ctrl+C to stop\n")

        # Try to register
        self.register_with_server()

        try:
            while self.running:
                # Poll for actions
                actions = self.poll_for_actions()

                for action in actions:
                    print(f"\n{'='*50}")
                    print(f"[ACTION] Processing action from server")
                    result = self.execute_action(action)
                    self.send_status_update(result)
                    print(f"{'='*50}\n")

                # Heartbeat
                print(f"[HEARTBEAT] {datetime.now().strftime('%H:%M:%S')} - Agent active (demo mode)")
                time.sleep(poll_interval)

        except KeyboardInterrupt:
            print("\n[AGENT] Shutdown requested")
            self.running = False

        print("[AGENT] Demo agent stopped")

    def simulate_action(self, action_type, target="test_user"):
        """Manually simulate an action for demonstration"""
        print(f"\n{'='*50}")
        print(f"[DEMO] Manual simulation triggered")
        action = {
            "type": action_type,
            "target": target,
            "timestamp": datetime.now().isoformat()
        }
        result = self.execute_action(action)
        print(f"{'='*50}\n")
        return result


def main():
    """Entry point for demo agent"""
    import argparse

    parser = argparse.ArgumentParser(description="IGNISYL Demo Agent")
    parser.add_argument(
        "--server",
        default="http://localhost:8000",
        help="IGNISYL server URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Poll interval in seconds (default: 5)"
    )
    parser.add_argument(
        "--demo-action",
        choices=["BLOCK", "RESTRICT", "ISOLATE", "ALLOW"],
        help="Run a single demo action and exit"
    )

    args = parser.parse_args()

    agent = DemoAgent(args.server)

    if args.demo_action:
        # Single demo action mode
        agent.simulate_action(args.demo_action)
    else:
        # Continuous polling mode
        agent.run(poll_interval=args.interval)


if __name__ == "__main__":
    main()
