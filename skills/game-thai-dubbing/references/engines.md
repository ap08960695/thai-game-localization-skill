# Engine adapters

## Unity Mono + BepInEx — proven pilot seam

Detect Mono from the installed managed assemblies; do not infer it from the
Unity name alone. Use a loader compatible with the installed Unity/runtime and
architecture. The pilot used BepInEx 5, HarmonyX, and a `net46` plugin. A successful
SDK build on another runtime is not Unity Mono patch execution proof.

Inspect the managed request path and exact iterator's IL. Replace exactly one
`AudioSource.clip` assignment in the shared voice iterator; retain instruction
labels and exception blocks. The game still loads its original clip, supplies
volume, calls Play, and stops/skips via its existing channel. A missing original
asset cannot be repaired by this late assignment seam.

The template's `GAME_VOICE_CONTAINER_TYPE` and `<GAME_VOICE_COROUTINE>` are
deliberate placeholders. In one Unity Mono title, the observed example was a
voice coroutine's `AudioSource.clip` assignment, with one matching setter in the
target iterator:

```text
target: shared voice coroutine iterator
operation: replace AudioSource.clip assignment
expected matching assignments: 1
```

This is a technique example, not a portable ABI promise. Reinspect each build;
the compiler-generated state-machine structure can change. The template omits
the pilot's title controller, hardcoded scene IDs, bundle paths, and automated
launch adapter. Create that test adapter privately from the game's real request
API.

Build with owner-local assemblies referenced with `Private=false`:

```bash
dotnet build scripts/plugin/ThaiVoiceOverride.csproj -c Release \
  -p:GameManagedDir="<game-managed-dir>" -p:BepInExDir="<bepinex-core-dir>"
```

The placeholder hook deliberately disables overrides until adapted. The project
needs the appropriate .NET reference assemblies via NuGet; dependencies and
compiled output must stay out of a public source-only contribution.

Lookup uses the original clip name as voice ID; loose files live under
`BepInEx/plugins/ThaiVoiceOverride/voices/`. HIT/MISS/OVERRIDE/FALLBACK logs are
required. The WAV decoder enforces RIFF chunk bounds, PCM16, mono/stereo, 8–192 kHz,
alignment, and a 64 MiB file limit. Clips stay cached until restart; stage only
the selected scene and budget decoded float PCM memory, not just WAV disk bytes.
The voice folder and files must be trusted local regular paths, with no symlink
escape from the plugin subtree.

## CRI/HCA — surveyed, unproven replacement adapter

Identify ACB cue metadata, AWB/AFS2 storage, and any CPK outer container separately.
Join cue names/indices to text keys before encoding. A successful HCA decode does
not prove encode/rebuild support. Preserve sample counts, cue lengths, AFS2 offsets,
alignment, ACB metadata, and encryption mode/key requirements. Round-trip a single
owner-local cue and test fallback/timing before scaling. Never publish keys or
original archives. The pilot survey found plausible HCA routes, but no accepted
CRI replacement/runtime test. Tools with unclear licences are not cleared.

## Wwise — surveyed, unproven replacement adapter

Trace dialogue event → media ID → localized bank/media → subtitle key. WEM files
are encoded media, not renamed WAVs. Match codec, seek tables, bank/event lengths,
and cooked metadata; decode tooling does not imply a compatible encoder. An
archive route used by a text mod does not establish Wwise audio replacement.
No accepted Wwise audio repack or runtime gate was established in this pilot.

## Unreal cooked PAK — surveyed, unproven dubbing adapter

Classic PAK and IoStore (`.utoc/.ucas`) require different tooling. Identify cooked
assets, localization path, mount precedence, and the underlying audio middleware.
Where supported, prefer an additive delta PAK, preserving mount paths and asset
metadata. Validate packing by fresh extraction and exact delta comparison; then
prove in-game cue resolution. Merely listing/repacking a PAK or a prior text patch
does not prove changed audio plays. Encryption, signing, and game restrictions
can block the route; do not bypass them. UE audio replacement remains unproven here.
