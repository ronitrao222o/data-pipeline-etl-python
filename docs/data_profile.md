# Data Profile Report

## Purpose
The profile report gives a fast observability snapshot of the trusted records produced by the pipeline.
It helps reviewers understand data shape, completeness, and cardinality without opening the database.

## Default Output
```text
artifacts/data_profile_report.json
```

Production profile runs write to:

```text
artifacts/prod/data_profile_report.json
```

## Metrics
Each column profile includes:

- inferred type
- null count
- null rate
- distinct value count
- minimum value
- maximum value

## Runtime Behavior
The profile is generated after transformation, so it describes cleaned and enriched records.
It is still written for dry runs and failed quality-gate runs because those modes are useful for validation and debugging.
