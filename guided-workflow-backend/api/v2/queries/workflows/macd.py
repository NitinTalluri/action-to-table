from sqlalchemy import Date, Integer, String, TextualSelect, text


def make_macd_hdr_query(dc_engagement_id: int) -> TextualSelect:
    """
    Generate a SQLAlchemy query to retrieve MACD header records for a given engagement ID.
    """

    stmt = (
        text(
            """
    SELECT    REQUEST_ID,
              DC_ENGAGEMENT_ID,
              DC_USER_ID,
              ROW_COUNT,
              APPROVED_BY,
              SIGN_OFF_IDENTITY_ID,
              EFFECTIVE_DATE,
              TOOL_NAME,
              TOOL_ACTION,
              NOTES,
              CREATED_BY,
              CREATE_DTM,
              UPDATE_DTM,
              UPDATED_BY
    FROM DC_WF_MACD_UPLOAD_HDR
    WHERE IS_DELETED = 'F'
    AND DC_ENGAGEMENT_ID = :dc_engagement_id
    """
        )
        .bindparams(dc_engagement_id=dc_engagement_id)
        .columns(
            request_id=Integer,
            dc_engagement_id=Integer,
            dc_user_id=Integer,
            row_count=Integer,
            approved_by=String,
            sign_off_identity_id=Integer,
            effective_date=Date,
            tool_name=String,
            tool_action=String,
            notes=String,
            created_by=String,
            create_dtm=Date,
            update_dtm=Date,
            updated_by=String,
        )
    )

    return stmt
