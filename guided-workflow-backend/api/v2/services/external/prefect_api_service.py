from datetime import datetime
from enum import Enum
from functools import wraps
from typing import TYPE_CHECKING, Any, Literal, Optional, Union

from dateutil.relativedelta import relativedelta
from prefect.utilities.graphql import EnumValue, parse_graphql, with_args
from pydantic.v1 import BaseModel as PydanticBaseModel
from pydantic.v1 import parse_obj_as

from api.v2.services import ServiceException

if TYPE_CHECKING:
    from prefect import Client as PrefectClient

    from api.settings import AppSettings


class MessageType(str, Enum):
    flow_run = "flow_run"
    text = "text"

    def __str__(self) -> str:
        return str.__str__(self)


class MessageModel(PydanticBaseModel):
    message: str
    id: Union[str, int]
    message_type: Literal["text"] = MessageType.text


class PrefectBaseModel(PydanticBaseModel):
    class Config:
        use_enum_values = True
        allow_population_by_field_name = False


class FlowParameters(PrefectBaseModel):
    name: str
    slug: str
    default: Optional[Any]
    required: bool


class FlowStorage(PrefectBaseModel):
    path: Optional[str]
    type: Optional[str]
    image_tag: Optional[str]
    image_name: Optional[str]
    registry_url: Optional[str]
    prefect_version: Optional[str]
    stored_as_script: Optional[bool]


class FlowRunConfig(PrefectBaseModel):
    env: Optional[str]
    type: Optional[str]
    image: Optional[str]
    labels: list[str]


class FlowModel(PrefectBaseModel):
    id: str
    name: str
    flow_group_id: str
    version_group_id: str
    parameters: list[FlowParameters]
    storage: FlowStorage
    updated: Optional[datetime]
    url: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        self.url = f"https://cloud.prefect.io/cisco-dev/flow/{self.flow_group_id}"


class FlowRunModel(PrefectBaseModel):
    id: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    state: str


class FlowRunLog(PrefectBaseModel):
    id: str
    message: str
    timestamp: datetime


class FlowRunParametersModel(PrefectBaseModel):
    id: str
    parameters: dict
    state: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    logs: list[FlowRunLog]
    message_type: Literal["flow_run"] = MessageType.flow_run


def wrap_json_messages(generator_method):
    """If a string is yielded wrap it in a json message, otherwise pass it through."""

    @wraps(generator_method)
    def wrapped(*args, **kwargs):
        message_stream = generator_method(*args, **kwargs)
        for i, message in enumerate(message_stream, start=1):
            match message:
                case str():
                    yield MessageModel(message=message, id=i)
                case ServiceException():
                    yield MessageModel(message=f"{message.code} - {message.msg}", id=i)
                case _:
                    yield message

    return wrapped


def handle_query_exceptions(generator_method):
    @wraps(generator_method)
    def wrapped(*args, **kwargs):
        try:
            yield from generator_method(*args, **kwargs)
        except ServiceException as e:
            yield str(e)
            return

    return wrapped


class PrefectApiService:
    """
    This class is provides methods for interacting with the Prefect API.
    For scheduling and creating flows, see the `PrefectFlowService` class.
    """

    def __init__(self, client: "PrefectClient", settings: "AppSettings"):
        self.client = client
        self.settings = settings

    def list_flows(self) -> list[FlowModel]:
        query = parse_graphql(
            {
                "query": {
                    with_args("flow", "distinct_on: version_group_id"): {
                        "id",
                        "name",
                        "flow_group_id",
                        "version_group_id",
                        "run_config",
                        "parameters",
                        "storage",
                        "updated",
                    }
                }
            }
        )

        result = self.client.graphql(query).to_dict()
        return parse_obj_as(list[FlowModel], result["data"]["flow"])

    def search_flows_by_name(self, name: str) -> list[FlowModel]:
        query = parse_graphql(
            {
                "query": {
                    with_args("flow", {"where": {"name": {"_ilike": f"%{name}%"}}}): {
                        "id",
                        "name",
                        "flow_group_id",
                        "version_group_id",
                        "run_config",
                        "parameters",
                        "storage",
                        "updated",
                    }
                }
            }
        )

        result = self.client.graphql(query).to_dict()
        return parse_obj_as(list[FlowModel], result["data"]["flow"])

    def get_flow_runs(self, version_group_id: str, last_n_days: int = 3) -> list:
        offset_timestamp = (
            datetime.now() - relativedelta(days=last_n_days)
        ).isoformat()

        args = with_args(
            "flow_run",
            {
                "where": {
                    "_and": {
                        "flow": {
                            "version_group_id": {"_eq": version_group_id},
                        },
                        "start_time": {"_gte": offset_timestamp},
                    }
                }
            },
        )

        query = parse_graphql(
            {
                "query": {
                    args: {
                        "id": True,
                        "start_time": True,
                        "end_time": True,
                        "state": True,
                    }
                }
            }
        )

        result = self.client.graphql(query).to_dict()
        return parse_obj_as(list[FlowRunModel], result["data"]["flow_run"])

    def get_flow_run_logs(self, flow_run_id: str):
        parse_graphql(
            {
                "query": {
                    with_args("flow_run_by_pk", {"id": flow_run_id}): {
                        "id": True,
                        "state": True,
                        with_args(
                            "logs",
                            with_args("order_by", {"timestamp": EnumValue("asc")}),
                        ): {
                            "id": True,
                            "timestamp": True,
                            "message": True,
                            "name": True,
                        },
                    }
                }
            }
        )

    def search_in_parameters(self, having_key: str, last_n_days: int = 3):
        """
        Parameters
        ----------
        having_key : str
            Search for flows run with these parameters
                {"_has_key": having_key}
        last_n_days : int
            Search for flows run in the last n days

        Returns
        -------

        """

        offset_timestamp = (
            datetime.now() - relativedelta(days=last_n_days)
        ).isoformat()

        args = with_args(
            "flow_run",
            {
                "where": {
                    "_and": [
                        {"start_time": {"_gte": offset_timestamp}},
                        {"parameters": {"_has_key": having_key}},
                    ]
                }
            },
        )

        query = parse_graphql(
            {
                "query": {
                    args: {
                        "id": True,
                        "start_time": True,
                        "end_time": True,
                        "parameters": True,
                        "state": True,
                        "logs": {"id": True, "message": True, "timestamp": True},
                    }
                }
            }
        )

        result = self.client.graphql(query).to_dict()["data"]["flow_run"]
        return parse_obj_as(list[FlowRunParametersModel], result)
