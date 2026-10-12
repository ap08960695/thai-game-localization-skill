# Exclusive runtime gate and uninstall journal

Prepare the test fully before launching. Runtime policy and install/publication
permission are separate. With `forbidden` or `manual-by-user`, stop at offline
evidence and provide the owner a concrete route; do not launch a game implicitly.

## Installation

Hash the current installed baseline, not an assumed pristine Steam build. Stage
the plugin and generated delta outside live targets. Recheck the named game's
processes/handles before installation. Record added versus overwritten paths,
candidate hashes, before hashes/backups, and directories created in a journal.
Install through temporary files and atomic rename, then verify every live hash.
Keep original bundles and managed assemblies unchanged for the loose-WAV route.

## Exclusive automated gate

Reserve one game launch with no GPU/CPU-heavy work or other games in parallel.
Use an ownership lock plus read-only process/resource checks; the lock alone
cannot detect unrelated workers. If busy, wait and report. Record launch runner,
build hashes, audio sink, start/end times, and a bounded attempt count. Do not
kill unrelated jobs. Prefer in-game clean exit; escalate teardown only within
explicit permission for the exact owned test process.

Use a generated tone as the HIT fixture and an **actually existing** original
voice ID with no override as the MISS fixture. Verify those IDs in the bundle
before launch. Test IDs in order via the real request path. Require:

1. loader READY and the expected hook;
2. HIT/OVERRIDE assignment with expected frames/rate/channels and audible tone;
3. MISS with the existing original audible;
4. request → assignment → playing → stopped for each line;
5. at most one active voice at a time, measured through sources and corroborated
   with the sink capture; different legitimate source IDs are not duplicates;
6. clean exit as its own result, independent of whether playback passed;
7. unchanged original hashes, journaled runtime changes, and no owned process left.

In launch-local test mode, isolate title music/effects from capture without
creating another AudioSource or muting the voice being tested. Frame-sampled
source counts can miss very short overlaps; sink audio from other applications
can contaminate results. A split tone can be Bluetooth dropout, background
interference, or real playback trouble. Retain that failed capture until diagnosis;
do not infer a loader defect or a PASS from one metric alone.

A tone/fallback gate proves the exercised loader seam. It does not prove real
Thai dialogue, scene acting, lips, volume slider, skip/stop, backlog, auto mode,
or untested cues. Test those separately within owner-authorised scope. Disable
test mode afterward and record the current installed candidate hashes.

## Removal

Track config regeneration explicitly: loaders can rewrite headers/defaults.
Preserve the candidate hash and record a verified runtime-generated hash after
checking that only expected settings/comments changed. Do not simply trust an
arbitrary changed file or replace the original record with the latest hash.

Dry-run removal must list exactly the journal targets. Remove an added file only
when its hash matches an authorised candidate/runtime hash. Restore an overwritten
file only from its verified before-image after checking current ownership/hash.
Preserve user changes, symlinks, unexpected targets, and hash mismatches for review.
Remove created directories only if empty. Never delete a whole game subtree.
Verify baseline hashes after actual removal; a dry run proves only the plan.
