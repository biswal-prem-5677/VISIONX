"""
VisionX — Role-Based Access Control (RBAC)
=============================================
Defines user roles and permissions for access control.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from loguru import logger
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """System roles."""
    VIEWER = "viewer"       # Can only view live feeds
    USER = "user"           # Standard user
    MANAGER = "manager"     # Can manage devices, rules
    ADMIN = "admin"         # Full admin access
    SUPER_ADMIN = "super_admin"  # God mode


class Permission(str, Enum):
    """System permissions."""
    VIEW_FEED = "view_feed"
    MANAGE_DEVICES = "manage_devices"
    MANAGE_RULES = "manage_rules"
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_DATA = "export_data"
    MANAGE_USERS = "manage_users"
    MANAGE_BILLING = "manage_billing"
    ADMIN_DASHBOARD = "admin_dashboard"
    ADMIN_TAKEOVER = "admin_takeover"
    SYSTEM_CONFIG = "system_config"


# Role → Permissions mapping
ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.VIEWER: {
        Permission.VIEW_FEED,
    },
    UserRole.USER: {
        Permission.VIEW_FEED,
        Permission.VIEW_ANALYTICS,
        Permission.MANAGE_RULES,
    },
    UserRole.MANAGER: {
        Permission.VIEW_FEED,
        Permission.VIEW_ANALYTICS,
        Permission.MANAGE_RULES,
        Permission.MANAGE_DEVICES,
        Permission.EXPORT_DATA,
    },
    UserRole.ADMIN: {
        Permission.VIEW_FEED,
        Permission.VIEW_ANALYTICS,
        Permission.MANAGE_RULES,
        Permission.MANAGE_DEVICES,
        Permission.EXPORT_DATA,
        Permission.MANAGE_USERS,
        Permission.MANAGE_BILLING,
        Permission.ADMIN_DASHBOARD,
    },
    UserRole.SUPER_ADMIN: set(Permission),  # All permissions
}


class RBACChecker:
    """
    Role-Based Access Control checker.

    Verifies if a user role has the required permission.
    """

    @staticmethod
    def has_permission(role: str, permission: Permission) -> bool:
        """Check if a role has a specific permission."""
        try:
            user_role = UserRole(role)
        except ValueError:
            return False

        perms = ROLE_PERMISSIONS.get(user_role, set())
        return permission in perms

    @staticmethod
    def get_permissions(role: str) -> set[Permission]:
        """Get all permissions for a role."""
        try:
            user_role = UserRole(role)
        except ValueError:
            return set()

        return ROLE_PERMISSIONS.get(user_role, set())

    @staticmethod
    def require_permission(role: str, permission: Permission) -> None:
        """Raise error if role lacks permission."""
        if not RBACChecker.has_permission(role, permission):
            raise PermissionError(
                f"Role '{role}' lacks permission: {permission.value}"
            )
