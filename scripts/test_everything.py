#!/usr/bin/env python3
"""
GENESIS PROTOCOL - Comprehensive System Test
Tests all components to ensure robustness
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import os
os.environ['TESTING'] = 'true'  # Prevent actual BigQuery calls

from backend.core.validators import (
    TenantValidator, 
    LedgerValidator, 
    QueryValidator,
    EntityValidator
)
from backend.core.exceptions import (
    TenantIsolationError,
    LedgerValidationError
)
from backend.core.events import EventBus, Event
from datetime import datetime, date
from decimal import Decimal


class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def test(self, name: str, func):
        """Run a test"""
        try:
            func()
            print(f"✅ {name}")
            self.passed += 1
            self.tests.append((name, True, None))
        except AssertionError as e:
            print(f"❌ {name}: {str(e)}")
            self.failed += 1
            self.tests.append((name, False, str(e)))
        except Exception as e:
            print(f"💥 {name}: {type(e).__name__}: {str(e)}")
            self.failed += 1
            self.tests.append((name, False, f"{type(e).__name__}: {str(e)}"))
    
    def summary(self):
        print("\n" + "="*60)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📊 Total: {self.passed + self.failed}")
        print("="*60)
        
        if self.failed > 0:
            print("\n❌ FAILED TESTS:")
            for name, passed, error in self.tests:
                if not passed:
                    print(f"  • {name}")
                    if error:
                        print(f"    {error}")
            return False
        else:
            print("\n🎉 ALL TESTS PASSED!")
            return True


def run_all_tests():
    """Run all tests"""
    print("🧬 GENESIS PROTOCOL - Comprehensive System Test")
    print("="*60 + "\n")
    
    runner = TestRunner()
    
    # =========================================================================
    # TENANT VALIDATION TESTS
    # =========================================================================
    print("📌 Testing Tenant Validation...")
    
    runner.test("Valid org_id", lambda: TenantValidator.validate_org_id("org123") == "org123")
    runner.test("Wildcard org_id", lambda: TenantValidator.validate_org_id("*") == "*")
    
    def test_empty_org_id():
        try:
            TenantValidator.validate_org_id("")
            raise AssertionError("Should have raised TenantIsolationError")
        except TenantIsolationError:
            pass
    
    runner.test("Empty org_id raises error", test_empty_org_id)
    
    def test_invalid_org_id():
        try:
            TenantValidator.validate_org_id("org@#$")
            raise AssertionError("Should have raised TenantIsolationError")
        except TenantIsolationError:
            pass
    
    runner.test("Invalid org_id chars raises error", test_invalid_org_id)
    
    # =========================================================================
    # AMOUNT VALIDATION TESTS
    # =========================================================================
    print("\n📌 Testing Amount Validation...")
    
    runner.test("Valid amount 100.50", lambda: LedgerValidator.validate_amount(100.50) == Decimal("100.50"))
    runner.test("Valid amount 0", lambda: LedgerValidator.validate_amount(0) == Decimal("0"))
    runner.test("Valid amount 999999", lambda: LedgerValidator.validate_amount(999999.99))
    
    def test_negative_amount():
        try:
            LedgerValidator.validate_amount(-100)
            raise AssertionError("Should have raised LedgerValidationError")
        except LedgerValidationError:
            pass
    
    runner.test("Negative amount raises error", test_negative_amount)
    
    def test_too_many_decimals():
        try:
            LedgerValidator.validate_amount(100.123)
            raise AssertionError("Should have raised LedgerValidationError")
        except LedgerValidationError:
            pass
    
    runner.test("Too many decimals raises error", test_too_many_decimals)
    
    # =========================================================================
    # DATE VALIDATION TESTS
    # =========================================================================
    print("\n📌 Testing Date Validation...")
    
    runner.test("Valid date", lambda: LedgerValidator.validate_date("2026-01-25") == date(2026, 1, 25))
    
    def test_invalid_date_format():
        try:
            LedgerValidator.validate_date("25-01-2026")
            raise AssertionError("Should have raised LedgerValidationError")
        except LedgerValidationError:
            pass
    
    runner.test("Invalid date format raises error", test_invalid_date_format)
    
    def test_invalid_date_value():
        try:
            LedgerValidator.validate_date("2026-13-01")
            raise AssertionError("Should have raised LedgerValidationError")
        except LedgerValidationError:
            pass
    
    runner.test("Invalid date value raises error", test_invalid_date_value)
    
    # =========================================================================
    # DATE RANGE VALIDATION TESTS
    # =========================================================================
    print("\n📌 Testing Date Range Validation...")
    
    def test_valid_range():
        start, end = QueryValidator.validate_date_range("2026-01-01", "2026-01-31")
        assert start == date(2026, 1, 1)
        assert end == date(2026, 1, 31)
    
    runner.test("Valid date range", test_valid_range)
    
    def test_reversed_range():
        try:
            QueryValidator.validate_date_range("2026-12-31", "2026-01-01")
            raise AssertionError("Should have raised LedgerValidationError")
        except LedgerValidationError:
            pass
    
    runner.test("Reversed date range raises error", test_reversed_range)
    
    def test_too_large_range():
        try:
            QueryValidator.validate_date_range("2020-01-01", "2026-01-01")
            raise AssertionError("Should have raised LedgerValidationError")
        except LedgerValidationError:
            pass
    
    runner.test("Too large range raises error", test_too_large_range)
    
    # =========================================================================
    # PHONE VALIDATION TESTS
    # =========================================================================
    print("\n📌 Testing Phone Validation...")
    
    runner.test("Valid phone 10 digits", lambda: EntityValidator.validate_phone("9876543210") == "9876543210")
    runner.test("Valid phone with +91", lambda: EntityValidator.validate_phone("+919876543210") == "+919876543210")
    runner.test("None phone", lambda: EntityValidator.validate_phone(None) is None)
    
    def test_invalid_phone_short():
        try:
            EntityValidator.validate_phone("123")
            raise AssertionError("Should have raised LedgerValidationError")
        except LedgerValidationError:
            pass
    
    runner.test("Short phone raises error", test_invalid_phone_short)
    
    def test_invalid_phone_start():
        try:
            EntityValidator.validate_phone("1234567890")
            raise AssertionError("Should have raised LedgerValidationError")
        except LedgerValidationError:
            pass
    
    runner.test("Invalid phone start digit raises error", test_invalid_phone_start)
    
    # =========================================================================
    # EMAIL VALIDATION TESTS
    # =========================================================================
    print("\n📌 Testing Email Validation...")
    
    runner.test("Valid email", lambda: EntityValidator.validate_email("test@example.com") == "test@example.com")
    runner.test("None email", lambda: EntityValidator.validate_email(None) is None)
    
    def test_invalid_email():
        try:
            EntityValidator.validate_email("invalid-email")
            raise AssertionError("Should have raised LedgerValidationError")
        except LedgerValidationError:
            pass
    
    runner.test("Invalid email raises error", test_invalid_email)
    
    # =========================================================================
    # EVENT BUS TESTS
    # =========================================================================
    print("\n📌 Testing Event Bus...")
    
    def test_event_bus():
        bus = EventBus()
        received_events = []
        
        def handler(event):
            received_events.append(event)
        
        bus.subscribe("test.event", handler)
        
        event = Event(
            event_type="test.event",
            timestamp=datetime.now(),
            org_id="test",
            location_id="test",
            payload={"message": "hello"}
        )
        
        bus.emit(event)
        
        assert len(received_events) == 1
        assert received_events[0].event_type == "test.event"
        assert received_events[0].payload["message"] == "hello"
    
    runner.test("Event Bus subscribe and emit", test_event_bus)
    
    def test_event_bus_multiple_handlers():
        bus = EventBus()
        bus.clear_all()  # Clear previous subscriptions
        
        counter = {"count": 0}
        
        def handler1(event):
            counter["count"] += 1
        
        def handler2(event):
            counter["count"] += 10
        
        bus.subscribe("multi.event", handler1)
        bus.subscribe("multi.event", handler2)
        
        event = Event(
            event_type="multi.event",
            timestamp=datetime.now(),
            org_id="test",
            location_id="test",
            payload={}
        )
        
        bus.emit(event)
        
        assert counter["count"] == 11  # Both handlers called
    
    runner.test("Event Bus multiple handlers", test_event_bus_multiple_handlers)
    
    # =========================================================================
    # QUERY LIMIT VALIDATION
    # =========================================================================
    print("\n📌 Testing Query Limit Validation...")
    
    runner.test("Default limit", lambda: QueryValidator.validate_limit(None) == 100)
    runner.test("Valid limit 50", lambda: QueryValidator.validate_limit(50) == 50)
    
    def test_negative_limit():
        try:
            QueryValidator.validate_limit(-10)
            raise AssertionError("Should have raised LedgerValidationError")
        except LedgerValidationError:
            pass
    
    runner.test("Negative limit raises error", test_negative_limit)
    
    def test_excessive_limit():
        try:
            QueryValidator.validate_limit(5000)
            raise AssertionError("Should have raised LedgerValidationError")
        except LedgerValidationError:
            pass
    
    runner.test("Excessive limit raises error", test_excessive_limit)
    
    # =========================================================================
    # ENTITY TYPE VALIDATION
    # =========================================================================
    print("\n📌 Testing Entity Type Validation...")
    
    runner.test("Valid entity type employee", lambda: EntityValidator.validate_entity_type("employee") == "employee")
    runner.test("Valid entity type vendor", lambda: EntityValidator.validate_entity_type("vendor") == "vendor")
    runner.test("Case insensitive", lambda: EntityValidator.validate_entity_type("EMPLOYEE") == "employee")
    
    def test_invalid_entity_type():
        try:
            EntityValidator.validate_entity_type("invalid_type")
            raise AssertionError("Should have raised LedgerValidationError")
        except LedgerValidationError:
            pass
    
    runner.test("Invalid entity type raises error", test_invalid_entity_type)
    
    # Summary
    return runner.summary()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
