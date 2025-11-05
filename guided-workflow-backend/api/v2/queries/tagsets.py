import json
from collections import defaultdict
from typing import TypedDict

from sqlalchemy import (
    BindParameter,
    Connection,
    Integer,
    TextClause,
    TextualSelect,
    text,
)

from api.v2.orm.json_varchar import JSONVarchar


def query_engagement_tagsets(engagement_id: int):
    stmt = (
        text(
            """
        WITH tagsets_cte AS (SELECT ts.DC_ENGAGEMENT_ID,
                            ts.TAGSET_ID,
                            ts.TAGSET_NAME,
                            ts.TAGSET_DESC,
                            ts.scope,
                            ts.CARDINALITY,
                            ts.TAGSET_TYPE
                     FROM DC_TAGSET ts
                     WHERE ts.DC_ENGAGEMENT_ID = :engagement_id
                       AND ts.IS_DELETED = 'F'
                       )
        SELECT TO_JSON(
               OBJECT_CONSTRUCT_KEEP_NULL(
                       'dc_engagement_id', tagsets_cte.DC_ENGAGEMENT_ID,
                       'tagset_id', tagsets_cte.TAGSET_ID,
                       'scope', tagsets_cte.scope,
                       'cardinality', tagsets_cte.cardinality,
                       'tagset_type', tagsets_cte.tagset_type,
                       'tagset_name', tagsets_cte.TAGSET_NAME,
                       'tagset_desc', tagsets_cte.TAGSET_DESC,
                       'tags', ARRAY_AGG(
                       
                       IFF(t.TAG_ID IS NOT NULL, OBJECT_CONSTRUCT_KEEP_NULL
                                         (
                       'tag_id', t.TAG_ID,
                       'tag_name', t.TAG_NAME,
                       'tag_desc', t.TAG_DESC,
                       'tagset_id', t.tagset_id
                                         )
                               
                               , NULL)
                               )
                               
                               
               )) AS tagset_row 
        FROM tagsets_cte
            LEFT JOIN DC_TAGS t ON (tagsets_cte.TAGSET_ID = t.TAGSET_ID and t.IS_DELETED = 'F')
        GROUP BY tagsets_cte.DC_ENGAGEMENT_ID, tagsets_cte.TAGSET_ID, tagsets_cte.TAGSET_NAME, tagsets_cte.TAGSET_DESC,
            tagsets_cte.scope, tagsets_cte.CARDINALITY, tagsets_cte.TAGSET_TYPE
"""
        )
        .bindparams(engagement_id=engagement_id)
        .columns(
            tagset_row=JSONVarchar,
        )
    )
    return stmt


def query_global_tagsets():
    # TAGSET_NAME != 'Asset Manager' is a private tagset

    stmt = text(
        """
        with tagsets as (
                    select 
                    ts.TAGSET_ID,
                    ts.TAGSET_NAME,
                    ts.TAGSET_DESC,
                    ts.scope,
                    ts.CARDINALITY,
                    ts.TAGSET_TYPE
                    from DC_TAGSET ts  
                        where ts.scope = 'Global' and ts.IS_DELETED = 'F'  and ts.TAGSET_NAME != 'Asset Manager'
                )
                select TO_JSON(OBJECT_CONSTRUCT_KEEP_NULL(
                                             'dc_engagement_id',                     1,
                                             'tagset_id',                            c.TAGSET_ID,
                                             'scope',                                c.scope,
                                             'cardinality',                          c.cardinality,
                                             'tagset_type',                          c.tagset_type,
                                             'tagset_name',                          c.TAGSET_NAME,
                                             'tagset_desc',                          c.TAGSET_DESC,
                                             'tags', ARRAY_AGG(
                                             
                                             IFF(
                                                t.TAG_ID IS NOT NULL,
                                                OBJECT_CONSTRUCT_KEEP_NULL (
                                                'tag_id'                                  , t.TAG_ID,
                                                'tag_name'                              , t.TAG_NAME,
                                                'tag_desc'                              , t.TAG_DESC,
                                                'tagset_id'                             , t.tagset_id
                                           ) , NULL
                                           )
                                        )
                                   )) as tagset_row
                               from tagsets c
                               left join DC_TAGS t on (c.TAGSET_ID = t.TAGSET_ID and t.IS_DELETED = 'F')
                               group by c.TAGSET_ID, c.TAGSET_NAME, c.TAGSET_DESC,c.scope, c.CARDINALITY, c.TAGSET_TYPE
                               """
    ).columns(
        tagset_row=JSONVarchar,
    )

    return stmt


def query_engagement_tagsets_with_global(dc_engagement_id: int):
    """Assume user has been verified to have access to the engagement in upstream
    dependencies."""
    stmt = (
        text(
            """
        WITH tagsets_cte AS (SELECT ts.DC_ENGAGEMENT_ID,
                            ts.TAGSET_ID,
                            ts.TAGSET_NAME,
                            ts.TAGSET_DESC,
                            ts.scope,
                            ts.CARDINALITY,
                            ts.TAGSET_TYPE
                     FROM DC_TAGSET ts
                     WHERE
                        (
                        ts.DC_ENGAGEMENT_ID = :engagement_id
                        OR (
                            ts.DC_ENGAGEMENT_ID = 1
                            AND ts.TAGSET_NAME != 'Asset Manager'
                            )
                        )
                        AND ts.IS_DELETED = 'F'
                    )
            
        SELECT TO_JSON(
               OBJECT_CONSTRUCT_KEEP_NULL(
                       'dc_engagement_id', tagsets_cte.DC_ENGAGEMENT_ID,
                       'tagset_id', tagsets_cte.TAGSET_ID,
                       'scope', tagsets_cte.scope,
                       'cardinality', tagsets_cte.cardinality,
                       'tagset_type', tagsets_cte.tagset_type,
                       'tagset_name', tagsets_cte.TAGSET_NAME,
                       'tagset_desc', tagsets_cte.TAGSET_DESC,
                       'tags', ARRAY_AGG(
                       IFF(t.TAG_ID IS NOT NULL,
                       OBJECT_CONSTRUCT_KEEP_NULL (
                       'tag_id', t.TAG_ID,
                       'tag_name', t.TAG_NAME,
                       'tag_desc', t.TAG_DESC,
                       'tagset_id', t.tagset_id
                                         )
                                         , NULL
                                         )
                                         
                               )
               )) AS tagset_row 
        FROM tagsets_cte
            LEFT JOIN DC_TAGS t ON (tagsets_cte.TAGSET_ID = t.TAGSET_ID and t.IS_DELETED = 'F')
        GROUP BY tagsets_cte.DC_ENGAGEMENT_ID, tagsets_cte.TAGSET_ID, tagsets_cte.TAGSET_NAME, tagsets_cte.TAGSET_DESC,
            tagsets_cte.scope, tagsets_cte.CARDINALITY, tagsets_cte.TAGSET_TYPE
        """
        )
        .bindparams(engagement_id=dc_engagement_id)
        .columns(
            tagset_row=JSONVarchar,
        )
    )
    return stmt


def query_tagsets_from_tag_ids(tag_ids: list[int]) -> TextualSelect:
    """
    Query to get rows of form tagset_id, tag_id
    given a list of tag_ids.
    """

    stmt = (
        text(
            """
        SELECT t.TAGSET_ID, t.TAG_ID
        FROM DC_TAGS t
        WHERE t.TAG_ID IN :tag_ids
          AND t.IS_DELETED = 'F'
        """
        )
        .bindparams(BindParameter("tag_ids", tag_ids, expanding=True))
        .columns(tagset_id=Integer, tag_id=Integer)
    )

    return stmt


__all__ = [
    "query_engagement_tagsets",
    "query_engagement_tagsets_with_global",
    "query_global_tagsets",
    "query_tagsets_from_tag_ids",
]
