Parent Customer View allows managers to see engagements assigned to another manager.
All the people who have access to manager portal will have access to this portal.
This portal will list down all the parent customers and engagements assigned to them,
Also it provide option to add/modify/delete parent customer.

#### Table Information:
1) DC_SUPER_CUSTOMER: This table contain details of all the parent customers.

2) DC_SUPER_CUSTOMER_ENGAGEMENTS: This table contains details of parent customer and associated engagement id.

#### Endpoint Information:
Below 4 endpoints are responsible to manage operations for this portal.

#### 1) api/v2/manager/scv: Get
This endpoint is mainly responsible to return all the parent customers and engagements associated with them.

:::api.v2.routers.manager.super_customers.get_super_customers

this end point executes below query to produce the result:

:::api.v2.queries.manager.super_customers.query_super_customers

#### 2) /api/v2/manager/scv: Post

:::api.v2.routers.manager.super_customers.create_super_customer

this end point run store procedure create_super_customer which enter new parent customer details 
in table DC_SUPER_CUSTOMER and associated engagement details in table DC_SUPER_CUSTOMER_ENGAGEMENTS.

#### Validations: 

i) unique case insensitive parent customer name is required. 

ii) only unassigned engagements will be visible as an engagement can be assigned to one parent customer only. 

iii) assigning an engagement is not a mandatory field, which means parent customer with no engagement can also be created. 

#### 3) api/v2/manager/scv/{engagement_id}: Put

:::api.v2.routers.manager.super_customers.update_super_customer

this end point run store procedure update_super_customer which update parent customer details 
in table DC_SUPER_CUSTOMER and associated engagement details in table DC_SUPER_CUSTOMER_ENGAGEMENTS accordingly.

#### 4) api/v2/manager/scv/{engagement_id}: Delete

:::api.v2.routers.manager.super_customers.delete_super_customer

this end point run store procedure delete_super_customer which delete requested parent customer details 
in table DC_SUPER_CUSTOMER and associated engagement details in table DC_SUPER_CUSTOMER_ENGAGEMENTS accordingly.