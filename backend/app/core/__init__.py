# Makes 'core' a Python package
from .config import settings
from .security import get_current_active_user, UserInfo

__all__ = ["settings", "get_current_active_user", "UserInfo"]
