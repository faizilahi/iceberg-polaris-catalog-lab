-- Contrast current snapshot vs pinned historical snapshot
SELECT COUNT(*) AS rows_now, SUM(census_count) AS census_sum_now
FROM hf.census_fact;

SELECT COUNT(*) AS rows_as_of_1, SUM(census_count) AS census_sum_as_of_1
FROM hf.census_fact VERSION AS OF 1;
