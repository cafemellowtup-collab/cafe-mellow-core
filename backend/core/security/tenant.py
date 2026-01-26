"""
Tenant Isolation Layer
CRITICAL: All BigQuery queries MUST be scoped by org_id and location_id
"""
from typing import Optional
from .models import TenantContext


class TenantIsolation:
    """
    Tenant Isolation Enforcement
    Ensures all queries are scoped by tenant context
    """
    
    @staticmethod
    def inject_where_clause(base_query: str, context: TenantContext) -> str:
        """
        Inject tenant isolation WHERE clause into query
        CRITICAL: This prevents cross-tenant data leakage
        """
        isolation_clause = context.to_sql_where()
        
        if "WHERE" in base_query.upper():
            return base_query.replace("WHERE", f"WHERE {isolation_clause} AND", 1)
        else:
            if "GROUP BY" in base_query.upper():
                return base_query.replace("GROUP BY", f"WHERE {isolation_clause} GROUP BY", 1)
            elif "ORDER BY" in base_query.upper():
                return base_query.replace("ORDER BY", f"WHERE {isolation_clause} ORDER BY", 1)
            elif "LIMIT" in base_query.upper():
                return base_query.replace("LIMIT", f"WHERE {isolation_clause} LIMIT", 1)
            else:
                return f"{base_query} WHERE {isolation_clause}"
    
    @staticmethod
    def validate_query_has_isolation(query: str, context: TenantContext) -> bool:
        """
        Validate that query contains tenant isolation
        Returns True if query is safe, False otherwise
        """
        query_upper = query.upper()
        
        has_org_filter = f"ORG_ID = '{context.org_id.upper()}'" in query_upper
        
        if context.location_id:
            has_location_filter = f"LOCATION_ID = '{context.location_id.upper()}'" in query_upper
            return has_org_filter and has_location_filter
        
        return has_org_filter
