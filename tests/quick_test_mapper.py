"""Quick test for Phase 2E Universal Mapper"""
import sys
sys.path.insert(0, r"c:\Users\USER\OneDrive\Desktop\Cafe_AI")

from backend.universal_adapter.mapper import UniversalMapper

# Test 1: Basic mapping with standard columns
print("Test 1: Standard columns (date, amount, item)")
raw_data = [
    {"date": "2024-01-15", "amount": 1500.50, "item": "Coffee Beans", "qty": 5},
    {"date": "2024-01-16", "amount": 2300.00, "item": "Milk", "qty": 10},
    {"date": "2024-01-17", "amount": 875.25, "item": "Sugar", "qty": 3},
]
result = UniversalMapper.map_to_events(raw_data, "test-tenant")
print(f"  Valid: {result['stats']['valid']}, Failed: {result['stats']['failed']}")
print(f"  Column mapping: {result['column_mapping']}")
assert result['stats']['valid'] == 3, "Should map all 3 rows"
print("  PASS\n")

# Test 2: Currency symbols
print("Test 2: Currency symbols (Rs, $, commas)")
raw_data = [
    {"bill_date": "2024-01-15", "total_amount": "Rs 1,500.50", "description": "Order 1"},
    {"bill_date": "2024-01-16", "total_amount": "$2,300.00", "description": "Order 2"},
]
result = UniversalMapper.map_to_events(raw_data, "test-tenant")
print(f"  Valid: {result['stats']['valid']}, Failed: {result['stats']['failed']}")
if result['valid_events']:
    print(f"  First amount: {result['valid_events'][0].amount}")
assert result['stats']['valid'] == 2, "Should map both rows"
assert result['valid_events'][0].amount == 1500.50, "Should strip currency"
print("  PASS\n")

# Test 3: Missing required fields
print("Test 3: Missing date AND amount")
raw_data = [
    {"name": "Test", "category": "Food"},  # No date, no amount
]
result = UniversalMapper.map_to_events(raw_data, "test-tenant")
print(f"  Valid: {result['stats']['valid']}, Failed: {result['stats']['failed']}")
assert result['stats']['failed'] == 1, "Should fail row with no date/amount"
print("  PASS\n")

# Test 4: Alternative column names
print("Test 4: Alternative column names (created_at, price, product_name)")
raw_data = [
    {"created_at": "2024-01-15", "price": 500, "product_name": "Espresso"},
]
result = UniversalMapper.map_to_events(raw_data, "test-tenant")
print(f"  Column mapping: {result['column_mapping']}")
assert result['column_mapping']['timestamp_col'] == 'created_at'
assert result['column_mapping']['amount_col'] == 'price'
assert result['column_mapping']['entity_col'] == 'product_name'
print("  PASS\n")

# Test 5: Event structure
print("Test 5: Event structure verification")
raw_data = [{"date": "2024-01-15", "amount": 100, "item": "Test", "order_id": "ORD001"}]
result = UniversalMapper.map_to_events(raw_data, "cafe-001", source_system="test")
event = result['valid_events'][0]
print(f"  event_id: {event.event_id[:8]}...")
print(f"  tenant_id: {event.tenant_id}")
print(f"  timestamp: {event.timestamp}")
print(f"  amount: {event.amount}")
print(f"  entity_name: {event.entity_name}")
print(f"  reference_id: {event.reference_id}")
assert event.tenant_id == "cafe-001"
assert event.amount == 100.0
assert event.entity_name == "Test"
assert event.reference_id == "ORD001"
print("  PASS\n")

print("=" * 50)
print("All 5 tests PASSED!")
