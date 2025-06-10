from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from google_ads_mcp_server.utils.token_utils import hash_token
from google_ads_mcp_server.db.factory import get_database_manager

security = HTTPBearer()

db_manager = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """FastAPI dependency to authenticate a request using a bearer token."""
    global db_manager
    if db_manager is None:
        db_manager = get_database_manager()

    token = credentials.credentials
    token_hash = hash_token(token)

    token_data = await db_manager.get_token_data_by_hash(token_hash)
    if not token_data or token_data.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    await db_manager.update_token_last_used(token_data["token_id"])

    user_data = await db_manager.get_user_by_id(token_data["user_id"])
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user_data
