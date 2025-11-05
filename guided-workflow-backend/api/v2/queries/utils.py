import json
import logging
from datetime import datetime
from operator import attrgetter
from typing import TYPE_CHECKING, Iterable, Literal, Optional, Type, TypedDict, Union

from snowflake.sqlalchemy import MergeInto
from sqlalchemy import (
    Integer,
    String,
    and_,
    column,
    literal,
    literal_column,
    select,
    union_all,
    values,
)
from sqlalchemy.orm import InstrumentedAttribute

from api.v2.queries.parse_json_into_table import parse_json_into_table, using_source

if TYPE_CHECKING:
    from api.dependencies import UserRequest
    from api.v2.orm import V2MetadataBase

CatType = Literal["insert", "undelete", "delete"]
CatRelation = tuple[int, CatType]
TAccessor = Union[InstrumentedAttribute, int]

logger = logging.getLogger("api")


def categorize_set_relations(
    left: set[int], right: set[int], right_deleted: set[int]
) -> list[CatRelation]:
    """
    Given incoming set (left) and existing set (right) which is not deleted and existing set (right_deleted) which is deleted,

    Returns
    -------
    list[CatRelation]:
        A list of tuples of form (int, CatType) where CatType is a Literal type of 'insert', 'undelete', 'delete'
    """

    inserts = left - (right | right_deleted)
    undeletes = left & right_deleted
    deletes = right - left

    return [
        *((i, "insert") for i in inserts),
        *((u, "undelete") for u in undeletes),
        *((d, "delete") for d in deletes),
    ]


class QueryMembership:
    """
    This constructs a query that given a list of ids and a model, returns ids that are not tracked in the database.
    This is mostly useful for Snowflake as it does not enforce foreign key constraints. The query can be chained so that multiple models can be checked for membership.

    If a model a member_id refers to a non-existent row, it will be returned in the query like:



    | ID | TYPE          |
    |----|---------------|
    | 1  | ORMModelName  |


    """

    def __init__(self):
        self._memberships = []

    def add_orm_membership(
        self,
        model: "Type[V2MetadataBase]",
        member_ids: Iterable[int],
        model_id_accessor: Optional[TAccessor] = None,
    ):
        """
        Add a membership to the query

        Parameters
        ----------
        model
        member_ids
        model_id_accessor : Optional[InstrumentedAttribute]
            If provided the query will check for membership using this column. Otherwise, it will use the primary key.

        Returns
        -------
        """
        if model_id_accessor is None:
            pk_cols = model.__table__.primary_key.columns.values()
            if len(pk_cols) != 1:
                raise ValueError("Model does not have a single primary key")
            model_id_accessor = attrgetter(pk_cols[0].key)(model)

        self._memberships.append((model, model_id_accessor, member_ids))
        return self

    @property
    def empty(self):
        return not self._memberships

    def build(self):
        rows = [
            (id, model.__name__) for model, _, ids in self._memberships for id in ids
        ]

        source_values = values(
            column("id", Integer), column("type", String), name="source_values"
        ).data(rows)

        source_cte = (
            select(source_values.c.id.label("id"), source_values.c.type.label("type"))
            .select_from(source_values)
            .cte("sv")
        )

        model_queries = []
        for model, model_id_accessor, _ in self._memberships:
            id_query = select(model_id_accessor).where(
                model_id_accessor == source_cte.c.id
            )
            if hasattr(model, "is_deleted"):
                id_query = id_query.where(model.is_deleted == "F")

            query = (
                select(source_cte.c.id, source_cte.c.type)
                .where(source_cte.c.type == model.__name__)
                .where(source_cte.c.id.notin_(id_query))
            )
            model_queries.append(query)

        return union_all(*model_queries)


class MergeTargetRelations:
    def __init__(
        self,
        target: Type["V2MetadataBase"],
        target_id_col: TAccessor,
        secondary: Type["V2MetadataBase"],
        secondary_target_col: TAccessor,
        secondary_rel_col: TAccessor,
        related: Type["V2MetadataBase"],
        related_id_col: TAccessor,
    ):
        self.target = target
        self.target_id_col = target_id_col
        self.secondary = secondary
        self.secondary_target_col = secondary_target_col
        self.secondary_rel_col = secondary_rel_col
        self.related = related
        self.related_id_col = related_id_col

    def build_existing_query(self, target_id: int):
        """Query for existing relationships and their current is_deleted status"""
        return select(self.related_id_col, self.secondary.is_deleted).join(
            self.secondary,
            and_(
                self.related_id_col == self.secondary_rel_col,
                self.secondary_target_col == target_id,
            ),
        )

    def build_virtual_source(
        self, target_id: int, proposed: list[int], existing: list[tuple[int, str]]
    ):
        """
        Build a virtual source table for the merge operation using ``parse_json``

        Parameters
        ----------
        target_id : The target id
        proposed : The proposed ids
        existing : list of tuples of form (int, str) where str is either 'T' or 'F' for is_deleted

        Returns
        -------

        """

        # Categorize the proposed and existing ids
        actions = categorize_set_relations(
            set(proposed),
            {id for id, is_deleted in existing if is_deleted == "F"},
            {id for id, is_deleted in existing if is_deleted == "T"},
        )

        # Build the source_values with JSON

        target_key = self.target_id_col.key
        secondary_key = self.secondary_rel_col.key

        source_values = []
        for row_id, action in actions:
            match (row_id, action):
                case (row_id, "insert" | "undelete"):
                    source_values.append(
                        {
                            target_key: target_id,
                            secondary_key: row_id,
                            "is_deleted": "F",
                        }
                    )
                case (row_id, "delete"):
                    source_values.append(
                        {
                            target_key: target_id,
                            secondary_key: row_id,
                            "is_deleted": "T",
                        }
                    )
                case _:
                    raise ValueError(f"Invalid action {action}")

        fn = parse_json_into_table(json.dumps(source_values, separators=(",", ":")))

        source_virtual = (
            select(
                literal_column(f"value:{target_key}::INTEGER").label(target_key),
                literal_column(f"value:{secondary_key}::INTEGER").label(secondary_key),
                literal_column("value:is_deleted::VARCHAR").label("is_deleted"),
            )
            .select_from(fn)
            .cte("source_virtual")
        )

        return source_virtual

    def build_merge_query(self, target_id: int, virtual_source, user: str):
        dt_now = datetime.now()
        user_lit = literal(user)
        dt_lit = literal(dt_now)
        false_lit = literal("F")
        true_lit = literal("T")

        target_key = self.target_id_col.key
        rel_key = self.related_id_col.key
        virtual_target_col = getattr(virtual_source.c, target_key)
        virtual_rel_col = getattr(virtual_source.c, rel_key)

        insert_values = {
            target_key: virtual_target_col,
            rel_key: virtual_rel_col,
            "create_dtm": dt_lit,
            "created_by": user_lit,
            "is_deleted": virtual_source.c.is_deleted,
        }

        merge_statement = MergeInto(
            target=self.secondary.__table__,
            source=using_source(virtual_source),
            on=and_(
                self.secondary_target_col == virtual_target_col,
                self.secondary_rel_col == virtual_rel_col,
            ),
        )

        merge_statement.when_matched_then_update().where(
            and_(self.secondary.is_deleted == "T", virtual_source.c.is_deleted == "F")
        ).values(is_deleted=false_lit, update_dtm=dt_lit, updated_by=user_lit)
        merge_statement.when_matched_then_update().where(
            and_(self.secondary.is_deleted == "F", virtual_source.c.is_deleted == "T")
        ).values(is_deleted=true_lit, update_dtm=dt_lit, updated_by=user_lit)
        merge_statement.when_not_matched_then_insert().values(**insert_values)

        return merge_statement


class KeyedVirtual(TypedDict):
    key: str
    data_type: str
    label: Optional[str]


def build_virtual_source(data: list[dict], data_keys: list[KeyedVirtual]):
    """
    Build a virtual source table for the mergeinto operation
    Parameters
    ----------
    data
    data_keys

    Returns
    -------

    """

    fn = parse_json_into_table(json.dumps(data, separators=(",", ":")))

    def _make_literal_column(entry: KeyedVirtual):
        return literal_column(f"value:{entry['key']}::{entry['data_type']}").label(
            entry["label"] or entry["key"]
        )

    source_virtual = (
        select(*[_make_literal_column(entry) for entry in data_keys])
        .select_from(fn)
        .cte("source_virtual")
    )

    return source_virtual


def GET_logged_user(req: "UserRequest", logged_user: Optional[str]) -> str:
    """
    Check if a user is admin, and if so, return the logged_user, otherwise return the logged in user
    Parameters
    ----------
    req : UserRequest
    logged_user : Optional[str]

    Returns
    -------
    """
    if req.user.is_admin and logged_user:
        return logged_user
    elif not req.user.is_admin and logged_user:
        logger.warning(
            "User %s is not admin, but passed logged_user=%s",
            req.user.username,
            logged_user,
        )
        return req.user.username
    else:
        return req.user.username
