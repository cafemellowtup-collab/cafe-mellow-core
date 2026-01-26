"""
RBAC Engine - Role-Based Access Control
"""
from typing import List, Optional
from .models import User, Role, Permission, PermissionScope


class RBACEngine:
    """RBAC Authorization Engine"""
    
    def __init__(self):
        self.roles: dict[str, Role] = {}
        self._initialize_system_roles()
    
    def _initialize_system_roles(self):
        """Initialize default system roles"""
        self.roles["admin"] = Role(
            id="admin",
            name="Administrator",
            description="Full system access",
            permissions=[PermissionScope.ADMIN_FULL],
            is_system_role=True
        )
        
        self.roles["manager"] = Role(
            id="manager",
            name="Manager",
            description="Dashboard, Chat, Analytics, Config",
            permissions=[
                PermissionScope.READ_DASHBOARD,
                PermissionScope.READ_SALES,
                PermissionScope.READ_EXPENSES,
                PermissionScope.READ_INVENTORY,
                PermissionScope.WRITE_EXPENSES,
                PermissionScope.MANAGE_CONFIG,
            ],
            is_system_role=True
        )
        
        self.roles["staff"] = Role(
            id="staff",
            name="Staff",
            description="Dashboard and Chat only",
            permissions=[
                PermissionScope.READ_DASHBOARD,
                PermissionScope.READ_SALES,
            ],
            is_system_role=True
        )
    
    def get_user_permissions(self, user: User) -> List[PermissionScope]:
        """Get all permissions for a user (from roles + direct permissions)"""
        permissions = set(user.permissions)
        
        for role_id in user.role_ids:
            role = self.roles.get(role_id)
            if role:
                permissions.update(role.permissions)
        
        return list(permissions)
    
    def check_permission(self, user: User, required_scope: PermissionScope) -> bool:
        """Check if user has required permission"""
        user_permissions = self.get_user_permissions(user)
        
        if PermissionScope.ADMIN_FULL in user_permissions:
            return True
        
        return required_scope in user_permissions
    
    def check_any_permission(self, user: User, required_scopes: List[PermissionScope]) -> bool:
        """Check if user has ANY of the required permissions"""
        user_permissions = self.get_user_permissions(user)
        
        if PermissionScope.ADMIN_FULL in user_permissions:
            return True
        
        return any(scope in user_permissions for scope in required_scopes)
    
    def check_all_permissions(self, user: User, required_scopes: List[PermissionScope]) -> bool:
        """Check if user has ALL required permissions"""
        user_permissions = self.get_user_permissions(user)
        
        if PermissionScope.ADMIN_FULL in user_permissions:
            return True
        
        return all(scope in user_permissions for scope in required_scopes)
