-- ----------------------------------------------------------------------------
-- 0: Some of the queries required in setting up the database
-- ----------------------------------------------------------------------------

SELECT 'ALTER TABLE '|| schemaname || '.' || tablename ||' OWNER TO vicnode;'
FROM pg_tables WHERE NOT schemaname IN ('pg_catalog', 'information_schema')
ORDER BY schemaname, tablename;

SELECT 'ALTER SEQUENCE '|| sequence_schema || '.' || sequence_name ||' OWNER TO vicnode;'
FROM information_schema.sequences WHERE NOT sequence_schema IN ('pg_catalog', 'information_schema')
ORDER BY sequence_schema, sequence_name;

SELECT 'ALTER VIEW '|| table_schema || '.' || table_name ||' OWNER TO vicnode;'
FROM information_schema.views WHERE NOT table_schema IN ('pg_catalog', 'information_schema')
ORDER BY table_schema, table_name;

-- ----------------------------------------------------------------------------
-- 1: Storage Allocated by Type
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
      AND last_modified >= '2015-05-15'
      AND last_modified < ('2015-05-15' :: DATE + '1 day' :: INTERVAL);

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
         AND applications_allocation.last_modified < ('2015-05-15' :: DATE + '1 day' :: INTERVAL)) a
  CROSS JOIN
  (SELECT sum(size) AS market_size
   FROM applications_allocation
     LEFT JOIN applications_request
       ON applications_allocation.application_id = applications_request.id
   WHERE storage_product_id = 4
         AND institution_id = 2
         AND applications_allocation.last_modified < ('2015-05-15' :: DATE + '1 day' :: INTERVAL)) b
  CROSS JOIN
  (SELECT sum(size) AS vault_size
   FROM applications_allocation
     LEFT JOIN applications_request
       ON applications_allocation.application_id = applications_request.id
   WHERE storage_product_id = 10
         AND institution_id = 2
         AND applications_allocation.last_modified < ('2015-05-15' :: DATE + '1 day' :: INTERVAL)) c;

-- restricts it to unimelb only and gives
-- 85000	258000	633000


-- ----------------------------------------------------------------------------
-- Storage allocated by faculty
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

-- shows that Monash have a faculty of science allocated to them?

-- applications_allocation	{application_id}	applications_request
-- so we have allocation -> request -> faculty
-- Thus to break this down by faculty for storage type for UOM we need
-- for each storage type:

SELECT
  sum(size) AS computational_size,
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
GROUP BY name
;


