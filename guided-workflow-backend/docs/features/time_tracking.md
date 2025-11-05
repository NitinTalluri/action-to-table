Time tracking feature allows CAMs to submit time spent on each deliverable.
All the engagements and associated deliverables assigned to CAM along with standard deliverable such as training will be visible on the portal.

![Time Tracking Portal](Images/time_tracking.png)

#### Table Information:

1) Deliverables associated with engagement are fetched from joining below tables.
```
DC_DELIVERABLES_OWED_SCHEDULED_ENG DL 
JOIN DC_ENGAGEMENT_TO_BOOKINGS_RESPONSIBLE_USER ERU
ON (DL.BOOKING_CONTRACT = ERU.BOOKING_CONTRACT AND
DL.DC_ENGAGEMENT_ID = ERU.DC_ENGAGEMENT_ID AND
ERU.IS_DELETED = 'F' AND ERU.DC_USER_ID = :dc_user_id)
```
2) Standard deliverables which are not associated with engagement are fetched from table DC_SDP_ABSTRACT_DELIVERABLE.

3) All the time entries are stored in table DC_SDP_TIME_ENTRY.

#### Endpoint Information

Below 3 endpoints are responsible to manage operations for this portal.

#### 1) /api/v2/sdp/time_tracking/weekly: Get
This endpoint is mainly responsible to return list of weeks to display and total number of hours spent per week.

:::api.v2.routers.sdp.time_tracking.get_weekly_view

this end point executes below query to produce the result:

:::api.v2.queries.sdp.time_tracking.query_weekly_summary

#### 2) /api/v2/sdp/time_tracking: Get
This endpoint is mainly responsible to fetch existing time entries for current user.

:::api.v2.routers.sdp.time_tracking.get_user_time_tracking

this end point executes below query to produce the result:

:::api.v2.queries.sdp.time_tracking.query_user_time_tracking_detail

#### 3) /api/v2/sdp/time_tracking: Post
This endpoint is mainly responsible to store submitted time entries for current user.

:::api.v2.routers.sdp.time_tracking.submit_user_time_tracking

this end point executes store procedure PutUserTimeEntries which store entry in table DC_SDP_TIME_ENTRY.

#### May Release:
We have modified UI to take entry for Saturday and Sunday as well.

![Time Tracking Portal](Images/time_tracking_weekend.png)

Time entries will be stored in table DC_SDP_TIME_ENTRY. 

No backed changes are made, so due date/visibility date logic will work as previously. 