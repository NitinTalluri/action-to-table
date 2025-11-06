
# Enhanced mappings found by fix_mapping_issues.py
ENHANCED_PROC_MAPPINGS = {'rebuild_sdp_for_booking_contract': ['dc_sdp_contract_changes'], 'rebuild_sdp_for_booking': ['dc_sdp_contract_changes', 'dc_sdp_changes'], 'replace_assignment_responsible_user': ['replace_responsible_user'], 'update_verified_booking_assignments': ['assign_responsible_users'], 'rebuild_sdp': ['dc_sdp_changes'], 'run_rebuild_sdp': ['dc_sdp_changes'], 'process_sea_upload': ['load_sea_data'], 'process_macd_upload': ['load_macd_data'], 'create_cxea_revenue_entries': ['create_revenue_entries', 'update_cxea_revenue'], 'create_htec_revenue_entries': ['create_revenue_entries', 'update_htec_revenue'], 'create_cogs_revenue_entries': ['create_revenue_entries', 'update_cogs_revenue']}

ENHANCED_SERVICE_PATTERNS = [
    # Add more comprehensive service detection patterns
    r'(\w+)\.(rebuild_sdp_for_booking|create_\w+_revenue_entries)\s*\(',
    r'with\s+(\w*Service\w*)\(\)\s+as\s+(\w+):.*?\2\.(\w+)\s*\(',
    r'(\w*Service\w*)\(\)\.(\w+)\s*\(',
]

# Functions that should be tracked even if not in service classes
STANDALONE_TARGET_FUNCTIONS = {'create_cxea_revenue_entries': {'type': 'function_def', 'file': 'guided-workflow-backend\\api\\v2\\routers\\admin\\financial\\revenue.py', 'pattern': 'def create_cxea_revenue_entries('}, 'create_htec_revenue_entries': {'type': 'function_def', 'file': 'guided-workflow-backend\\api\\v2\\routers\\admin\\financial\\revenue.py', 'pattern': 'def create_htec_revenue_entries('}, 'create_cogs_revenue_entries': {'type': 'function_def', 'file': 'guided-workflow-backend\\api\\v2\\routers\\admin\\financial\\revenue.py', 'pattern': 'def create_cogs_revenue_entries('}, 'rebuild_sdp_for_booking': {'type': 'function_def', 'file': 'guided-workflow-backend\\api\\v2\\routers\\manager\\sdp.py', 'pattern': 'def rebuild_sdp_for_booking('}}
