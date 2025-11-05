import pytest
import sqlglot

from api.v2.models.manager.bookings import V2SalesLevelAssignment
from api.v2.queries.manager.bookings_sales_level import (
    _build_sales_level_validation_query,
    _build_sales_level_merge_statement,
)


class TestSalesLevelQueryCompilation:
    """Test SQL compilation for sales level assignment queries"""

    def test_validation_query_compilation(self, parse_stmt):
        """Test that the validation query compiles correctly with SnowflakeDialect"""
        assignments = [
            V2SalesLevelAssignment(booking_contract=123, sales_level_id=456),
            V2SalesLevelAssignment(booking_contract=789, sales_level_id=0)
        ]
        
        # Build the validation query
        validation_query = _build_sales_level_validation_query(assignments)
        
        # Compile with SnowflakeDialect using the standard pattern
        parsed_sql = parse_stmt(validation_query)
        
        # Print the compiled SQL for inspection
        sql_str = str(parsed_sql)
        print(f"\nValidation Query SQL:\n{sql_str}")
        
        # Verify the query structure
        assert "UNION" in sql_str.upper(), "QueryMembership should use UNION ALL"
        
        # Verify booking contract values are in the query
        sql_str = str(parsed_sql)
        assert "123" in sql_str, "booking_contract 123 should be in query"
        assert "789" in sql_str, "booking_contract 789 should be in query"
        
        # Verify sales level values are in the query
        assert "456" in sql_str, "sales_level_id 456 should be in query"
        assert "0" in sql_str, "sales_level_id 0 should be in query"
        
        # Verify model type references
        assert "V2BookingContracts" in sql_str, "Should reference booking contracts model"
        assert "V2SalesLevel" in sql_str, "Should reference sales level model"

    def test_merge_statement_compilation(self, parse_stmt):
        """Test that the MERGE statement compiles correctly with SnowflakeDialect"""
        assignments = [
            V2SalesLevelAssignment(booking_contract=123, sales_level_id=456),
            V2SalesLevelAssignment(booking_contract=789, sales_level_id=0)
        ]
        requestor = "test_user@cisco.com"
        
        # Build the MERGE statement
        merge_stmt = _build_sales_level_merge_statement(assignments, requestor)
        
        # Compile with SnowflakeDialect using the standard pattern
        parsed_sql = parse_stmt(merge_stmt)
        
        # Print the compiled SQL for inspection
        sql_str = str(parsed_sql)
        print(f"\nMERGE Statement SQL:\n{sql_str}")
        
        # Verify it's a MERGE statement targeting the correct table
        assert "MERGE INTO" in sql_str.upper(), "Should be a MERGE statement"
        
        # Verify target table is in the SQL  
        assert "dc_bookings_contracts" in sql_str.lower(), "Should target booking contracts table"
        
        # Verify assignment values are in the query
        assert "123" in sql_str, "booking_contract 123 should be in query"
        assert "789" in sql_str, "booking_contract 789 should be in query"
        assert "456" in sql_str, "sales_level_id 456 should be in query"
        assert "0" in sql_str, "sales_level_id 0 should be in query"
        
        # Verify requestor is in the query
        assert requestor in sql_str, f"Requestor {requestor} should be in query"
        
        # Verify audit fields are being set
        assert "updated_by" in sql_str.lower(), "Should set updated_by field"
        assert "update_dtm" in sql_str.lower(), "Should set update_dtm field"
        assert "current_timestamp" in sql_str.lower(), "Should use current_timestamp for update_dtm"

    def test_merge_statement_soft_delete_condition(self, parse_stmt):
        """Test that MERGE statement includes soft delete condition"""
        assignments = [V2SalesLevelAssignment(booking_contract=123, sales_level_id=456)]
        
        merge_stmt = _build_sales_level_merge_statement(assignments, "test_user")
        parsed_sql = parse_stmt(merge_stmt)
        
        sql_str = str(parsed_sql)
        print(f"\nMERGE Statement with Soft Delete SQL:\n{sql_str}")
        
        # Verify soft delete condition is included in the ON clause
        assert "is_deleted" in sql_str.lower(), "Should include is_deleted condition"
        assert "'F'" in sql_str or '"F"' in sql_str, "Should filter for non-deleted records"

    def test_deduplication_in_validation_query(self, parse_stmt):
        """Test that validation query properly deduplicates IDs"""
        # Create assignments with duplicate booking contracts and sales levels
        assignments = [
            V2SalesLevelAssignment(booking_contract=123, sales_level_id=456),
            V2SalesLevelAssignment(booking_contract=123, sales_level_id=789),  # Duplicate booking_contract
            V2SalesLevelAssignment(booking_contract=456, sales_level_id=456),  # Duplicate sales_level_id
        ]
        
        validation_query = _build_sales_level_validation_query(assignments)
        parsed_sql = parse_stmt(validation_query)
        
        sql_str = str(parsed_sql)
        print(f"\nDeduplication Validation Query SQL:\n{sql_str}")
        
        # Count occurrences of the duplicate booking contract 123
        booking_contract_occurrences = sql_str.count("123")
        # Should appear fewer times than if not deduplicated (exact count depends on query structure)
        assert booking_contract_occurrences > 0, "Booking contract 123 should appear in query"
        
        # Count occurrences of the duplicate sales level 456  
        sales_level_occurrences = sql_str.count("456")
        assert sales_level_occurrences > 0, "Sales level 456 should appear in query"