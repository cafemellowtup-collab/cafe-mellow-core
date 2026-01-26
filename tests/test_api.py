"""
GENESIS PROTOCOL - Comprehensive API Tests
Test all endpoints to ensure robustness
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, date, timedelta
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import app

client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test /health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "project_id" in data
        assert "dataset_id" in data


class TestCronEndpoints:
    """Test cron endpoints (requires CRON_SECRET)"""
    
    def test_daily_close_without_secret(self):
        """Test daily_close requires CRON_SECRET"""
        response = client.post("/cron/daily_close")
        assert response.status_code in [403, 500]
    
    def test_health_check_public(self):
        """Test cron health check is public"""
        response = client.get("/cron/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestLedgerEndpoints:
    """Test ledger API endpoints"""
    
    def test_create_ledger_entry_validation(self):
        """Test ledger entry validation"""
        # Missing required fields
        response = client.post("/ledger/entries", json={})
        assert response.status_code == 422
        
        # Invalid amount (negative)
        invalid_entry = {
            "org_id": "test",
            "location_id": "test",
            "timestamp": datetime.now().isoformat(),
            "entry_date": str(date.today()),
            "type": "SALE",
            "amount": -100,
            "entry_source": "pos_petpooja"
        }
        response = client.post("/ledger/entries", json=invalid_entry)
        assert response.status_code in [400, 422]
    
    def test_query_ledger_validation(self):
        """Test ledger query parameter validation"""
        # Missing required params
        response = client.get("/ledger/entries")
        assert response.status_code == 422
        
        # Valid params structure
        response = client.get(
            "/ledger/entries",
            params={
                "org_id": "test",
                "location_id": "test",
                "start_date": str(date.today() - timedelta(days=7)),
                "end_date": str(date.today())
            }
        )
        # May fail due to BigQuery, but params should be valid
        assert response.status_code in [200, 500]


class TestAnalyticsEndpoints:
    """Test analytics endpoints"""
    
    def test_data_quality_params(self):
        """Test data quality endpoint parameter validation"""
        # Missing params
        response = client.get("/analytics/data_quality")
        assert response.status_code == 422
        
        # Invalid days parameter
        response = client.get(
            "/analytics/data_quality",
            params={"org_id": "test", "location_id": "test", "days": -5}
        )
        assert response.status_code in [400, 422]
    
    def test_profit_calculation_params(self):
        """Test profit calculation parameter validation"""
        # Missing dates
        response = client.get(
            "/analytics/profit",
            params={"org_id": "test", "location_id": "test"}
        )
        assert response.status_code == 422


class TestHREndpoints:
    """Test HR endpoints"""
    
    def test_create_entity_validation(self):
        """Test entity creation validation"""
        # Invalid entity type
        invalid_entity = {
            "entity_type": "invalid_type",
            "name": "Test Employee",
            "org_id": "test",
            "location_id": "test"
        }
        response = client.post("/hr/entities", json=invalid_entity)
        assert response.status_code in [400, 422]
        
        # Invalid phone format
        invalid_phone = {
            "entity_type": "employee",
            "name": "Test Employee",
            "org_id": "test",
            "location_id": "test",
            "contact_phone": "invalid"
        }
        response = client.post("/hr/entities", json=invalid_phone)
        assert response.status_code in [400, 422]


class TestValidation:
    """Test validation functions"""
    
    def test_tenant_validation(self):
        """Test tenant ID validation"""
        from backend.core.validators import TenantValidator
        from backend.core.exceptions import TenantIsolationError
        
        # Valid org_id
        assert TenantValidator.validate_org_id("org123") == "org123"
        assert TenantValidator.validate_org_id("*") == "*"
        
        # Invalid org_id
        with pytest.raises(TenantIsolationError):
            TenantValidator.validate_org_id("")
        
        with pytest.raises(TenantIsolationError):
            TenantValidator.validate_org_id("org@#$")
    
    def test_amount_validation(self):
        """Test amount validation"""
        from backend.core.validators import LedgerValidator
        from backend.core.exceptions import LedgerValidationError
        from decimal import Decimal
        
        # Valid amounts
        assert LedgerValidator.validate_amount(100.50) == Decimal("100.50")
        assert LedgerValidator.validate_amount(0) == Decimal("0")
        
        # Invalid amounts
        with pytest.raises(LedgerValidationError):
            LedgerValidator.validate_amount(-100)
        
        with pytest.raises(LedgerValidationError):
            LedgerValidator.validate_amount(100.123)  # Too many decimals
    
    def test_date_validation(self):
        """Test date validation"""
        from backend.core.validators import LedgerValidator
        from backend.core.exceptions import LedgerValidationError
        
        # Valid date
        assert LedgerValidator.validate_date("2026-01-25") == date(2026, 1, 25)
        
        # Invalid dates
        with pytest.raises(LedgerValidationError):
            LedgerValidator.validate_date("invalid")
        
        with pytest.raises(LedgerValidationError):
            LedgerValidator.validate_date("2026-13-01")  # Invalid month
    
    def test_phone_validation(self):
        """Test phone number validation"""
        from backend.core.validators import EntityValidator
        from backend.core.exceptions import LedgerValidationError
        
        # Valid phones
        assert EntityValidator.validate_phone("9876543210") == "9876543210"
        assert EntityValidator.validate_phone("+919876543210") == "+919876543210"
        assert EntityValidator.validate_phone(None) is None
        
        # Invalid phones
        with pytest.raises(LedgerValidationError):
            EntityValidator.validate_phone("123")  # Too short
        
        with pytest.raises(LedgerValidationError):
            EntityValidator.validate_phone("1234567890")  # Doesn't start with 6-9


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
