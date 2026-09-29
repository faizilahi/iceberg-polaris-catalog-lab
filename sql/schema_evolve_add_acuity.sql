-- Metadata-only schema evolve: add acuity_band after snapshot 2
-- Old snapshots remain readable; new writes populate the column.

ALTER TABLE hf.census_fact
ADD COLUMN acuity_band VARCHAR COMMENT 'HIGH|MED|LOW — added in schema-id 2';
