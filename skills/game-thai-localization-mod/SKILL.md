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
- Read references/batch-translation.md before translating a routine batch.
- Read references/font-cluster-spacing.md only when runtime evidence shows a
  Thai cluster-spacing collision.
- For Larian/DOS2 PAK, Nexus `English.pak`, loose-font, and release work, read
  references/engines/larian-dos2.md.
- For Unreal cooked `.pak`/`.uasset`/`.uexp`, platform overrides, PAK signing,
  or loader-option work, read references/engines/unreal-cooked-pak.md.
- For Unity/CPK release gates and delivery-only cleanup, read
  references/release-gate-lessons.md.
- For Unity Addressables/AssetBundles, binary dialogue databases, and TMP or
  legacy font rebuilding, read references/engines/unity-addressables-fonts.md.
- For Solar2D/Corona resource.car, read
  references/engines/solar2d-corona.md.
- For Klei/Don't Starve assets, read
  references/engines/klei-dont-starve.md.

Do not load an engine reference that does not match local evidence.

## Workflow

### 1. Freeze the preflight contract

Follow references/preflight-and-status.md. Freeze source/archive hashes,
encodings, runner/account/config and loader ownership, runtime policy, live
targets, backup retention/headroom, declared IDs/fields, glossary, and
scene/spoiler scope before editing.

Use exactly `forbidden`, `manual-by-user`, or `permitted` for runtime policy.
A changed source hash, install map, runner/config owner, or policy requires a
new preflight. Declare archive-specific source or translation overrides instead
of assuming sibling members are identical.

### 2. Inventory runtime surfaces

- Run scripts/audit_game_text.py against the game root for a read-only first
  pass, then inspect the largest archives and text-like resources.
- Parse structured formats to count records. Never use physical line count for
  multiline CSV.
- Check external JSON/CSV/PO/MO/map files, language packs, scripts/bytecode,
  Unity/Unreal assets, engine containers, font packages, remote panels, and
  image-baked text.
- Scan platform, device, DLC, and cooked override trees separately; a generic
  locale folder can be complete internally while a higher-priority PC/UI
  override remains English.
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

Follow references/batch-translation.md. Prefer one coherent scene or UI surface,
review every declared row from a compact context inventory, and run cheap
structural checks after each context window. Pack and diff full archives only at
the documented release gates. Generated drafts never become `reviewed`
automatically.

### 4b. Continuation and goal-loop guard

- Never leave a half-translated scene in the manifest or coverage ledger. Add
  source, target, validation-pair, and coverage entries together only after
  the whole declared scene is reviewed.
- If a scene cannot be completed and structurally checked in the current work
  unit, leave it unmodified and record a concise checkpoint instead.

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

When runtime evidence isolates a collision to a Thai cluster, follow
references/font-cluster-spacing.md. Fix the shared glyph metrics for the
observed cluster family; never rewrite translation text merely to avoid a font
defect.

### 6. Validate the whole declared pass

Follow references/validation.md and run scripts/validate_localization.py with a
versioned manifest. `static-valid` requires fresh validator output, the exact
declared field delta, and pack/unpack/diff proof for every candidate archive.
Stale reports never apply to new bytes.

### 6a. Package the complete install set

List every file and runner-side loader setting the working game needs after
installation, then compare that contract with the release archive and README.
Do not silently omit a required base patch or launch option because it predates
the new overlay. For a self-contained local package, include every required
runtime payload plus a manifest, SHA-256 checksums, and concise install/removal
instructions; test the release archive and its checksums before installation.

Keep release metadata self-contained and package-relative. Make the
README/manifest/evidence status agree and remove references to reports,
rollback trees, or scripts that cleanup will delete. Removal instructions must
work without the development workspace, normally through the launcher's
Verify/repair action when the mod overwrites official files.

The release README is a required artifact, not a pointer to the manifest. It
must tell the user how to open the game root from the launcher, name an anchor
file or directory found there, state the exact archive extraction destination
(and whether to merge/replace), identify the resulting target directory, and
say how to launch afterward. Its removal section must list every mod file by
exact name and identify similarly named official files that must not be
deleted. Include the update/Verify-files recovery step. After packing, read the
README back from the archive and confirm it contains those concrete
instructions; vague text such as "extract into the game folder" is not
sufficient.

Drive archive verification from the package's actual paths and schema, not
guessed names or old keys. Use `set -o pipefail`; empty output from a failed
`jq`, `grep`, or timed-out pipeline is not a pass. Inspect and correct a schema
mismatch, then rerun the full gate: format-appropriate integrity checks such as
`unzip -t` or `gzip -t` plus `tar -tf`, fresh extraction, metadata and README
assertions, payload checksums, and recursive comparison with staging.

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

Follow references/install-recovery.md. Stop the target game and every process
that actually holds a live target open. Stop a launcher or runtime helper only
when it owns such a handle or a persisted setting being edited; never stop an
unrelated host/container runner. On Linux, resolve exact PIDs and corroborate
with two independent read-only handle checks.

Build outside the live directory, journal before/candidate hashes, install
through verified same-filesystem temporary files, and restore the complete
target set after any partial failure. Keep recovery material until the
transaction reaches a verified terminal state, then clean only explicit
superseded paths under the retention contract.

### 8. Apply the runtime-test policy

When runtime testing is explicitly permitted, refresh the preflight with the
exact target AppID/executable, current candidate/live hashes, runner, account
config root, loader contract, and allowed scope. Then:

- Launch through the delivery runner with a process allowlist. An injected
  option may diagnose a loader failure, but final proof requires a normal launch
  with no ad hoc arguments, the final command line, and evidence that the
  process opened the installed candidate. Recheck the allowlist before launch,
  after every transition, and at handoff; never open another game for comparison.
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
  browser. Leave the game and Playbeam running when the user asks to continue.

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

Scope runtime proof to the runner/account/config that launched it. If the user
sees English through another Steam instance, downgrade that runner immediately
and inspect its active config and final process; a shared library path does not
make host and Playbeam launch settings equivalent.

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

Report the items applicable to the current request and lifecycle stage:

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

If the user wants only the final package, retain that deliverable and remove
verified superseded work by exact path. Never touch the live install; put the
package outside every deletion target and include removal instructions before
discarding rollback journals. Reverify the retained archive afterward.

When runtime policy is `permitted` and the live install was involved, require a
normal-launch check on the delivery runner before irreversible cleanup. Under
`forbidden` or `manual-by-user`, do not launch; keep the status
runtime-unverified and restrict cleanup to byte-verified workspace artifacts.

## Commands

    python3 <skill-dir>/scripts/audit_game_text.py /path/to/game
    python3 <skill-dir>/scripts/validate_localization.py --self-check --pretty
    python3 <skill-dir>/scripts/validate_localization.py /path/to/manifest.json --pretty

For relevant formats, also use msgfmt -c and unzip -t or an engine-equivalent integrity check.
