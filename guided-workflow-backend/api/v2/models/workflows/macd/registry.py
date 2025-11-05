import json
from typing import Annotated, TypeVar, cast, get_origin, overload

from pydantic import create_model
from pydantic.main import ModelMetaclass
from pydantic.schema import model_schema
from typing_extensions import get_args

from . import (
    AMRRToolAction,
    SchemaModelBase,
    ToolName,
    TRegistryExport,
)
from .base import (
    ACATToolAction,
    CCWRToolAction,
    DiscriminatedUnionModelSchema,
    ModelSchema,
    TRegistryKey,
    TToolActionLiteral,
    TToolNameLiteral,
    UnionModelSchema,
)

T = TypeVar("T", bound=SchemaModelBase)
Ann = TypeVar("Ann")


def is_annotation(model: object) -> bool:
    """
    Detect if the provided model is of the form
    Annotated[ModelA | ModelB, Field(discriminator="data_type")]
    """
    return get_origin(model) is Annotated


def build_shim_model(model_annotation, name: str | None) -> ModelMetaclass:
    """
    To go from Annotated[ModelA | ModelB, Field(discriminator="data_type")] or Annotated[ModelA | ModelB, Field()]
    we a Model we need to use __root__
    """
    # Access the args from the Annotated type
    # tuple of union type and FieldInfo
    target_model_grp, field_info = get_args(model_annotation)
    target_models = get_args(target_model_grp)

    module_name = target_models[0].__module__
    model_name = (
        f"ShimModel_{'_'.join(m.__name__ for m in target_models)}"
        if name is None
        else name
    )

    return create_model(
        model_name,
        __root__=(model_annotation, ...),
        __module__=module_name,
    )


tool2action = {
    ToolName.amrr: AMRRToolAction,
    ToolName.ccwr: CCWRToolAction,
    ToolName.acat: ACATToolAction,
}


class MACDSchemaRegistry:
    """
    A registry for MACD (Model Action Configuration Document) schemas.

    This registry maintains a mapping between tool names, their associated actions,
    and their corresponding Pydantic model schemas. It ensures that all registered
    models have the required fields and validates the tool names and actions.

    Tool names from [`ToolName`](api.v2.models.workflows.macd.base.ToolName) and their corresponding action enums:
    - `ToolName.amrr` -> [`AMRRToolAction`](api.v2.models.workflows.macd.base.AMRRToolAction)
    - `ToolName.ccwr` -> [`CCWRToolAction`](api.v2.models.workflows.macd.base.CCWRToolAction)
    - `ToolName.acat` -> [`ACATToolAction`](api.v2.models.workflows.macd.base.ACATToolAction)

    Example:
        ```python
        from pydantic import Field

        @register_schema
        class SomeSchema(SchemaModelBase):
            ...
        ```

    The registry validates that any registered schema's tool_name and tool_action
    fields contain valid values from these enums.

    The registry is used as a decorator to register schema models and provides
    methods to export the schemas as dictionaries or JSON.

    Discriminated Unions are supported, in which case the model's __root__ field must
    have the discriminator field defined in the model annotation and the model's must follow
    the above semantics regarding tool names and actions. The __root__ models must share a
    common tool_name and tool_action.
    """

    models: dict[TRegistryKey, type[SchemaModelBase] | type[ModelMetaclass]]
    models_schema_: TRegistryExport

    def __init__(self):
        """Initialize an empty registry for models and their schemas."""
        self.models = {}
        self.models_schema_ = []
        self._json_schema = None

    @overload
    def __call__(
        self,
        cls: type[T],
        /,
    ) -> type[T]: ...

    @overload
    def __call__(self, cls: Ann, /, name: str) -> Ann: ...

    def __call__(self, cls, /, name=None):
        """
        Register a schema model class with the registry.

        This method is used as a decorator and validates that:
        1. The class is a proper subclass of SchemaModelBase
        2. The class has required tool_name and tool_action fields
        3. The tool name and action are valid enum values

        Args:
            cls: The schema model class to register

        Returns:
            The registered class unchanged

        Raises:
            TypeError: If cls is not a class or not a subclass of SchemaModelBase
            ValueError: If required fields are missing or contain invalid values
        """

        # Route based on type of cls
        # if cls is a class type (decorator above the class definition), route to _register_model_cls
        # if cls is not a type (e.g., Annotated), route to _register_model_metaclass

        is_cls = isinstance(cls, type)
        if is_cls:
            return self._register_model_cls(cls)
        is_annotated = is_annotation(cls)
        if is_annotated:
            return self._register_model_metaclass(cls, name=name)
        msg = f"[{self.__class__.__name__}] Attempted to register an unsupported type: {cls}"
        raise TypeError(msg)

    def _register_model_metaclass(self, cls: Ann, /, name: str | None) -> Ann:
        # Here we need to build a shim model (just like FastAPI does) to get the schema
        try:
            shim_model = build_shim_model(cls, name=name)
        except Exception as e:
            msg = (
                f"[{self.__class__.__name__}] Failed to build shim model for {cls}: {e}"
            )
            raise ValueError(msg) from e

        # Need to use private apis to perform our own validation about tool_name and tool_action

        sub_fields = shim_model.__fields__["__root__"].sub_fields

        tool_name_defaults = {
            sm.type_.__fields__["tool_name"].default for sm in sub_fields
        }
        tool_name_defaults.discard(None)  # Ensure we don't have None as a default
        tool_action_defaults = {
            sm.type_.__fields__["tool_action"].default for sm in sub_fields
        }
        tool_action_defaults.discard(None)  # Ensure we don't have None as a default
        if len(tool_name_defaults) != 1 or len(tool_action_defaults) != 1:
            msg = f"[{self.__class__.__name__}] Union Model {shim_model.__name__} must have a single, default tool_name and tool_action value across all __root__ models"
            raise ValueError(msg)

        tool_name_value = tool_name_defaults.pop()
        tool_action_value = tool_action_defaults.pop()

        try:
            tool_name_enum = ToolName(tool_name_value)
        except ValueError as e:
            msg = f"[{self.__class__.__name__}] Invalid tool name in class {cls.__name__}: {tool_name_value}"
            raise ValueError(msg) from e

        tool_name_value_valid = cast("TToolNameLiteral", tool_name_enum.value)

        try:
            action_name_enum = tool2action[tool_name_enum](tool_action_value)
        except ValueError as e:
            msg = f"[{self.__class__.__name__}] Invalid action name in class {cls.__name__}: {tool_action_value}"
            raise ValueError(msg) from e

        tool_action_value_valid = cast("TToolActionLiteral", action_name_enum.value)

        self.models[(tool_name_value_valid, tool_action_value_valid)] = shim_model

        shim_schema = shim_model.schema(ref_template="{model}")
        if "discriminator" in shim_schema:
            self.models_schema_.append(
                DiscriminatedUnionModelSchema(
                    **shim_schema,
                )
            )
        else:
            self.models_schema_.append(
                UnionModelSchema(
                    **shim_schema,
                )
            )
        return cls

    def _register_model_cls(self, cls: type[T]) -> type[T]:
        if not isinstance(cls, type):
            msg = f"[{self.__class__.__name__}] Attempted to register a non-class object: {cls}"
            raise TypeError(msg)
        if not issubclass(cls, SchemaModelBase):
            msg = f"[{self.__class__.__name__}] Attempted to register a non-SchemaModelBase class: {cls}"
            raise TypeError(msg)

        tool_name = cls.__fields__.get("tool_name")
        tool_action = cls.__fields__.get("tool_action")
        if tool_name is None or tool_action is None:
            msg = f"[{self.__class__.__name__}] Class {cls.__name__} must have 'tool_name' and 'tool_action' fields"
            raise ValueError(msg)
        tool_name_value = tool_name.default
        tool_action_value = tool_action.default

        # Must not be None
        if tool_name_value is None or tool_action_value is None:
            msg = f"[{self.__class__.__name__}] Class {cls.__name__} must have 'tool_name' and 'tool_action' fields with default values"
            raise ValueError(msg)

        try:
            tool_name_enum = ToolName(tool_name_value)
        except ValueError as e:
            msg = f"[{self.__class__.__name__}] Invalid tool name in class {cls.__name__}: {tool_name_value}"
            raise ValueError(msg) from e

        tool_name_value_valid = cast("TToolNameLiteral", tool_name_enum.value)

        try:
            action_name_enum = tool2action[tool_name_enum](tool_action_value)
        except ValueError as e:
            msg = f"[{self.__class__.__name__}] Invalid action name in class {cls.__name__}: {tool_action_value}"
            raise ValueError(msg) from e

        tool_action_value_valid = cast("TToolActionLiteral", action_name_enum.value)

        self.models[(tool_name_value_valid, tool_action_value_valid)] = cls
        cls_schema = ModelSchema(**model_schema(cls))
        self.models_schema_.append(cls_schema)
        return cls

    def schemas(self) -> TRegistryExport:
        """
        Export the registered schemas as a list of JSON Schema dicts.

        Returns:
            A nested dictionary of tool names and actions mapping to their schemas
        """
        return self.models_schema_

    def json(self) -> str:
        """
        Export the registered schemas as a JSON string.

        Returns:
            A compact JSON string representation of all registered schemas
        """
        if self._json_schema is not None:
            return self._json_schema
        self._json_schema = json.dumps(self.schemas(), separators=(",", ":"))
        return self._json_schema


register_schema = MACDSchemaRegistry()
