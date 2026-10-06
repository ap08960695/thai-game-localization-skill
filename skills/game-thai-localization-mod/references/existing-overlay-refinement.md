# Refining an Existing Thai Overlay

## Contents

- Freeze and inventory the three-way baseline
- Parse and refine Nexus references
- Apply and validate the smallest delta
- Build one private combined package
- Keep runtime proof tied to immutable bytes

Use this reference when the user asks to improve an installed Thai mod, merge
better wording from NexusMods, or continue a previous localization ledger.

## Freeze the three-way baseline

- Freshly extract the live language archive before every revision. Treat its
  parsed values as `current`, not as pristine source.
- Keep pristine English, the Nexus reference, and the live extraction as three
  separate inputs. A changed live value is already translated work and is not
  a new candidate merely because the Nexus row is different.
- Record the live hash, source hash, candidate hash, Game/base-archive hash,
  exact live member, and the one retained rollback before editing.

## Build an honest candidate inventory

- For each row, classify `current == source`, `Nexus != source`, Thai present,
  and any control/UI/book/scene category before selecting a batch.
- Report `candidate_count`, `selected_count`, `reviewed_count`,
  `changed_count`, and `intentionally_unchanged_count` separately. A scan of
  the whole archive is inventory evidence, not proof that every row was
  manually reviewed.
- Prefer a coherent scene or UI surface. Cap high-risk multiline, control,
  proper-noun, and ambiguous rows at 150. A smaller final remainder is valid
  only when the report records why it is a remainder.
- Mark unresolved player-facing controls explicitly in the coverage ledger;
  never let a generated target silently make them look reviewed.

## Parse Nexus references defensively

- Preserve the raw source, raw Nexus value, and chosen Thai reference in the
  inventory. Nexus translations may be appended in a parenthetical wrapper,
  contain markup, or contain prose such as `1)` and `2)` that is not balanced
  grouping syntax.
- Do not discard a candidate because a naive last-parenthesis parser mistakes
  numbered prose or inline markup for the wrapper. Use a structure-aware
  parser, a safe fallback, or a manual override and record which path was used.
- Do not copy the Nexus English prefix or its wrapper into the target. Review
  the Thai as a target string against the original speaker, scene, state, and
  established glossary.

## Apply and validate the smallest delta

- Preserve the source control-token multiset, literal/escaped newline count,
  line-break tags, placeholders, and locked fields exactly.
- Do not add `<i>`, `<b>`, or other markup merely to restore emphasis when the
  source has no corresponding tag; the validator correctly treats that as a
  token change. Preserve source markup first, then improve wording within it.
- Treat `[Translate...]`, generated IDs, and other internal control tokens as
  intentionally unchanged until their runtime meaning is known. A Thai note
  in Nexus is not enough authority to replace the control value.
- Run row-level token/newline/glossary/Thai-mark checks after each review
  window. At the release gate, pack once, unpack to a fresh tree, compare the
  exact declared XML delta, and prove the live archive matches the candidate.

## Close the loop accurately

- After installation, scan the actual live archive against source and Nexus;
  report residual control, image-baked, remote, debug/internal, and untested
  surfaces separately.
- Keep the lifecycle at `static-valid` or
  `installed-and-byte-verified` when runtime is forbidden. Do not convert a
  full-corpus scan, font metrics pass, or archive hash into runtime proof.
- Clean only explicit staging/candidate paths after byte verification, retain
  exactly one verified rollback, and include its path in the final report.

## Build one private combined package

- When the working mod needs an older third-party base plus a new improvement
  overlay, inventory the complete install set before packing. Compose a fresh
  package tree base-first and overlay-last; never assume the improvement ZIP
  contains unchanged base-only members.
- Inventory every functional root in the upstream archive, including loose
  fonts, selectors, plugins, and mod overrides outside its primary language
  archive. A current development install can hide an omitted dependency that
  already exists in a patched base archive.
- Record each upstream payload as included byte-identically, merged,
  superseded, or excluded with a reason. If a raw language PAK is superseded by
  a merged locale PAK, explain that conflict avoidance in the README/manifest.
- Before extraction, reject absolute/traversal paths, unsafe links, duplicate or
  case-colliding names, and unexpected executables from every external archive.
- Classify every payload member as base-only, overlay-replaced, or overlay-added
  and record each count. Keep README, manifest, provenance, and checksum members
  separate from the runtime payload count.
- Treat a user-supplied/Nexus archive as local-use authority only. Record its
  name and SHA-256, label a combined archive private/local-use, and do not
  publish it without the original author's permission.
- Verify the combined ZIP from a fresh extraction: archive integrity, metadata,
  all listed checksums, payload count, overlay precedence, and concrete
  install/removal instructions. Install that ZIP itself, not an equivalent
  development tree.

## Keep runtime proof tied to immutable bytes

- Keep a runtime report outside an already tested package and bind it to the
  package SHA-256, installed-member hashes, AppID, executable, locale, and
  capture hashes. Adding the report to the ZIP changes the candidate; reinstall
  and repeat the runtime gate before promoting the new hash.
- When a staged mod manager performs the install, record its operation and
  installed IDs plus overwritten/backed-up, created, and blocked counts.
  Byte-verify every live member and every overwritten before-image. Retain the
  current rollback and any extracted source the manager requires for removal.
- Before opening a save/overwrite prompt, inventory the real save files and
  their hashes or mtimes. Cancel destructive confirmation unless the user
  explicitly authorized it, then verify that no save changed.
- When the package contains both base-only and improved members, exercise one
  identifiable visible string from each class when practical. Do not call the
  overlay refinement runtime-checked from unrelated Thai screens alone.
- If the user asks to leave the game running, recheck the runner's
  `game_running` state and the exact executable after all captures and
  controller cleanup. A compositor watchdog can recover the session while the
  game exits; relaunch only the allowlisted target and disclose the interruption.
- If delivery cleanup must leave only the ZIP, disclose that deleting the
  external runtime report removes independently auditable runtime evidence from
  the filesystem. Retain a sidecar when durable evidence is required; putting
  it inside the ZIP creates a new hash that must be reinstalled and retested.
