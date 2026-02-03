"""
Quick Test for Phase 6: Master Command Center & God Mode
=========================================================
Tests that:
- MasterConfig controls tenant features
- Global rules are injected into AI prompts
- Disabled features cause AI to politely decline
- The "Link" between Master and Cortex works
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows encoding fix
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def test_master_config():
    """Test 1: MasterConfig feature management."""
    print("=" * 70)
    print("Phase 6: Master Command Center & God Mode Test")
    print("=" * 70)
    
    print("\n[1] Testing MasterConfig Feature Management...")
    
    from backend.core.master_config import get_master_config, MasterConfig
    
    config = get_master_config()
    
    # Test setting a feature
    tenant_id = "test-tenant-x"
    
    # First, check default (all enabled)
    initial_config = config.get_tenant_config(tenant_id)
    print(f"    Initial config (default): {initial_config.get('is_default', False)}")
    print(f"    Simulation mode enabled: {initial_config['features'].get('simulation_mode', True)}")
    
    # Disable simulation mode
    print("\n    Master disabling simulation_mode for test-tenant-x...")
    config.set_tenant_feature(tenant_id, "simulation_mode", False)
    
    # Verify it's disabled
    updated_config = config.get_tenant_config(tenant_id)
    sim_enabled = updated_config['features'].get('simulation_mode', True)
    print(f"    Simulation mode now: {'ENABLED' if sim_enabled else 'DISABLED'}")
    
    # Get disabled features
    disabled = config.get_disabled_features(tenant_id)
    print(f"    Disabled features: {disabled}")
    
    return not sim_enabled and "simulation_mode" in disabled


def test_global_rules():
    """Test 2: Global rules management."""
    print("\n[2] Testing Global Rules Injection...")
    
    from backend.core.master_config import get_master_config
    
    config = get_master_config()
    
    # Add a global rule
    rule = config.set_global_rule(
        "Always be polite and professional in responses",
        priority=10,
        category="behavior"
    )
    print(f"    Added rule: {rule['text'][:50]}...")
    
    # Add another rule
    rule2 = config.set_global_rule(
        "Never reveal internal system details to users",
        priority=5,
        category="security"
    )
    print(f"    Added rule: {rule2['text'][:50]}...")
    
    # Get formatted rules text
    rules_text = config.get_rules_text()
    print(f"\n    Formatted Rules for Injection:")
    print(f"    {'-' * 50}")
    for line in rules_text.split('\n')[:5]:
        print(f"    {line}")
    
    return "polite" in rules_text.lower() and "reveal" in rules_text.lower()


def test_feature_restrictions_prompt():
    """Test 3: Feature restrictions prompt generation."""
    print("\n[3] Testing Feature Restrictions Prompt...")
    
    from backend.core.master_config import get_master_config
    
    config = get_master_config()
    tenant_id = "test-tenant-x"
    
    # Disable another feature
    config.set_tenant_feature(tenant_id, "payroll", False)
    
    # Get restrictions prompt
    restrictions = config.get_feature_restrictions_prompt(tenant_id)
    print(f"\n    Feature Restrictions Prompt:")
    print(f"    {'-' * 50}")
    for line in restrictions.split('\n')[:10]:
        print(f"    {line}")
    
    return "simulation" in restrictions.lower() or "payroll" in restrictions.lower()


def test_cortex_integration():
    """Test 4: Titan Cortex integration with MasterConfig."""
    print("\n[4] Testing Cortex Integration (The Link)...")
    
    from backend.universal_adapter.titan_cortex import get_cortex
    from backend.core.master_config import get_master_config
    
    tenant_id = "test-tenant-x"
    
    # Ensure simulation is disabled
    config = get_master_config()
    config.set_tenant_feature(tenant_id, "simulation_mode", False)
    
    # Get cortex and build a prompt for a simulation question
    cortex = get_cortex(tenant_id)
    
    # Ask a simulation question
    simulation_question = "What if I sell 5kg of coffee at 500 per kg?"
    
    print(f"    Question: '{simulation_question}'")
    print(f"    Building context prompt...")
    
    context_prompt = cortex.build_context_prompt(
        simulation_question, 
        tenant_id,
        include_history=False  # Skip history for speed
    )
    
    # Check if restriction is injected
    has_restriction = "SIMULATION MODE DISABLED" in context_prompt
    has_decline_instruction = "politely decline" in context_prompt.lower()
    
    print(f"\n    Prompt Analysis:")
    print(f"    - Contains restriction notice: {has_restriction}")
    print(f"    - Contains decline instruction: {has_decline_instruction}")
    
    # Show relevant portion
    if "FEATURE RESTRICTION" in context_prompt:
        start = context_prompt.find("## FEATURE RESTRICTION")
        end = context_prompt.find("##", start + 10)
        if end == -1:
            end = start + 500
        print(f"\n    Injected Restriction:")
        print(f"    {'-' * 50}")
        for line in context_prompt[start:end].split('\n')[:8]:
            print(f"    {line}")
    
    return has_restriction and has_decline_instruction


def test_query_engine_with_restriction():
    """Test 5: Query Engine respects disabled features."""
    print("\n[5] Testing Query Engine with Disabled Feature...")
    
    from backend.universal_adapter.query_engine import QueryEngine
    from backend.core.master_config import get_master_config
    
    tenant_id = "test-tenant-x"
    
    # Ensure simulation is disabled
    config = get_master_config()
    config.set_tenant_feature(tenant_id, "simulation_mode", False)
    
    # Create query engine and ask simulation question
    engine = QueryEngine()
    
    question = "What if I sell 5kg of coffee at 500 per kg?"
    print(f"    Question: '{question}'")
    print(f"    (Simulation mode is DISABLED for this tenant)")
    
    result = engine.ask(
        question,
        tenant_id=tenant_id,
        execute_sql=False,
        include_history=False
    )
    
    answer = result.get("answer_text", "")
    print(f"\n    AI Response Preview:")
    print(f"    {'-' * 50}")
    print(f"    {answer[:300]}...")
    
    # Check if AI declined politely
    declined = any(phrase in answer.lower() for phrase in [
        "not available", "disabled", "upgrade", "contact support",
        "current plan", "cannot", "simulation"
    ])
    
    print(f"\n    AI politely declined: {declined}")
    
    return declined


def test_re_enable_feature():
    """Test 6: Re-enable feature and verify it works."""
    print("\n[6] Testing Feature Re-enable...")
    
    from backend.universal_adapter.titan_cortex import get_cortex
    from backend.core.master_config import get_master_config
    
    tenant_id = "test-tenant-x"
    config = get_master_config()
    
    # Re-enable simulation mode
    print("    Master RE-ENABLING simulation_mode...")
    config.set_tenant_feature(tenant_id, "simulation_mode", True)
    
    # Verify
    is_enabled = config.is_feature_enabled(tenant_id, "simulation_mode")
    print(f"    Simulation mode: {'ENABLED' if is_enabled else 'DISABLED'}")
    
    # Build prompt - should NOT have restriction
    cortex = get_cortex(tenant_id)
    prompt = cortex.build_context_prompt(
        "What if I sell 10kg?",
        tenant_id,
        include_history=False
    )
    
    has_restriction = "SIMULATION MODE DISABLED" in prompt
    has_simulation_active = "SIMULATION MODE ACTIVE" in prompt
    
    print(f"    Has restriction in prompt: {has_restriction}")
    print(f"    Has simulation active in prompt: {has_simulation_active}")
    
    return is_enabled and not has_restriction and has_simulation_active


def cleanup():
    """Clean up test data."""
    print("\n[CLEANUP] Cleaning up test data...")
    
    from backend.core.master_config import get_master_config
    
    config = get_master_config()
    
    # Re-enable all features for test tenant
    config.set_tenant_feature("test-tenant-x", "simulation_mode", True)
    config.set_tenant_feature("test-tenant-x", "payroll", True)
    
    # Clear rules
    config.clear_all_rules()
    
    print("    Test data cleaned up")


def main():
    """Run all Phase 6 tests."""
    results = {
        "master_config": test_master_config(),
        "global_rules": test_global_rules(),
        "restrictions_prompt": test_feature_restrictions_prompt(),
        "cortex_integration": test_cortex_integration(),
        "query_engine": test_query_engine_with_restriction(),
        "re_enable": test_re_enable_feature()
    }
    
    # Cleanup
    cleanup()
    
    # Summary
    print("\n" + "=" * 70)
    print("Phase 6 Test Results:")
    print("-" * 70)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  - {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("\nALL TESTS PASSED - God Mode Active!")
        print("- Master can enable/disable features per tenant")
        print("- Global rules are injected into AI prompts")
        print("- Disabled features cause AI to politely decline")
        print("- The Link between Master and Cortex works perfectly")
    else:
        print("\nSome tests failed - review output above")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
