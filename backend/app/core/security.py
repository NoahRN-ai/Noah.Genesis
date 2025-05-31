import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth, credentials
from pydantic import BaseModel

from .config import settings

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
_firebase_app_initialized = False

def initialize_firebase_admin():
    global _firebase_app_initialized
    if not _firebase_app_initialized:
        try:
            # Option 1: Use a service account JSON file (path from settings)
            if settings.FIREBASE_SERVICE_ACCOUNT_JSON_PATH:
                cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_JSON_PATH)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized with service account JSON.")
            # Option 2: Rely on GOOGLE_APPLICATION_CREDENTIALS or default credentials in GCP environment
            else:
                # This will use ADC if GOOGLE_APPLICATION_CREDENTIALS is not set,
                # or the explicit SA file if GOOGLE_APPLICATION_CREDENTIALS is set.
                # On Cloud Run with appropriate SA, this should "just work".
                firebase_admin.initialize_app()
                logger.info("Firebase Admin SDK initialized using application default credentials or environment.")
            _firebase_app_initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}", exc_info=True)
            # Depending on strictness, might want to raise an error to prevent app startup
            # For now, log and subsequent auth calls will fail.


# Call initialization when this module is loaded (FastAPI app startup can also manage this)
# initialize_firebase_admin() # Better to call this explicitly in main.py lifespan event

class UserInfo(BaseModel):
    user_id: str # Firebase UID
    email: Optional[str] = None
    email_verified: bool = False
    # You can add custom claims or roles here if you set them in Firebase

http_bearer = HTTPBearer(auto_error=True) # auto_error will raise HTTPException for missing token

async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(http_bearer)
) -> UserInfo:
    """
    Dependency to verify Firebase ID token and return user information.
    """
    if not _firebase_app_initialized:
        # This error occurs if initialize_firebase_admin() hasn't been called or failed.
        # This helps to catch it early in the request cycle rather than only logging at startup.
        logger.error("Firebase Admin SDK not initialized. Cannot authenticate user.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not available.",
        )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated (no bearer token)",
        )
    try:
        decoded_token = auth.verify_id_token(token.credentials)
        user_id = decoded_token.get("uid")
        if not user_id:
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: UID missing.",
            )
        return UserInfo(
            user_id=user_id,
            email=decoded_token.get("email"),
            email_verified=decoded_token.get("email_verified", False)
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ID token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.InvalidIdTokenError as e:
        logger.warning(f"Invalid ID token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid ID token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e: # Catch other Firebase admin errors
        logger.error(f"Error verifying Firebase ID token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not verify authentication credentials.",
        )

async def get_current_active_user(current_user: UserInfo = Depends(get_current_user)) -> UserInfo:
    """
    Placeholder for checking if user is active (e.g., not disabled).
    For MVP, just returns the current user.
    """
    # if not current_user.is_active: # Assuming an 'is_active' field or similar check
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
