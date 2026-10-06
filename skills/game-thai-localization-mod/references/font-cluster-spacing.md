# Thai Runtime Cluster Spacing

Use this reference only when a following character collides after a Thai
base-plus-upper-vowel or base-plus-upper-vowel-plus-tone sequence.

## Diagnose the rendered glyph

- Trace the runtime glyph sequence before changing text. Some runtimes replace
  the Unicode sequence with a precomposed Private Use Area glyph, so offline
  Unicode preview can differ from the game.
- Map the visible failure to its runtime codepoint and glyph. Inventory sibling
  vowel/tone combinations that share metrics for the same base consonant.
- Treat a failure on another base consonant as a new cluster-family diagnosis.
  Reuse the method, not a previous numeric delta.

## Fix and prove the shared metric

- Fix the cluster-family metrics across every runtime font variant the game can
  select. Do not hard-code a word, string ID, or source substitution.
- Record codepoints, glyphs, advance and side-bearing values before and after,
  changed tables, and hashes.
- For an advance-only fix, assert that cmap mappings, glyph indices, outlines,
  and unrelated metrics remain unchanged. Require a deterministic second build.
- Scan the translated corpus for every affected cluster occurrence.
- Runtime-test the original string plus representative sibling combinations,
  wraps, compact UI, and dialogue. Keep proof scoped to the observed cluster
  family and tested surfaces.

Reject translation rewrites whose only purpose is avoiding the bad cluster.
