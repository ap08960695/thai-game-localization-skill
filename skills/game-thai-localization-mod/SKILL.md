---
name: game-thai-localization-mod
description: Create or continue context-aware Thai localization mods for installed games. Use when translating game UI/dialog/story, tracing runtime text across JSON/CSV/PO/scripts or engine archives, preserving placeholders and encodings, adapting Thai fonts, refining or combining an existing user-supplied/Nexus Thai overlay, packing and installing archives transactionally, validating a locale pack, or separating static validation from permitted runtime proof.
---

# Game Thai Localization Mod

## Core rule

Find the real runtime text source, translate in scene and game context, preserve
format invariants, install transactionally, and prove only the strongest level
the user permits. Never imply that static checks prove the game boots. If the
user forbids runtime tests, run no game, Steam URI, Proton/Wine, display, input,
or screenshot command. A read-only process/handle guard before an install is
allowed, but is not runtime proof.

## Hard scope guards

- Treat the named game as a hard isolation boundary. Start in its dedicated
  workspace subtree and keep tools, reports, candidates, backups, install
  journals, screenshots, and logs there; do not mix sibling-game artifacts.
- Record an allowlist of the target game's AppID, executable/process names,
  window title, and live targets. Before and after install or runtime testing,
  scan for other game executables. If another game appears, stop input/launch
  work and report the contamination instead of continuing.
- Runtime permission is scoped to the named game and candidate. A later user
  authorization can promote that candidate after a refreshed preflight; it
  never authorizes opening or testing a different game.
- Never copy a previous candidate, snapshot, or release into a new candidate
  directory. A candidate holds only its own delta, release, reports, and
  validation; superseded iterations stay where they are or are removed by exact
  path. Nesting prior copies makes workspace bytes grow with the square of the
  iteration count, not linearly.
- Cap live candidate directories at the retention limit even when no install has
  happened. Before creating the next candidate, remove superseded ones by exact
  path, keeping the newest verified candidate plus any explicit user-requested
  deliverable. Candidate retention is not conditional on reaching an install.
- Re-measure candidate count, retained bytes, and free space at every release
  gate. If bytes grew without a matching declared delta, stop and report the
  growth instead of creating another candidate.

## Load relevant references

- Read references/preflight-and-status.md before editing or packing.
- Read references/validation.md when creating the validation manifest or running
  the central static validator.
- Read references/install-recovery.md before packing or installing live files.
- For refinement of an already-installed Thai/Nexus overlay, read references/existing-overlay-refinement.md before selecting rows.
- For Larian/DOS2 PAK, Nexus `English.pak`, loose-font, and release work, read
  references/engines/larian-dos2.md.
- For Unity/CPK release gates and delivery-only cleanup, read
  references/release-gate-lessons.md.
- For Solar2D/Corona resource.car, read
  references/engines/solar2d-corona.md.
- For Klei/Don't Starve assets, read
  references/engines/klei-dont-starve.md.

Do not load an engine reference that does not match local evidence.

## Workflow

### 1. Freeze the preflight contract

Record install/target paths, engine/archive mapping, source hashes and sizes,
encoding/BOM policy, runtime-test policy, backup retention, every backup/staging
root, free space, required pack/install headroom, fields/IDs/limits, glossary,
scene scope, spoiler boundary, per-archive text variants/overrides, and any
companion-field policy (for example, censored text mirroring Thai). Unless the
user explicitly requests otherwise, keep exactly one verified rollback set and
no completed staging, unpack, candidate, snapshot, or regenerable working-data
backup after a committed byte-verified install. A changed source hash or policy
invalidates the old preflight.

Record runtime permission as `forbidden`, `manual-by-user`, or `permitted`,
including the authorization time, runner, exact AppID/executable allowlist, and
tested candidate hash. A policy change is a new preflight; do not reuse an old
runtime screenshot or permission record for a different build or game.

Inventory the count and bytes of all backup roots created manually or by
scripts. Generated backups count toward retention. Before starting another
full-archive cycle, enforce the retention limit and remove only explicit,
verified superseded paths. If an incomplete transaction prevents cleanup, stop;
do not create another backup. Estimate rollback, candidate, unpack/diff,
temporary, and scratch space before packing.

For each declared pass, record the expected changed member, IDs, and fields per
archive. Do not assume sibling archives have identical text: declare a source
or translation override when they differ.

### 2. Inventory runtime surfaces

- Run scripts/audit_game_text.py against the game root for a read-only first
  pass, then inspect the largest archives and text-like resources.
- Parse structured formats to count records. Never use physical line count for
  multiline CSV.
- Check external JSON/CSV/PO/MO/map files, language packs, scripts/bytecode,
  Unity/Unreal assets, engine containers, font packages, remote panels, and
  image-baked text.
- Distinguish runtime data from source exports and backups. Do not assume the
  first language file found is loaded.
- Trace each visible untranslated string to runtime text, scripted text,
  image-baked text, remote content, or out-of-scope before declaring a gap.
- Prefer a shipped Thai payload and existing locale path over new machine
  translation. Keep module paths and internal keys unchanged.
- For Unity/IL2CPP/Addressables and similar locale-slot systems, record the
  logical locale, physical archive/member, launch/config locale, and runtime
  resolver. A patched filename or command-line flag alone does not prove that
  the game selected the patched slot; require a runtime locale probe or log.
- For games with separate locale archives, run an official non-English control
  before promoting a replacement in the English slot. If the same IDs resolve
  in a shipped control locale but an edited `English.pak` remains English at
  runtime, treat the English slot as fallback/compiled UI and test a dedicated
  locale archive plus its selector file instead.

Maintain a coverage ledger for every player-facing runtime source with one of:
translated, intentionally-unchanged, image-baked, remote, or out-of-scope.

### 3. Establish context and research evidence

For story text, record scene location, speaker, preceding event, intended
reveal, relationship tone, and spoiler boundary before translating.

Use evidence in this order:

1. the local primary source and its scene context;
2. other shipped languages only when the primary source or local context leaves
   a material ambiguity, or to confirm a proper noun, token, joke, implied
   subject, or speaker intent;
3. official game source, documentation, localization, or publisher material;
4. walkthroughs and wikis only when local and official evidence is insufficient.

Do not routinely triangulate every row against every shipped language. Translate
from the primary source in context; consult Chinese, Korean, or another shipped
locale selectively to resolve the ambiguity, then record the reason in the
scene evidence. This preserves nuance without making routine dialogue work
needlessly slow. For web evidence, record URL, access date, relevant
fact/quotation, affected row or term, and confidence. Scope searches to the
current spoiler boundary; do not read or use future reveals unless the user
authorizes it.

### 4. Translate only player-facing text

- Use machine translation only as a draft; review every declared row in context.
- Preserve placeholder/control-token multisets exactly: bracket, brace, angle,
  printf/Lua/Python markers, color/stat tags, and escaped newlines.
- Preserve row order, IDs, speaker IDs, locked fields, deliberate line-break
  counts, punctuation-only rows, and exact source bytes where fields are locked.
- Treat alternate archives and companion/censored fields as separately verified
  targets. Declare whether they use a source/translation override or intentionally
  mirror Thai; never infer equality from matching member names.
- Do not normalize trailing spaces or retype locked source text.
- Keep a glossary before batching. Preserve game titles, species/location names,
  HP/SP/XP, system abbreviations, and proper nouns unless the user decides
  otherwise.
- Skip pure references and internal keys. Record intentionally unchanged
  player-facing text with a reason rather than letting it resemble an omission.
- Reject flattened voice, added explanations, changed reveals, token damage,
  broken Thai/English spacing, and inconsistent terms.

### 4a. Batch routine dialogue safely

- Default target: 300--800 reviewed player-facing rows in one coherent scene,
  chapter segment, or UI surface (permitted range: 100--1,200). Prefer the
  whole local scene over an arbitrary row count. Use more than 800 rows only
  when the speaker set, location, terminology, and state remain stable and the
  compact scene inventory remains reviewable in one pass.
- Keep one release ledger for the complete scene, but divide its review queue
  into contiguous 100--300-row context windows. This is a review aid, not
  separate translation passes: retain the preceding event, speaker, tone, and
  spoiler boundary for every window, then reconcile recurring wording across
  the whole scene before marking it reviewed.
- Route high-risk rows—control tokens, multiline layout, proper nouns, jokes,
  implied subjects, speaker changes, branching choices, or material
  ambiguity—to a dedicated context window of at most 150 rows. Do not enlarge
  a high-risk window merely to meet a batch target.
- Use a smaller batch only for a true scene remainder, an unusually token-heavy
  segment, or material ambiguity, and record the reason in its scene evidence.
  This keeps context intact while avoiding thousands of tiny translation passes
  on a large game.
- Treat full-archive unpack, pack, unpack-and-diff, and live installation as
  release gates: do them once after a completed scene/chapter segment or after
  3,000--5,000 reviewed rows accumulate, never once per ordinary drafting
  batch. Run cheap row-level token, newline, glossary, and ledger checks after
  every context window; reserve full candidates for these release gates.
  This avoids repeatedly rebuilding multi-gigabyte archives without weakening
  the final exact-delta or round-trip proof.
- Do not defer a release gate past 5,000 rows, a source-hash change, a locale
  mapping change, or a scene-boundary decision that alters the glossary. Run
  the gate immediately when any of these occurs, even if the numeric target is
  not yet reached.
- Before editing, make a compact batch inventory containing file, row ID,
  speaker, source text, line count, control tokens, and scene context. Review
  every row from that inventory; do not let a generated draft silently mark a
  row reviewed. Keep recurring wording in a batch glossary/reuse map only
  after the speaker and state match.
- Group work by scene, location, speaker, or shared dialogue pattern so one
  context review supports a coherent batch; do not mix unrelated story beats.
- Maintain an approved glossary and reusable translations for repeated UI,
  token-bearing prompts, and NPC fallback replies. Reuse them only after
  checking that speaker, tone, and state match the current row.
- A script may generate ledger drafts and fill exact repeated templates, but it
  must never invent or silently approve Thai. Review every declared row in its
  scene context before assigning `reviewed`.
- Validate after each declared 300--800-row batch is complete, while running
  cheap structural checks after every context window. Run full archive
  packaging and archive-wide diffs only at the release gates above. Run an
  individual check immediately for any row with unusual tokens, multiline
  layout, trailing whitespace, quote-sensitive source text, or an ambiguous
  source.
- Consult other shipped languages and the web selectively, not by default:
  use them only when local primary context leaves a material ambiguity.
- Do not split a coherent scene merely to publish progress. A batch below 100
  rows needs a recorded exception: final remainder, no coherent next scene, or
  a segment that is unusually token-heavy or materially ambiguous.

### 4b. Continuation and goal-loop guard

- Treat an automatic goal-continuation prompt as permission to resume work, not
  as a request for a status reply. Do not emit repetitive “still working”
  messages: either complete a concrete, validated work unit or wait silently
  for a real user request.
- Before opening a scene, ensure the turn has enough capacity to translate,
  register, and run its structural validation. If it does not, keep the scene
  unmodified and leave a concise checkpoint (table, IDs, context, names, and
  required tokens) for the next substantive pass.
- Never leave a half-translated scene in the manifest or coverage ledger. Add
  source, target, validation-pair, and coverage entries together only after
  the whole declared scene is reviewed.
- Do not set a localization goal to `blocked` merely to stop repeated automatic
  continuation messages. `blocked` requires an external/user-dependent impasse
  that has persisted for the required audit threshold; resource or turn limits
  are a checkpoint, not a localization blocker.
- Prefer a whole small self-contained scene when it is a genuine remainder;
  otherwise accumulate adjacent compatible scenes into the normal 300--800-row
  review batch instead of publishing a stream of tiny progress-only passes.

### 5. Pass encoding, shaping, and font gates

Pin UTF-8, UTF-8 BOM, CP874, or TIS-620 from format/engine evidence; require
strict decode/encode round-trip. Enforce field byte limits where containers use
fixed or bounded storage. Reject replacement characters, embedded BOMs,
and orphaned or duplicated Thai combining marks.

Inspect the actual font/atlas/metrics package. Prove Thai glyph coverage and
real UI width/line limits through validator metrics or recorded engine-tool
evidence. Boxes or blanks can indicate an atlas/metrics/orientation mismatch,
not a translation failure.

Thai fonts must also fit the game's art direction: weight, contrast, roundness,
age, spacing, and UI density. Preserve the original Latin font when possible.
Use custom/mixed fonts only after simpler choices fail screenshot QA. When
runtime screenshots are forbidden, report visual/font-fit uncertainty.

Do not treat visible Thai glyphs as a legibility pass. When Thai renders but is
hard to read, reproduce the exact surface and classify weight, contrast,
blur/SDF, spacing, clipping, and mark placement apart from translation quality.
For Unity, trace every font route used by the observed surfaces: dialogue may
use embedded TMP SDF bundles while menus use legacy `Font` assets in `common`
or `resources.assets`. Do not assume an external TTF or one TMP variant is the
only route without runtime evidence.

- Preserve the original Latin face and unrelated glyphs when possible; apply
  one proven Thai face/weight across every selected runtime variant and record
  deterministic asset hashes.
- Compare before/after captures on the same bright and dark surfaces. Check
  marks, wraps, compact UI, and dialogue rather than one title-screen sample.

### 5a. Fix runtime-cluster spacing at the font boundary

When a following character collides only after a Thai base-plus-upper-vowel or
base-plus-upper-vowel-plus-tone sequence, trace the actual rendered glyph
sequence before changing translation text. Some runtimes replace the Unicode
sequence with one precomposed Private Use Area (PUA) glyph, so an offline
Unicode preview can differ from the game and the fault can be that cluster
glyph's advance width rather than the sentence.

- Map the failing visible sequence to its runtime codepoint and glyph, then
  inventory the complete affected cluster family for that base consonant.
  Include unreported sibling vowel/tone combinations that share the same
  metrics defect, but do not widen unrelated bases or all Thai glyphs.
- Fix the shared font metrics once for that cluster family across every runtime
  font variant the game can select. Do not hard-code a word, sentence, string
  ID, or source-text substitution to hide a glyph-spacing fault.
- Keep the delta minimal. Record the exact glyphs/codepoints, advance and
  side-bearing values before and after, changed font tables, and hashes. Assert
  that cmap mappings, glyph indices, outlines, and unrelated metrics remain
  unchanged when the intended fix is advance-only; require a deterministic
  second build.
- Scan the translated corpus for every occurrence of the affected clusters.
  Runtime-test the originally failing string plus representative sibling
  combinations, line wraps, and both compact and dialogue UI. A pass on one
  word proves the shared glyph fix for that observed cluster, not every base
  consonant or every screen.
- Treat a later collision on another base consonant as a new cluster-family
  diagnosis. Reuse the method, not the previous numeric delta without fresh
  measurements.

Reject translation rewrites whose only purpose is avoiding the bad cluster.
They conceal a reusable font defect, alter wording, and leave other strings
with the same glyph broken.

### 6. Validate the whole declared pass

Run scripts/validate_localization.py with a versioned manifest. It checks JSON/
CSV parsing, source/target record and ID-order parity, locked fields, tokens,
newlines, glossary drift, untranslated rows, coverage, encodings, byte limits,
Thai mark sanity, font glyphs, and declared width/line fit, then emits JSON.

Before packing, audit pristine source versus working data and assert the exact
changed IDs and fields for every target. A mirrored companion/censored field is
valid only when that policy is declared. For every binary member and full
archive: pack, unpack the candidate to a fresh tree, parse, recursively diff
against the intended tree, and byte-compare each changed member. Test archive
integrity and spot-check representative strings. Use fresh hashes and reports;
stale verifier output is not evidence for a new candidate.

### 6a. Package the complete install set

List every file the working game needs after installation, then compare that list
with the release archive. Do not silently omit a required base patch because it
predates the new overlay. For a self-contained local package, include every
required PAK plus a manifest, SHA-256 checksums, and concise install/removal
instructions; test the ZIP's integrity and its checksums before installation.

Keep release metadata self-contained and package-relative. Make the
README/manifest/evidence status agree and remove references to reports,
rollback trees, or scripts that cleanup will delete. Removal instructions must
work without the development workspace, normally through the launcher's
Verify/repair action when the mod overwrites official files.

The release README is a required artifact, not a pointer to the manifest. It
must tell the user how to open the game root from the launcher, name an anchor
file or directory found there, state the exact ZIP extraction destination (and
whether to merge/replace), identify the resulting target directory, and say how
to launch afterward. Its removal section must list every mod file by exact name
and identify similarly named official files that must not be deleted. Include
the update/Verify-files recovery step. After packing, read the README back from
the ZIP and confirm it contains those concrete instructions; vague text such as
"extract into the game folder" is not sufficient.

Drive archive verification from the package's actual paths and schema, not
guessed names or old keys. Use `set -o pipefail`; empty output from a failed
`jq`, `grep`, or timed-out pipeline is not a pass. Inspect and correct a schema
mismatch, then rerun the full gate: `unzip -t`, fresh extraction, metadata and
README assertions, payload checksums, and recursive comparison with staging.

Before bundling a third-party base patch, confirm that the user has authority to
redistribute it. A user-supplied archive authorizes local use only, not public
republication. Record its source, name, and hash in the manifest. If it cannot
be bundled, make the dependency explicit and do not describe the package as
self-contained.

When the user explicitly authorizes a clean-install test, hash the fresh
official baseline, extract the release archive itself (not a separate working
tree), then hash every installed member. This distinguishes a package that
works only in the development folder from one that installs cleanly.

### 7. Install and recover transactionally

Require the game, launcher/runtime helper, and packer stopped, with no open
handle to any live target. On Linux, inspect `/proc` process names and use two
independent read-only handle checks such as `fuser` and `lsof`; use an equivalent
platform check elsewhere. Build outside the live directory, retain a verified
before-image, record before/candidate hashes in an install journal, copy through
unique same-filesystem temporary files, atomically rename, and byte/hash-verify
every installed target.

Multi-archive installs are not jointly atomic. After any partial failure, stop
and restore the complete target set, then verify every restored before hash.
Remove temporary files on success and failure. Keep rollback/journal artifacts
until recovery or full install verification is complete.

For hard-linked staging, unlink each changed member before copying; overwriting
a hard link corrupts the baseline. Audit that the unlinked-member set is exactly
the declared delta. After successful full verification, update any current-
backup pointer before removing the exact superseded rollback, snapshot, or
staging paths; never use a broad cleanup glob in a backup root.

After the install journal is committed and every live target byte-matches the
candidate, perform retention cleanup in the same pass. Keep the newest verified
rollback set, small journals/manifests/reports, and any explicit user-requested
deliverable. Remove the completed staging/unpack/candidate trees and
regenerable script-created backups by exact path, then re-measure retained count,
retained bytes, and free space. Do not defer this cleanup to a later pass.

### 8. Apply the runtime-test policy

When runtime testing is explicitly permitted, refresh the preflight with the
exact target AppID/executable, current candidate/live hashes, runner, and
allowed scope. Then:

- Launch through the actual runner and keep a process allowlist for the target
  game. Recheck it before launch, after every transition, and at handoff; never
  open another game to obtain a comparison screen.
- Capture ordered current native frames, each tied to the exact input that
  reached it. Use a safe sequence such as title → menu → confirmation → real
  gameplay dialogue when the game supports it; one title screenshot is not a
  gameplay check.
- Prove input by a visible state transition and corroborate it with the game
  log or scene state. A cinematic that looks like a map, an idle field frame,
  or a frame that later returns to the title is not proof that gameplay was
  reached.
- Require at least one current nonblank Thai text surface and record the
  tested surface, input sequence, screenshot hash, log path, process evidence,
  and candidate/live hash together. Keep `runtime-proven` scoped to those
  tested surfaces; do not turn a short route into a claim that every screen
  was runtime-tested.
- For locale-slot loaders, log the selected runtime locale and resolve one
  known localized ID/value. For Thai fonts, record the fallback/plugin load and
  a visible Thai glyph result; static glyph coverage alone is not font proof.
- Treat title, main menu, Story setup, and deeper setup/dialogue as separate
  surfaces. A Thai menu proves the selected locale path, not complete coverage;
  record residual English such as an option label as an explicit remaining gap.
- When the user asks to observe the game "for a while," record requested and
  actual duration, capture count/cadence, distinct dialogue strings, speakers,
  and surfaces. Repeated identical frames are continuity evidence, not added
  text coverage. Review every distinct sample for boxes/blanks, clipping,
  overlap, Thai-mark placement, weight, and background contrast.
- If the user announces a manual confirmation or input step, stop synthetic
  input immediately. Resume only after the user explicitly says it is done,
  then capture a fresh frame and re-establish the current scene/process state
  before continuing the ordered test route.
- Separate warnings from fatal errors and stop only the temporary controller or
  browser. Leave the game and the streaming runtime running when the user asks to continue.

A live executable/window proves successful boot only; it does not prove Thai UI
rendered. If the capture path returns an all-black frame while the game is live,
record `boot-proven; capture-blocked`, investigate the compositor/capture path,
and retain the lifecycle at installed-and-byte-verified. Do not promote it to
runtime-proven without current nonblank Thai evidence. Earlier screenshots may
be linked only as historical evidence when the complete installed file/hash set
is identical; label them as historical rather than current proof.

When runtime testing is forbidden, stop at static or installed byte proof and
give the user the candidate hashes and exact manual-test scope. When testing is
manual-by-user, do not drive the game yourself; record only the user's result
with the exact tested build/hash and promote it to `runtime-proven` only when
current nonblank Thai surface and process/log evidence is supplied.

## Evidence status

Use this exact lifecycle:

draft → translated → reviewed → static-valid → installed-and-byte-verified →
runtime-proven

Do not skip levels. The evidence required for each level is defined in
references/preflight-and-status.md. A passing validator establishes only the
declared static scope; installed hashes and runtime evidence are separate gates.

## Completion and reporting

Do not call the full localization complete while the runtime-source inventory
has unexplained player-facing gaps. One scene/archive check proves only that
scope.

Always report:

- changed files, candidate hashes, install targets, and rollback/journal paths;
- exact status from the lifecycle above and whether runtime remains unverified;
- validator/archive/installed-byte evidence from the current candidate;
- exact game allowlist/process gate, tested runtime surfaces, and ordered input
  sequence when runtime was permitted;
- coverage classifications and residual untranslated strings;
- unresolved image-baked, remote/event, font-fit, debug/internal, and untested
  surfaces;
- all retained backups/staging roots, cleanup performed, and remaining disk
  cost;
- screenshot/log paths only when a current permitted runtime test created them.

If the user explicitly wants only the final package after verification, retain
only that deliverable in the workspace and remove the verified superseded
rollback, journals, reports, and working trees by exact path. Never touch the
live game install during delivery-only cleanup; ensure the package contains the
removal instructions before discarding the rollback journal. Place the final
package outside every deletion target and verify its hash, archive integrity,
and live installed-member hashes again after cleanup.

## Commands

    python3 <skill-dir>/scripts/audit_game_text.py /path/to/game
    python3 <skill-dir>/scripts/validate_localization.py --self-check --pretty
    python3 <skill-dir>/scripts/validate_localization.py /path/to/manifest.json --pretty

For relevant formats, also use msgfmt -c and unzip -t or an engine-equivalent integrity check.
