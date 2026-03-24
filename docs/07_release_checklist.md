# Release Checklist

Use this checklist before publishing a new thesis-facing update.

## Code and Runtime

1. Confirm main runners still execute dry-run correctly.
2. If hierarchical logic changed, dry-run guarded hierarchical runner.
3. Ensure no accidental hardcoded output paths outside intended runtime folders.

## Evidence Integrity

1. Distinguish matrix definition from completed execution.
2. Update status counts with explicit numbers and date.
3. Label historical runs as context if fresh campaign is incomplete.
4. Ensure claimed results map to real completed summaries.

## Documentation

1. Update `README.md` and affected `docs/*.md` pages.
2. Keep thesis status consistent with `Refrence Material/Latex/extracted_latex/` chapters and generated tables.
3. Keep scope boundaries explicit (implemented vs deferred).

## Presentation Assets

1. Regenerate or update defense deck if thesis status changed.
2. Do not overwrite baseline proposal deck.
3. Keep generated slide source script alongside final pptx.

## Final Review

1. Read docs as a new reader and check for contradictory claims.
2. Confirm no document claims fresh campaign completion unless true.
3. Verify `git status` contains intentional changes only.

## Definition of Done

A release is ready when implementation claims, run status, docs, and presentation all tell the same story.
