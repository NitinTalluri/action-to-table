import pytest
from snowflake.sqlalchemy import MergeInto
from snowflake.sqlalchemy.snowdialect import SnowflakeDialect
from sqlalchemy import Column, Integer, String, Table, MetaData, literal
from sqlmodel import select


def test_cte_compiles_successfully_with_merge_into():
    """
    Test that CTEs work correctly with MergeInto compilation when used with the using_source wrapper.
    
    This test verifies that the fix works: using CTEs with the using_source wrapper that creates
    a proper merge_source_wrapper construct for MergeInto compilation.
    
    Related to the issue where snowflake-sqlalchemy MergeInto doesn't properly handle CTEs as sources.
    """
    from api.v2.queries.parse_json_into_table import using_source
    
    # Create a simple table for testing
    metadata = MetaData()
    test_table = Table(
        'test_table',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String(50))
    )
    
    # Create a CTE (Common Table Expression) similar to what build_virtual_source() creates
    source_query = select(
        literal(1).label('id'),
        literal('test').label('name')
    )
    source_cte = source_query.cte("source_virtual")
    
    # Create a MergeInto statement using the CTE with the using_source wrapper
    merge_stmt = MergeInto(
        target=test_table,
        source=using_source(source_cte),
        on=test_table.c.id == source_cte.c.id
    )
    
    # The critical test: compile the MergeInto statement with SnowflakeDialect
    # This should work without any AttributeError
    compiled_sql = str(merge_stmt.compile(dialect=SnowflakeDialect(), compile_kwargs={"literal_binds": True}))
    
    # Print the compiled SQL to see the output
    print(f"\nCompiled SQL:\n{compiled_sql}")
    
    # Basic sanity check that the SQL was generated correctly
    assert "MERGE INTO" in compiled_sql
    assert "USING" in compiled_sql
    assert "source_virtual" in compiled_sql
    # Verify the source is properly wrapped
    assert "AS source_virtual" in compiled_sql