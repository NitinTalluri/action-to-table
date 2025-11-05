from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.elements import BindParameter
from sqlalchemy.sql.functions import FunctionElement


# noinspection PyPep8Naming
class lateral_flatten(FunctionElement):
    name = "lateral_flatten"

    def __init__(self, column, *args, **kwargs):
        self.column = column
        self.parse_json = kwargs.pop("parse_json", False)
        super().__init__(column, *args, **kwargs)


@compiles(lateral_flatten)
def compile_lateral_flatten(element: lateral_flatten, compiler, **kwargs):
    if element.parse_json:
        return "LATERAL FLATTEN( input => parse_json({}))".format(
            compiler.process(element.column)
        )
    else:
        return "LATERAL FLATTEN( input => {})".format(compiler.process(element.column))


# noinspection PyPep8Naming
class parse_json_into_table(FunctionElement):
    name = "parse_json_into_table"

    def __init__(self, json, *clauses, **kwargs):
        super().__init__(json, *clauses, **kwargs)


@compiles(parse_json_into_table)
def compile_parse_json_into_table(element: parse_json_into_table, compiler, **kwargs):
    json_data = element.clauses.clauses[0]

    match json_data:
        case BindParameter() as param:
            json_data = param.value
        case str():
            ...
        case _:
            raise ValueError(f"Unsupported type: {type(json_data)}")

    processed = "LATERAL FLATTEN( input => parse_json('{}'))".format(json_data)
    return processed


from sqlalchemy.sql.selectable import Subquery


class MergeSourceProxy:
    """
    A proxy object that wraps a CTE or subquery for use as a source in MergeInto statements.
    This addresses the issue where snowflake-sqlalchemy MergeInto compilation doesn't properly
    handle CTEs as sources.

    The proxy delegates _compiler_dispatch calls to the wrapped source but ensures proper
    formatting for MergeInto USING clauses.
    """

    def __init__(self, source):
        self.source = source
        # Expose the columns attribute so the MergeInto can access source.c.column_name
        self.c = source.c

    def _compiler_dispatch(self, compiler, asfrom=False, **kwargs):
        """
        Handle compiler dispatch by wrapping the source compilation in parentheses with alias.
        This is what snowflake-sqlalchemy MergeInto expects for the USING clause.
        """
        if asfrom:
            # When called with asfrom=True (as MergeInto does), wrap in parentheses with alias
            source_sql = compiler.process(self.source, **kwargs)
            return f"({source_sql}) AS {self.source.description}"
        else:
            # For other cases, delegate to the original source
            return self.source._compiler_dispatch(compiler, asfrom=asfrom, **kwargs)

    def __getattr__(self, name):
        """Delegate any other attribute access to the wrapped source"""
        return getattr(self.source, name)


def using_source(source):
    """
    When using the result of `parse_json_into_table` as a source, in a snowflake-sqlalchemy `MergeInto`
    statement, this wraps the subquery in a way that snowflake-sqlalchemy can understand.

    This function was removed in commit ad8ae9b but needs to be restored because snowflake-sqlalchemy
    MergeInto compilation doesn't properly handle CTEs as sources without this wrapper.

    Returns a MergeSourceProxy that properly handles _compiler_dispatch calls.
    """
    return MergeSourceProxy(source)
