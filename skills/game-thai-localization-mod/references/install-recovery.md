# Transactional Install and Recovery

## Contents

- Before packing
- Install transaction and journal
- Partial-failure recovery
- Retention and cleanup

Use this for every install, especially when one pass updates several archives.

## Before packing

1. Re-read the preflight and verify current source hashes.
2. Inventory every configured backup root and any backup directory created by
   pack/install scripts. Record count and bytes; generated backups count toward
   retention.
3. Estimate rollback, candidate, unpack/diff, temporary-copy, and scratch bytes.
   Stop if measured free space is below required headroom.
4. Enforce the retention contract before creating another full candidate. Remove
   only verified terminal artifacts by exact path. If an incomplete transaction
   or unverifiable artifact keeps the inventory over the limit, stop.
5. Build candidates outside the live game directory.
6. Pack, unpack, recursively diff, and audit every reviewed member.
7. Record each candidate SHA-256 and size.

Do not remove an older verified backup merely to make an unverified candidate
fit. Ask before changing the retention/headroom contract.

## Install transaction

1. Require the target game, packer, and every process that holds a live target
   open to be stopped. Stop a launcher/runtime helper only when it owns such a
   handle or a persisted setting being edited; never stop an unrelated
   host/container runner. On Linux, resolve exact PIDs and use two independent
   handle checks such as `fuser` and `lsof`; use platform-equivalent read-only
   checks elsewhere. If runtime activity is forbidden, this guard remains
   allowed but must launch nothing. A full-command `ps | grep/rg` probe can
   match its own scanner and create a false positive.
2. Create the new rollback copy immediately before install and verify its hash.
3. Create an install journal before replacing the first live target.
4. For each target, write a unique temporary file on the target filesystem,
   fsync when supported, byte-compare/hash it against the candidate, then
   atomically rename it over the target.
5. After all replacements, hash every live target against its candidate.
6. Mark the journal committed only after the complete target set verifies.

Hard-linked staging is allowed only for unchanged content. Unlink a target
member before copying its replacement; overwriting a hard link mutates the
baseline and every linked pass. Audit that the only unlinked members are the
declared replacements before packing the candidate.

## Minimal install journal

Record at least:

    {
      "transaction_id": "unique-id",
      "state": "prepared",
      "started_at": "ISO-8601",
      "game_process_check": "evidence",
      "targets": [
        {
          "live": "/game/archive.car",
          "backup": "/backup/archive.car",
          "before_sha256": "...",
          "candidate": "/staging/archive.car",
          "candidate_sha256": "...",
          "installed_sha256": null,
          "state": "pending"
        }
      ]
    }

Update target states as work proceeds. Valid transaction states are prepared,
installing, committed, restoring, and restored. Write journal updates
atomically so a crash does not leave ambiguous state.

## Partial-failure recovery

If any copy, rename, hash, or journal update fails:

1. Stop installing remaining candidates.
2. Mark the transaction restoring.
3. Restore every target in the transaction from its verified before-image,
   including targets not yet replaced when needed to prove one coherent set.
4. Hash every restored live target against its recorded before hash.
5. Mark restored only when the full set matches; otherwise report a blocker and
   preserve journal/backups for manual recovery.
6. Remove candidate temporary files on both success and failure. Never remove
   the journal or rollback material while recovery is incomplete.

Multi-archive replacement is not jointly atomic. Full-set rollback is therefore
mandatory after a partial failure.

## Retention and cleanup

- Unless the user explicitly overrides retention, keep exactly one verified
  rollback set and zero completed staging/unpack/candidate/snapshot or
  regenerable working-data backup trees after commit. Keep small journals,
  manifests, hashes, and QA reports.
- Count backups from all manual and generated roots, not only the preferred
  backup directory. Count both entries and bytes.
- Rotate the prior backup only after the candidate is installed and every live
  target byte-verifies.
- Repoint any current-backup/rollback ledger to the new verified rollback before
  removing its predecessor.
- After the journal is committed and every live target byte-matches its
  candidate, delete the completed staging/unpack/candidate trees for that pass
  unless the user requested an offline deliverable. Delete script-created
  working backups when the current source plus ledger can regenerate them.
- Complete retention cleanup before beginning the next pack/install cycle; do
  not let successful pass artifacts accumulate for later cleanup.
- Delete only explicit, verified superseded paths; do not use a broad glob in a
  rollback or snapshot root.
- Never delete the current rollback, a user-managed backup, or material required
  by a prepared, installing, restoring, failed, or otherwise incomplete
  transaction. Remove incomplete temporary copies only when recovery no longer
  needs them.
- Re-inventory after cleanup. If the retained set still exceeds policy, stop
  before creating any new backup and report the exact blocker.
- Report retained backups, removed paths, freed bytes, journal state, retained
  bytes, and remaining free space.
