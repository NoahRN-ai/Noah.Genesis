# Makes 'core' a Python package
from .config import settings
from .security import UserInfo, get_current_active_user

__all__ = ["settings", "get_current_active_user", "UserInfo"]
