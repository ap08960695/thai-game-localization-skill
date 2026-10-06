# Context-safe Translation Batches

Use this reference for routine dialogue, story, or UI batches.

## Select a coherent batch

- Default to 300--800 reviewed player-facing rows in one coherent scene,
  chapter segment, or UI surface. The permitted range is 100--1,200.
- Use more than 800 only when speaker set, location, terminology, and state
  remain stable and reviewable. A batch below 100 needs a recorded reason:
  final remainder, no coherent next scene, unusual token density, or material
  ambiguity.
- Do not split a coherent scene merely to publish progress or mix unrelated
  story beats to reach a numeric target.

## Review through bounded context windows

- Divide the batch into contiguous 100--300-row context windows while retaining
  preceding event, speaker, tone, and spoiler boundary.
- Route control tokens, multiline layout, proper nouns, jokes, implied subjects,
  speaker changes, branching choices, and material ambiguity to a window of at
  most 150 rows.
- Before editing, inventory file, row ID, speaker, source text, line count,
  control tokens, and scene context. Review every declared row from that
  inventory.
- Reuse approved translations only after checking speaker, tone, and state.
  Scripts may draft ledgers or fill exact repeated templates, but may not invent
  or silently approve Thai.

## Validate cheaply, release deliberately

- After each context window, check tokens, newlines, glossary, coverage, Thai
  marks, and unusual whitespace or quoting.
- Reconcile recurring wording across the whole scene before assigning
  `reviewed`.
- Treat full unpack, pack, unpack-and-diff, and live installation as release
  gates. Run them after a completed scene/chapter segment or after 3,000--5,000
  reviewed rows, not after ordinary drafting windows.
- Do not defer a release gate past 5,000 rows, a source-hash or locale-map
  change, or a scene-boundary decision that changes the glossary.
- Consult other shipped languages or web evidence only when local primary
  context leaves a material ambiguity.
