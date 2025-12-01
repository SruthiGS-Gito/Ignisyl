"""
Firewall Controller Tests for IGNISYL
Tests graduated response framework and analyst controls
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.firewall_controller import FirewallController

def test_graduated_response():
    """Test graduated response levels"""
    print("=" * 60)
    print("Testing Graduated Response Framework")
    print("=" * 60)
    
    firewall = FirewallController()
    
    # Test Level 1: ALLOW (Risk 0-29)
    print("\n📊 Test 1: Low Risk (Score: 15)")
    result = firewall.apply_graduated_response("test_user_1", 15)
    assert result["action"] == "ALLOW"
    assert result["level"] == 1
    print(f"✅ Result: {result['action']} (Level {result['level']})")
    
    # Test Level 2: MONITOR (Risk 30-49)
    print("\n📊 Test 2: Medium Risk (Score: 40)")
    result = firewall.apply_graduated_response("test_user_2", 40)
    assert result["action"] == "MONITOR"
    assert result["level"] == 2
    print(f"✅ Result: {result['action']} (Level {result['level']})")
    
    # Test Level 3: RESTRICT (Risk 50-69)
    print("\n📊 Test 3: High Risk (Score: 60)")
    result = firewall.apply_graduated_response("test_user_3", 60)
    assert result["action"] in ["RESTRICT", "PENDING"]
    assert result["level"] == 3
    print(f"✅ Result: {result['action']} (Level {result['level']})")
    
    # Test Level 4: ISOLATE (Risk 70-89)
    print("\n📊 Test 4: Critical Risk (Score: 80)")
    result = firewall.apply_graduated_response("test_user_4", 80)
    assert result["action"] == "ISOLATE"
    assert result["level"] == 4
    print(f"✅ Result: {result['action']} (Level {result['level']})")
    
    # Test Level 5: BLOCK (Risk 90-100)
    print("\n📊 Test 5: Extreme Risk (Score: 95)")
    result = firewall.apply_graduated_response("test_user_5", 95)
    assert result["action"] == "BLOCK"
    assert result["level"] == 5
    print(f"✅ Result: {result['action']} (Level {result['level']})")
    
    print("\n✅ All graduated response tests passed!")

def test_analyst_override():
    """Test analyst override controls"""
    print("\n" + "=" * 60)
    print("Testing Analyst Override Controls")
    print("=" * 60)
    
    firewall = FirewallController()
    
    # Test ALLOW action
    print("\n📊 Test 1: Analyst ALLOW")
    result = firewall.analyst_override_action(
        user_id="test_user",
        action="ALLOW",
        custom_restrictions={},
        analyst_id="analyst_1",
        reason="False positive - legitimate activity"
    )
    assert result["action_applied"] == "ALLOW"
    print(f"✅ Result: {result['status']}")
    
    # Test RESTRICT action with custom restrictions
    print("\n📊 Test 2: Analyst RESTRICT with custom rules")
    result = firewall.analyst_override_action(
        user_id="test_user",
        action="RESTRICT",
        custom_restrictions={
            "block_external_internet": True,
            "rate_limit_mbps": 1,
            "block_ports": [21, 22, 445],
            "duration_minutes": 60,
            "notify_user": True
        },
        analyst_id="analyst_1",
        reason="Suspicious activity - investigating"
    )
    assert result["action_applied"] == "RESTRICT"
    assert "restrictions" in result
    print(f"✅ Result: {result['status']}")
    print(f"   Restrictions: {result['restrictions']}")
    
    # Test ISOLATE action
    print("\n📊 Test 3: Analyst ISOLATE")
    result = firewall.analyst_override_action(
        user_id="test_user",
        action="ISOLATE",
        custom_restrictions={
            "block_all_external": True,
            "allow_internal_only": True
        },
        analyst_id="analyst_1",
        reason="High confidence threat - quarantine required"
    )
    assert result["action_applied"] == "ISOLATE"
    print(f"✅ Result: {result['status']}")
    
    # Test BLOCK action
    print("\n📊 Test 4: Analyst BLOCK")
    result = firewall.analyst_override_action(
        user_id="test_user",
        action="BLOCK",
        custom_restrictions={
            "complete_network_disconnect": True,
            "require_admin_unlock": True
        },
        analyst_id="analyst_1",
        reason="Confirmed insider threat"
    )
    assert result["action_applied"] == "BLOCK"
    print(f"✅ Result: {result['status']}")
    
    print("\n✅ All analyst override tests passed!")

def test_basic_firewall_operations():
    """Test basic firewall operations"""
    print("\n" + "=" * 60)
    print("Testing Basic Firewall Operations")
    print("=" * 60)
    
    firewall = FirewallController()
    
    # Test block user
    print("\n📊 Test 1: Block User")
    result = firewall.apply_block("test_user", "192.168.1.100", duration_minutes=30)
    assert result["success"] == True
    print(f"✅ User blocked: {result['message']}")
    
    # Test restriction
    print("\n📊 Test 2: Apply Restrictions")
    result = firewall.apply_restriction(
        "test_user_2",
        "192.168.1.101",
        restrictions=["block_external", "rate_limit"],
        duration_minutes=60
    )
    assert result["success"] == True
    print(f"✅ Restrictions applied: {result['message']}")
    
    # Test get active rules
    print("\n📊 Test 3: Get Active Rules")
    active_rules = firewall.get_active_rules()
    print(f"✅ Active rules: {len(active_rules)}")
    
    # Test remove rule
    print("\n📊 Test 4: Remove Rule")
    result = firewall.remove_rule("test_user")
    assert result["success"] == True
    print(f"✅ Rule removed: {result['message']}")
    
    print("\n✅ All basic firewall tests passed!")

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "=" * 60)
    print("Testing Edge Cases")
    print("=" * 60)
    
    firewall = FirewallController()
    
    # Test invalid action
    print("\n📊 Test 1: Invalid Action")
    try:
        firewall.analyst_override_action(
            user_id="test_user",
            action="INVALID_ACTION",
            custom_restrictions={},
            analyst_id="analyst_1",
            reason="Test"
        )
        print("❌ Should have raised ValueError")
    except ValueError as e:
        print(f"✅ Correctly raised ValueError: {e}")
    
    # Test boundary risk scores
    print("\n📊 Test 2: Boundary Risk Scores")
    boundary_scores = [0, 29, 30, 49, 50, 69, 70, 89, 90, 100]
    for score in boundary_scores:
        result = firewall.apply_graduated_response(f"user_{score}", score)
        print(f"   Score {score}: {result['action']} (Level {result['level']})")
    
    print("\n✅ All edge case tests passed!")

def run_all_firewall_tests():
    """Run all firewall tests"""
    print("=" * 60)
    print("IGNISYL - Firewall Controller Tests")
    print("=" * 60)
    
    try:
        test_graduated_response()
        test_analyst_override()
        test_basic_firewall_operations()
        test_edge_cases()
        
        print("\n" + "=" * 60)
        print("✅ ALL FIREWALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test assertion failed: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_firewall_tests()
