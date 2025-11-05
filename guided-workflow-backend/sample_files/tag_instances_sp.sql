create procedure TAG_INSTANCES_10(INVALUE VARCHAR)
	returns VARIANT
	language SQL
	strict
	as $$
        DECLARE
        found_user_cco varchar; -- validated member of engagement
        tag_access VARCHAR;     -- tags you can modify
        user_cco varchar;       --request user
        target_dc_engagement int default -1;  -- hardcoded for this
        --this_dc_engagement_sp int default 9;
        tag_id int;             --request tag id
        proposed_tagset_id int; --request tagset based on requested tag
        param_tagset_id int; --only used in unset
        proposed_action varchar default 'set' ; --request to set or unset a tag id
        tag_deleted varchar;    -- indicator if this tag is deleted
        tagset_deleted varchar; -- indicator if this tagset is deleted
        tagset_type varchar;    -- is this a cam or iba tag
        tag_scope varchar;      -- global or engagement tag
        tag_set_compat varchar;  -- flag for is allowed
        tag_table varchar ;
        looked_up_tag_dc_eng int;
        tagging_comments varchar;
        instance_list varchar;
        instance_cnt int;

        EXCEPTION_1 EXCEPTION (-20001, 'ERROR: USER NOT A MEMBER OF ENGAGEMENT');
        EXCEPTION_2 EXCEPTION (-20002, 'ERROR: USER DOES NOT HAVE ACCESS TO THIS TAG TYPE');
        EXCEPTION_3 EXCEPTION (-20003, 'ERROR: TAG SET or TAG is deleted');
        EXCEPTION_4 EXCEPTION (-20004, 'ERROR: Engagement misalignment between Procedure and Parameter');

        begin
            -- core json data
            select
            parse_json(:invalue):userId::VARCHAR,
            parse_json(:invalue):tagId::INT,
            parse_json(:invalue):engagementId::INT,
            parse_json(:invalue):ddl_action::varchar,
            nvl(parse_json(:invalue):tagsetId,-1)::INT,
            concat( 'CPS_DSCI_API.DC_ENGAGEMENT_TAGS_', parse_json(:invalue):engagementId::INT),
            parse_json(:invalue):comment::varchar,
            parse_json(:invalue):instance::varchar,
            regexp_count(parse_json(:invalue):instance::varchar,'[,]', 1, 'i')+1
            into  :user_cco, :tag_id, :target_dc_engagement, :proposed_action, :param_tagset_id,:tag_table, :tagging_comments, :instance_list , :instance_cnt ;

            -- tag info for valiation
            case when :proposed_action = 'set' then
                    select t.TAGSET_ID , nvl(ts.dc_engagement_id,-1),
                             nvl(t.IS_DELETED, 'F')  ,
                             nvl(ts.IS_DELETED, 'F') ,
                             ts.TAGSET_TYPE ,
                             ts.SCOPE
                        into  :proposed_tagset_id, :looked_up_tag_dc_eng, :tag_deleted,:tagset_deleted, :tagset_type, :tag_scope
                        from
                        CPS_DSCI_API.DC_TAGS t
                        join CPS_DSCI_API.DC_TAGSET ts on (ts.TAGSET_ID = t.TAGSET_ID)
                     where t.TAG_ID = :tag_id
                     and
                     (nvl(ts.dc_engagement_id,:target_dc_engagement) = :target_dc_engagement
                         OR
                     ts.SCOPE='Global')

                     ;

                when :proposed_action = 'unset' then
                    select NULL ,
                             NULL  ,
                             nvl(ts.IS_DELETED, 'F') ,
                             ts.TAGSET_TYPE ,
                             ts.SCOPE
                        into  :proposed_tagset_id, :tag_deleted,:tagset_deleted, :tagset_type, :tag_scope
                        from
                        CPS_DSCI_API.DC_TAGSET ts where ts.TAGSET_ID = :param_tagset_id;
                end;



            -- requestor info for validation
            select nvl(u.CISCO_CCO_ID,'-'),
                case
                    when u.USER_TITLE = 'ADMIN' then '1,2'
                    when u.USER_TITLE = 'CAM' then '1'
                    when u.USER_TITLE = 'IBA' then '2'     end  ,
                m.DC_ENGAGEMENT_ID,
                case when POSITION( :tagset_type IN
                    case
                    when u.USER_TITLE = 'ADMIN' then '1,2'
                    when u.USER_TITLE = 'CAM' then '1'
                    when u.USER_TITLE = 'IBA' then '2'     end ) > 0 then 'T' else 'F' end
            into :found_user_cco, :tag_access, :target_dc_engagement, :tag_set_compat
            from CPS_DSCI_API.dc_users u join  CPS_DSCI_API.dc_CAM_to_engagement m on (m.USER_ID=u.user_id)
            where u.CISCO_CCO_ID = :user_cco and m.DC_ENGAGEMENT_ID =:target_dc_engagement;

            -- test if valid requests
            case
                when  :found_user_cco != :user_cco  OR  :found_user_cco is  null OR  :found_user_cco ='-' THEN
                    --RETURN 'ERROR: USER NOT A MEMBER OF ENGAGEMENT: ' || :user_cco ;
                    RAISE EXCEPTION_1;


                when :tag_set_compat = 'F' THEN
                 --RETURN 'ERROR: USER not part of tag access ' || :tagset_type || 'tagset type '|| :tag_access || ':tag_set_compat'|| :tag_set_compat  || '%';
                 RAISE EXCEPTION_2;

                when  :tag_deleted = 'T' OR :tagset_deleted = 'T' THEN
                  --RETURN 'ERROR: TAGSET OR TAG DELETED TAGSET:' || :tagset_deleted  || ' TAG '|| :tag_deleted  ;
                   RAISE EXCEPTION_3;


            end;



        -- if not deleted tag or tag set
        -- and user hase access to teh type of tag (plus global unless we need to restrict it)
    case when :proposed_action = 'set' then
          MERGE INTO  IDENTIFIER(:tag_table)
            USING (
                -- make a table from the JSON
                with x as (
                        -- replace with instance_list
                    select parse_json(:invalue):instance   as instances
                ),allowed_tags as (
                    SELECT   distinct s2.value as INSTANCE_ID, :tag_id as proposed_tag_id, :proposed_tagset_id as proposed_tagset_id
                    FROM x
                    ,TABLE(FLATTEN(x.instances)) s2
                )
                select allowed_tags.INSTANCE_ID as b_INSTANCE_ID, allowed_tags.proposed_tag_id as b_proposed_tag_id, allowed_tags.proposed_tagset_id as b_proposed_tagset_id,
                :target_dc_engagement as b_ENGAGEMENT_ID, :user_cco as b_username
                from allowed_tags
            ) AS b
            ON INSTANCE_ID = b.b_INSTANCE_ID and TAGSET_ID= b.b_proposed_tagset_id  -- core update bc we have an instance and look to update since something is three in this ts
            -- tag exists just deleted or not exists
            WHEN MATCHED AND TAG_ID= b.b_proposed_tag_id and IS_DELETED = 'T' THEN  -- same tag.. sort of ignore it
                UPDATE SET update_by=b.b_username, UPDATE_DTM=current_timestamp, IS_DELETED = 'F'
            WHEN MATCHED AND TAG_ID= b.b_proposed_tag_id and IS_DELETED = 'F' THEN  -- same tag.. sort of ignore it
                UPDATE SET update_by=b.b_username, UPDATE_DTM=current_timestamp

            WHEN MATCHED AND  TAG_ID != b.b_proposed_tag_id  THEN  -- diff tag in same ts then update
                UPDATE SET TAG_ID= b.b_proposed_tag_id ,  update_by=b.b_username, UPDATE_DTM=current_timestamp, IS_DELETED = 'F'
              WHEN NOT MATCHED THEN -- well nothing for instance and tag set, then insert
                INSERT(INSTANCE_ID, TAGSET_ID, TAG_ID, dc_engagement_id,update_by,UPDATE_DTM)
                VALUES (b.b_INSTANCE_ID, b.b_proposed_tagset_id, b.b_proposed_tag_id,b.b_ENGAGEMENT_ID,b.b_username ,current_timestamp);


            -- log the set



        insert into CPS_DSCI_API.DC_TAG_LOGGING
            (DC_ENGAGEMENT_ID, TAG_ID, TAGSET_ID, COMMENT, JSON, LIST_OF_INSTANCES, USER_ACTION, COUNT_INSTANCES, CREATED_BY, CREATE_DTM)
            values (:target_dc_engagement,:tag_id,:proposed_tagset_id,:tagging_comments,:invalue,:instance_list,:proposed_action,:instance_cnt,:user_cco,
                    current_timestamp
                    );


        when :proposed_action = 'unset' then

    MERGE INTO IDENTIFIER(:tag_table)
            USING (
            with x as (
                 select parse_json(:invalue):instance as instances
             ),
                  allowed_tags as (
                      SELECT distinct s2.value as INSTANCE_ID, :param_tagset_id as proposed_tagset_id
                      FROM x
                         , TABLE (FLATTEN(x.instances)) s2
                  )
             select allowed_tags.INSTANCE_ID as b_INSTANCE_ID,
                    allowed_tags.proposed_tagset_id as b_proposed_tagset_id,
                    :target_dc_engagement as b_ENGAGEMENT_ID,
                    :user_cco             as b_username
             from allowed_tags
            ) AS b
            ON INSTANCE_ID = b.b_INSTANCE_ID and TAGSET_ID= b.b_proposed_tagset_id
                WHEN MATCHED AND :proposed_action = 'unset' THEN  -- same tag.. sort of ignore it
                UPDATE SET IS_DELETED = 'T' , update_by=b.b_username, UPDATE_DTM=current_timestamp;


        -- log the unset

        insert into CPS_DSCI_API.DC_TAG_LOGGING
            (DC_ENGAGEMENT_ID, TAG_ID, TAGSET_ID, COMMENT, JSON, LIST_OF_INSTANCES, USER_ACTION, COUNT_INSTANCES, CREATED_BY, CREATE_DTM)
            values (:target_dc_engagement,:tag_id,:param_tagset_id,:tagging_comments,:invalue,:instance_list,:proposed_action,:instance_cnt,:user_cco,
                    current_timestamp
                    );



        end;


        --really should return true or error and insert these into audit table
        RETURN OBJECT_CONSTRUCT('SQLID',SQLID,'rowcount',SQLROWCOUNT, 'invalue',:invalue,'found_user_cco',:found_user_cco,
        'tagset_type',:tagset_type,'tag_set_compat', :tag_set_compat,'tag_access',:tag_access,':target_dc_engagement;',:target_dc_engagement
        );

        EXCEPTION
         WHEN statement_error THEN
        RETURN OBJECT_CONSTRUCT('Error type', 'STATEMENT_ERROR',
                                'SQLCODE', sqlcode,
                                'SQLERRM', sqlerrm,
                                'SQLSTATE', sqlstate);

        end;


$$;

