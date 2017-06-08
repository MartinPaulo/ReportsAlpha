CREATE TABLE cloud_allocated
  -- the cumulative record of capacity allocated by faculty
(
  date TEXT PRIMARY KEY,  -- the day for which the capacity totals were calculated
  FoA INTEGER,
  VAS INTEGER,
  FBE INTEGER,
  MSE INTEGER,
  MGSE INTEGER,
  MDHS INTEGER,
  FoS INTEGER,
  ABP INTEGER,
  MLS INTEGER,
  VCAMCM INTEGER,
  Other INTEGER,
  Unknown INTEGER
);

CREATE TABLE cloud_used
  -- the amount used on a given day by faculty
(
  date TEXT PRIMARY KEY, -- the for which the used totals were calculated
  FoA INTEGER,
  VAS INTEGER,
  FBE INTEGER,
  MSE INTEGER,
  MGSE INTEGER,
  MDHS INTEGER,
  FoS INTEGER,
  ABP INTEGER,
  MLS INTEGER,
  VCAMCM INTEGER,
  Other INTEGER,
  Unknown INTEGER
);

CREATE TABLE cloud_active_users
  -- a count of the users who are running in which data center on the given day
(
  date TEXT PRIMARY KEY,  -- the day for which the totals were calculated.
  at_uom_only INTEGER NOT NULL, -- UoM project users running only in UoM data centers
  elsewhere_only INTEGER NOT NULL, -- UoM project users running only outside of UoM data centers
  in_both INTEGER NOT NULL, -- UoM project users running both inside and outside UoM data centers
  others_at_uom INTEGER NOT NULL  -- non UoM project users running in UoM data centers
);

CREATE TABLE cloud_top_twenty
  -- the top twenty UoM projects on a given date
(
  date TEXT NOT NULL, -- the given date
  project_id VARCHAR(32) NOT NULL,  -- the OpenStack project ID
  vcpus INTEGER NOT NULL, -- the total count on the given date
  tenant_name VARCHAR(64) NOT NULL, -- the display name for the project
  PRIMARY KEY ( date, project_id)
);