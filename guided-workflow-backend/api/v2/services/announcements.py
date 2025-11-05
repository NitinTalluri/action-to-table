import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic.v1 import parse_obj_as
from snowflake.sqlalchemy import MergeInto
from sqlalchemy import and_, func, insert, literal, literal_column, text, update
from sqlmodel import select
from toolz import groupby

from api.v2.models import (
    V2AnnouncementLinkRead,
)
from api.v2.orm import V2Announcement

from ..queries import QueryMembership
from ..queries.parse_json_into_table import parse_json_into_table, using_source
from . import ServiceException, SessionMixin

if TYPE_CHECKING:
    from sqlmodel import Session

    from api.v2.models import (
        V2AnnouncementBase,
        V2AnnouncementLinkBase,
        V2AnnouncementLinkWrite,
        V2AnnouncementUpdate,
    )

logger = logging.getLogger("api")


class AnnouncementsService(SessionMixin):
    def __init__(self, session: "Session"):
        super().__init__(session)

    def _announcement_exists(self, id: int) -> bool:
        from api.v2.orm import V2Announcement

        query = (
            select(V2Announcement.id)
            .where(V2Announcement.id == id)
            .where(V2Announcement.is_deleted == "F")
        )
        # noinspection PyTypeChecker,PydanticTypeChecker
        query = select(query.exists())
        return self.session.execute(query).scalar_one()

    def _links_exist(self, link_ids: list[int]) -> bool:
        from api.v2.orm import V2AnnouncementLink

        query_links = (
            QueryMembership().add_orm_membership(V2AnnouncementLink, link_ids).build()
        )
        non_existent_links = self.session.exec(query_links).all()
        return not non_existent_links

    def _put_announcement_links(
        self,
        announcement_id: int,
        links: "list[V2AnnouncementLinkBase]",
        requestor: str,
    ):
        """PUT like operation. Remove existing links not in `links`, insert or update"""
        existing_links = [l for l in links if l.id is not None]

        existing_links_models = parse_obj_as(
            list[V2AnnouncementLinkRead], existing_links
        )
        existing_links_ids = [l.id for l in existing_links_models]

        self._delete_hanging_announcement_links(
            announcement_id, existing_links_ids, requestor
        )

        self._merge_announcement_links(
            announcement_id, existing_links_models, requestor
        )

        self._create_announcement_links(announcement_id, links, requestor)

    def _create_announcement_links(
        self,
        announcement_id: int,
        links: list["V2AnnouncementLinkBase"],
        requestor: str,
    ):
        from api.v2.orm import V2AnnouncementLink

        # Insert new links
        if not links:
            return
        lit_dt = literal(datetime.utcnow().isoformat())
        lit_user = literal(requestor)
        logger.info(
            "Creating Announcement Links for announcement %s with %d links",
            announcement_id,
            len(links),
        )
        new_stmt = insert(V2AnnouncementLink).values(
            [
                {
                    "name": link.name,
                    "href": link.href,
                    "created_by": lit_user,
                    "create_dtm": lit_dt,
                    "announcement_id": announcement_id,
                    "is_deleted": "F",
                }
                for link in links
                if link.id is None
            ]
        )
        self.session.exec(new_stmt)

    def _merge_announcement_links(
        self,
        announcement_id: int,
        links: list["V2AnnouncementLinkRead"],
        requestor: str,
    ):
        from api.v2.orm import V2AnnouncementLink

        if not links:
            return
        lit_dt = literal(datetime.utcnow().isoformat())
        lit_user = literal(requestor)
        source_values = [
            {
                "id": link.id,
                "name": link.name,
                "href": link.href,
                "announcement_id": announcement_id,
            }
            for link in links
        ]
        logger.info(
            "Merging Announcement Links for announcement %s with %d links",
            announcement_id,
            len(source_values),
        )
        fn = parse_json_into_table(json.dumps(source_values, separators=(",", ":")))
        # noinspection PyTypeChecker,PydanticTypeChecker
        source_virtual = (
            select(
                literal_column("value:id::INTEGER").label("id"),
                literal_column("value:name::VARCHAR").label("name"),
                literal_column("value:href::VARCHAR").label("href"),
                literal_column("value:announcement_id::INTEGER").label(
                    "announcement_id"
                ),
            )
            .select_from(fn)
            .cte("source_virtual")
        )
        merge_links = MergeInto(
            target=V2AnnouncementLink.__table__,
            source=using_source(source_virtual),
            on=and_(
                V2AnnouncementLink.announcement_id == source_virtual.c.announcement_id,
                V2AnnouncementLink.id == source_virtual.c.id,
            ),
        )
        merge_links.when_matched_then_update().where(
            V2AnnouncementLink.is_deleted == "F"
        ).values(
            updated_by=lit_user,
            update_dtm=lit_dt,
            name=source_virtual.c.name,
            href=source_virtual.c.href,
        )
        self.session.exec(merge_links)

    def _delete_hanging_announcement_links(
        self, announcement_id: int, existing_links_ids: list[int], requestor: str
    ):
        """Note: This does the inverse of deleting from ids - it removes links that are not in `existing_links_ids` and match announcement_id."""

        from api.v2.orm import V2AnnouncementLink

        if not existing_links_ids:
            return
        logger.info(
            "Deleting any announcement links not in: %s for announcement %s by %s",
            existing_links_ids,
            announcement_id,
            requestor,
        )
        stmt = (
            update(V2AnnouncementLink)
            .where(V2AnnouncementLink.announcement_id == announcement_id)
            .where(V2AnnouncementLink.is_deleted == "F")
            .where(~V2AnnouncementLink.id.in_(existing_links_ids))
            .values(is_deleted="T", update_dtm=func.utc_time(), updated_by=requestor)
        )
        self.session.exec(stmt)

    def update_announcement(
        self, announcement_id: int, model: "V2AnnouncementUpdate", requestor: str
    ):
        announcement_exists = self._announcement_exists(announcement_id)
        if not announcement_exists:
            raise ServiceException(
                code=404,
                msg=f"Announcement '{announcement_id}' not found",
            )

        model_links: list[V2AnnouncementLinkBase] = model.links

        links_by_persisted = groupby(
            lambda l: getattr(l, "id", None) is not None, model_links
        )
        persisted_links = links_by_persisted.get(True, [])
        new_links = links_by_persisted.get(False, [])

        if persisted_links and not self._links_exist(
            [link.id for link in persisted_links]
        ):
            raise ServiceException(
                code=404,
                msg=f"One or mode Announcement links not found: {[link.id for link in persisted_links]}",
            )

        self._put_announcement_links(
            announcement_id=announcement_id, links=new_links, requestor=requestor
        )

        update_stmt = (
            update(V2Announcement)
            .where(V2Announcement.id == announcement_id)
            .values(
                {
                    **model.dict(exclude={"links"}, exclude_unset=True),
                    **{"updated_by": requestor, "update_dtm": func.utc_time()},
                }
            )
        )
        self.session.exec(update_stmt)

    def track_announcement_dismissal(
        self, announcement_id: int, user_id: int, requestor: str, is_dismissed: bool
    ):
        """
        When a user toggles dismissed announcement, we track it via dc_user_to_announcement

        The user_announcement row likely doesn't exist so we use merge
        """

        if not self._announcement_exists(announcement_id):
            raise ServiceException(
                code=404,
                msg=f"Announcement '{announcement_id}' not found",
            )

        stmt = text(
            """
            MERGE INTO dc_user_to_announcement as target
            USING (VALUES(:user_id, :announcement_id, :is_dismissed)) as source (user_id, announcement_id, is_dismissed)
            ON target.user_id = source.user_id AND target.announcement_id = source.announcement_id
            WHEN MATCHED THEN UPDATE SET target.is_dismissed = source.is_dismissed, target.update_dtm = sysdate(), target.updated_by = :requestor
            WHEN NOT MATCHED THEN
                INSERT (user_id, announcement_id, is_dismissed, create_dtm, created_by, is_deleted)
                VALUES (source.user_id, source.announcement_id, source.is_dismissed, sysdate(), :requestor, 'F')
            
            """
        ).bindparams(
            user_id=user_id,
            announcement_id=announcement_id,
            is_dismissed=is_dismissed,
            requestor=requestor,
        )

        self.session.exec(stmt)
        self.session.commit()

    def delete_announcement(self, announcement_id: int, requestor: str):
        if not self._announcement_exists(announcement_id):
            raise ServiceException(
                code=404,
                msg=f"Announcement '{announcement_id}' not found",
            )

        stmt = (
            update(V2Announcement)
            .where(V2Announcement.id == announcement_id)
            .where(V2Announcement.is_deleted == "F")
            .values(is_deleted="T", update_dtm=func.utc_time(), updated_by=requestor)
        )
        self.session.exec(stmt)
        self.session.commit()

    def create_announcement(self, model: "V2AnnouncementBase", requestor: str) -> int:
        """
        Create a new announcement
        """
        from api.v2.orm import (
            V2Announcement,
            V2AnnouncementLink,
            seq_dc_announcement_links,
            seq_dc_announcements,
        )

        announcement_id: int = self.session.exec(
            select(seq_dc_announcements.next_value())
        ).one()

        def make_link(link_model: "V2AnnouncementLinkWrite", announcement_id: int):
            link_id = self.session.exec(
                select(seq_dc_announcement_links.next_value())
            ).one()
            return {
                "id": link_id,
                "name": link_model.name,
                "href": link_model.href,
                "create_dtm": func.utc_time(),
                "created_by": requestor,
                "is_deleted": "F",
                "announcement_id": announcement_id,
            }

        insert_announcement = insert(V2Announcement).values(
            id=announcement_id,
            title=model.title,
            subtitle=model.subtitle,
            body=model.body,
            category=model.category,
            priority=model.priority,
            push_date=model.push_date,
            expiration_date=model.expiration_date,
            audience=model.audience,
            is_deleted="F",
            created_by=requestor,
            create_dtm=func.utc_time(),
        )

        self.session.exec(insert_announcement)
        self.session.commit()

        link_values = [
            make_link(link_model=link, announcement_id=announcement_id)
            for link in model.links
        ]

        if not link_values:
            return announcement_id

        insert_announcement_links = insert(V2AnnouncementLink).values(link_values)

        self.session.exec(insert_announcement_links)
        self.session.commit()

        return announcement_id
