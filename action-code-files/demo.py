from sqllineage.runner import LineageRunner

sql = """
WITH main AS (
    SELECT
        announce.ID AS ID,
        TITLE,
        SUBTITLE,
        BODY,
        CATEGORY,
        PRIORITY,
        announce.CREATE_DTM as CREATE_DTM,
        PUSH_DATE,
        EXPIRATION_DATE,
        AUDIENCE,
        ARRAY_AGG(
            OBJECT_CONSTRUCT(
                'id', link.id,
                'name', link.name,
                'href', link.href
            )
        ) AS LINKS,
        FALSE AS IS_DISMISSED_BY_USER
    FROM DC_ANNOUNCEMENTS announce
    LEFT JOIN DC_ANNOUNCEMENT_LINK link 
        ON (announce.ID = link.ANNOUNCEMENT_ID AND link.IS_DELETED = 'F')
    WHERE announce.IS_DELETED = 'F'
      AND EXPIRATION_DATE > CURRENT_TIMESTAMP
    GROUP BY announce.ID, TITLE, SUBTITLE, BODY, CATEGORY, PRIORITY, announce.CREATE_DTM, PUSH_DATE, EXPIRATION_DATE, AUDIENCE
    ORDER BY PRIORITY, announce.CREATE_DTM DESC
)

SELECT
    ID,
    TITLE,
    SUBTITLE,
    BODY,
    CATEGORY,
    PRIORITY,
    CREATE_DTM,
    PUSH_DATE,
    EXPIRATION_DATE,
    AUDIENCE,
    IS_DISMISSED_BY_USER,
    FILTER(main.links, l -> l:id IS NOT NULL) AS LINKS
FROM main
LIMIT :limit;
"""

# Run lineage analysis
runner = LineageRunner(sql)

print(" Source Tables:")
for t in runner.source_tables:
    print("  -", t)

print("\n Target Tables:")
for t in runner.target_tables:
    print("  -", t)

print("\nColumn Lineage:")
for col in runner.get_column_lineage():
    print(f"  {col.target}  ←  {col.source}")


