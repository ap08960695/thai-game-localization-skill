# AI pre-filter and owner ear

Ask whether the candidate is intelligible, natural, correctly acted, consistent
with the designed voice, and suitable for the scene. Keep these dimensions
separate from signal quality. ASR agreement, F0, or a clean spectrogram cannot
certify Thai tones, perceived age, or character fit.

For attribute calibration, use blind filenames/order with no transcript, actor
name, target age, or expected answer. For a separate pronunciation/fit review,
supply the intended Thai line and character sheet; label those judgements as
context-assisted. Avoid claiming a model actually heard a file unless its backend
supports audio and the response demonstrates access. Tool failure, missing JSON,
or unsupported input is `UNVERIFIED`, never PASS.

Use owner-rated A/B samples, repeatable prompts, and matched playback level to
check listener agreement. Keep naturalness/fit/pronunciation decisions and owner
disagreements. Scores are ordinal suggestions, not ground truth; calibration on
another language or microphone does not prove Thai animated acting performance.
The owner selects the design and approves the final takes by ear.

## Adapted listen panel scripts

The pilot's scripts existed and are included under `scripts/listen/`:

- `listen_ai.py`: serial file staging, hosted `agy` review, strict response parser,
  at most two attempts, structured failure records. The owner chooses an available
  audio-capable model through `THAI_LISTENER_MODEL`. The CLI and model are external.
- `viz_audio.py`: CPU mel/F0/RMS and metric comparison plots; needs NumPy, librosa,
  and Pillow. Its 60–500 Hz analysis window is a plotting default, not a gate or
  universal character pitch range. Thai alphabetic chars/s is a coarse display
  metric, not the synthesis articulation metric.
- `panel.py`: combines reports and plots. It sends the supplied character sheet
  and optional text to the listener, so it is **context-assisted fit review**, not
  a blind age/tone calibration. Use a neutral sheet/no text for exploratory blind
  review; for rigorous attribute calibration use a separate blind protocol.
- `test_listen_ai.py`: offline parser and prompt tests; no backend call.

Use only owner-authorised designed takes. Do not send originals, copyrighted
dialogue, or private metadata to a hosted service without separate permission.
Check retention/use terms before uploading. GPU visibility is disabled in the
scripts, but plots can be CPU-heavy: run them after synthesis has stopped.
No new installation, credentials, model download, or upload is automatic.

```bash
python3 scripts/listen/viz_audio.py "<designed-take.wav>" --out-dir "<private-plots-dir>"
# After upload permission and external CLI setup:
THAI_LISTENER_MODEL="<audio-capable-model>" python3 scripts/listen/panel.py \
  "<designed-takes-dir>" --character "<private-character-sheet>" \
  --out-dir "<private-listen-dir>"
```

WAVs are staged as MP3 for the backend; lossy conversion/model preprocessing can
change brightness or high-frequency evidence. Measure those properties locally
on delivery PCM. Model errors contain no raw backend output. Reports contain
private local paths/text: keep generated results and plots out of public commits.
