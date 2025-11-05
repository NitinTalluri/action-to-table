select * from CPS_DSCI_API.dc_ENGAGEMENT_SFC_TYPES
--###############################################################################################################################
create or replace table CPS_DSCI_API.dc_ENGAGEMENT_SFC_TYPES
(  -- pk = sfc_agreement_type
    sfc_type_id int identity primary key,
    sfc_agreement_type   varchar(5000) unique ,  -- NOT NULL
    CREATED_BY  VARCHAR(250),
    create_DTM  DATETIME,
    update_DTM  DATETIME,
    updated_BY  VARCHAR(250),
    IS_DELETED VARCHAR(100) DEFAULT 'F'
);
insert into CPS_DSCI_API.dc_ENGAGEMENT_SFC_TYPES(SFC_AGREEMENT_TYPE, CREATED_BY, CREATE_DTM, UPDATE_DTM, UPDATED_BY) values
(  'NET FIXED PRICE','alanzen',current_date, current_date, 'alanzen'),
(  'NET FIXED PRICE WITH GROWTH RATESE','alanzen',current_date, current_date, 'alanzen'),
(  'OTHER','alanzen',current_date, current_date, 'alanzen'),
(  'PAY AS YOU GROW','alanzen',current_date, current_date, 'alanzen'),
(  'SYMPHONY','alanzen',current_date, current_date, 'alanzen'),
(  'TIERED PRICING MODEL WITH BANDS','alanzen',current_date, current_date, 'alanzen'),
(  'TIERED PRICING MODEL WITH CAPS','alanzen',current_date, current_date, 'alanzen');

--###############################################################################################################################
create or replace table CPS_DSCI_API.dc_CONTRACT_TYPES
( -- pk =SERVICE_CONTRACT_TYPE
    contract_type_id int identity primary key ,
    SERVICE_CONTRACT_TYPE   varchar(5000) unique ,  -- NOT NULL
    CREATED_BY  VARCHAR(250),
    create_DTM  DATETIME,
    update_DTM  DATETIME,
    updated_BY  VARCHAR(250),
    IS_DELETED VARCHAR(100) DEFAULT 'F'
);
insert into CPS_DSCI_API.dc_CONTRACT_TYPES(SERVICE_CONTRACT_TYPE, CREATED_BY, CREATE_DTM, UPDATE_DTM, UPDATED_BY) values
        ('CXEA','alanzen',current_date, current_date, 'alanzen'),
        ('Financial Agreement','alanzen',current_date, current_date, 'alanzen'),
        ('WPA','alanzen',current_date, current_date, 'alanzen'),
        ('SFC','alanzen',current_date, current_date, 'alanzen'),
        ('Financial Sweeps','alanzen',current_date, current_date, 'alanzen'),
        ('Stand Alone Asset Management','alanzen',current_date, current_date, 'alanzen');

--###############################################################################################################################
create or replace table CPS_DSCI_API.dc_CONTRACT_ASSET_MGT_TYPES
( -- pk =asset_management_type
    am_type_id int identity primary key,
    asset_management_type   varchar(5000) unique ,  -- NOT NULL
    CREATED_BY  VARCHAR(250),
    create_DTM  DATETIME,
    update_DTM  DATETIME,
    updated_BY  VARCHAR(250),
    IS_DELETED VARCHAR(100) DEFAULT 'F'
);



insert into CPS_DSCI_API.dc_CONTRACT_ASSET_MGT_TYPES(asset_management_type, CREATED_BY, CREATE_DTM, UPDATE_DTM, UPDATED_BY) values
        ('Standard (HW)','alanzen',current_date, current_date, 'alanzen'),
        ('Premium (HW/SW)','alanzen',current_date, current_date, 'alanzen'),
        ('Premium (HW/SW)','alanzen',current_date, current_date, 'alanzen')


--###############################################################################################################################
create or replace table CPS_DSCI_API.dc_CONTRACT_MONITOR_TYPES
( -- pk =monitor_reason
    monitor_type_id int identity  primary key,
    monitor_reason   varchar(5000)  unique,  -- NOT NULL
    CREATED_BY  VARCHAR(250),
    create_DTM  DATETIME,
    update_DTM  DATETIME,
    updated_BY  VARCHAR(250),
    IS_DELETED VARCHAR(100) DEFAULT 'F'
);
insert into CPS_DSCI_API.dc_CONTRACT_MONITOR_TYPES(MONITOR_REASON, CREATED_BY, CREATE_DTM, UPDATE_DTM, UPDATED_BY)
values ('waiting for coverage to drop off','alanzen',current_date, current_date, 'alanzen'),
        ('waiting for budget to expand','alanzen',current_date, current_date, 'alanzen'),
        ('partner contract that will come into scope','alanzen',current_date, current_date, 'alanzen'),
        ('deployment and/or sparing contract','alanzen',current_date, current_date, 'alanzen'),
        ('new shipment temp contract','alanzen',current_date, current_date, 'alanzen'),
        ('non-serviceable location','alanzen',current_date, current_date, 'alanzen'),
        ('other','alanzen',current_date, current_date, 'alanzen');

--###############################################################################################################################
create or replace table CPS_DSCI_API.dc_ENGAGEMENT_stakeholder_TYPES
(  -- pk = stakeholder_type
    stakeholder_type_id int identity primary key,
    stakeholder_type   varchar(5000) unique,  -- NOT NULL
    CREATED_BY  VARCHAR(250),
    create_DTM  DATETIME,
    update_DTM  DATETIME,
    updated_BY  VARCHAR(250),
    IS_DELETED VARCHAR(100) DEFAULT 'F'
);

insert into CPS_DSCI_API.dc_ENGAGEMENT_stakeholder_TYPES(STAKEHOLDER_TYPE, CREATED_BY, CREATE_DTM, UPDATE_DTM, UPDATED_BY)


select  distinct STAKEHOLDER_TYPE, 'alanzen',current_timestamp,current_timestamp,  'alanzen'  from CPS_BIA_BR.DATA_CANVAS_STAKEHOLDER_DATA_V
where STAKEHOLDER_TYPE in ('ASSET MANAGER',
'RENEWAL MANAGER',
'CUSTOMER STAKEHOLDER',
'PARTNER STAKEHOLDER',
'SERVICE DELIVERY EXECUTIVE',
'HTOM',
'ACCOUNT MANAGER',
'CISCO SERVICE MANAGER',
'SFC DEAL ASSURANCE'
)

--#####################################################################################################################
--#####################################################################################################################
--#####################################################################################################################

create oR REPLACE sequence CPS_DSCI_API.SEQ_DC_USERS
    start with 1;

create or replace table CPS_DSCI_API.dc_users
( -- pk cisco_cco_id
    user_id int default CPS_DSCI_API.SEQ_DC_USERS.nextval primary key ,
    cisco_cco_id   varchar(5000) unique,  -- NOT NULL
    user_title     varchar(5000) ,
    CREATED_BY  VARCHAR(250),
    create_DTM  DATETIME,
    update_DTM  DATETIME,
    updated_BY  VARCHAR(250),
    IS_DELETED VARCHAR(100) DEFAULT 'F'
);
insert into CPS_DSCI_API.dc_users(CISCO_CCO_ID, USER_TITLE, CREATED_BY, CREATE_DTM, UPDATE_DTM, UPDATED_BY)
select cec_id || '@cisco.com', role as title, CREATED_BY, CREATE_DTM,  UPDATE_DTM, UPDATED_BY
from CPS_BIA_BR.DATA_CANVAS_USER_ROLE_V;

create sequence CPS_DSCI_API.SEQ_DC_ENGAGEMENTS
    start with 20000;

-- insert into CPS_DSCI_API.dc_ENGAGEMENT_HDR(DC_ENGAGEMENT_ID, ENGAGEMENT_NAME, IS_SFC, SFC_AGREEMENT_TYPE, IS_CXEA, IS_SOFTWARE, NOTES, CREATED_BY, UPDATED_BY, UPDATE_DTM, CREATE_DTM, IS_DELETED)
-- select * from CPS_DSCI_API.dc_ENGAGEMENT_HDR_bax where DC_ENGAGEMENT_ID = 20000
--alter table CPS_DSCI_API.dc_ENGAGEMENT_HDR rename to CPS_DSCI_API.dc_ENGAGEMENT_HDR_bax
--#####################################################################################################################
create or replace table CPS_DSCI_API.dc_ENGAGEMENT_HDR
(  -- pk dc_engagement_id
    dc_engagement_id   int default CPS_DSCI_API.SEQ_DC_ENGAGEMENTS.nextval primary key ,  -- PK
    engagement_name VARCHAR(5000),
    is_sfc          VARCHAR(100),
    sfc_agreement_type INT,                 -- FK TO TABLE
    IS_CXEA         VARCHAR(100),
    IS_SOFTWARE     VARCHAR(100),
    notes           VARCHAR(60000),
    CREATED_BY  VARCHAR(250),
    UPDATED_BY  VARCHAR(250),
    UPDATE_DTM  DATETIME,
    create_DTM  DATETIME,
    IS_DELETED VARCHAR(100) DEFAULT 'F' , --<- visibility
    CONSTRAINT fkey_sfc_type FOREIGN KEY (sfc_agreement_type) REFERENCES CPS_DSCI_API.dc_ENGAGEMENT_SFC_TYPES (sfc_type_id) ENFORCED
);

select * from CPS_DSCI_BR.DATA_CANVAS_HDR







--
-- create or replace sequence CPS_DSCI_API.SEQ_DC_ENGAGEMENTS
--     start with 20000;
-- select CPS_DSCI_API.SEQ_DC_ENGAGEMENTS.nextval
c1  -----------------------------                         -------------------------------------


create or replace table CPS_DSCI_API.dc_CAM_to_engagement
( -- pk =cam_id,dc_engagement_id
    user_id int  ,
    dc_engagement_id int ,
    CREATED_BY  VARCHAR(250),
    create_DTM  DATETIME,
    update_DTM  DATETIME,
    updated_BY  VARCHAR(250),
    IS_DELETED VARCHAR(100) DEFAULT 'F',
    CONSTRAINT pkey_cam_2_e PRIMARY KEY (dc_engagement_id, user_id) ENFORCED,
   CONSTRAINT fkey_user_2_engage FOREIGN KEY (user_id) REFERENCES CPS_DSCI_API.dc_users (user_id) ENFORCED,
   CONSTRAINT fkey_eg_2_engage FOREIGN KEY (dc_engagement_id) REFERENCES CPS_DSCI_API.dc_ENGAGEMENT_HDR (dc_engagement_id) ENFORCED
);


--
create or replace TABLE CPS_DB.CPS_DSCI_API.DC_CAM_TO_ENGAGEMENT (
   USER_ID NUMBER(38,0) NOT NULL,
   DC_ENGAGEMENT_ID NUMBER(38,0) NOT NULL,
   CREATED_BY VARCHAR(250),
   CREATE_DTM TIMESTAMP_NTZ(9),
   UPDATE_DTM TIMESTAMP_NTZ(9),
   UPDATED_BY VARCHAR(250),
   IS_DELETED VARCHAR(100) DEFAULT 'F',
   primary key (USER_ID, DC_ENGAGEMENT_ID),
   foreign key (USER_ID) references CPS_DB.CPS_DSCI_API.DC_USERS(USER_ID),
   foreign key (DC_ENGAGEMENT_ID) references CPS_DB.CPS_DSCI_API.DC_ENGAGEMENT_HDR(DC_ENGAGEMENT_ID)
);

create or replace transient table CPS_DSCI_ARCHIVE.global_cco_engagement as
with i as (
select distinct i.UID,i.CAMCECID,i.ACCOUNTNAME,i.MCEENGAGEMENTID,i.ACATACCOUNTID,i.SMARTACCOUNTID,i.GUID
from CPS_BIA_BR.DATA_CANVAS_ENGAGEMENT_HDR_V i where nvl(is_active,'Y') = 'Y'
)
select  distinct i.UID, trim(value)|| '@cisco.com' as this_value ,  'cco_id' as src
from i , lateral split_to_table(replace(trim(i.CAMCECID), ' ',',')  , ',')
where trim(value)  != '';

insert into CPS_DSCI_API.dc_CAM_to_engagement(user_id, dc_engagement_id, CREATED_BY, create_DTM, update_DTM, updated_BY)
select u.USER_ID,  e.UID ,CREATED_BY, create_DTM, update_DTM, updated_BY from  CPS_DSCI_ARCHIVE.global_cco_engagement e
join  CPS_DSCI_API.dc_users u on( upper(e.THIS_VALUE)=upper(u.CISCO_CCO_ID) ) ;

create or replace table CPS_DSCI_API.dc_ENGAGEMENT_CONTRACTS
(  -- pk dc_engagement_id, CONTRACT_NUMBER
    CONTRACT_NUMBER int,
    dc_engagement_id  int,
    booking_contract  varchar(5000), -- multiple values so 1 big string
    CAMS  varchar(5000),             -- multi value via commas
    AM_start_date date,
    am_end_date date,
    allowed_SERVICE_LEVELS VARCHAR(5000),-- comma sep list
    SERVICE_CONTRACT_TYPE_ID int , -- fk
    asset_management_type_ID int , -- fk
    monitor_reason_TYPE_ID int, -- FK
    CREATED_BY  VARCHAR(250),
    create_DTM  DATETIME,
    update_DTM  DATETIME,
    updated_BY  VARCHAR(250),
    IS_DELETED VARCHAR(100) DEFAULT 'F',
    CONSTRAINT pkey_acparty_lnk PRIMARY KEY (dc_engagement_id, CONTRACT_NUMBER) ENFORCED,
     CONSTRAINT fkey_acat_lnk_ FOREIGN KEY (dc_engagement_id) REFERENCES CPS_DSCI_API.dc_ENGAGEMENT_HDR (dc_engagement_id) ENFORCED,
     CONSTRAINT fkey_contract_type FOREIGN KEY (SERVICE_CONTRACT_TYPE_ID) REFERENCES CPS_DSCI_API.dc_CONTRACT_TYPES (contract_type_id) ENFORCED,
     CONSTRAINT fkey_am_type FOREIGN KEY (asset_management_type_ID) REFERENCES CPS_DSCI_API.dc_CONTRACT_ASSET_MGT_TYPES (am_type_id) ENFORCED,
     CONSTRAINT fkey_monitor_type FOREIGN KEY (monitor_reason_TYPE_ID) REFERENCES CPS_DSCI_API.dc_CONTRACT_MONITOR_TYPES (monitor_type_id) ENFORCED
);


select * from CPS_DSCI_API.dc_ENGAGEMENT_STAKEHOLDERS

create oR REPLACE sequence CPS_DSCI_API.SEQ_stakeholders
    start with 1;

create or replace table CPS_DSCI_API.dc_ENGAGEMENT_STAKEHOLDERS
(  -- pk = sfc_agreement_type
    stakeholder_id int default CPS_DSCI_API.SEQ_stakeholders.nextval ,
    dc_engagement_id int,
    STAKEHOLDER_NAME   varchar(5000) ,  -- NOT NULL
    STAKEHOLDER_EMAIL   varchar(5000) ,
    STAKEHOLDER_PHONE   varchar(5000) ,
    stakeholder_type_id int,               -- fk
    CREATED_BY  VARCHAR(250),
    create_DTM  DATETIME,
    update_DTM  DATETIME,
    updated_BY  VARCHAR(250),
    IS_DELETED VARCHAR(100) DEFAULT 'F',
    CONSTRAINT pkey_ae_stakeholders PRIMARY KEY (dc_engagement_id, stakeholder_id) ENFORCED,
    CONSTRAINT fkey_stake_2_e_lnk_ FOREIGN KEY (dc_engagement_id) REFERENCES CPS_DSCI_API.dc_ENGAGEMENT_HDR (dc_engagement_id) ENFORCED,
    CONSTRAINT fkey_stake_type FOREIGN KEY (stakeholder_type_id) REFERENCES CPS_DSCI_API.dc_ENGAGEMENT_stakeholder_TYPES (stakeholder_type_id) ENFORCED
);

insert into CPS_DSCI_API.dc_ENGAGEMENT_STAKEHOLDERS
         (dc_engagement_id, STAKEHOLDER_NAME, STAKEHOLDER_EMAIL, STAKEHOLDER_PHONE, stakeholder_type_id, CREATED_BY,    create_DTM,  update_DTM, updated_BY)
select  uid,  STAKEHOLDER_NAME, STAKEHOLDER_EMAIL, STAKEHOLDER_PHONE, t.stakeholder_type_id  , split_part(CAMCECID,',',0),   s.CREATE_DTM, s.UPDATE_DTM,  split_part(s.UPDATED_BY,',',0)
from CPS_BIA_BR.DATA_CANVAS_STAKEHOLDER_DATA_V s join CPS_DSCI_API.dc_ENGAGEMENT_stakeholder_TYPES t on (t.stakeholder_type=s.STAKEHOLDER_TYPE)
where UID is not null;


select * from CPS_DSCI_API.dc_ENGAGEMENT_stakeholder_TYPES


create or replace transient table CPS_DSCI_ARCHIVE.global_relevant as
with i as (
select distinct i.UID,i.CAMCECID,i.ACCOUNTNAME,i.MCEENGAGEMENTID,i.ACATACCOUNTID,i.SMARTACCOUNTID,i.GUID
from CPS_BIA_BR.DATA_CANVAS_ENGAGEMENT_HDR_V i where nvl(is_active,'Y') = 'Y'
)
select  distinct i.UID, trim(value)::bigint as this_value ,  'ACATACCOUNTID' as src
    from i , lateral split_to_table(replace(trim(i.ACATACCOUNTID), ' ',',')  , ',')
    where trim(value)  != ''   and try_to_number(trim(value))  is not null
union
    select  distinct i.UID, trim(value)::bigint as this_value ,  'MCEENGAGEMENTID' as src
    from i , lateral split_to_table(replace(trim(i.MCEENGAGEMENTID), ' ',',')  , ',')
    where trim(value)  != ''   and try_to_number(trim(value)) is not null
union
    select  distinct i.UID, trim(value)::bigint as this_value ,  'SMARTACCOUNTID' as src
    from i ,  lateral split_to_table(replace(trim(i.SMARTACCOUNTID), ' ',',')  , ',')
    where trim(value)  != ''   and try_to_number(trim(value)) is not null
union
    select  distinct i.UID, trim(value)::bigint as this_value ,  'GUID' as src
    from i , lateral split_to_table(replace(trim(i.GUID), ' ',',')  , ',')
    where trim(value)  != ''   and try_to_number(trim(value))  is not null
;


i
create or replace table CPS_DSCI_API.dc_ACAT_LINKS
(  -- PK -> dc_engagement_id, ACAT_CUSTOMER_ID
    id   int ,  -- NOT NULL
    dc_engagement_id  int ,
    CREATED_BY  VARCHAR(250),
    create_DTM  DATETIME,
    update_DTM  DATETIME,
    updated_BY  VARCHAR(250),
    IS_DELETED VARCHAR(100) DEFAULT 'F',
     CONSTRAINT pkey_acat_lnk PRIMARY KEY (dc_engagement_id, id) ENFORCED,
     CONSTRAINT fkey_acat_lnk_ FOREIGN KEY (dc_engagement_id) REFERENCES CPS_DSCI_API.dc_ENGAGEMENT_HDR (dc_engagement_id) ENFORCED
);


create or replace table CPS_DSCI_API.dc_PARTY_LINKS
(  --pk = dc_engagement_id, cr_party_id
    id   int ,  -- NOT NULL
    dc_engagement_id  int,
    CREATED_BY  VARCHAR(250),
    create_DTM  DATETIME,
    update_DTM  DATETIME,
    updated_BY  VARCHAR(250),
    IS_DELETED VARCHAR(100) DEFAULT 'F',
    CONSTRAINT pkey_party_lnk PRIMARY KEY (dc_engagement_id, id) ENFORCED,
     CONSTRAINT fkey_partyt_e_lnk_ FOREIGN KEY (dc_engagement_id) REFERENCES CPS_DSCI_API.dc_ENGAGEMENT_HDR (dc_engagement_id) ENFORCED
);


create or replace table CPS_DSCI_API.dc_MCE_LINKS
(  --pk = dc_engagement_id, MCE_ENGAGEMENT_NUMBER
    id   int ,  -- NOT NULL
    dc_engagement_id  int,
    CREATED_BY  VARCHAR(250),
    create_DTM  DATETIME,
    update_DTM  DATETIME,
    updated_BY  VARCHAR(250),
    IS_DELETED VARCHAR(100) DEFAULT 'F',
    CONSTRAINT pkey_mce_lnk PRIMARY KEY (dc_engagement_id, id) ENFORCED,
    CONSTRAINT fkey_mce_e_lnk_ FOREIGN KEY (dc_engagement_id) REFERENCES CPS_DSCI_API.dc_ENGAGEMENT_HDR (dc_engagement_id) ENFORCED
);


create or replace table CPS_DSCI_API.dc_SMART_ACCOUNT_LINKS
( --pk  dc_engagement_id, SMART_ACCOUNT
    id   int ,  -- NOT NULL
    dc_engagement_id  int,
    CREATED_BY  VARCHAR(250),
    create_DTM  DATETIME,
    update_DTM  DATETIME,
    updated_BY  VARCHAR(250),
    IS_DELETED VARCHAR(100) DEFAULT 'F',
    CONSTRAINT pkey_smart_lnk PRIMARY KEY (dc_engagement_id, id) ENFORCED,
     CONSTRAINT fkey_smart_lnk_ FOREIGN KEY (dc_engagement_id) REFERENCES CPS_DSCI_API.dc_ENGAGEMENT_HDR (dc_engagement_id) ENFORCED
);



insert into CPS_DSCI_API.dc_ACAT_LINKS(id, DC_ENGAGEMENT_ID, CREATED_BY, CREATE_DTM, UPDATE_DTM,UPDATED_BY)
select this_value, uid, 'alanzen', current_timestamp, current_timestamp, 'alanzen' from CPS_DSCI_ARCHIVE.global_relevant where SRC ='ACATACCOUNTID'
and this_value is not null;



insert into CPS_DSCI_API.dc_SMART_ACCOUNT_LINKS(id, DC_ENGAGEMENT_ID, CREATED_BY, CREATE_DTM, UPDATE_DTM,UPDATED_BY)
select this_value, uid, 'alanzen', current_timestamp, current_timestamp, 'alanzen' from CPS_DSCI_ARCHIVE.global_relevant where SRC ='SMARTACCOUNTID'
and this_value is not null;

insert into CPS_DSCI_API.dc_MCE_LINKS(id, DC_ENGAGEMENT_ID, CREATED_BY, CREATE_DTM, UPDATE_DTM, UPDATED_BY)
select this_value, uid, 'alanzen', current_timestamp, current_timestamp, 'alanzen' from CPS_DSCI_ARCHIVE.global_relevant where SRC ='MCEENGAGEMENTID'
and this_value is not null;


insert into CPS_DSCI_API.dc_PARTY_LINKS(id, DC_ENGAGEMENT_ID, CREATED_BY, CREATE_DTM, UPDATE_DTM, UPDATED_BY)
select this_value, uid, 'alanzen', current_timestamp, current_timestamp, 'alanzen' from CPS_DSCI_ARCHIVE.global_relevant where SRC ='GUID'
and this_value is not null;

insert into CPS_DSCI_API.dc_ENGAGEMENT_CONTRACTS(CONTRACT_NUMBER, DC_ENGAGEMENT_ID, CAMS,
                                                 ALLOWED_SERVICE_LEVELS,
                                                 SERVICE_CONTRACT_TYPE_ID,
                                                 ASSET_MANAGEMENT_TYPE_ID,
                                                 MONITOR_REASON_TYPE_ID,
                                                 CREATED_BY, CREATE_DTM, UPDATE_DTM, UPDATED_BY)
with i as (  select distinct c.ID as engagement_id, replace(c.contract_number, ' ', ',') as contract_number,
        CONTRACT_TYPE, AM_SERVICE_TYPE, SERVICE_LEVEL
        from CPS_BIA_BR.DATA_CANVAS_CONTRACT_DATA_V c
        where nvl(contract_del_flag, 'N') != 'Y' and c.ID is not null
        ),
        flattened_contracts as
        (select CONTRACT_TYPE, AM_SERVICE_TYPE, SERVICE_LEVEL,
        try_to_number(trim(value))::bigint as contract_number, engagement_id
        from i, lateral
        split_to_table(i.contract_number, ',')
        where
        trim(value) != '' and try_to_number(trim(value)) is not null
        )
        select distinct contract_number,
               replace(engagement_id,'CAM-','') as engagement_id,   -- DC_ENGAGEMENT_ID
               'alanzen' as CAM,  --CAMS
               SERVICE_LEVEL,    ---ALLOWED_SERVICE_LEVELS
                ctt.CONTRACT_TYPE_ID,  -- SERVICE_CONTRACT_TYPE
                ct.am_type_id,  --- ASSET_MANAGEMENT_TYPE
                mt.monitor_type_id,   -- MONITOR_REASON_TYPE
             'alanzen',current_date, current_date, 'alanzen'
        from flattened_contracts
        left join  CPS_DSCI_API.dc_CONTRACT_MONITOR_TYPES mt on ( mt.MONITOR_REASON = monitor_reason)
        left join  CPS_DSCI_API.dc_CONTRACT_ASSET_MGT_TYPES ct on ( ct.ASSET_MANAGEMENT_TYPE =AM_SERVICE_TYPE )
        left join CPS_DSCI_API.dc_CONTRACT_TYPES ctt on (ctt.SERVICE_CONTRACT_TYPE=CONTRACT_TYPE);


insert into CPS_DSCI_API.dc_ENGAGEMENT_HDR
(dc_engagement_id, ENGAGEMENT_NAME,  IS_SFC, SFC_AGREEMENT_TYPE, IS_CXEA, IS_SOFTWARE, NOTES,
CREATED_BY,  CREATE_DTM, UPDATED_BY, UPDATE_DTM)
select uid , accountname, sfcfa , sfc.SFC_TYPE_ID, h.iscxea , iscam ,exclusion_notes, h.created_by, h.create_dtm, h.updated_by, h.update_dtm
from CPS_BIA_BR.DATA_CANVAS_ENGAGEMENT_HDR_V  h
left join CPS_DSCI_API.dc_ENGAGEMENT_SFC_TYPES sfc on (sfc.SFC_AGREEMENT_TYPE = h.SFC_AGREEMENT_TYPE);

--###########################################################################################################################
--###########################################################################################################################



-- basic ddl for engagement tag table
create or replace table CPS_DSCI_API.DC_ENGAGEMENT_TAGS_zzzzzzzzzzzzzzz
(
    INSTANCE_ID int not null ,
    TAGSET_ID int  not null ,
    TAG_ID  int  not null ,
    dc_engagement_id   int not null , --fk
    update_DTM  DATETIME default current_timestamp,
    update_by  varchar(250),
    primary key (INSTANCE_ID, TAGSET_ID),
    foreign key (TAGSET_ID) references CPS_DB.CPS_DSCI_API.DC_TAGSET(TAGSET_ID),
    foreign key (dc_engagement_id) REFERENCES CPS_DSCI_API.dc_ENGAGEMENT_HDR (dc_engagement_id),
    foreign key (TAG_ID) references CPS_DB.CPS_DSCI_API.DC_TAGS(TAG_ID)
);




--APP info:
if your a CAM you can edit the engagement tagsets that are of type CAM
if your an IBA you can edit the engagement tagsets that are of type IBA
You can always see them its just about editing

create or replace table CPS_DSCI_API.dc_TAGSET_TYPES
(  -- pk = sfc_agreement_type
    tagset_type_id int identity primary key,
    tagset_type   varchar(5000) unique ,  -- NOT NULL
    CREATED_BY  VARCHAR(250),
    create_DTM  DATETIME,
    update_DTM  DATETIME,
    updated_BY  VARCHAR(250),
    IS_DELETED VARCHAR(100) DEFAULT 'F'
);
insert into CPS_DSCI_API.dc_TAGSET_TYPES(tagset_type, CREATED_BY, CREATE_DTM, UPDATE_DTM, UPDATED_BY) values
(  'CAM-Engagement-Tag','alanzen',current_date, current_date, 'alanzen'),
(  'IBA-Engagement-Tag','alanzen',current_date, current_date, 'alanzen');



create oR REPLACE sequence CPS_DSCI_API.SEQ_DC_tagset
    start with 5000;

create or replace table CPS_DSCI_API.dc_TAGSET
( -- pk cisco_cco_id
    TAGSET_ID int default CPS_DSCI_API.SEQ_DC_tagset.nextval  ,
    TAGSET_NAME   varchar(5000),  -- NOT NULL
    TAGSET_DESC     varchar(15000) ,
    SCOPE  VARCHAR(250),
    CARDINALITY  VARCHAR(250),
    TAGSET_TYPE int,
    DC_ENGAGEMENT_ID int , --NULL FOR GLOBAL!!!  only admins can edit these  all normal users will be in an engagement scope to edit these
    CREATED_BY  VARCHAR(250),
    create_DTM  DATETIME,
    update_DTM  DATETIME,
    updated_BY  VARCHAR(250),
    IS_DELETED VARCHAR(100) DEFAULT 'F',
    primary key (TAGSET_ID)
       --,foreign key (dc_engagement_id) REFERENCES CPS_DSCI_API.dc_ENGAGEMENT_HDR (dc_engagement_id)  if we need this then we nned a "master" engagement which i do not like
);
insert into CPS_DSCI_API.dc_TAGSET(TAGSET_ID, TAGSET_NAME, TAGSET_DESC,scope, CARDINALITY, TAGSET_TYPE,  DC_ENGAGEMENT_ID, CREATED_BY,CREATE_DTM, UPDATE_DTM, UPDATED_BY)
select tagset_id, TAGSET_NAME, TAGSET_DESC, scope , type , 1, engagement_id ,  split_part(CREATED_BY,',',0),  CREATE_DTM,  nvl(UPDATE_DTM,CREATE_DTM), UPDATED_BY
from CPS_BIA_BR.DATA_CANVAS_TAGSET_V;

select * from CPS_DSCI_API.dc_TAGSET ts join CPS_DSCI_API.dc_TAGSET_TYPES t on (t.tagset_type_id=ts.TAGSET_TYPE);






create oR REPLACE sequence CPS_DSCI_API.SEQ_DC_tags
    start with 200000;

create or replace table CPS_DSCI_API.dc_TAGS
( -- pk cisco_cco_id
    TAG_ID int default CPS_DSCI_API.SEQ_DC_tags.nextval,
    TAG_NAME   varchar(5000),  -- NOT NULL
    TAG_DESC     varchar(15000) ,
    TAGSET_ID   int,  --FK
    CREATED_BY  VARCHAR(250),
    create_DTM  DATETIME,
    update_DTM  DATETIME,
    updated_BY  VARCHAR(250),
    IS_DELETED VARCHAR(100) DEFAULT 'F',
    primary key (TAG_ID),
    foreign key (TAGSET_ID) references CPS_DB.CPS_DSCI_API.DC_TAGSET(TAGSET_ID)
);
insert into CPS_DSCI_API.dc_TAGS(TAG_ID, TAG_NAME, TAG_DESC,TAGSET_ID, CREATED_BY,CREATE_DTM, UPDATE_DTM, UPDATED_BY)
select tag_id, TAG_NAME, TAG_DESC, TAGSET_ID,  split_part(CREATED_BY,',',0),  CREATE_DTM,  nvl(UPDATE_DTM,CREATE_DTM), UPDATED_BY
from CPS_BIA_BR.DATA_CANVAS_TAG_V where nvl(TAG_DEL_FLG,'N')='N' and TAGSET_ID is not null ;



select t.TAGSET_ID, t.TAG_ID,ts.TAGSET_NAME, t.TAG_NAME from CPS_DSCI_API.dc_TAGS t join CPS_DSCI_API.dc_TAGSET ts on (ts.TAGSET_ID=t.TAGSET_ID)






--###########################################################################################################################

select * from CPS_DSCI_API.dc_ENGAGEMENT_HDR

--  acat links
select h.dc_engagement_id, h.ENGAGEMENT_NAME,e.ACAT_CUSTOMER_ID
from CPS_DSCI_API.dc_ENGAGEMENT_HDR h
join CPS_DSCI_API.dc_ACAT_LINKS e on (e.DC_ENGAGEMENT_ID = h.DC_ENGAGEMENT_ID );

-- party links
select h.dc_engagement_id, h.ENGAGEMENT_NAME,e.CR_PARTY_ID
from CPS_DSCI_API.dc_ENGAGEMENT_HDR h
join CPS_DSCI_API.dc_PARTY_LINKS e on (e.DC_ENGAGEMENT_ID = h.DC_ENGAGEMENT_ID );


-- mce links
select h.dc_engagement_id, h.ENGAGEMENT_NAME,e.MCE_ENGAGEMENT_NUMBER
from CPS_DSCI_API.dc_ENGAGEMENT_HDR h
join CPS_DSCI_API.dc_MCE_LINKS e on (e.DC_ENGAGEMENT_ID = h.DC_ENGAGEMENT_ID );



-- smart accoubnt links
select h.dc_engagement_id, h.ENGAGEMENT_NAME,e.SMART_ACCOUNT
from CPS_DSCI_API.dc_ENGAGEMENT_HDR h
join CPS_DSCI_API.dc_SMART_ACCOUNT_LINKS e on (e.DC_ENGAGEMENT_ID = h.DC_ENGAGEMENT_ID );




select dc_engagement_id, ENGAGEMENT_NAME, IS_SFC, sfc.SFC_AGREEMENT_TYPE , IS_CXEA, IS_SOFTWARE, NOTES, h.CREATED_BY, h.UPDATED_BY, h.UPDATE_DTM, h.CREATE_DTM
from CPS_DSCI_API.dc_ENGAGEMENT_HDR h
left join CPS_DSCI_API.dc_ENGAGEMENT_SFC_TYPES sfc on (sfc.SFC_TYPE_ID = h.SFC_AGREEMENT_TYPE );

select c.CONTRACT_NUMBER, c.DC_ENGAGEMENT_ID, c.BOOKING_CONTRACT, c.CAMS, c.AM_START_DATE, c.AM_END_DATE, c.ALLOWED_SERVICE_LEVELS,
       ctt.SERVICE_CONTRACT_TYPE, ct.ASSET_MANAGEMENT_TYPE, mt.MONITOR_REASON, c.CREATED_BY, c.CREATE_DTM, c.UPDATE_DTM, c.UPDATED_BY
from CPS_DSCI_API.dc_ENGAGEMENT_CONTRACTS c
left join  CPS_DSCI_API.dc_CONTRACT_MONITOR_TYPES mt on ( mt.monitor_type_id = c.MONITOR_REASON_TYPE_ID  )
left join  CPS_DSCI_API.dc_CONTRACT_ASSET_MGT_TYPES ct on ( ct.am_type_id =c.ASSET_MANAGEMENT_TYPE_ID )
left join CPS_DSCI_API.dc_CONTRACT_TYPES ctt on (ctt.CONTRACT_TYPE_ID=c.SERVICE_CONTRACT_TYPE_ID)
where c.DC_ENGAGEMENT_ID =3107