-- Change detection for Trial Watch.
--
-- Input table: versions  (one row = one trial at one registered version)
-- Output: one row for every time a tracked field differs from the previous
-- version of the same trial.
--
-- How it works:
--   1. "paired" puts each version next to the version before it (LAG looks one
--      row back within the same trial, ordered by version number).
--   2. Each SELECT below checks one field: keep the row if old and new differ.
--      "IS NOT" is used instead of "<>" so that empty values compare correctly.
--   3. UNION ALL stacks the results of all fields into one list.
--
-- Run it: python run_change_detection.py   (writes changes.json)

WITH paired AS (
  SELECT
    nct, company, label, version, version_date, compare_url,
    overall_status,
    LAG(overall_status)          OVER w AS old_overall_status,
    enrollment,
    LAG(enrollment)              OVER w AS old_enrollment,
    enrollment_type,
    LAG(enrollment_type)         OVER w AS old_enrollment_type,
    primary_completion_date,
    LAG(primary_completion_date) OVER w AS old_primary_completion_date,
    primary_completion_type,
    LAG(primary_completion_type) OVER w AS old_primary_completion_type,
    study_completion_date,
    LAG(study_completion_date)   OVER w AS old_study_completion_date,
    study_completion_type,
    LAG(study_completion_type)   OVER w AS old_study_completion_type
  FROM versions
  WINDOW w AS (PARTITION BY nct ORDER BY version)
),
changes AS (
  SELECT nct, company, label, version, version_date, compare_url,
         'overall_status' AS field,
         old_overall_status AS old_value, overall_status AS new_value
  FROM paired WHERE version > 1 AND overall_status IS NOT old_overall_status
  UNION ALL
  SELECT nct, company, label, version, version_date, compare_url,
         'enrollment',
         CAST(old_enrollment AS TEXT), CAST(enrollment AS TEXT)
  FROM paired WHERE version > 1 AND enrollment IS NOT old_enrollment
  UNION ALL
  SELECT nct, company, label, version, version_date, compare_url,
         'enrollment_type',
         old_enrollment_type, enrollment_type
  FROM paired WHERE version > 1 AND enrollment_type IS NOT old_enrollment_type
  UNION ALL
  SELECT nct, company, label, version, version_date, compare_url,
         'primary_completion_date',
         old_primary_completion_date, primary_completion_date
  FROM paired WHERE version > 1 AND primary_completion_date IS NOT old_primary_completion_date
  UNION ALL
  SELECT nct, company, label, version, version_date, compare_url,
         'primary_completion_type',
         old_primary_completion_type, primary_completion_type
  FROM paired WHERE version > 1 AND primary_completion_type IS NOT old_primary_completion_type
  UNION ALL
  SELECT nct, company, label, version, version_date, compare_url,
         'study_completion_date',
         old_study_completion_date, study_completion_date
  FROM paired WHERE version > 1 AND study_completion_date IS NOT old_study_completion_date
  UNION ALL
  SELECT nct, company, label, version, version_date, compare_url,
         'study_completion_type',
         old_study_completion_type, study_completion_type
  FROM paired WHERE version > 1 AND study_completion_type IS NOT old_study_completion_type
)
SELECT * FROM changes
ORDER BY version_date DESC, nct, field;
