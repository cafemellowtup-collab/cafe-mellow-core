"""
GENESIS PROTOCOL - Custom Exceptions
Comprehensive error handling for robustness
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class TitanBaseException(Exception):
    """Base exception for all TITAN errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class TenantIsolationError(TitanBaseException):
    """Raised when tenant isolation is violated"""
    pass


class DataQualityError(TitanBaseException):
    """Raised when data quality checks fail"""
    pass


class LedgerValidationError(TitanBaseException):
    """Raised when ledger entry validation fails"""
    pass


class EventBusError(TitanBaseException):
    """Raised when event processing fails"""
    pass


class ConfigurationError(TitanBaseException):
    """Raised when required configuration is missing"""
    pass


class BigQueryError(TitanBaseException):
    """Raised when BigQuery operations fail"""
    pass


class RBACPermissionError(TitanBaseException):
    """Raised when RBAC permission check fails"""
    pass


class StorageError(TitanBaseException):
    """Raised when storage operations fail"""
    pass


# HTTP Exception Wrappers
def raise_http_400(message: str, details: Optional[Dict[str, Any]] = None):
    """Bad Request"""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"message": message, "details": details or {}}
    )


def raise_http_403(message: str, details: Optional[Dict[str, Any]] = None):
    """Forbidden"""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"message": message, "details": details or {}}
    )


def raise_http_404(message: str, details: Optional[Dict[str, Any]] = None):
    """Not Found"""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"message": message, "details": details or {}}
    )


def raise_http_500(message: str, details: Optional[Dict[str, Any]] = None):
    """Internal Server Error"""
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={"message": message, "details": details or {}}
    )


def raise_http_503(message: str, details: Optional[Dict[str, Any]] = None):
    """Service Unavailable"""
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={"message": message, "details": details or {}}
    )
