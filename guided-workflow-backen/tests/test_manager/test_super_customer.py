import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text


@pytest.fixture(scope="session")
def predefined_engagement_ids(request) -> list[int]:
    """
    Fixture to provide predefined engagement IDs for testing.
    These IDs should be valid engagement IDs that exist in the database.

    To use different IDs in a specific test, you can parametrize the fixture:

    @pytest.mark.parametrize("predefined_engagement_ids", [[101, 102, 103]], indirect=True)
    def test_something(self, predefined_engagement_ids):
        # This test will use [101, 102, 103] instead of the default IDs
        ...
    """
    default_ids = [94, 727, 20254, 20285]
    return getattr(request, "param", default_ids)


class TestSuperCustomer:
    """
    Test the super customer feature.

    This test class tracks the lifecycle of a super customer through creation, updates, and deletion.
    """

    # Track state across tests
    super_customer_id = None
    super_customer_name = "Test Super Customer"
    updated_name = "Updated Super Customer"
    engagement_ids = []

    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup(cls, predefined_engagement_ids: list[int], db_engine):
        """Setup the test class with predefined engagement IDs."""
        cls.engagement_ids = predefined_engagement_ids
        assert len(cls.engagement_ids) >= 1, (
            "Need at least one engagement ID for testing"
        )
        yield
        if cls.super_customer_id:
            with db_engine.connect() as conn:
                stmt = text("""
                            DELETE FROM dc_super_customer
                                   WHERE super_customer_id = :super_customer_id
                            """).bindparams(super_customer_id=cls.super_customer_id)
                conn.execute(stmt)
                stmt = text(
                    """
                    DELETE FROM dc_super_customer_engagements
                           WHERE super_customer_id = :super_customer_id
                    """
                ).bindparams(super_customer_id=cls.super_customer_id)
                conn.execute(stmt)
        else:
            print("No super customer ID to clean up.")

    def test_get_super_customers(self, test_client: TestClient):
        """Test GET endpoint to ensure 200 response."""
        app = test_client.app
        route = app.url_path_for("get_super_customers")

        response = test_client.get(route)
        print(f"Response for GET super customers: {response.json()}")
        assert response.status_code == 200

    def test_create_super_customer(self, test_client: TestClient):
        """Test POST endpoint to create a new super customer with at least one engagement_id."""
        app = test_client.app
        route = app.url_path_for("create_super_customer")

        payload = {
            "super_customer_name": self.__class__.super_customer_name,
            "dc_engagement_ids": [self.__class__.engagement_ids[0]],
        }

        response = test_client.post(route, json=payload)
        print(f"Response for CREATE super customer: {response.json()}")
        assert response.status_code == 200

        # Store the super_customer_id for later use
        data = response.json()
        for sc in data["super_customers"]:
            if sc["super_customer_name"] == self.__class__.super_customer_name:
                self.__class__.super_customer_id = sc["super_customer_id"]
                break

        assert self.__class__.super_customer_id is not None, (
            "Failed to get super_customer_id from response"
        )

    def test_create_super_customer_duplicate_engagement(self, test_client: TestClient):
        """Test POST endpoint with an engagement ID that's already associated with another super customer."""
        app = test_client.app
        route = app.url_path_for("create_super_customer")

        payload = {
            "super_customer_name": "Another Super Customer",
            "dc_engagement_ids": [
                self.__class__.engagement_ids[0]
            ],  # Same engagement ID as the first super customer
        }

        response = test_client.post(route, json=payload)
        print(
            f"Response for CREATE super customer with duplicate engagement: {response.json()}"
        )
        assert response.status_code == 409, (
            "Should fail with conflict when using an already associated engagement ID"
        )

    def test_create_super_customer_duplicate_name(self, test_client: TestClient):
        """Test POST endpoint with a name that's already used by another super customer."""
        app = test_client.app
        route = app.url_path_for("create_super_customer")

        payload = {
            "super_customer_name": self.__class__.super_customer_name,  # Same name as the first super customer
            "dc_engagement_ids": [],
        }

        response = test_client.post(route, json=payload)
        print(
            f"Response for CREATE super customer with duplicate name: {response.json()}"
        )
        assert response.status_code == 409, (
            "Should fail with conflict when using an already used name"
        )

    def test_update_super_customer_no_changes(self, test_client: TestClient):
        """Test PUT endpoint with no changes to name or engagements."""
        app = test_client.app
        route = app.url_path_for(
            "update_super_customer", super_customer_id=self.__class__.super_customer_id
        )

        # Get current state
        get_route = app.url_path_for("get_super_customers")
        get_response = test_client.get(get_route)
        get_data = get_response.json()

        current_engagement_ids = []
        for sc in get_data["super_customers"]:
            if sc["super_customer_id"] == self.__class__.super_customer_id:
                current_engagement_ids = sc["dc_engagement_ids"]
                break

        # Update with same data
        payload = {
            "super_customer_id": self.__class__.super_customer_id,
            "super_customer_name": self.__class__.super_customer_name,
            "dc_engagement_ids": current_engagement_ids,
        }

        response = test_client.put(route, json=payload)
        print(f"Response for UPDATE super customer with no changes: {response.json()}")
        assert response.status_code == 200

        # Verify nothing changed
        get_response = test_client.get(get_route)
        get_data = get_response.json()

        for sc in get_data["super_customers"]:
            if sc["super_customer_id"] == self.__class__.super_customer_id:
                assert sc["super_customer_name"] == self.__class__.super_customer_name
                assert set(sc["dc_engagement_ids"]) == set(current_engagement_ids)
                break

    def test_update_super_customer_change_name(self, test_client: TestClient):
        """Test PUT endpoint with a change to the name."""
        app = test_client.app
        route = app.url_path_for(
            "update_super_customer", super_customer_id=self.__class__.super_customer_id
        )

        # Get current state
        get_route = app.url_path_for("get_super_customers")
        get_response = test_client.get(get_route)
        get_data = get_response.json()

        current_engagement_ids = []
        for sc in get_data["super_customers"]:
            if sc["super_customer_id"] == self.__class__.super_customer_id:
                current_engagement_ids = sc["dc_engagement_ids"]
                break

        # Update with new name
        payload = {
            "super_customer_id": self.__class__.super_customer_id,
            "super_customer_name": self.__class__.updated_name,
            "dc_engagement_ids": current_engagement_ids,
        }

        response = test_client.put(route, json=payload)
        print(f"Response for UPDATE super customer with name change: {response.json()}")
        assert response.status_code == 200

        # Verify name changed
        get_response = test_client.get(get_route)
        get_data = get_response.json()

        name_changed = False
        for sc in get_data["super_customers"]:
            if sc["super_customer_id"] == self.__class__.super_customer_id:
                assert sc["super_customer_name"] == self.__class__.updated_name
                name_changed = True
                break

        assert name_changed, "Name was not updated"

    def test_update_super_customer_change_engagements(self, test_client: TestClient):
        """Test PUT endpoint with changes to the engagements."""
        app = test_client.app
        route = app.url_path_for(
            "update_super_customer", super_customer_id=self.__class__.super_customer_id
        )

        # Get current state and available engagement IDs
        get_route = app.url_path_for("get_super_customers")
        get_response = test_client.get(get_route)
        get_data = get_response.json()

        # If we have a second engagement ID, add it
        if len(self.__class__.engagement_ids) > 1:
            new_engagement_ids = [
                self.__class__.engagement_ids[0],
                self.__class__.engagement_ids[1],
            ]
        # Otherwise, remove the current engagement ID
        else:
            new_engagement_ids = []

        # Update with new engagements
        payload = {
            "super_customer_id": self.__class__.super_customer_id,
            "super_customer_name": self.__class__.updated_name,
            "dc_engagement_ids": new_engagement_ids,
        }

        response = test_client.put(route, json=payload)
        print(
            f"Response for UPDATE super customer with engagement change: {response.json()}"
        )
        assert response.status_code == 200

        # Verify engagements changed
        get_response = test_client.get(get_route)
        get_data = get_response.json()

        for sc in get_data["super_customers"]:
            if sc["super_customer_id"] == self.__class__.super_customer_id:
                assert set(sc["dc_engagement_ids"]) == set(new_engagement_ids)
                break

    def test_update_super_customer_non_unique_name(self, test_client: TestClient):
        """Test PUT endpoint with a name that's already used by another super customer."""
        app = test_client.app

        # First, create another super customer
        create_route = app.url_path_for("create_super_customer")
        create_payload = {
            "super_customer_name": "Another Test Super Customer",
            "dc_engagement_ids": [],
        }

        create_response = test_client.post(create_route, json=create_payload)
        print(f"Response for CREATE another super customer: {create_response.json()}")
        assert create_response.status_code == 200, (
            "Should fail with conflict when using a name that's already in use"
        )

        # Now try to update our super customer with the name of the new one
        update_route = app.url_path_for(
            "update_super_customer", super_customer_id=self.__class__.super_customer_id
        )
        update_payload = {
            "super_customer_id": self.__class__.super_customer_id,
            "super_customer_name": "Another Test Super Customer",
            "dc_engagement_ids": [],
        }

        update_response = test_client.put(update_route, json=update_payload)
        print(
            f"Response for UPDATE super customer with non-unique name: {update_response.json()}"
        )
        assert update_response.status_code == 409, (
            "Should fail with conflict when using a name that's already in use"
        )

    def test_delete_super_customer(self, test_client: TestClient):
        """Test DELETE endpoint to soft delete a super customer."""
        app = test_client.app
        route = app.url_path_for(
            "delete_super_customer", super_customer_id=self.__class__.super_customer_id
        )

        # Get current state to check engagement IDs
        get_route = app.url_path_for("get_super_customers")
        get_response = test_client.get(get_route)
        get_data = get_response.json()

        current_engagement_ids = []
        for sc in get_data["super_customers"]:
            if sc["super_customer_id"] == self.__class__.super_customer_id:
                current_engagement_ids = sc["dc_engagement_ids"]
                break

        # Delete the super customer
        response = test_client.delete(route)
        print(f"Response for DELETE super customer: {response.json()}")
        assert response.status_code == 200

        # Verify super customer is deleted
        get_response = test_client.get(get_route)
        get_data = get_response.json()

        # Super customer should no longer be in the list
        super_customer_exists = False
        for sc in get_data["super_customers"]:
            if sc["super_customer_id"] == self.__class__.super_customer_id:
                super_customer_exists = True
                break

        assert not super_customer_exists, "Super customer was not deleted"

        # Verify that the engagement IDs are now available
        for engagement_id in current_engagement_ids:
            assert engagement_id in get_data["available_dc_engagement_ids"], (
                f"Engagement ID {engagement_id} was not marked as available after deletion"
            )
