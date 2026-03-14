# Release Checklist

## Goal

Use this checklist before pushing a public repo update that changes experiment code, reporting logic, or docs.

## Code And Runtime

1. Confirm the cleaned root still contains the canonical runners.
2. Run at least one dry-run command for the main matrix.
3. If hierarchical code changed, run a dry-run for `run_hierarchical_guarded_parallel.py`.
4. Confirm no new local output paths were hardcoded outside `runs/` or `wandb/`.

## Artifacts

1. Do not commit raw `wandb/` output.
2. Do not commit raw `runs/` outputs except intentional placeholders.
3. Keep only lightweight static docs assets under `docs/assets/`.
4. If a model is worth preserving, promote it outside raw run folders first.

## Documentation

1. Update the relevant page under `docs/`.
2. Keep image links relative and GitHub-renderable.
3. Keep command examples aligned with the current root layout.
4. Keep scope statements honest when results are based on archived data.

## Final Review

1. Read `docs/README.md` as if you were a new maintainer.
2. Confirm the root `README.md` points to `docs/`.
3. Confirm the repo no longer depends on archived folders for basic understanding.
4. Check `git status` and make sure the diff looks intentional.

## Definition Of Done

The repo is ready to push when:

- the root tells a clean runtime story
- `docs/` explains setup, usage, reporting, and artifact management
- generated results are treated as outputs, not as permanent source files
- the current limitations are documented instead of hidden
