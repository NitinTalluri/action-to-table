import logging
from typing import Annotated, Callable

import cognitojwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic.v1 import ValidationError
from starlette import status
from starlette.authentication import AuthCredentials
from starlette.status import HTTP_401_UNAUTHORIZED

from .. import GetSettingsDep  # noqa: TC001
from . import DataCanvasUser, JWTToken

logger = logging.getLogger("api")
http_bearer_security = HTTPBearer()
GetTokenDep = Annotated[HTTPAuthorizationCredentials, Depends(http_bearer_security)]


async def decode_bearer(
    request: Request,
    token: GetTokenDep,
    settings: GetSettingsDep,
) -> DataCanvasUser:
    """
    Dependency to verify the bearer token is valid with cognito.

    At the router level, this can be used to ensure that the user is authenticated, but will not return the user's
    information as part of the parameters in a route. Instead, the user will be attached to the request.user scope

    Parameters
    ----------
    request
    token: str - Depends(get_authorization_header)
    settings : Settings - Depends(get_settings)

    Returns
    -------
    CognitoResponse
    """
    from api.settings import Environment

    try:
        verified_claims: dict = await cognitojwt.decode_async(
            token=token.credentials,
            region=settings.aws_region,
            userpool_id=settings.user_pool_id,
            app_client_id=settings.app_client_id,
            testmode=settings.env != Environment.test,
        )
        try:
            parsed_token = JWTToken.parse_obj(verified_claims).__root__
        except ValidationError as e:
            logger.error(e)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED) from e
        user = DataCanvasUser(
            username=parsed_token.username,
            email=parsed_token.email,
            scopes=set(parsed_token.groups) if parsed_token.groups else set(),
        )

        cred = AuthCredentials(scopes=parsed_token.groups)

        request.scope["user"] = user
        request.scope["auth"] = cred
        return user
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED) from e


AuthenticatedUserDep = Annotated[DataCanvasUser, Depends(decode_bearer)]


async def require_admin(user: AuthenticatedUserDep) -> DataCanvasUser:
    """
    Dependency to verify the bearer token is valid with cognito and that the user is an admin

    At the router level, this can be used to ensure that the user is authenticated, but will not return the user's
    information as part of the parameters in a route. Instead, the user will be attached to the request.user scope

    Parameters
    ----------
    user: DataCanvasUser - Depends(decode_bearer)
        A user that has been authenticated by cognito that may or may not be an admin

    Returns
    -------
    AdminDataCanvasUser
        Simple check to ensure that the user is an admin

    Raises
    ------
    HTTP_403_FORBIDDEN
        If the user is not an admin
    """
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return user


async def require_financial_admin(user: AuthenticatedUserDep) -> DataCanvasUser:
    if not user.is_financial_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return user


class PermissionChecker:
    """
    Dynamic permission checker for FastAPI dependency injection

    Examples
    -----
    # Require a user to be a sme or admin

    ```python
    is_sme_or_admin_ = lambda user: user.is_sme or user.is_admin
    is_sme_or_admin = PermissionChecker(is_sme_or_admin_)

    SmeOrAdminRequiredDep = Annotated[AuthenticatedUserDep, Depends(is_sme_or_admin)]
    """

    def __init__(self, attribute_check: Callable[[DataCanvasUser], bool]):
        self.attribute_check = attribute_check

    def __call__(self, user: AuthenticatedUserDep):
        if not self.attribute_check(user):
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="User does not have permission to access this resource",
            )
        return user


is_sme_or_admin = PermissionChecker(lambda user: user.is_sme)
is_manager = PermissionChecker(lambda user: user.is_manager)
is_support = PermissionChecker(lambda user: user.is_support)
is_pool_manager = PermissionChecker(lambda user: user.is_pool_manager)
is_manager_or_pool_manager = PermissionChecker(
    lambda user: user.is_manager or user.is_pool_manager
)

__all__ = [
    "decode_bearer",
    "is_manager",
    "is_manager_or_pool_manager",
    "is_pool_manager",
    "is_sme_or_admin",
    "is_support",
    "require_admin",
    "require_financial_admin",
]
