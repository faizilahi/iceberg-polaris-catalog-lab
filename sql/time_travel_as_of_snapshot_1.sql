-- Iceberg time travel (engine dialect varies)
-- Spark:  SELECT * FROM hf.census_fact VERSION AS OF 1
-- DuckDB stand-in: read parquet paths listed in snapshot 1 manifest only

SELECT
    census_date,
    facility_id,
    census_count
FROM census_fact FOR VERSION AS OF 1
ORDER BY census_date, facility_id;
