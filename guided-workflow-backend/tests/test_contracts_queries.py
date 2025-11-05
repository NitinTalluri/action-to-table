import pytest
import sqlglot

from api.v2.queries.contracts import query_engagement_booking_contracts


class TestContractsQueryCompilation:
    """Test SQL compilation for contracts queries"""

    def test_booking_contracts_query_compilation(self, parse_stmt):
        """Test that the booking contracts query compiles correctly with SnowflakeDialect"""
        dc_engagement_id = 12345
        cisco_cco_id = "test_user@cisco.com"
        booking_contract = None

        # Build the booking contracts query
        booking_query = query_engagement_booking_contracts(
            dc_engagement_id, cisco_cco_id, booking_contract
        )

        # Compile with SnowflakeDialect using the standard pattern
        parsed_sql = parse_stmt(booking_query)

        # Print the compiled SQL for inspection
        sql_str = str(parsed_sql)
        print(f"\nBooking Contracts Query SQL:\n{sql_str}")

        # Verify the query structure contains expected CTEs
        assert "extensions_cte" in sql_str.lower(), "Should contain extensions_cte"
        assert "booking" in sql_str.lower(), "Should contain booking CTE"
        assert "contracts" in sql_str.lower(), "Should contain contracts CTE"

        # Verify JSON functions are present
        assert "to_json" in sql_str.lower(), "Should use TO_JSON function"
        assert "object_construct_keep_null" in sql_str.lower(), "Should use OBJECT_CONSTRUCT_KEEP_NULL"
        assert "array_agg" in sql_str.lower(), "Should use ARRAY_AGG function"

        # Verify parameter values are in the query
        assert str(dc_engagement_id) in sql_str, "dc_engagement_id should be in query"
        assert cisco_cco_id in sql_str, "cisco_cco_id should be in query"

        # Verify key table references (actual table names, not ORM names)
        assert "dc_booking_contracts" in sql_str.lower(), "Should reference booking contracts table"
        assert "dc_user" in sql_str.lower(), "Should reference user table"
        assert "dc_bookings_contracts_responsible_users" in sql_str.lower(), "Should reference engagement responsible user table"

    def test_booking_contracts_query_with_filter(self, parse_stmt):
        """Test that the booking contracts query compiles correctly with booking_contract filter"""
        dc_engagement_id = 12345
        cisco_cco_id = "test_user@cisco.com"
        booking_contract = 67890

        # Build the booking contracts query with filter
        booking_query = query_engagement_booking_contracts(
            dc_engagement_id, cisco_cco_id, booking_contract
        )

        # Compile with SnowflakeDialect using the standard pattern
        parsed_sql = parse_stmt(booking_query)

        # Print the compiled SQL for inspection
        sql_str = str(parsed_sql)
        print(f"\nBooking Contracts Query with Filter SQL:\n{sql_str}")

        # Verify parameter values are in the query
        assert str(dc_engagement_id) in sql_str, "dc_engagement_id should be in query"
        assert cisco_cco_id in sql_str, "cisco_cco_id should be in query"
        assert str(booking_contract) in sql_str, "booking_contract filter should be in query"

        # Verify the query still contains the expected structure
        assert "extensions_cte" in sql_str.lower(), "Should contain extensions_cte"
        assert "to_json" in sql_str.lower(), "Should use TO_JSON function"

        # Verify soft delete conditions are included
        assert "is_deleted" in sql_str.lower(), "Should include is_deleted conditions"
        assert "'F'" in sql_str or '"F"' in sql_str, "Should filter for non-deleted records"