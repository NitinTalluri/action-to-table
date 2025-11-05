from enum import Enum
from typing import Literal, Union

from pydantic.v1 import BaseModel, Field, root_validator, validator
from starlette.authentication import SimpleUser
from starlette.requests import Request


class GroupScopes(str, Enum):
    dc_admin = "dc_admin"
    dc_financial_admin = "dc_financial_admin"
    dc_financial_admin_cxea = "dc_financial_admin_cxea"
    dc_financial_admin_revenue = "dc_financial_admin_revenue"
    dc_sme = "dc_sme"
    dc_manager = "dc_manager"
    dc_support = "dc_support"
    dc_pool_manager = "dc_pool_manager"

    def __str__(self) -> str:
        return str.__str__(self)


TGroupScopes = Literal[
    "dc_admin",
    "dc_financial_admin",
    "dc_financial_admin_cxea",
    "dc_financial_admin_revenue",
    "dc_sme",
    "dc_manager",
    "dc_support",
    "dc_pool_manager",
]


class DataCanvasUserBase(SimpleUser):
    scopes: set[TGroupScopes]

    def __init__(self, username, **kwargs):
        super().__init__(username)
        self.email = kwargs.get("email")
        # Our routes use username, but they mean email. This is a hack to make it work
        self.username = self.email
        self.scopes = set(kwargs.get("scopes", []))

    @property
    def is_admin(self) -> bool:
        return "dc_admin" in self.scopes

    @property
    def is_financial_admin(self) -> bool:
        return "dc_financial_admin" in self.scopes or self.is_admin

    @property
    def is_financial_admin_cxea(self) -> bool:
        return "dc_financial_admin_cxea" in self.scopes or self.is_financial_admin

    @property
    def is_financial_admin_revenue(self) -> bool:
        return "dc_financial_admin_revenue" in self.scopes or self.is_financial_admin

    @property
    def is_sme(self) -> bool:
        return "dc_sme" in self.scopes or self.is_admin

    @property
    def is_manager(self) -> bool:
        return "dc_manager" in self.scopes or self.is_admin

    @property
    def is_support(self) -> bool:
        return "dc_support" in self.scopes or self.is_admin

    @property
    def is_pool_manager(self) -> bool:
        return "dc_pool_manager" in self.scopes or self.is_admin


class DataCanvasUser(DataCanvasUserBase): ...


class AccessJWTToken(BaseModel):
    class Config:
        extra = "ignore"
        use_enum_values = True

    groups: list[str] = Field(alias="cognito:groups")
    username: str
    email: str
    token_use: Literal["access"]

    @root_validator(pre=True)
    def parse_email(cls, values):
        """
        Access tokens provide us with 'username' but this is actually email from duo
        """
        username_raw = values.get("username")
        if username_raw is None:
            raise ValueError("username is required")
        user_email = username_raw.removeprefix("duo_")
        username = user_email.split("@")[0]
        values["username"] = username
        values["email"] = user_email
        return values


class JWTIdToken(BaseModel):
    class Config:
        extra = "ignore"

    groups: list[str] = Field(..., alias="cognito:groups")
    username: str = Field(..., alias="cognito:username")
    email: str
    token_use: Literal["id"]

    @validator("email")
    def remove_email_prefix(cls, v):
        return v.removeprefix("duo_")

    @validator("username")
    def remove_username_prefix(cls, v):
        v = v.removeprefix("duo_")
        return v.split("@")[0]


class JWTToken(BaseModel):
    __root__: Union[AccessJWTToken, JWTIdToken] = Field(..., discriminator="token_use")


class UserRequest(Request):
    """
    This class adds no functionality, but is used to add type hints to the request object so that we can access
    request.user in our routes and have it be typed as a DataCanvasUser
    """

    user: DataCanvasUser


__all__ = [
    "AccessJWTToken",
    "DataCanvasUser",
    "GroupScopes",
    "JWTIdToken",
    "JWTToken",
    "TGroupScopes",
    "UserRequest",
]
