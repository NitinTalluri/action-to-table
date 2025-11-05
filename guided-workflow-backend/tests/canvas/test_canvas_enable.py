import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from starlette.authentication import AuthCredentials
from starlette.requests import Request

from api.dependencies import DataCanvasUser


class TestCanvasEnable:
    """Test the canvas enable endpoint functionality."""

    @pytest.fixture
    def test_app(self, username):
        from api.main import app
        from api.dependencies.security import decode_bearer

        def decode_bearer_override(r: Request):
            user = DataCanvasUser(username=username, email=username, scopes={})
            cred = AuthCredentials(scopes=list(user.scopes))
            r.scope["user"] = user
            r.scope["auth"] = cred
            return user

        overrides = app.dependency_overrides
        app.dependency_overrides = {**overrides, decode_bearer: decode_bearer_override}
        yield app
        app.dependency_overrides = overrides

    @pytest.fixture
    def client(self, test_app):
        with TestClient(test_app) as client:
            yield client

    def test_enable_endpoint_exists(self, client):
        """Test that the enable endpoint exists and responds appropriately."""
        # Test with a non-existent canvas ID
        response = client.put("/api/v2/canvas/999999/enable")

        # Should return 404 (not found) rather than 405 (method not allowed)
        # This confirms the endpoint exists and handles the request
        assert response.status_code == 404

    def test_enable_endpoint_method_validation(self, client):
        """Test that only PUT method is allowed on enable endpoint."""
        canvas_id = 999999

        # Test wrong HTTP methods
        get_response = client.get(f"/api/v2/canvas/{canvas_id}/enable")
        assert get_response.status_code == 405  # Method Not Allowed

        post_response = client.post(f"/api/v2/canvas/{canvas_id}/enable")
        assert post_response.status_code == 405  # Method Not Allowed

        delete_response = client.delete(f"/api/v2/canvas/{canvas_id}/enable")
        assert delete_response.status_code == 405  # Method Not Allowed

    @pytest.fixture
    def dummy_canvas_record(self, db_session, username):
        """Create and manage dummy canvas record for testing (-99999)."""
        test_canvas_id = -99999
        test_engagement_id = 94

        # Insert dummy canvas record
        insert_stmt = text("""
            INSERT INTO DC_CANVAS_HDR 
            (CANVAS_ID, DC_ENGAGEMENT_ID, CANVAS_NAME, CANVAS_DESC, CANVAS_TYPE, 
             ENABLED, IS_DELETED, CREATE_DTM, CREATED_BY, FILE_PATH, FILE_UPLOAD_STATUS)
            VALUES 
            (:canvas_id, :engagement_id, 'Test Canvas', 'Test Description', 'unified view canvas',
             TRUE, 'F', CURRENT_TIMESTAMP, :username, '/test/path', 'success')
        """).bindparams(
            canvas_id=test_canvas_id,
            engagement_id=test_engagement_id,
            username=username,
        )
        db_session.execute(insert_stmt)
        db_session.commit()

        yield {"canvas_id": test_canvas_id, "engagement_id": test_engagement_id}

        # Cleanup: Delete the test record
        cleanup_stmt = text("DELETE FROM DC_CANVAS_HDR WHERE CANVAS_ID = :canvas_id")
        db_session.execute(cleanup_stmt.bindparams(canvas_id=test_canvas_id))
        db_session.commit()

    def _reset_canvas_state(
        self,
        db_session,
        canvas_id,
        username,
        enabled,
        canvas_name="Test Canvas",
        is_deleted="F",
    ):
        """Helper to reset canvas to specified state for consistent test setup."""
        reset_stmt = text("""
            UPDATE DC_CANVAS_HDR 
            SET ENABLED = :enabled, IS_DELETED = :is_deleted, CANVAS_NAME = :canvas_name,
                UPDATED_BY = :username, UPDATE_DTM = CURRENT_TIMESTAMP
            WHERE CANVAS_ID = :canvas_id
        """).bindparams(
            canvas_id=canvas_id,
            username=username,
            enabled=enabled,
            canvas_name=canvas_name,
            is_deleted=is_deleted,
        )
        db_session.execute(reset_stmt)
        db_session.commit()

    def test_enable_canvas_304_already_enabled(
        self, client, db_session, username, dummy_canvas_record
    ):
        """Test HTTP 304 when canvas is already enabled."""
        canvas_id = dummy_canvas_record["canvas_id"]

        # Ensure canvas is in enabled state
        self._reset_canvas_state(db_session, canvas_id, username, enabled=True)

        # Call API with enabled=TRUE - should return HTTP 304
        response = client.put(f"/api/v2/canvas/{canvas_id}/enable")
        assert response.status_code == 304
        # 304 Not Modified has no response body (per HTTP spec)

    def test_enable_canvas_200_successful_enable(
        self, client, db_session, username, dummy_canvas_record
    ):
        """Test HTTP 200 when canvas is successfully enabled."""
        canvas_id = dummy_canvas_record["canvas_id"]

        # Set canvas to disabled state
        self._reset_canvas_state(db_session, canvas_id, username, enabled=False)

        # Call API - should return HTTP 200
        response = client.put(f"/api/v2/canvas/{canvas_id}/enable")
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["canvas_id"] == canvas_id
        assert response_data["enabled"] is True
        assert response_data["message"] == "Canvas enabled successfully"

        # Verify canvas is actually enabled in database
        check_stmt = text(
            "SELECT ENABLED FROM DC_CANVAS_HDR WHERE CANVAS_ID = :canvas_id"
        )
        enabled_status = db_session.execute(
            check_stmt.bindparams(canvas_id=canvas_id)
        ).scalar()
        assert enabled_status is True

    def test_enable_canvas_404_soft_deleted(
        self, client, db_session, username, dummy_canvas_record
    ):
        """Test HTTP 404 when canvas is soft-deleted."""
        canvas_id = dummy_canvas_record["canvas_id"]

        # Set canvas to soft-deleted state
        self._reset_canvas_state(
            db_session, canvas_id, username, enabled=True, is_deleted="T"
        )

        # Call API - should return HTTP 404
        response = client.put(f"/api/v2/canvas/{canvas_id}/enable")
        assert response.status_code == 404
        response_data = response.json()
        assert "not found" in response_data["detail"].lower()
        assert "not authorized" in response_data["detail"].lower()

    def test_enable_canvas_403_deactivated_name(
        self, client, db_session, username, dummy_canvas_record
    ):
        """Test HTTP 403 for canvas with (DEACTIVATED) name prefix."""
        canvas_id = dummy_canvas_record["canvas_id"]

        # Set canvas to deactivated state with deactivated name
        self._reset_canvas_state(
            db_session,
            canvas_id,
            username,
            enabled=False,
            canvas_name="(DEACTIVATED) Test Canvas",
        )

        # Call API - should return HTTP 403
        response = client.put(f"/api/v2/canvas/{canvas_id}/enable")
        assert response.status_code == 403
        response_data = response.json()
        assert response_data["detail"] == "Cannot enable canvas marked as deactivated"
