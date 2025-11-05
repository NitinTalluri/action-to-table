"""
Import order of modules is critical here.
Standalone dependencies should be imported first, followed by dependencies that depend on them.
"""

from .settings import get_settings, GetSettingsDep

# Database needs GetSettingsDep
from .database import GetSessionDep, get_session

# AWS needs GetSettingsDep
from .aws import (
    S3ClientDep,
    PresignedDocsDep,
    IdpClientDep,
    S3DocumentationPresigner,
    S3PresignerDep,
    GroupGetterDep,
)

# Security needs GetSettingsDep
from .security import (
    decode_bearer as login_required,
    require_admin,
    UserRequest,
    DataCanvasUser,
    JWTToken,
    require_financial_admin,
    is_sme_or_admin,
    is_support,
    is_manager,
    is_manager_or_pool_manager,
    is_pool_manager,
)

# Queries needs GetSessionDep, UserRequest
# ORM Models are imported locally
# Query functions are imported locally
from .queries import (
    GetUserDep,
    ActionItemsDep,
    AuthorizedEngagementBody,
    AuthorizedEngagementPath,
    fetch_engagement_links,
    ManagerBookingsServiceTypesDep,
    CurrentDateParamDep,
    DateRangeParamDep,
)

# Prefect needs GetSettingsDep, S3ClientDep, GetSessionDep
from .prefect import (
    PrefectClientDep,
    FlowServiceDep,
    PrefectV3ClientDep,
    PrefectV3DeploymentDeps,
    FlowV3ServiceDep,
)
