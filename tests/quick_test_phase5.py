"""
Quick Test for Phase 5: Library Migration & System Evolution
=============================================================
Tests that:
- No FutureWarning from google.generativeai
- New google.genai library works correctly
- System Evolution logs friction points
- AI suggests features from friction log
"""

import sys
import os
import warnings

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows encoding fix
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def test_no_warnings():
    """Test 1: Import modules without FutureWarning."""
    print("=" * 70)
    print("Phase 5: Library Migration & System Evolution Test")
    print("=" * 70)
    
    print("\n[1] Testing Library Imports (No Warnings)...")
    
    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Import the migrated modules
        from backend.universal_adapter.titan_cortex import TitanCortex
        from backend.universal_adapter.query_engine import QueryEngine
        from backend.core.system_evolution import SystemEvolution
        
        # Check for FutureWarning about google.generativeai
        future_warnings = [x for x in w if issubclass(x.category, FutureWarning)]
        genai_warnings = [x for x in future_warnings if 'google.generativeai' in str(x.message)]
        
        if genai_warnings:
            print(f"    WARNING: Found {len(genai_warnings)} google.generativeai warnings")
            for warn in genai_warnings:
                print(f"    - {warn.message}")
            return False
        else:
            print(f"    SUCCESS: No google.generativeai FutureWarnings!")
            print(f"    (Total warnings captured: {len(w)})")
    
    return True


def test_genai_client():
    """Test 2: Verify google.genai client works."""
    print("\n[2] Testing google.genai Client...")
    
    try:
        from google import genai
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("    SKIP: No GEMINI_API_KEY found")
            return True
        
        client = genai.Client(api_key=api_key)
        
        # Quick test call
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Say 'Hello from google.genai!' in exactly those words."
        )
        
        print(f"    Response: {response.text[:50]}...")
        print(f"    SUCCESS: google.genai client working!")
        return True
        
    except Exception as e:
        print(f"    ERROR: {e}")
        return False


def test_system_evolution():
    """Test 3: System Evolution friction logging."""
    print("\n[3] Testing System Evolution Module...")
    
    from backend.core.system_evolution import (
        SystemEvolution, FrictionType, get_evolution, log_friction
    )
    
    evolution = get_evolution()
    
    # Log some test friction points
    print("    Logging test friction points...")
    
    # Friction 1: Missing feature request
    log_friction(
        FrictionType.MISSING_FEATURE,
        "User asked for Payroll module - not available",
        tenant_id="test-tenant"
    )
    
    # Friction 2: Another missing feature
    log_friction(
        FrictionType.MISSING_FEATURE,
        "User asked for Payroll integration with banks",
        tenant_id="test-tenant"
    )
    
    # Friction 3: Unhandled query
    log_friction(
        FrictionType.UNHANDLED_QUERY,
        "User asked: 'Show me employee salaries' - no HR data",
        tenant_id="test-tenant"
    )
    
    # Friction 4: Repeated request pattern
    for i in range(3):
        log_friction(
            FrictionType.REPEATED_REQUEST,
            "User keeps asking for export to Excel feature",
            tenant_id="test-tenant"
        )
    
    # Get summary
    summary = evolution.get_friction_summary()
    print(f"\n    Friction Summary:")
    print(f"    - Total Points: {summary['total_points']}")
    print(f"    - By Type: {summary['by_type']}")
    print(f"    - Patterns Detected: {len(summary.get('patterns', []))}")
    
    return summary['total_points'] > 0


def test_feature_suggestions():
    """Test 4: AI suggests features from friction log."""
    print("\n[4] Testing Feature Suggestions to Master...")
    
    from backend.core.system_evolution import get_evolution
    
    evolution = get_evolution()
    
    print("    Asking AI for feature suggestions...")
    suggestions = evolution.suggest_features_to_master()
    
    print(f"\n    Feature Suggestions for Master:")
    print(f"    {'-' * 50}")
    
    for i, suggestion in enumerate(suggestions[:3], 1):
        name = suggestion.get('feature_name', suggestion.get('suggestion', 'Unknown'))
        priority = suggestion.get('priority', 'N/A')
        reasoning = suggestion.get('reasoning', '')[:100]
        
        print(f"    {i}. {name}")
        print(f"       Priority: {priority}")
        print(f"       Reason: {reasoning}...")
        print()
    
    return len(suggestions) > 0


def test_query_engine_integration():
    """Test 5: Query Engine with new google.genai."""
    print("\n[5] Testing Query Engine (google.genai integration)...")
    
    from backend.universal_adapter.query_engine import QueryEngine
    
    engine = QueryEngine()
    
    # Test a simple query
    result = engine.ask(
        "What is my total revenue?",
        tenant_id="test-tenant",
        execute_sql=False,
        include_history=False  # Skip history for speed
    )
    
    print(f"    Question Understood: {result.get('question_understood')}")
    print(f"    SQL Generated: {result.get('sql_generated')}")
    print(f"    Answer Preview: {result.get('answer_text', '')[:100]}...")
    
    return result.get('question_understood', False)


def main():
    """Run all Phase 5 tests."""
    results = {
        "no_warnings": test_no_warnings(),
        "genai_client": test_genai_client(),
        "system_evolution": test_system_evolution(),
        "feature_suggestions": test_feature_suggestions(),
        "query_engine": test_query_engine_integration()
    }
    
    # Summary
    print("\n" + "=" * 70)
    print("Phase 5 Test Results:")
    print("-" * 70)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  - {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("\nALL TESTS PASSED - Immortal System Ready!")
        print("- No FutureWarnings")
        print("- google.genai library working")
        print("- System Evolution logging friction")
        print("- AI suggesting features to Master")
    else:
        print("\nSome tests failed - review output above")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
