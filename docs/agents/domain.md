# Domain Docs

How engineering skills should consume this repo's domain documentation when exploring the codebase.

## Layout

This is a single-context repo.

Expected files:

- `CONTEXT.md` at the repo root
- `docs/adr/` for architectural decision records

If these files do not exist yet, proceed silently. Do not flag their absence or create them upfront. Producer skills such as `grill-with-docs` can create them lazily when terms or decisions are resolved.

## Before exploring, read these

- `CONTEXT.md`, if it exists
- Relevant ADRs under `docs/adr/`, if they exist

## Use the glossary's vocabulary

When output names a domain concept, use the term as defined in `CONTEXT.md`. Do not drift to synonyms the glossary explicitly avoids.

If the concept is missing, either reconsider whether it belongs to the project language or note it as a gap for future domain-doc work.

## Flag ADR conflicts

If output contradicts an existing ADR, surface the conflict explicitly rather than silently overriding it.
