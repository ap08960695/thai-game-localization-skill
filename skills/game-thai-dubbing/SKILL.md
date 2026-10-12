---
name: game-thai-dubbing
description: Create or continue Thai dubbing mods for installed games with existing speech. Use for voice-to-text manifests, original timing analysis, designed character voices, segment-aware synthesis, calibrated audio QA, loose-WAV loader overrides, scoped in-game tests, and journaled removal.
---

# Game Thai Dubbing

Build a small, reversible voice replacement before scaling to a scene. Reuse an
installed, reviewed Thai text overlay; do not silently rewrite its translation.
Keep manifest, voice design, synthesis acceptance, loader proof, and owner
listening acceptance as separate evidence. A tone test proves routing, not Thai
pronunciation or character fit.

## Boundaries

- Use **designed voices only**. Original game audio is for local measurement
  only: never use it as a synthesis prompt, speaker embedding, cloning reference,
  training input, or distributed asset. See [rights.md](references/rights.md).
- Keep game assets, dialogue, original audio, private manifests, and trained
  weights outside the public skill. Never publish LoRA weights trained on BY-SA
  data. CC0, CC-BY, and CC-BY-SA datasets are eligible under the project policy;
  NC, ND, and unknown licences are forbidden. Record attribution and obligations.
- Run one GPU job at a time. Game launch is exclusive: no synthesis, training,
  GPU listener, other game, or CPU-heavy analysis during its gate. Do not run
  CPU-heavy jobs alongside the GPU job. If resources are occupied, wait; never
  terminate someone else's work. Record VRAM, RAM, swap, and free disk headroom.
- Freeze the named game, build hashes, allowed processes, install targets, and
  runtime policy (`forbidden`, `manual-by-user`, or `permitted`). A request to
  prepare a skill or package grants no game launch or publication permission.

## Workflow

1. **Survey.** Read metadata before extracting. Establish engine/runtime,
   spoken languages, actual voice containers, text overlay, timing/lip triggers,
   and a feasible replacement seam. Exclude speechless games from this first
   replacement workflow. Read [engines.md](references/engines.md) for the matching
   adapter; Unity Mono is the pilot-proven route, other adapters are unproven.
2. **Manifest.** Join `voice_id ↔ text_key ↔ speaker_key` from actual script calls
   and audio metadata. Record rate, channels, duration, scene, nonverbal status,
   source hashes, and unmatched IDs. Calls, assets, and joined rows are different
   counts. Never invent timing or alias a missing cue into a test fixture.
3. **Design voices.** Write a character sheet from scene evidence. Audition a
   small set of independent synthetic anchors. Lock one own-designed voice per
   character with hashes, design/settings, seed, and prompt transcript. Reuse
   that anchor plus own synthetic prompt continuation on every line. An
   emotion-specific lock must belong to the same design. No original actor audio.
4. **Measure the original locally.** Derive timing/activity segments, pauses,
   breath cues, pitch/energy envelope, articulation, and broad spectral target
   bands. Store numeric guide/profile data privately, then delete temporary
   decoded originals. Reference-guided means a performance target, never actor
   identity transfer. See [synthesis-and-qa.md](references/synthesis-and-qa.md).
5. **Synthesize by segment.** Group Thai phrases onto ordered active guide spans;
   place them at guide onsets, keep pauses silent, and render designed breaths
   separately. Correct speech pace before placement without changing pitch.
   Pad to exact guide duration; bounded acceleration may fit a near miss, but
   never truncate words. Reject an overrun instead of forcing acceptance.
6. **Gate real speech.** Check raw, fitted, and delivery PCM separately. Calibrate
   signal/prosody/ASR thresholds on licensed real Thai speech using the same
   preprocessing; include shouting, short reactions, and noise controls. Keep
   primary text/confidence, clipping, timing, and identity checks independent.
   Validate PCM16 with `scripts/validate_wav.py`; it does not judge naturalness.
7. **Listen.** Use AI only to pre-filter takes and surface uncertainty, then get
   the owner's ear for Thai tones, acting, fit, and naturalness. Preserve rejected
   takes/receipts long enough to diagnose failures. The optional adapted
   [listen panel](references/listening.md) needs external tools and explicit
   permission for hosted uploads; none are invoked by loading this skill.
8. **Override.** Stage `<voice_id>.wav` through a loader rather than rewriting
   original bundles when that seam is proven. The
   [plugin template](scripts/plugin/Plugin.cs) replaces one shared clip assignment
   and preserves the game's source, volume/play/stop path, and original fallback.
   Adapt and inspect the placeholder hook; never apply a guessed global patch.
9. **Test exclusively.** If permitted, run a bounded automated gate for loader
   READY, generated tone HIT, real original MISS/fallback, audible duration,
   ordered start/stop, simultaneous-voice count, and clean exit. Capture logs and
   sink evidence against installed hashes. Existing playback, backlog, skip,
   volume, lips, and real dialogue require separate scoped checks. See
   [runtime-and-recovery.md](references/runtime-and-recovery.md).
10. **Journal removal.** Record added/overwritten files, original/candidate hashes,
    and legitimate runtime-generated config hashes. Uninstall only unchanged
    journal targets; retain edits for review. Recheck original hashes afterward.
    Ship designed voice deltas only when authorised, with exact install/removal
    instructions and licence provenance. Public contributions need owner approval.

## Evidence and handoff

Report manifest coverage and unmatched IDs, locked design hashes, accepted versus
rejected synthesis counts, calibration population/limits, owner listening status,
installed delta hashes, runtime scope/results, and uninstall journal. Distinguish
`prepared`, `static-valid`, `installed-and-byte-verified`, `loader-runtime-proven`,
and `owner-listening-approved`; never promote one from another.

The [pilot lessons](references/pilot-evidence.md) describe what worked and what
remained uncertain. Repository code/docs are MIT; third-party tools are referenced,
not vendored. Their licences and game rights remain separate.
