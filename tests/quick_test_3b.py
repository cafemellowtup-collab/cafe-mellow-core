"""
Quick Test for Phase 3B: Semantic Brain Classification
=======================================================
Tests that:
- "Electricity" + "Paid via GPay" -> OVERHEAD
- "Milku" (typo) -> INVENTORY
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

from backend.universal_adapter.semantic_brain import SemanticBrain
from backend.universal_adapter.polymorphic_ledger import UniversalEvent


def test_semantic_brain():
    print("=" * 60)
    print("Phase 3B: Semantic Brain Classification Test")
    print("=" * 60)
    
    # Initialize brain
    brain = SemanticBrain()
    print(f"\n[1] Brain initialized. Cache has {len(brain._cache)} entries.")
    
    # Create test events
    print("\n[2] Creating test events...")
    
    events = [
        # Test 1: Electricity (should be OVERHEAD)
        UniversalEvent(
            event_id="test_elec_001",
            tenant_id="test_cafe",
            timestamp="2026-01-31T10:00:00",
            source_system="test",
            category="UNKNOWN",
            sub_category="unknown",
            confidence_score=0.0,
            ai_reasoning="",
            amount=2500.00,
            entity_name="Electricity Bill",
            reference_id="ELEC-001",
            rich_data='{"narration": "Paid via GPay to BESCOM", "month": "January"}',
            schema_fingerprint="test"
        ),
        # Test 2: Milku (typo for Milk, should be INVENTORY)
        UniversalEvent(
            event_id="test_milk_002",
            tenant_id="test_cafe",
            timestamp="2026-01-31T11:00:00",
            source_system="test",
            category="UNKNOWN",
            sub_category="unknown",
            confidence_score=0.0,
            ai_reasoning="",
            amount=150.00,
            entity_name="Milku",
            reference_id="INV-002",
            rich_data='{"description": "Daily dairy supply", "liters": 5}',
            schema_fingerprint="test"
        ),
        # Test 3: Staff Salary (should be LABOR)
        UniversalEvent(
            event_id="test_salary_003",
            tenant_id="test_cafe",
            timestamp="2026-01-31T12:00:00",
            source_system="test",
            category="UNKNOWN",
            sub_category="unknown",
            confidence_score=0.0,
            ai_reasoning="",
            amount=15000.00,
            entity_name="Rahul - Barista",
            reference_id="SAL-003",
            rich_data='{"narration": "January salary payment", "department": "Kitchen"}',
            schema_fingerprint="test"
        ),
        # Test 4: Coffee Beans (should be INVENTORY)
        UniversalEvent(
            event_id="test_coffee_004",
            tenant_id="test_cafe",
            timestamp="2026-01-31T13:00:00",
            source_system="test",
            category="UNKNOWN",
            sub_category="unknown",
            confidence_score=0.0,
            ai_reasoning="",
            amount=3200.00,
            entity_name="Arabica Coffee Beans",
            reference_id="INV-004",
            rich_data='{"description": "Premium beans from Coorg", "kg": 2}',
            schema_fingerprint="test"
        ),
    ]
    
    print(f"    Created {len(events)} test events")
    
    # Test context building
    print("\n[3] Testing context string building...")
    for i, event in enumerate(events):
        ctx = brain._build_context_string(event)
        print(f"    Event {i+1}: {ctx[:80]}...")
    
    # Run classification
    print("\n[4] Running batch classification...")
    classified_events = brain.classify_batch(events)
    
    # Check results
    print("\n[5] Classification Results:")
    print("-" * 60)
    
    expected = [
        ("Electricity Bill", "OVERHEAD"),
        ("Milku", "INVENTORY"),
        ("Rahul - Barista", "LABOR"),
        ("Arabica Coffee Beans", "INVENTORY"),
    ]
    
    all_passed = True
    for i, (event, (name, expected_cat)) in enumerate(zip(classified_events, expected)):
        actual_cat = event.category
        status = "PASS" if actual_cat == expected_cat else "FAIL"
        if status == "FAIL":
            all_passed = False
        
        print(f"    {i+1}. {name}")
        print(f"       Category: {actual_cat} (expected: {expected_cat}) [{status}]")
        print(f"       Sub-cat:  {event.sub_category}")
        print(f"       Confidence: {event.confidence_score:.2f}")
        print(f"       Reasoning: {event.ai_reasoning[:60]}...")
        print()
    
    # Summary
    print("=" * 60)
    if all_passed:
        print("ALL TESTS PASSED! SemanticBrain classification working.")
    else:
        print("SOME TESTS FAILED. Check classifications above.")
    print("=" * 60)
    
    # Show cache stats
    stats = brain.get_cache_stats()
    print(f"\nCache Stats: {stats}")
    
    return all_passed


if __name__ == "__main__":
    test_semantic_brain()
