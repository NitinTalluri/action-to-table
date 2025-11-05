import logging
import time
from functools import lru_cache
from typing import TYPE_CHECKING, Annotated, Any, Iterable, Literal

import httpx
import prefect
from fastapi import Depends

from . import GetSessionDep, GetSettingsDep, S3ClientDep  # noqa

logger = logging.getLogger("api")

if TYPE_CHECKING:
    from api.v2.models import DeploymentItem
    from api.v2.services import PrefectFlowService, PrefectV3FlowService


async def get_prefect_client(
    settings: GetSettingsDep,
):
    auth_token = settings.prefect_settings.auth_token
    if not auth_token:
        raise ValueError(
            "Prefect Auth Token is required - Check PREFECT_AUTH_TOKEN ENV Variable"
        )
    with prefect.context(
        {
            "config": {
                "cloud": {"request_timeout": settings.prefect_settings.request_timeout}
            }
        }
    ):
        yield prefect.Client(api_token=auth_token)


class RetryingHttpxClient(httpx.Client):
    """
    Injects retries
    """

    def __init__(
        self,
        retry_count: int,
        retry_codes: Iterable[int],
        backoff_factor: float,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._retry_count = max(0, retry_count)
        self._retry_codes = frozenset(retry_codes)
        self._backoff_factor = backoff_factor

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._request_with_retry("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._request_with_retry("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._request_with_retry("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._request_with_retry("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._request_with_retry("DELETE", url, **kwargs)

    def head(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._request_with_retry("HEAD", url, **kwargs)

    def options(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._request_with_retry("OPTIONS", url, **kwargs)

    def _request_with_retry(
        self,
        method: Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make an HTTP request and retry when the response status code
        is in self._retry_codes. Retries are **not** attempted for network
        exceptions -- bubble those up so the caller can decide.
        """
        attempt: int = 0
        while True:
            response: httpx.Response = super().request(method, url, **kwargs)
            if response.status_code not in self._retry_codes:
                return response

            attempt += 1
            logger.warning(
                "Retrying %s request to %s (attempt %d/%d) due to status code %d",
            )
            if attempt > self._retry_count:
                logger.error(
                    "Exceeded maximum retry attempts (%d) for %s request to %s",
                    self._retry_count,
                    method,
                    url,
                )
                return response

            # Optional exponential back-off
            if self._backoff_factor:
                sleep_for = self._backoff_factor * (2 ** (attempt - 1))
                time.sleep(sleep_for)


def get_prefect_v3_client(
    settings: GetSettingsDep,
) -> httpx.Client:
    """
    https://github.com/PrefectHQ/prefect/blob/main/src/prefect/client/orchestration.py#L248
    https://github.com/PrefectHQ/prefect/blob/e825a0f1e8789e69fc3a2578c4101cc12f04fa9e/src/prefect/client/base.py#L354-L358
    """

    api_key = settings.prefect_v3_settings.api_key
    return RetryingHttpxClient(
        retry_count=3,
        retry_codes=(429, 503, 502, 408),
        backoff_factor=0.5,
        headers={
            "Authorization": f"Bearer {api_key}",
            "X-PREFECT-API-VERSION": settings.prefect_v3_settings.api_version,
        },
        timeout=httpx.Timeout(connect=60, read=60, write=60, pool=60),
        follow_redirects=True,
        limits=httpx.Limits(
            max_connections=16,
            max_keepalive_connections=8,
            keepalive_expiry=25,
        ),
        base_url=settings.prefect_v3_settings.api_url,
    )


@lru_cache(maxsize=1)
def _get_prefect_v3_deployments(
    client: httpx.Client, env: str, account_id: str, workspace_id: str
):
    """
    Cached function to get all deployments from Prefect V3 filtering by the 'env' tag

    Note: client should have base_url set with domain
    e.g. https://api.prefect.cloud
    /api/accounts/{account_id}/workspaces/{workspace_id}/
    """
    from api.v2.models import DeploymentItem, safe_parse_collection

    data = {
        "deployments": {
            "operator": "and_",
            "tags": {"operator": "and_", "all_": [str(env)]},
        }
    }

    api_url = f"/api/accounts/{account_id}/workspaces/{workspace_id}"
    endpoint = "/deployments/filter"
    url = f"{api_url}{endpoint}"
    resp = client.post(url, json=data)
    resp.raise_for_status()

    return safe_parse_collection(list[DeploymentItem], resp.json())


PrefectClientDep = Annotated[prefect.Client, Depends(get_prefect_client)]
PrefectV3ClientDep = Annotated[httpx.Client, Depends(get_prefect_v3_client)]


def get_prefect_flow_service(
    prefect_client: PrefectClientDep,
    s3_client: S3ClientDep,
    settings: GetSettingsDep,
    session: GetSessionDep,
):
    from api.v2.services import PrefectFlowService

    yield PrefectFlowService(prefect_client, s3_client, settings, session)


def get_prefect_v3_deployments(
    client: PrefectV3ClientDep,
    settings: GetSettingsDep,
) -> list["DeploymentItem"]:
    return _get_prefect_v3_deployments(
        client,
        settings.env,
        settings.prefect_v3_settings.account_id,
        settings.prefect_v3_settings.workspace_id,
    )


PrefectV3DeploymentDeps = Annotated[
    list["DeploymentItem"], Depends(get_prefect_v3_deployments)
]


def get_prefect_v3_flow_service(
    prefect_v3_client: PrefectV3ClientDep,
    s3_client: S3ClientDep,
    settings: GetSettingsDep,
    session: GetSessionDep,
    deployments: PrefectV3DeploymentDeps,
):
    from api.v2.services import PrefectV3FlowService

    yield PrefectV3FlowService(
        prefect_v3_client, s3_client, settings, session, deployments
    )


FlowServiceDep = Annotated["PrefectFlowService", Depends(get_prefect_flow_service)]
FlowV3ServiceDep = Annotated[
    "PrefectV3FlowService", Depends(get_prefect_v3_flow_service)
]

__all__ = [
    "FlowServiceDep",
    "FlowV3ServiceDep",
    "PrefectClientDep",
    "PrefectV3ClientDep",
]
