from enum import Enum
from typing import Optional, Union

from prefect.run_configs import DockerRun, KubernetesRun
from pydantic.v1 import BaseModel as PydanticBaseModel
from pydantic.v1 import Field


class BaseModel(PydanticBaseModel):
    class Config:
        use_enum_values = True
        allow_population_by_field_name = True


class PrefectRunConfigName(str, Enum):
    KubernetesRun = "KubernetesRun"
    DockerRun = "DockerRun"

    def __str__(self) -> str:
        return str.__str__(self)


class DockerRunConfigParams(BaseModel):
    image: Optional[str] = None
    env: Optional[dict] = None
    labels: Optional[list[str]] = None
    host_config: Optional[dict] = None


class RunConfigSetting(BaseModel):
    name: PrefectRunConfigName
    parameters: dict = Field(default_factory=dict)

    def to_object(self) -> Union[DockerRun, KubernetesRun]:
        match self.name:
            case "KubernetesRun":
                return KubernetesRun(**self.parameters)
            case "DockerRun":
                return DockerRun(**self.parameters)
            case _:
                raise ValueError(f"Invalid run config name: {self.name}")
