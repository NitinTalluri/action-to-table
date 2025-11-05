from functools import lru_cache
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends

if TYPE_CHECKING:
    from api.settings import AppSettings


@lru_cache(maxsize=1)
def _get_settings(**kwargs) -> "AppSettings":
    from api.settings import AppSettings

    return AppSettings(**kwargs)


def get_settings() -> "AppSettings":
    return _get_settings()


GetSettingsDep = Annotated["AppSettings", Depends(get_settings)]
