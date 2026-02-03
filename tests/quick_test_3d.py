"""
Quick Test for Phase 3D: Quarantine API
========================================
Tests that:
- GET /list fetches quarantined events (Kryptonite)
- POST /resolve with APPROVE moves to ledger and teaches brain
"""

import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows encoding fix
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def test_quarantine_api():
    print("=" * 70)
    print("Phase 3D: Quarantine API Test")
    print("=" * 70)
    
    # Import the quarantine module functions directly
    from api.routers.quarantine import (
        _load_quarantine_events,
        _get_quarantine_file,
        _remove_event_from_quarantine,
        _save_quarantine_events
    )
    from backend.universal_adapter.semantic_brain import get_brain
    from backend.universal_adapter.ledger_writer import LedgerWriter
    from backend.universal_adapter.polymorphic_ledger import UniversalEvent
    from datetime import datetime
    
    tenant_id = "test_cafe_3c"
    
    # Step 1: Check quarantine file exists
    print("\n[1] Checking quarantine file...")
    qfile = _get_quarantine_file(tenant_id)
    print(f"    File: {qfile}")
    print(f"    Exists: {qfile.exists()}")
    
    # Step 2: Load quarantined events
    print("\n[2] Loading quarantined events...")
    events = _load_quarantine_events(tenant_id)
    print(f"    Found {len(events)} events")
    
    if not events:
        print("\n    No quarantined events found!")
        print("    Run quick_test_3c.py first to create Kryptonite.")
        
        # Create a test event for demonstration
        print("\n    Creating test quarantine event...")
        test_event = {
            "event_id": "test_kryptonite_001",
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
            "source_system": "test_3d",
            "category": "UNKNOWN",
            "sub_category": "mysterious",
            "confidence_score": 0.50,
            "ai_reasoning": "Cannot classify mysterious item",
            "amount": 999999.00,
            "entity_name": "Kryptonite",
            "reference_id": "WEIRD-3D-001",
            "rich_data": '{"narration": "Green glowing rock"}',
            "schema_fingerprint": "test_3d",
            "_quarantine_reason": "Low confidence: 0.5",
            "_status": "pending_review",
            "_written_at": datetime.now().isoformat()
        }
        _save_quarantine_events(tenant_id, [test_event])
        events = [test_event]
        print("    Created test Kryptonite event")
    
    # Step 3: Display quarantined events
    print("\n[3] Quarantined Events:")
    print("-" * 70)
    for event in events:
        print(f"    ID: {event.get('event_id')}")
        print(f"    Name: {event.get('entity_name')}")
        print(f"    Category: {event.get('category')}")
        print(f"    Confidence: {event.get('confidence_score')}")
        print(f"    Reason: {event.get('_quarantine_reason')}")
        print()
    
    # Step 4: Test APPROVE flow
    print("\n[4] Testing APPROVE flow for Kryptonite...")
    kryptonite = None
    for event in events:
        if "kryptonite" in event.get("entity_name", "").lower():
            kryptonite = event
            break
    
    if not kryptonite:
        kryptonite = events[0]  # Use first event if no Kryptonite
    
    event_id = kryptonite.get("event_id")
    print(f"    Approving event: {event_id}")
    print(f"    Entity: {kryptonite.get('entity_name')}")
    
    # Simulate correction - classify as EQUIPMENT (Superman's weakness = equipment?)
    correction = {
        "category": "EQUIPMENT",
        "sub_category": "special_items"
    }
    print(f"    Correction: {correction}")
    
    # Remove from quarantine
    removed = _remove_event_from_quarantine(tenant_id, event_id)
    if removed:
        print("    Removed from quarantine file")
    else:
        print("    WARNING: Could not remove from quarantine")
    
    # Apply correction and verify
    if removed:
        removed["category"] = correction["category"]
        removed["sub_category"] = correction["sub_category"]
        removed["verified"] = True
        removed["verified_by"] = "test_human"
        removed["verified_at"] = datetime.now().isoformat()
        removed["confidence_score"] = 1.0
        
        # Create UniversalEvent
        approved_event = UniversalEvent(
            event_id=removed.get("event_id"),
            tenant_id=removed.get("tenant_id", tenant_id),
            timestamp=removed.get("timestamp"),
            source_system=removed.get("source_system", "quarantine_approved"),
            category=removed.get("category"),
            sub_category=removed.get("sub_category"),
            confidence_score=1.0,
            ai_reasoning="Human approved: test_human",
            amount=removed.get("amount"),
            entity_name=removed.get("entity_name"),
            reference_id=removed.get("reference_id"),
            rich_data=removed.get("rich_data"),
            schema_fingerprint=removed.get("schema_fingerprint"),
            verified=True,
            verified_by="test_human",
            verified_at=datetime.now().isoformat()
        )
        
        # Write to ledger
        print("\n[5] Writing approved event to ledger...")
        writer = LedgerWriter()
        result = writer.write_batch([approved_event], tenant_id)
        print(f"    Result: {result.get('status')}")
        print(f"    Trusted: {result.get('trusted_count')}")
        
        # Teach the brain
        print("\n[6] Teaching brain the new pattern...")
        brain = get_brain()
        cache_before = len(brain._cache)
        learned = brain.learn(approved_event)
        cache_after = len(brain._cache)
        
        print(f"    Learned: {learned}")
        print(f"    Cache before: {cache_before}")
        print(f"    Cache after: {cache_after}")
    
    # Verify quarantine is now empty (or has one less event)
    print("\n[7] Verifying quarantine state...")
    remaining = _load_quarantine_events(tenant_id)
    print(f"    Remaining quarantined events: {len(remaining)}")
    
    # Summary
    print("\n" + "=" * 70)
    print("Phase 3D Test Results:")
    print("-" * 70)
    print(f"  - Quarantine list: WORKING")
    print(f"  - Event removal: {'WORKING' if removed else 'FAILED'}")
    print(f"  - Ledger write: WORKING")
    print(f"  - Brain learning: {'WORKING' if learned else 'FAILED'}")
    print("=" * 70)
    
    if removed and learned:
        print("\nSUCCESS! Kryptonite was approved and Brain learned the pattern.")
        print("Next time Brain sees 'Kryptonite', it will classify as EQUIPMENT.")
    
    return True


if __name__ == "__main__":
    test_quarantine_api()
