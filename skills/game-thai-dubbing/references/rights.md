# Rights and public payload

This is project policy, not a claim that a dataset licence grants every right to
a person's voice or to a game. Check consent, provenance, model terms, and the
game's mod/distribution conditions separately. Keep the exact licence/version,
source URL, attribution, and intended use in the private project ledger.

| Dataset licence | Project rule |
|---|---|
| CC0 | Eligible; retain provenance and check separate voice/personality rights |
| CC-BY | Eligible with required attribution and change notices |
| CC-BY-SA | Eligible for local work with attribution and applicable ShareAlike obligations; **never publish LoRA weights trained on this data** |
| Any NC variant | Forbidden in this workflow |
| Any ND variant | Forbidden in this workflow |
| Missing, ambiguous, or conflicting terms | Stop that dataset's use until resolved |

The no-BY-SA-weight-publication rule is a conservative project boundary, not a
legal conclusion about whether any particular training output is an adaptation.
Do not label outputs or weights MIT merely because this repository is MIT.
See the [Creative Commons licence overview](https://creativecommons.org/cc-licenses/)
and [CC0 deed](https://creativecommons.org/publicdomain/zero/1.0/).

Use independently designed voices. A lawful dataset does not authorise imitation
of an identifiable actor. Keep original game audio local and temporary for
measurement only; never condition, clone, train, upload, or distribute it.
Do not publish game binaries, bundles, dialogue, extracted text, subtitle joins,
original audio, or private owner details. A public adapter example may name a
game and its hook API; it must contain no extracted implementation or assets.

## Tools and licence note

Repository docs and generic scripts use the root [MIT licence](../../../LICENSE).
Tools, model weights, training data, runtime assemblies, and codecs have separate
terms. Tools below are referenced upstream, **not vendored**. Confirm the exact
version and its dependency notices before use; this list is not a redistribution
grant. The listen helper needs an already installed `agy` CLI and an owner-chosen
audio-capable model; no account setup or credentials are included.

- [UnityPy](https://github.com/K0lb3/UnityPy): local Unity metadata/inspection.
- [BepInEx](https://github.com/BepInEx/BepInEx) and
  [HarmonyX](https://github.com/BepInEx/HarmonyX): Mono loader and patching.
- [.NET SDK](https://github.com/dotnet/sdk): source-template compilation.
- [vgmstream](https://github.com/vgmstream/vgmstream): original-format decoding;
  it is not an encoder. Preserve codec/dependency notices if packaging tools.
- [VGAudio](https://github.com/Thealexbarney/VGAudio): prospective HCA encoding.
- [repak](https://github.com/trumank/repak) and
  [UAssetAPI](https://github.com/atenfyr/UAssetAPI): prospective UE asset work.
- [FFmpeg](https://ffmpeg.org/legal.html),
  [librosa](https://librosa.org/), [NumPy](https://numpy.org/), and
  [Pillow](https://python-pillow.github.io/): optional audio staging/plots.

No speech generator, LoRA, trained listener, dataset, game assembly, or compiled
plugin ships here. Choose synthesis/listener tools only after checking their
model and data terms; a code licence alone does not clear model weights.
