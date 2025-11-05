Release 2025-01-09

## Canvas Enable Endpoint

### New Features
- Added PUT `/api/v2/canvas/{canvas_id}/enable` endpoint to re-enable canvases soft-deactivated by dc-canvas-retention
- Added `enabled` and `rowcount` fields to canvas models
- Updated canvas listing API to include `enabled` status in response

### HTTP Status Codes
- **200**: Canvas enabled successfully
- **304**: Canvas already enabled 
- **403**: Deactivated canvas name
- **404**: Canvas not found or unauthorized
- **405**: Invalid HTTP method

### Technical Changes
- Updated ORM and API models with new fields
- Implemented endpoint with business logic
- JWT authentication via engagement validation
- Enhanced audit trail logging
- Modified `query_engagement_canvases` SQL to include `enabled` field in JSON response

### Test Coverage
- 6 test methods covering scenarios
- Shared test fixture for consistent data
- Helper method eliminates SQL duplication
- Real database operations verified

Release 2025-05-28

## Checklist
- [ ] Update version to v3.5.0
- [x] Run migration scripts
- [x] Move migration scripts to `migrations/prev` directory after successful migration
- [ ] Decide on SEA Macd Workflow Tree Scripts
- [x] Run [BulkInstanceTagging_2](scripts/sql/BulkInstanceTagging_2.sql).sql in CPS_DSCI_API
- [ ] Update config to call `BulkInstanceTagging_2` instead of `BulkInstanceTagging`
- [ ] Update config (remove env variables for Prefect V1 flows)
- [x] Run [LoadMACDData](scripts/sql/LoadMACDData.sql).sql in CPS_DSCI_API
- [x] Run [SuperCustomer](scripts/sql/SuperCustomer.sql).sql in CPS_DSCI_API
- [ ] Run SEA Upload (Need SQL script from Aaron)
- [x] Export dependencies using `uv export --no-hashes --no-dev --no-annotate --extra server > requirements.txt && git add requirements.txt`
- [x] Deploy dc_acat_discovery flow to Prod
- [ ] Delete [dc-acat-discovery (Prefect V1)](https://cloud.prefect.io/cisco-dev/flow/5cd658e6-472d-4cf2-a103-100b63a357c0)
- [x] Deploy macd_audit flow to Prod
- [x] Deploy dc_tag_history_report flow to Prod
- [x] Deploy dc_hostname_relink flow to Prod
- [ ] Delete [dc-p1-hostname-relink (Prefect V1)](https://cloud.prefect.io/cisco-dev/flow/2b5bee97-099d-4812-9ba9-46e4d5d1afa0)