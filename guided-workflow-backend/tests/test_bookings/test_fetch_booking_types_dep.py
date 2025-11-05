from api.dependencies import ManagerBookingsServiceTypesDep

def test_fetch_booking_service_types(db_session):
    """
    Test that ManagerBookingsServiceTypesDep returns a dictionary with the keys dc_bookings_user_role and dc_sold_as_service_types
    """
    
    callable = ManagerBookingsServiceTypesDep.__metadata__[0].dependency
    result = callable(db_session)
    assert result is not None
    assert isinstance(result, dict)
    assert "dc_bookings_user_role" in result
    assert "dc_sold_as_service_types" in result
    