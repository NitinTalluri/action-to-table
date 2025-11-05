from logging import getLogger

from sqlalchemy import and_, func
from sqlmodel import select

from api.v2.models import TextMessageCreate

from . import ServiceException, SessionMixin

logger = getLogger(__name__)


from typing import TYPE_CHECKING, Optional

from api.v2.orm import V2CamEngagement

if TYPE_CHECKING:
    from sqlmodel import Session

    from api.v2.orm import V2User
    from api.v2.services import ExternalServiceTracker, PrefectV3FlowService


class EngagementsService(SessionMixin):
    def __init__(self, session: "Session"):
        super().__init__(session)

    def share_engagement_via_prefect(
        self,
        flow_service: "PrefectV3FlowService",
        requestor: "V2User",
        shared_with_dc_user_id: int,
        dc_engagement_id: int,
        tracker: "ExternalServiceTracker",
    ):
        """
        In the event of a new share (or a share that was previously deleted),

        And confirming that the engagement exists and the user is authorized,

        Create a notification and emit an event to Prefect to handle the sharing of the engagement.

        *Important*: This function assumes that the engagement exists and the requestor is authorized to share it.
        """
        request_id = tracker.get_next_request_id(self.session)
        notification_id = tracker.get_next_notification_id(self.session)

        _db_notification = tracker.create_notification(
            dc_engagement_id=dc_engagement_id,
            db_session=self.session,
            messages=[
                TextMessageCreate(type="text", data="Processing engagement share.")
            ],
            user_id=requestor.user_id,
            request_id=request_id,
            notification_id=notification_id,
        )

        flow_service.emit_engagement_shared(
            dc_engagement_id=dc_engagement_id,
            dc_user_id=requestor.user_id,
            notification_id=notification_id,
            request_id=request_id,
            shared_with_dc_user_id=shared_with_dc_user_id,
        )

    def _get_existing_engagement_to_user(
        self, dc_engagement_id: int, share_user_id: int
    ) -> Optional["V2CamEngagement"]:
        from api.v2.orm import V2CamEngagement

        query = (
            select(V2CamEngagement)
            .where(V2CamEngagement.dc_engagement_id == dc_engagement_id)
            .where(V2CamEngagement.user_id == share_user_id)
        )
        existing = self.session.exec(query).one_or_none()
        return existing

    def _get_user_id_from_email(self, cisco_cco_id: str) -> Optional[int]:
        from api.v2.orm import V2User

        share_user_query = select(V2User.user_id).where(
            V2User.cisco_cco_id == cisco_cco_id
        )
        share_user = self.session.exec(share_user_query).one_or_none()
        return share_user

    def _engagement_exists(self, dc_engagement_id: int) -> bool:
        from api.v2.orm import V2Engagement

        query = (
            select(V2Engagement.dc_engagement_id)
            .where(V2Engagement.dc_engagement_id == dc_engagement_id)
            .where(V2Engagement.is_deleted == "F")
        )
        # noinspection PyTypeChecker,PydanticTypeChecker
        query = select(query.exists())
        return self.session.execute(query).scalar_one()

    def _engagement_exists_and_authorized(self, dc_engagement_id, requestor) -> bool:
        from api.v2.orm import V2CamEngagement, V2Engagement

        query = (
            select(V2Engagement.dc_engagement_id)
            .join(
                V2CamEngagement,
                and_(
                    V2Engagement.dc_engagement_id == V2CamEngagement.dc_engagement_id,
                    V2CamEngagement.is_deleted == "F",
                ),
            )
            .where(V2CamEngagement.user_id == requestor.user_id)
            .where(V2Engagement.dc_engagement_id == dc_engagement_id)
            .where(V2Engagement.is_deleted == "F")
        )
        # noinspection PyTypeChecker,PydanticTypeChecker
        query = select(query.exists())
        return self.session.execute(query).scalar_one()

    def _mutate_or_create_share(
        self,
        existing_share: V2CamEngagement | None,
        dc_engagement_id: int,
        requestor: "V2User",
        target_user_id: int,
    ):
        """
        Receives either a existing V2CamEngagement and mutates it, or creates a new one.

        The result is the same
        """
        if existing_share is not None:
            existing_share.is_deleted = "F"
            existing_share.updated_by = requestor.cisco_cco_id
            existing_share.update_dtm = func.now()
        else:
            existing_share = V2CamEngagement(
                dc_engagement_id=dc_engagement_id,
                user_id=target_user_id,
                created_by=requestor.cisco_cco_id,
                is_deleted="F",
            )
        self.session.add(existing_share)

    def share_engagement(
        self,
        requestor: "V2User",
        target_user_cisco_cco_id: str,
        dc_engagement_id: int,
        tracker: "ExternalServiceTracker",
        flow_service: "PrefectV3FlowService",
    ):
        """
        As a user, I want to share an engagement with another user using their Cisco CCO ID (email).

        If this is a new share, we will create a new entry as well as a prefect job for sharing the
        existing liveboards.

        We perform a check on whether the engagement exists and whether the requestor is authorized
        """
        target_user_id = self._get_user_id_from_email(target_user_cisco_cco_id)
        if target_user_id is None:
            raise ServiceException(
                code=404,
                msg="User not found",
            )

        is_authorized_and_engagement_exists = self._engagement_exists_and_authorized(
            dc_engagement_id, requestor
        )

        if not is_authorized_and_engagement_exists:
            raise ServiceException(
                code=403,
                msg="Engagement not found or user is not authorized to share this engagement",
            )

        existing_share = self._get_existing_engagement_to_user(
            dc_engagement_id=dc_engagement_id, share_user_id=target_user_id
        )

        self._mutate_or_create_share(
            existing_share=existing_share,
            dc_engagement_id=dc_engagement_id,
            requestor=requestor,
            target_user_id=target_user_id,
        )

        self.share_engagement_via_prefect(
            flow_service=flow_service,
            requestor=requestor,
            shared_with_dc_user_id=target_user_id,
            dc_engagement_id=dc_engagement_id,
            tracker=tracker,
        )

    def share_engagement_as_manager(
        self,
        requestor: "V2User",
        target_user_cisco_cco_id: str,
        dc_engagement_id: int,
        tracker: "ExternalServiceTracker",
        flow_service: "PrefectV3FlowService",
    ):
        """
        As a manager, I want to share an engagement with another user using their Cisco CCO ID (email).

        This is similar to sharing an engagement, but bypasses the requirement that the manager is directly associated with the engagement.

        """
        target_user_id = self._get_user_id_from_email(target_user_cisco_cco_id)
        if target_user_id is None:
            raise ServiceException(
                code=404,
                msg="User not found",
            )

        engagement_exists = self._engagement_exists(dc_engagement_id=dc_engagement_id)
        if not engagement_exists:
            raise ServiceException(
                code=404,
                msg=f"Engagement #{dc_engagement_id} not found",
            )

        existing_share = self._get_existing_engagement_to_user(
            dc_engagement_id=dc_engagement_id, share_user_id=target_user_id
        )

        self._mutate_or_create_share(
            existing_share=existing_share,
            dc_engagement_id=dc_engagement_id,
            requestor=requestor,
            target_user_id=target_user_id,
        )

        self.share_engagement_via_prefect(
            flow_service=flow_service,
            requestor=requestor,
            shared_with_dc_user_id=target_user_id,
            dc_engagement_id=dc_engagement_id,
            tracker=tracker,
        )

    def unshare_engagement(
        self, requestor: "V2User", target_user_cisco_cco_id: str, dc_engagement_id: int
    ):
        """
        As either a user or a manager, I want to unshare an engagement with another user using their Cisco CCO ID (email).

        The link between the user and target_user will be marked as is_deleted.

        We do not revoke liveboard permissions
        """
        target_user_id: int | None = self._get_user_id_from_email(
            cisco_cco_id=target_user_cisco_cco_id
        )
        if target_user_id is None:
            raise ServiceException(
                code=404,
                msg="User not found",
            )

        existing_share: V2CamEngagement | None = self._get_existing_engagement_to_user(
            dc_engagement_id=dc_engagement_id, share_user_id=target_user_id
        )
        if existing_share is None or existing_share.is_deleted == "T":
            logger.warning(
                "Engagement %s not shared with user %s - skipping unshare operation",
                dc_engagement_id,
                target_user_cisco_cco_id,
            )
            return
        existing_share.is_deleted = "T"
        existing_share.updated_by = requestor.cisco_cco_id
        existing_share.update_dtm = func.now()
        self.session.add(existing_share)
