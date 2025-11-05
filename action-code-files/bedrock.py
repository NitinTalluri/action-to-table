import os
import json
import csv
import re
from typing import List, Optional
os.environ["AWS_PROFILE"] = "bedrock"

# LangChain Imports
from langchain_core.prompts import ChatPromptTemplate
from langchain_aws import ChatBedrock
from pydantic import BaseModel, Field


# Boto3 is implicitly used by ChatBedrock, but we often need it for setup or configuration
import boto3
from botocore.config import Config


# --- 1. Define the Structured Output Schema using Pydantic ---
# This schema dictates the exact JSON structure the LLM must return.


class ColumnDetails(BaseModel):
    """Detailed metadata for a single column within the Snowflake View."""
    column_name: str = Field(description="The name of the column as projected in the view (e.g., CUSTOMER_ID).")
    data_type: str = Field(description="The final Snowflake data type of the column (e.g., VARCHAR, NUMBER(10,2)).")
    source_expression: Optional[str] = Field(description="The exact expression or source column it is derived from (e.g., 'C.CUSTOMER_NAME', 'UPPER(T1.ORDER_ID)'). Use 'N/A' if the DDL does not explicitly show the source (e.g., SELECT *).")
    is_key: bool = Field(description="True if this column appears to be a natural key, primary key, or foreign key. Look for conventions like '_ID', 'KEY', or obvious join columns.")
    transformation_applied: bool = Field(description="True if the source expression involves a function, calculation, type cast, or alias that changes the original value or name.")
    source_table: str = Field(description="The fully qualified name of the source table or view (e.g., DB.SCHEMA.TABLE_NAME).")
    alias_used: str = Field(description="alias used for tables for source table N/A in case of no alias")
    source_column_names: str = Field(description="The source column name/names from which this view column is derived. Use 'N/A' if not explicitly shown in the DDL. For expressions involving multiple columns, list them comma-separated.")
    derived_expression:str = Field(description="The expression used to derive this column in the view definition. If no expression defulat to N/A")

class SnowflakeViewDetails(BaseModel):
    """The complete, structured analysis of the Snowflake View DDL."""
    view_name: str = Field(description="The fully qualified name of the view (e.g., DB.SCHEMA.VIEW_NAME).")
    entity_type: str = Field(description="A single word describing the main business entity this view represents (e.g., 'Customer', 'Order', 'Product', 'DailySales').")
    source_tables: List[str] = Field(description="A list of all fully qualified tables or views referenced in the FROM and JOIN clauses.")
    join_conditions: List[str] = Field(description="A list of the explicit join conditions found in the DDL (e.g., 'T1.ID = T2.ID'). List only the ON clauses.")
    projection_columns: List[ColumnDetails] = Field(description="A detailed list of all columns projected by the view, conforming to the ColumnDetails schema.")
    filtration_criteria: Optional[str] = Field(description="Any specific WHERE or HAVING clauses applied to the view, or 'None' if none are present.")




# --- 2. Configure LangChain and Bedrock ---


def get_bedrock_llm():
    """Initializes and returns the ChatBedrock model for Claude 3.5 Sonnet."""
    print("-> Initializing ChatBedrock for Claude 3.5 Sonnet...")
   
    # Use the latest Claude model with tool-calling capabilities for structured output
    # Claude 3.5 Sonnet is highly recommended for complex reasoning and JSON extraction
    model_id = "us.anthropic.claude-sonnet-4-20250514-v1:0"
   
    # Configure Boto3 client with a standard retry config
    config = Config(
        retries={'max_attempts': 10, 'mode': 'standard'},
        region_name=os.environ.get("AWS_REGION", "us-east-1"), # Change region if needed
        # profile = "bedrock"
    )
   
    boto3_session = boto3.Session()
    bedrock_client = boto3_session.client(
        service_name="bedrock-runtime",
        config=config
    )
   
    # Instantiate the LangChain ChatBedrock model
    llm = ChatBedrock(
        model_id=model_id,
        client=bedrock_client,
        # Setting a low temperature encourages factual, deterministic output (best for extraction)
        model_kwargs={"temperature": 0.0, "max_tokens": 4096}
    )
   
    return llm


# --- 3. Define the Chain and Logic ---


def resolve_source_table(column_expression: str, alias_mapping: dict) -> str:
    """
    Resolves the source table name from the column expression using the alias mapping.
    For example, 'cd.SUB_TASK_ID' with alias_mapping {'cd': 'dc_completed_deliverables'}
    will return 'dc_completed_deliverables.SUB_TASK_ID'.
    """
    if '.' in column_expression:
        alias, column = column_expression.split('.', 1)
        return f"{alias_mapping.get(alias, alias)}.{column}"
    return column_expression


def infer_alias_mapping(ddl_script: str) -> dict:
    """
    Infers table alias mappings from the DDL script.
    For example, extracts {'cd': 'dc_completed_deliverables', 'sd': 'dc_deliverables_owed_scheduled_eng'}
    from the DDL script.
    """
    alias_pattern = re.compile(r"\b(\w+)\s+as\s+(\w+)\b", re.IGNORECASE)
    alias_mapping = {}

    for match in alias_pattern.finditer(ddl_script):
        table_name, alias = match.groups()
        alias_mapping[alias] = table_name

    return alias_mapping


def analyze_snowflake_ddl(ddl_script: str):
    """
    Creates a LangChain structured output chain and runs the DDL analysis.
    """
    llm = get_bedrock_llm()

    # Infer alias mapping from the DDL script
    alias_mapping = infer_alias_mapping(ddl_script)

    # 1. Define the System Prompt
    system_prompt = (
        "You are an expert Data Catalog Engineer specializing in Snowflake SQL. "
        "Your task is to analyze the provided Snowflake View DDL and extract "
        "all required metadata into a precise JSON format. Be meticulous in "
        "identifying source columns, data types, and transformations. "
        "Resolve table aliases to their corresponding source table names in the metadata. "
        "The view DDL is guaranteed to be valid Snowflake SQL. You MUST only "
        "return a JSON object that strictly adheres to the provided schema."
    )


    # 2. Define the Human Prompt Template
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Analyze the following Snowflake View DDL and extract the metadata: \n\n```sql\n{ddl_script}\n```"),
    ])


    # 3. Create the Structured Output Chain
    # The with_structured_output method handles the complex prompt engineering
    # to force the LLM to return JSON matching the Pydantic schema using tool-calling.
    structured_llm = llm.with_structured_output(SnowflakeViewDetails)
   
    chain = prompt | structured_llm


    print("-> Sending DDL to Claude 3.5 Sonnet for extraction...")
   
    # 4. Invoke the chain
    try:
        result: SnowflakeViewDetails = chain.invoke({"ddl_script": ddl_script})
       
        print("\n---  Extraction Successful ---")
        # Use Pydantic's built-in export to pretty-print the result
        print(json.dumps(result.dict(), indent=2))
        return result
       
    except Exception as e:
        print(f"\n---  Extraction Failed ---")
        print(f"An error occurred during LLM invocation: {e}")
        # In a real scenario, you would implement retry logic with exponential backoff
        # The ChatBedrock client handles basic retries, but a robust app needs more.
        return None


def save_to_csv(view_details: SnowflakeViewDetails, output_file: str, alias_mapping: dict):
    """
    Save the extracted Snowflake View details to a CSV file with resolved source table names.
    """
    headers = ["View_Name", "View_Column", "Column_Type", "Source_Table", "Source_Column", "Expression_Type","Derived_Expression"]

    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)

        for column in view_details.projection_columns:
            source_column = column.source_expression if column.source_expression else "N/A"
            resolved_source = resolve_source_table(source_column, alias_mapping) if source_column != "N/A" else "N/A"
            expression_type = "Transformation" if column.transformation_applied else "Direct"

            writer.writerow([
                view_details.view_name,
                column.column_name,
                column.data_type,
                column.source_table,
                # resolved_source.split('.')[0] if '.' in resolved_source else "N/A",
                # resolved_source.split('.')[1] if '.' in resolved_source else resolved_source,
                column.source_column_names,
                expression_type,
                column.derived_expression
            ])




# --- 4. Example Usage ---


if __name__ == "__main__":
    # Example Snowflake View DDL for testing
    snowflake_ddl_example = """
create or replace view CPS_DB.CPS_DSCI_API.DC_CURRENT_PARENT_IB(
	PARENT_INSTANCE_ID,
	INSTANCE_ID,
	PARENT_INSTANCE,
	PARENT_SERIAL_NUMBER,
	PARENT_INVENTORY_ITEM_ID,
	PARENT_DEVICE_ID,
	PARENT_PID,
	PARENT_SITE_ID,
	PARENT_LAST_DATE_OF_SUPPORT,
	DEVICE_LEVEL_IS_PARENT_LDOS_FLAG
) as SELECT * FROM IDENTIFIER('daily_parent_instance_2025_10_23');
    """
   
    analysis_result, alias_mapping = analyze_snowflake_ddl(snowflake_ddl_example),infer_alias_mapping(snowflake_ddl_example)


    if analysis_result:
        print(f"\n--- Catalog Summary ---")
        print(f"View Name: {analysis_result.view_name}")
        print(f"Main Entity: {analysis_result.entity_type}")
        print(f"Source Tables: {', '.join(analysis_result.source_tables)}")
        print(f"Total Columns Extracted: {len(analysis_result.projection_columns)}")
        print(f"Filtration: {analysis_result.filtration_criteria}")

        # Save to CSV
        output_csv_file = "snowflake_view_details.csv"
        save_to_csv(analysis_result, output_csv_file, alias_mapping)
        print(f"\nCSV file saved: {output_csv_file}")



