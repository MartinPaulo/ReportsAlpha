-- ----------------------------------------------------------------------------
-- 0: Some of the queries required in setting up the database
-- ----------------------------------------------------------------------------

SELECT 'ALTER TABLE ' || schemaname || '.' || tablename || ' OWNER TO vicnode;'
FROM pg_tables
WHERE NOT schemaname IN ('pg_catalog', 'information_schema')
ORDER BY schemaname, tablename;

SELECT 'ALTER SEQUENCE ' || sequence_schema || '.' || sequence_name ||
       ' OWNER TO vicnode;'
FROM information_schema.sequences
WHERE NOT sequence_schema IN ('pg_catalog', 'information_schema')
ORDER BY sequence_schema, sequence_name;

SELECT
  'ALTER VIEW ' || table_schema || '.' || table_name || ' OWNER TO vicnode;'
FROM information_schema.views
WHERE NOT table_schema IN ('pg_catalog', 'information_schema')
ORDER BY table_schema, table_name;

-- ----------------------------------------------------------------------------
-- 1: Storage allocated by type
-- ----------------------------------------------------------------------------

-- so to get the names and capacities for the storage products
SELECT
  value,
  product_name_id,
  capacity,
  applications_storageproduct.id AS storage_product_id
FROM applications_storageproduct
  LEFT JOIN labels_label
    ON labels_label.id = applications_storageproduct.product_name_id;

-- from the above we are interested in the following:
--
-- value										product_name_id		capacity	storage_product_id
-- Computational.Melbourne	72								288.00		1
-- Market.Melbourne					73								1482.00		4
-- Vault.Melbourne.Object		74								1263.15		10
--
-- But what about:
--
-- DO-NOT-USE.NSP.Computational.Melbourne	77	0.00	7
-- DO-NOT-USE.NSP.Market.Melbourne	78	0.00	8
-- DO-NOT-USE.X-Physics.Melbourne	79	0.00	12
-- DO-NOT-USE.Market.Melbourne.Disk	80	201.00	5
-- DO-NOT-USE.Market.Melbourne.Disk	80	201.00	9
--
SELECT COUNT(*)
FROM applications_allocation
WHERE storage_product_id
      IN (7, 8, 12, 5, 9);

-- returns 0, so no need to worry.

SELECT COUNT(*)
FROM applications_allocation
WHERE storage_product_id
      IN (1, 4, 10);

-- returns 128: 22 are in 1, 62 are in 4, and 44 in 10.

-- we'd think that we'd want to know the size: but some sizes are negative?

-- "The negative number are the storage that have been given back by the users
-- for for reduction purpose.

-- E.g., PeterMac could put in an initial storage request of 400000.00 but
-- then realised that they didn’t really need that much so they would put in a
-- reduction request of 150000 (hence the 1150000.00 entry) so PeterMac’s
-- final total will be 250000.00 (i.e. 400000.00 - 150000.00). There should be
-- always two or more request of the same collection and the final total of
-- storage used will be the sum of all the entries added together.

-- It’s because VicNode Office needs to maintain a history/record of all the
-- requests (i.e. increase or reduction). Hope that makes sense?"

-- So the history can be seen by something like:

SELECT
  collection_id,
  storage_product_id,
  size,
  allocation.creation_date,
  allocation.last_modified,
  name
FROM applications_allocation AS allocation
  LEFT JOIN applications_project
    ON collection_id = applications_project.id
WHERE storage_product_id IN (1, 4, 10)
ORDER BY collection_id, storage_product_id, creation_date NULLS FIRST,
  last_modified NULLS FIRST;

-- So a simple sum on each day will show the overall size allocated.

-- Now we want to know the allocated trend over time.
-- Allocations have a created date and a modified date.
-- And sadly some entries have one or both fields empty.

-- Further diving shows that 17 rows have different dates, 50 have identical
-- 61 have no created, and 30 have no last modified.
-- So we can probably use last modified to show the state on a given date,
-- with the null's indicating entries that were created before the dates were
-- introduced.
-- The earliest last modified is 2014-11-14

-- to do date ranges:
SELECT *
FROM table
WHERE _date >= '2013-05-03'
      AND _date < ('2013-05-03' :: DATE + '1 day' :: INTERVAL);

-- to do substitutions for null dates:
SELECT COALESCE(creation_date, to_date('05 Dec 2000', 'DD Mon YYYY')) AS date
FROM applications_allocation
WHERE storage_product_id IN (1, 4, 10)
      AND creation_date IS NULL;

-- so to select the amount allocate for a product on a given day:
SELECT SUM(size) AS total_to_date
FROM applications_allocation
WHERE storage_product_id = 1
      AND DATE '2015-05-15' <= last_modified
      AND last_modified < (DATE '2015-05-15' :: DATE + '1 day' :: INTERVAL);
-- vs: ? AND extraction_date < (DATE '2016-02-06' + INTERVAL '1' DAY)

-- to select the total amount allocated for a product up to a given day:
SELECT sum(size) AS computational_size
FROM applications_allocation
WHERE storage_product_id = 1
      --       AND last_modified >= '2015-05-15'
      AND last_modified < ('2015-05-15' :: DATE + '1 day' :: INTERVAL);

-- and the following gives allows us to wrap the results up into one query
SELECT *
FROM
  (SELECT sum(size) AS computational_size
   FROM applications_allocation
   WHERE storage_product_id = 1
         AND last_modified < ('2015-05-15' :: DATE + '1 day' :: INTERVAL)) a
  CROSS JOIN
  (SELECT sum(size) AS market_size
   FROM applications_allocation
   WHERE storage_product_id = 4
         AND last_modified < ('2015-05-15' :: DATE + '1 day' :: INTERVAL)) b
  CROSS JOIN
  (SELECT sum(size) AS vault_size
   FROM applications_allocation
   WHERE storage_product_id = 10
         AND last_modified < ('2015-05-15' :: DATE + '1 day' :: INTERVAL)) c;

-- 84400	258400	697000

-- Ps: technically same as;

SELECT
  sum(size),
  CASE
  WHEN storage_product_id = 1
    THEN 'computational'
  WHEN storage_product_id = 4
    THEN 'market'
  ELSE 'vault' END AS product
FROM applications_allocation
WHERE storage_product_id IN (1, 4, 10)
      AND applications_allocation.last_modified <
          ('2015-05-15' :: DATE + '1 day' :: INTERVAL)
GROUP BY storage_product_id;

-- but there's a sad issue with the above
-- not all of UoM (institution_id = 2)'s storage product is used by UoM only

SELECT
  size AS computational_size,
  storage_product_id,
  institution_id,
  short_name
FROM applications_allocation
  LEFT JOIN applications_request
    ON applications_allocation.application_id = applications_request.id
  LEFT JOIN contacts_organisation
    ON applications_request.institution_id = contacts_organisation.id
WHERE storage_product_id = 10;

-- for example, reveals other institutions using storage product 10. 1 and 4
-- are even more exiting...

-- So Andy says "Show the grand total allocated here"

-- So the following that breaks it down by UoM only is not needed...

SELECT *
FROM
  (SELECT SUM(size) AS computational_size
   FROM applications_allocation
     LEFT JOIN applications_request
       ON applications_allocation.application_id = applications_request.id
   WHERE storage_product_id = 1
         AND institution_id = 2
         AND applications_allocation.last_modified <
             ('2015-05-15' :: DATE + '1 day' :: INTERVAL)) a
  CROSS JOIN
  (SELECT sum(size) AS market_size
   FROM applications_allocation
     LEFT JOIN applications_request
       ON applications_allocation.application_id = applications_request.id
   WHERE storage_product_id = 4
         AND institution_id = 2
         AND applications_allocation.last_modified <
             ('2015-05-15' :: DATE + '1 day' :: INTERVAL)) b
  CROSS JOIN
  (SELECT sum(size) AS vault_size
   FROM applications_allocation
     LEFT JOIN applications_request
       ON applications_allocation.application_id = applications_request.id
   WHERE storage_product_id = 10
         AND institution_id = 2
         AND applications_allocation.last_modified <
             ('2015-05-15' :: DATE + '1 day' :: INTERVAL)) c;

-- restricts it to unimelb only and gives
-- 85000	258000	633000


-- ----------------------------------------------------------------------------
-- 2: Storage allocated by faculty
-- ----------------------------------------------------------------------------

-- But here include the non UoM users as a faculty named "external"

-- So to get the storage allocated by faculty...
-- We have  a table with the faculties:
SELECT
  id,
  name
FROM applications_suborganization;

-- To find who references this:
SELECT
  (SELECT r.relname
   FROM pg_class r
   WHERE r.oid = c.conrelid)                                   AS table,
  (SELECT array_agg(attname)
   FROM pg_attribute
   WHERE attrelid = c.conrelid AND ARRAY [attnum] <@ c.conkey) AS col,
  (SELECT r.relname
   FROM pg_class r
   WHERE r.oid = c.confrelid)                                  AS ftable
FROM pg_constraint c
WHERE c.confrelid = (SELECT oid
                     FROM pg_class
                     WHERE relname = 'applications_suborganization');

-- applications_request	{institution_faculty_id}	applications_suborganization

-- So our attention turns to the applications_request table.

-- But first

SELECT
  id,
  short_name
FROM contacts_organisation;

-- shows that melbourne has an ID of 2 (what about Peter Mac etc. Are they ours?

-- also

SELECT
  institution_id,
  institution_faculty_id
FROM applications_request
WHERE institution_faculty_id IS NOT NULL;

-- shows that several non UoM have faculties allocated to them?

-- applications_allocation	{application_id}	applications_request
-- so we have allocation -> request -> faculty
-- Thus to break this down by faculty for storage type for UOM we need
-- for each storage type:

SELECT
  count(applications_allocation.id) AS found,
  sum(size)                         AS computational_size,
  name
FROM applications_allocation
  LEFT JOIN applications_request
    ON applications_allocation.application_id = applications_request.id
  LEFT JOIN applications_suborganization
    ON applications_request.institution_faculty_id =
       applications_suborganization.id
WHERE storage_product_id = 10
      AND institution_id = 2
--      AND applications_allocation.last_modified < ('2015-05-15' :: DATE + '1 day' :: INTERVAL)
GROUP BY name;

-- shows that we still have some projects not allocated


-- To include the 'External ones'
-- This will move all the non allocated projects to 'External'

SELECT
  count(applications_allocation.id) AS found,
  sum(size)                         AS computational_size,
  CASE WHEN name IS NULL
    THEN 'External'
  ELSE name END
FROM applications_allocation
  LEFT JOIN applications_request
    ON applications_allocation.application_id = applications_request.id
  LEFT JOIN applications_suborganization
    ON applications_request.institution_faculty_id =
       applications_suborganization.id
WHERE storage_product_id = 10
--      AND applications_allocation.last_modified < ('2015-05-15' :: DATE + '1 day' :: INTERVAL)
GROUP BY name;

-- or more portably

SELECT
  count(applications_allocation.id)            AS found,
  sum(size)                                    AS computational_size,
  coalesce(applications_suborganization.id, 0) AS suborganization_id,
  coalesce(nullif(name, ''), 'External') -- handles nulls and empty strings
FROM applications_allocation
  LEFT JOIN applications_request
    ON applications_allocation.application_id = applications_request.id
  LEFT JOIN applications_suborganization
    ON applications_request.institution_faculty_id =
       applications_suborganization.id
WHERE storage_product_id IN (1, 4, 10)
--      AND applications_allocation.last_modified < ('2015-05-15' :: DATE + '1 day' :: INTERVAL)
GROUP BY suborganization_id, name;

-- But this groups the external orgs with the unknown...

SELECT
  applications_allocation.id                   AS found,
  size                                         AS computational_size,
  institution_id,
  coalesce(applications_suborganization.id, 0) AS suborganization_id,
  CASE
  WHEN institution_id != 2
    THEN 'External'
  WHEN applications_suborganization.id = 1
    THEN 'ABP'
  WHEN applications_suborganization.id = 2
    THEN 'FBE'
  WHEN applications_suborganization.id = 3
    THEN 'FoA'
  WHEN applications_suborganization.id = 4
    THEN 'MGSE'
  WHEN applications_suborganization.id = 5
    THEN 'MSE'
  WHEN applications_suborganization.id = 6
    THEN 'MLS'
  WHEN applications_suborganization.id = 7
    THEN 'MDHS'
  WHEN applications_suborganization.id = 8
    THEN 'FoS'
  WHEN applications_suborganization.id = 9
    THEN 'VAS'
  WHEN applications_suborganization.id = 10
    THEN 'VCAMCM'
  WHEN applications_suborganization.id = 11
    THEN 'US'
  ELSE 'Unknown' END                           AS faculty,
  name
FROM applications_allocation
  LEFT JOIN applications_request
    ON applications_allocation.application_id = applications_request.id
  LEFT JOIN applications_suborganization
    ON applications_request.institution_faculty_id =
       applications_suborganization.id
WHERE storage_product_id IN (1, 4, 10);

-- breaks it out

-- and
SELECT
  sum(size)          AS used,
  CASE
  WHEN institution_id != 2
    THEN 'external'
  WHEN applications_suborganization.id = 1
    THEN 'ABP'
  WHEN applications_suborganization.id = 2
    THEN 'FBE'
  WHEN applications_suborganization.id = 3
    THEN 'FoA'
  WHEN applications_suborganization.id = 4
    THEN 'MGSE'
  WHEN applications_suborganization.id = 5
    THEN 'MSE'
  WHEN applications_suborganization.id = 6
    THEN 'MLS'
  WHEN applications_suborganization.id = 7
    THEN 'MDHS'
  WHEN applications_suborganization.id = 8
    THEN 'FoS'
  WHEN applications_suborganization.id = 9
    THEN 'VAS'
  WHEN applications_suborganization.id = 10
    THEN 'VCAMCM'
  WHEN applications_suborganization.id = 11
    THEN 'services'
  ELSE 'unknown' END AS faculty
FROM applications_allocation
  LEFT JOIN applications_request
    ON applications_allocation.application_id = applications_request.id
  LEFT JOIN applications_suborganization
    ON applications_request.institution_faculty_id =
       applications_suborganization.id
WHERE storage_product_id IN (1, 4, 10)
      AND applications_allocation.last_modified <
          ('2016-08-16' :: DATE + '1 day' :: INTERVAL)
GROUP BY faculty;

-- gives us the grand totals...

-- But we also want it broken down by storage product


-- ----------------------------------------------------------------------------
-- 3: Storage capacity by type
-- ----------------------------------------------------------------------------

-- so to get the names and capacities for the storage products
SELECT
  value                          AS product_name,
  product_name_id,
  capacity,
  applications_storageproduct.id AS storage_product_id
FROM applications_storageproduct
  LEFT JOIN labels_label
    ON labels_label.id = applications_storageproduct.product_name_id
WHERE applications_storageproduct.id IN (1, 4, 10);

-- There is no history kept: so here we become the guardian of the history
-- and the first record we can't rebuild over time!
-- But surely there is a historical record we can add manually?

-- ----------------------------------------------------------------------------
-- 4: Storage headroom unallocated by type
-- ----------------------------------------------------------------------------

-- We simply run a join between the table resultant from 1 and the table
-- resultant in 3 and show the differences in the grand total

-- ----------------------------------------------------------------------------
-- 5: Storage headroom unused by type
-- ----------------------------------------------------------------------------

-- We want to the difference between what has been allocated (? notes say
-- capacity? ) and what is actually used.

-- If what is allocated:

SELECT current_size
FROM applications_collectionprofile;

-- pointless, is null

SELECT estimated_final_size
FROM applications_collectionprofile;

-- has some null fields. But then

SELECT
  collection_id,
  allocated_capacity,
  used_capacity,
  allocated_capacity - used_capacity AS headroom
FROM applications_ingest
WHERE storage_product_id IN (1, 4, 10)
ORDER BY collection_id;

-- shows the history over time (last_modified date) There are over 67000
-- records...
-- is the 'active' setting relevant?

-- so to get the amount per day...
SELECT
  collection_id,
  allocated_capacity,
  used_capacity,
  allocated_capacity - used_capacity AS headroom,
  extraction_date,
  storage_product_id
FROM applications_ingest
WHERE storage_product_id IN (1, 4, 10)
      AND DATE '2016-02-06' <= extraction_date
      AND extraction_date < (DATE '2016-02-06' + INTERVAL '1' DAY)
ORDER BY collection_id, storage_product_id;

-- But that excludes prior runs that might not be included?
-- As there are products that are not updated ingest
-- So to pick them up
SELECT
  collection_id,
  allocated_capacity,
  used_capacity,
  allocated_capacity - used_capacity AS headroom,
  extraction_date,
  storage_product_id
FROM applications_ingest AS ingest
WHERE storage_product_id IN (1, 4, 10)
      -- and this is the last record
      AND extraction_date =
          (SELECT MAX(extraction_date)
           FROM applications_ingest t2
           WHERE t2.collection_id = ingest.collection_id
                 AND t2.storage_product_id = ingest.storage_product_id
                 AND
                 t2.extraction_date < (DATE '2016-02-06' + INTERVAL '1' DAY)
          )
ORDER BY collection_id, storage_product_id;

-- to collapse into per product:

SELECT
  sum(allocated_capacity - used_capacity) AS headroom,
  storage_product_id
FROM applications_ingest AS ingest
WHERE storage_product_id IN (1, 4, 10)
      -- and this is the last record
      AND extraction_date =
          (SELECT MAX(extraction_date)
           FROM applications_ingest t2
           WHERE t2.collection_id = ingest.collection_id
                 AND t2.storage_product_id = ingest.storage_product_id
                 AND
                 t2.extraction_date < (DATE '2016-02-06' + INTERVAL '1' DAY)
          )
GROUP BY storage_product_id;

-- But we find that the allocated capacity in this table does not
-- necessarily match the allocation in the allocation table
-- Linh says that we return the amount that has been set aside in the storage
-- for the project. So the figure shown in the ingest is the physical amount
-- they have had made available to their project.

SELECT sum(size) AS computational_size
FROM applications_allocation
WHERE storage_product_id = 4
      AND collection_id = 1;

-- ----------------------------------------------------------------------------
-- ** 6: Storage headroom by faculty
-- ----------------------------------------------------------------------------
-- This is simply the above by faculty

SELECT
  collection_id,
  allocated_capacity - used_capacity AS headroom,
  extraction_date,
  storage_product_id
FROM applications_ingest AS ingest
WHERE storage_product_id IN (1, 4, 10)
      -- and this is the last record
      AND extraction_date =
          (SELECT MAX(extraction_date)
           FROM applications_ingest t2
           WHERE t2.collection_id = ingest.collection_id
                 AND t2.storage_product_id = ingest.storage_product_id
                 AND
                 t2.extraction_date < (DATE '2016-02-06' + INTERVAL '1' DAY)
          )
ORDER BY collection_id, storage_product_id;

-- tricky:
-- ingest.collection id -> project
-- request.project id -> project
-- request.institution faculty -> suborganization

SELECT
  sum(allocated_capacity - used_capacity) AS headroom,
  coalesce(nullif(name, ''),
           'External')                    AS name -- handles nulls and empty strings
FROM applications_ingest ingest
  LEFT JOIN (
              SELECT
                request.id,
                coalesce(nullif(name, ''),
                         'Unknown') AS name -- handles nulls and empty strings
              FROM applications_request request
                LEFT JOIN applications_suborganization suborganization
                  ON institution_faculty_id = suborganization.id
              WHERE
                request.institution_id = '2'
              ORDER BY id
            ) AS names ON names.id = ingest.collection_id
WHERE storage_product_id IN (1, 4, 10)
      -- and this is the last record
      AND extraction_date =
          (SELECT MAX(extraction_date)
           FROM applications_ingest t2
           WHERE t2.collection_id = ingest.collection_id
                 AND t2.storage_product_id = ingest.storage_product_id
                 AND
                 t2.extraction_date < (DATE '2016-02-06' + INTERVAL '1' DAY)
          )
GROUP BY name;

-- ----------------------------------------------------------------------------
-- 7: Storage used by type
-- ----------------------------------------------------------------------------

-- This must be calculated by looking at the total ingested.
SELECT *
FROM applications_ingest
WHERE collection_id = 2
ORDER BY storage_product_id;

-- shows that an ingest reports what is run: so we actually don't want to sum
-- all the records, as this would give us multiple duplicate values.
-- so we need to do a subquery to get the last row before the extraction date

-- So to select the last ingests on or before a given date, say '2016-02-06'
SELECT
  collection_id,
  extraction_date,
  used_capacity,
  storage_product_id
FROM applications_ingest t1
WHERE storage_product_id IN (1, 4, 10)
      -- and this is the last record
      AND extraction_date =
          (SELECT MAX(extraction_date)
           FROM applications_ingest t2
           WHERE t2.collection_id = t1.collection_id
                 AND t2.storage_product_id = t1.storage_product_id
                 AND
                 t2.extraction_date < (DATE '2016-02-06' + INTERVAL '1' DAY)
          )
ORDER BY collection_id, storage_product_id;

-- a slow running query :(

-- and the sum used on or before that given date, say '2016-02-06'
SELECT
  sum(used_capacity),
  storage_product_id
FROM applications_ingest t1
WHERE storage_product_id IN (1, 4, 10)
      -- and this is the last record
      AND extraction_date =
          (SELECT MAX(extraction_date)
           FROM applications_ingest t2
           WHERE t2.collection_id = t1.collection_id
                 AND t2.storage_product_id = t1.storage_product_id
                 AND
                 t2.extraction_date < (DATE '2016-02-06' + INTERVAL '1' DAY)
          )
GROUP BY storage_product_id;

-- or:
SELECT
  sum(used_capacity),
  CASE
  WHEN storage_product_id = 1
    THEN 'computational'
  WHEN storage_product_id = 4
    THEN 'market'
  ELSE 'vault' END AS product
FROM applications_ingest t1
WHERE storage_product_id IN (1, 4, 10)
      -- and this is the last record
      AND extraction_date =
          (SELECT MAX(extraction_date)
           FROM applications_ingest t2
           WHERE t2.collection_id = t1.collection_id
                 AND t2.storage_product_id = t1.storage_product_id
                 AND
                 t2.extraction_date < (DATE '2016-02-06' + INTERVAL '1' DAY)
          )
GROUP BY product;

-- ----------------------------------------------------------------------------
-- 8: Storage used by faculty
-- ----------------------------------------------------------------------------

-- We need to do the same complex query against the ingested data, but this
-- time we need to bundle it into by faculties.
--
-- tricky:
-- ingest.collection id -> project
-- request.project id -> project
-- request.institution faculty -> suborganization

-- following gives faculty names for unimelb projects.
SELECT
  t1.id,
  coalesce(nullif(name, ''), 'Unknown') -- handles nulls and empty strings
FROM applications_request t1
  LEFT JOIN applications_suborganization t2
    ON institution_faculty_id = t2.id
WHERE
  t1.institution_id = '2'
ORDER BY id;

-- So the following gives the names (and takes even longer to run)
-- But nicely, still the same number of rows as previous
SELECT
  collection_id        AS project_id,
  extraction_date,
  used_capacity,
  storage_product_id,
  coalesce(nullif(name, ''),
           'External') AS name -- handles nulls and empty strings
FROM applications_ingest ingest
  LEFT JOIN (
              SELECT
                request.id,
                coalesce(nullif(name, ''),
                         'Unknown') AS name -- handles nulls and empty strings
              FROM applications_request request
                LEFT JOIN applications_suborganization suborganization
                  ON institution_faculty_id = suborganization.id
              WHERE
                request.institution_id = '2'
              ORDER BY id
            ) AS names ON names.id = ingest.collection_id
WHERE storage_product_id IN (1, 4, 10)
      -- and this is the last record
      AND extraction_date =
          (SELECT MAX(extraction_date)
           FROM applications_ingest t2
           WHERE t2.collection_id = ingest.collection_id
                 AND t2.storage_product_id = ingest.storage_product_id
                 AND
                 t2.extraction_date < (DATE '2016-02-06' + INTERVAL '1' DAY)
          )
ORDER BY collection_id, storage_product_id, name;

SELECT
  sum(used_capacity),
  coalesce(nullif(name, ''),
           'External') AS name -- handles nulls and empty strings
FROM applications_ingest ingest
  LEFT JOIN (
              SELECT
                request.id,
                coalesce(nullif(name, ''),
                         'Unknown') AS name -- handles nulls and empty strings
              FROM applications_request request
                LEFT JOIN applications_suborganization suborganization
                  ON institution_faculty_id = suborganization.id
              WHERE
                request.institution_id = '2'
              ORDER BY id
            ) AS names ON names.id = ingest.collection_id
WHERE storage_product_id IN (1, 4, 10)
      -- and this is the last record
      AND extraction_date =
          (SELECT MAX(extraction_date)
           FROM applications_ingest t2
           WHERE t2.collection_id = ingest.collection_id
                 AND t2.storage_product_id = ingest.storage_product_id
                 AND
                 t2.extraction_date < (DATE '2016-02-06' + INTERVAL '1' DAY)
          )
GROUP BY name;