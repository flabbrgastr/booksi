# Pipeline as composable function

The booksi data pipeline (prune → parse → dedupe → delta → write) is extracted from booksi.py into a `run_pipeline()` function in `booksi/pipeline.py`. This makes the pipeline testable, composable, and separable from CLI concerns.

The decision was made during an architecture review on 2026-07-27. The existing `booksi/` package modules (parse, normalize, storage, render) were already well-factored — they just needed a composer.