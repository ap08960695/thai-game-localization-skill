# Manifest, voice lock, guide, and calibrated gates

## Private manifest

Each joined row needs `voice_id`, `text_key`, `speaker_key`, `scene`, `thai_text`,
`sample_rate`, `channels`, `duration_s`, `nonverbal`, and source/build hashes.
These are schema names only; do not commit real rows. Record unjoined calls and
unreferenced assets separately. Nonverbal rows need an explicit policy: designed
performance, intentional unchanged original fallback, or out of scope.

A guide records ordered active spans, breath candidates, pause intervals, and
total frame duration. A target profile records measured ranges and uncertainty,
not the original speaker's embedding. Measure original audio locally, keep
numeric analysis private, and verify temporary decoded audio was removed.

## Voice lock and segment synthesis

A design lock records anchor/prompt hashes, its own prompt transcript, character
sheet, seed/model/settings, and emotion scope. Conditioning with a reference
alone can preserve timbre while pitch still drifts; the pilot improved consistency
using the **same own-designed anchor plus synthetic prompt continuation**.
Keep the accepted lock-source line fixed instead of generating it again. Never
reuse another character's accepted line or original actor audio for a failed design.

Group Thai phrases monotonically onto active guide segments. Strong boundaries
come from punctuation, scripted pauses, or breath cues. Synthesize speech groups
separately; guide breath candidates must not become lexical speech. Place phrases
at guide onsets with deliberate gaps. Designed breath effects are separate from
speech; do not copy original breaths.

Measure articulation on speech-only material, excluding planned silence. If a
take is too fast, slow that speech group before placement using a pitch-preserving
method, then rerun pace and signal checks. Keep breaths and guide onsets fixed.
Only a bounded fit acceleration is allowed (the pilot used a 1.08 ceiling);
choose and record the bound before synthesis. Pad to the exact guide frame count;
never cut a tail, word, or breath merely to meet the duration. Reject impossible
fits. Matching total duration does not prove pauses or acting match.

## Gate calibration

Keep raw float, fitted float, and delivered PCM16 receipts. Record every seed's
score and rejection, including discarded seeds from an eventually accepted line.
Preserve failure audio long enough to investigate it. Replaying cached numbers
under a new threshold changes flags; it does not create newly accepted takes.

- **Signal:** validate format/chunk sizes, nonempty aligned frames, exact rate/
  channels, duration, clipping, true peak, silence/tails, and finite values.
  The bundled validator covers PCM format/frames/sample peak; use separate
  true-peak and loudness measurement. Never relax the peak ceiling to reach an
  infeasible LUFS target: back off gain and record the shortfall.
- **Spectral quality:** measure clean licensed real Thai speech with the same
  resampling/windows/metric. Include age/style/microphone relevance, shouting,
  and negative noise controls. An anchor-relative harshness bound alone rejected
  clean real speech in the pilot. PCM16 quantization also raised full-band
  flatness: calibrate raw float and final PCM16 separately. A percentile is an
  empirical bound for that population, not universal proof of naturalness.
- **Pace/F0/identity:** derive per-line pace from guide active time and a measured
  real-Thai dialogue range. Keep planned gaps out of articulation. Check pitch
  windows and similarity against the **designed anchor**, not the original actor.
  A real pace failure needs correction to delivery, not automatic window widening.
- **Thai text/tones:** compare primary ASR with the intended Thai text and inspect
  confidence; secondary-ASR disagreement is a diagnostic, not automatically a
  tone error. Calibrate disagreement on gold real speech, separately for short
  reactions and shouting. The pilot retained a strict primary CER/confidence
  gate while relaxing the secondary veto only in a calibrated trusted regime.
  Exact primary text/confidence was still required for its short-word exception.
  Weak ASR labels do not establish a false-reject rate. Do not invent a phonetic
  spelling or waive proper-name text merely because no gold name clip exists.

Store calibration population, counts, preprocessing, percentiles, thresholds,
controls, false rejects, and limitations. Recalibrate when delivery encoding or
the metric changes. AI listener and owner checks remain separate from these gates.
