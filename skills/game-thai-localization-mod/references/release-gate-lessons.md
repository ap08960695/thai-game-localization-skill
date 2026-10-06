# Unity and CPK Release-Gate Lessons

- When a target ledger was aligned to pristine text, do not align it against a
  CPK that already contains an older localized overlay. The source-text
  mismatch is expected. Build the language bundle from the matching pristine
  source CPK, then overlay the raw, verified UnityFS bundle into the latest
  candidate CPK. Record both source hashes and the archive-specific override.
- A passing coverage validator does not prove that no visible English remains.
  Intentional unchanged rows may contain names, locations, or onomatopoeia, and
  partial generated ledgers may be stale. Scan the actual target `text` fields
  and translation source maps for approved residual terms, classify proper
  names separately, and fix terms in the source-of-truth maps before
  regenerating targets, coverage, glossary, and manifest.
- Do not rely on ASCII `\b` boundaries when scanning text next to Thai. Use
  literal or Unicode-aware matching with context, then rerun the central
  validator. Apply only glossary-approved replacements; an unreviewed global
  replacement can corrupt proper nouns or other intentionally unchanged text.
- A new candidate hash invalidates runtime proof for an earlier candidate. Keep
  the new release at `static-valid` until that exact CPK is installed and
  current runtime evidence proves it; predecessor screenshots are historical
  evidence only.
- After runtime promotion, replace stale top-level `static-valid` metadata with
  a concise manifest and README bound to the tested bytes. Preserve the old
  static manifest under package-relative reports only when it remains useful
  provenance; do not let it define the final evidence status.
- For a large already-compressed CPK, use ZIP store mode (`zip -0`) to avoid
  futile recompression. Put the CPK, README, manifest, and SHA-256 checksums in
  the ZIP, then run `unzip -t`, stream-check the CPK hash from inside the ZIP,
  and read the README/manifest back before cleanup.
- Generate `SHA256SUMS` only after the final payload, metadata, and captures are
  in staging. For any archive format, reject absolute or parent-traversal
  members, duplicates, symlinks, hardlinks, special entries, and unexpected
  top-level roots. Fresh-extract the whole archive, verify every checksum, then
  execute the README's exact selective-install command and byte-compare its
  installed files with the runtime-tested live files.
- Keep one final staging tree outside the work-tree deletion target; never nest
  a prior candidate or staging tree inside the next revision. Place the archive
  outside both, verify it, then remove only the literal staging and game-work
  paths. Re-hash the retained archive and live installed members afterward.
- If delivery-only cleanup is explicitly requested, verify the package first,
  inventory exact deletion targets, check nested mounts and exact open handles,
  and delete only enumerated workspace roots with `find -P <target> -depth
  -delete`. Mount-level `fuser` can list unrelated games on the same volume;
  corroborate with exact workspace-path `lsof` and `/proc` checks, and never
  stop or delete another game's files.
- On very large workspaces, recursive `du` and `lsof +D` may time out. Bound
  those probes; never report a partial `find | wc` result as exact when an
  upstream command timed out. Fall back to an exact-prefix `/proc` scan of
  process `fd`, `cwd`, `root`, and `maps`, recheck `findmnt`, verify the final
  package is outside the deletion root, then delete only the validated literal
  path. Re-hash and integrity-test the retained package after deletion.
