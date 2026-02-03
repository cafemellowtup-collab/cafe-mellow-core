"""
Quick Test for Phase 3C: Quarantine Queue (Traffic Cop)
========================================================
Tests that:
- "Electricity" (known, high confidence) -> Main Ledger
- "Coffee Beans" (known, high confidence) -> Main Ledger  
- "Kryptonite" (weird, low confidence) -> Quarantine Queue
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
from backend.universal_adapter.ledger_writer import LedgerWriter
from backend.universal_adapter.polymorphic_ledger import UniversalEvent


def test_traffic_cop():
    print("=" * 70)
    print("Phase 3C: Quarantine Queue (Traffic Cop) Test")
    print("=" * 70)
    
    # Initialize components
    brain = SemanticBrain()
    writer = LedgerWriter()
    
    print(f"\n[1] Components initialized")
    print(f"    Brain cache: {len(brain._cache)} entries")
    print(f"    Writer mode: {writer.get_mode()}")
    print(f"    Confidence threshold: {writer.CONFIDENCE_THRESHOLD}")
    
    # Create test events - mix of known and weird items
    print("\n[2] Creating test events...")
    
    events = [
        # Known item 1: Electricity (should be OVERHEAD, high confidence)
        UniversalEvent(
            event_id="test_3c_001",
            tenant_id="test_cafe",
            timestamp="2026-01-31T20:00:00",
            source_system="test_3c",
            category="UNKNOWN",
            sub_category="unknown",
            confidence_score=0.0,
            ai_reasoning="",
            amount=2500.00,
            entity_name="Electricity Bill",
            reference_id="ELEC-3C-001",
            rich_data='{"narration": "Monthly BESCOM payment"}',
            schema_fingerprint="test_3c"
        ),
        # Known item 2: Coffee Beans (should be INVENTORY, high confidence)
        UniversalEvent(
            event_id="test_3c_002",
            tenant_id="test_cafe",
            timestamp="2026-01-31T20:01:00",
            source_system="test_3c",
            category="UNKNOWN",
            sub_category="unknown",
            confidence_score=0.0,
            ai_reasoning="",
            amount=1500.00,
            entity_name="Premium Coffee Beans",
            reference_id="INV-3C-002",
            rich_data='{"description": "Arabica from Coorg"}',
            schema_fingerprint="test_3c"
        ),
        # WEIRD ITEM: Kryptonite (should get LOW confidence -> QUARANTINE)
        UniversalEvent(
            event_id="test_3c_003",
            tenant_id="test_cafe",
            timestamp="2026-01-31T20:02:00",
            source_system="test_3c",
            category="UNKNOWN",
            sub_category="unknown",
            confidence_score=0.0,
            ai_reasoning="",
            amount=999999.00,
            entity_name="Kryptonite",
            reference_id="WEIRD-3C-003",
            rich_data='{"narration": "Mysterious green rock from Metropolis"}',
            schema_fingerprint="test_3c"
        ),
        # Known item 3: Milk (should be INVENTORY, high confidence - already cached)
        UniversalEvent(
            event_id="test_3c_004",
            tenant_id="test_cafe",
            timestamp="2026-01-31T20:03:00",
            source_system="test_3c",
            category="UNKNOWN",
            sub_category="unknown",
            confidence_score=0.0,
            ai_reasoning="",
            amount=200.00,
            entity_name="Milk",
            reference_id="INV-3C-004",
            rich_data='{"description": "Daily dairy supply"}',
            schema_fingerprint="test_3c"
        ),
    ]
    
    print(f"    Created {len(events)} test events")
    print(f"    - Electricity Bill (expected: OVERHEAD -> Ledger)")
    print(f"    - Coffee Beans (expected: INVENTORY -> Ledger)")
    print(f"    - Kryptonite (expected: UNKNOWN/LOW -> Quarantine)")
    print(f"    - Milk (expected: INVENTORY -> Ledger)")
    
    # Run classification
    print("\n[3] Running SemanticBrain classification...")
    classified_events = brain.classify_batch(events)
    
    # Show classification results
    print("\n[4] Classification Results:")
    print("-" * 70)
    for event in classified_events:
        status = "-> LEDGER" if event.confidence_score >= 0.85 else "-> QUARANTINE"
        print(f"    {event.entity_name}:")
        print(f"       Category: {event.category}, Confidence: {event.confidence_score:.2f} {status}")
        print(f"       Reasoning: {event.ai_reasoning[:60]}...")
    
    # Run Traffic Cop (write_batch)
    print("\n[5] Running LedgerWriter Traffic Cop...")
    result = writer.write_batch(classified_events, "test_cafe_3c")
    
    # Show write results
    print("\n[6] Traffic Cop Results:")
    print("-" * 70)
    print(f"    Status: {result.get('status')}")
    print(f"    Total events: {result.get('count')}")
    print(f"    Trusted (-> Ledger): {result.get('trusted_count')}")
    print(f"    Quarantined (-> Queue): {result.get('quarantined_count')}")
    print(f"    Details: {result.get('details')}")
    
    # Verification
    print("\n" + "=" * 70)
    trusted = result.get('trusted_count', 0)
    quarantined = result.get('quarantined_count', 0)
    
    # Expected: 3 trusted (Electricity, Coffee, Milk), 1 quarantined (Kryptonite)
    expected_trusted = 3
    expected_quarantined = 1
    
    if trusted >= expected_trusted and quarantined >= expected_quarantined:
        print("SUCCESS! Traffic Cop is working correctly:")
        print(f"  - {trusted} trusted events written to Main Ledger")
        print(f"  - {quarantined} weird event(s) diverted to Quarantine")
        print("\nKryptonite did NOT pollute the Main Ledger! ")
    else:
        print("UNEXPECTED RESULTS:")
        print(f"  Expected: {expected_trusted} trusted, {expected_quarantined} quarantined")
        print(f"  Got: {trusted} trusted, {quarantined} quarantined")
    
    print("=" * 70)
    
    # Show quarantine file contents if local mode
    if result.get('details', {}).get('quarantine', {}).get('file'):
        qfile = result['details']['quarantine']['file']
        print(f"\nQuarantine file contents ({qfile}):")
        print("-" * 70)
        try:
            with open(qfile, 'r') as f:
                for line in f:
                    import json
                    data = json.loads(line)
                    print(f"  - {data.get('entity_name')}: {data.get('_quarantine_reason')}")
        except Exception as e:
            print(f"  Could not read: {e}")
    
    return trusted >= expected_trusted and quarantined >= expected_quarantined


if __name__ == "__main__":
    test_traffic_cop()
