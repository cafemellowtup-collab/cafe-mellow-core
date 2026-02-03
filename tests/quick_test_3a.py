"""
Quick Test for Phase 3A: Ledger Writer
======================================
Tests the dual-mode storage engine.
Expected result: "saved_locally" (since no cloud credentials)
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

from backend.universal_adapter.ledger_writer import LedgerWriter
from backend.universal_adapter.polymorphic_ledger import UniversalEvent


def test_ledger_writer():
    print("=" * 60)
    print("Phase 3A: Ledger Writer Test")
    print("=" * 60)
    
    # Initialize writer
    writer = LedgerWriter()
    
    # Check mode
    print(f"\n[1] Writer Mode: {writer.get_mode()}")
    status = writer.get_status()
    print(f"    BigQuery Available: {status['bigquery_available']}")
    print(f"    Local Data Dir: {status['local_data_dir']}")
    
    # Create test events
    print("\n[2] Creating test events...")
    events = [
        UniversalEvent(
            event_id="test_001",
            tenant_id="test_tenant",
            timestamp="2026-01-31T12:00:00",
            source_system="quick_test",
            category="SALES",
            sub_category="POS_ORDER",
            confidence_score=0.95,
            ai_reasoning="Test event",
            amount=150.50,
            entity_name="Test Customer",
            reference_id="ORD-001",
            rich_data='{"item": "Coffee", "qty": 2}',
            schema_fingerprint="test_fp"
        ),
        UniversalEvent(
            event_id="test_002",
            tenant_id="test_tenant",
            timestamp="2026-01-31T12:05:00",
            source_system="quick_test",
            category="SALES",
            sub_category="POS_ORDER",
            confidence_score=0.92,
            ai_reasoning="Test event 2",
            amount=75.00,
            entity_name="Another Customer",
            reference_id="ORD-002",
            rich_data='{"item": "Pastry", "qty": 1}',
            schema_fingerprint="test_fp"
        )
    ]
    print(f"    Created {len(events)} test events")
    
    # Write batch
    print("\n[3] Writing batch to storage...")
    result = writer.write_batch(events, tenant_id="test_tenant")
    
    print(f"\n[4] Result:")
    print(f"    Status: {result.get('status')}")
    print(f"    Count: {result.get('count')}")
    if result.get('file'):
        print(f"    File: {result.get('file')}")
    
    # Verify file was created (for local mode)
    if result.get('status') == 'saved_locally' and result.get('file'):
        file_path = result.get('file')
        if os.path.exists(file_path):
            print(f"\n[5] Verifying file contents...")
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            print(f"    File has {len(lines)} line(s)")
            print(f"    [OK] Local storage verified!")
        else:
            print(f"\n[5] ERROR: File not found at {file_path}")
    
    # Summary
    print("\n" + "=" * 60)
    if result.get('status') in ['saved_locally', 'persisted_to_bigquery']:
        print("TEST PASSED: Ledger Writer is working!")
    else:
        print(f"TEST RESULT: {result.get('status')}")
    print("=" * 60)
    
    return result


if __name__ == "__main__":
    test_ledger_writer()
