# Unity Addressables, Binary Text, and Thai Fonts

## Trace the loaded data

- Treat loose exports as leads, not runtime authority. Resolve the Addressables
  catalog, bundle, asset path/file ID, component, and live resolver that the
  observed surface uses.
- Inspect vendor binary databases such as BansheeGz/BGDatabase when no loose
  dialogue source exists. Prefer the vendor reader and install any missing
  toolchain locally inside the isolated game workspace; do not modify system
  packages solely for inspection.
- Inventory base-game and DLC/event databases separately. Count and classify
  excluded rows instead of folding them into a base-game completeness claim.
- Trace each visible component from prefab or scene through `TextMeshProUGUI`
  or legacy `Text`, its external font asset, material, atlas texture, and every
  selectable bundle variant. A working title font does not prove the dialogue
  route, and one TMP asset does not prove legacy UI.

## Rebuild font assets without thinning Thai

- Determine whether the texture stores bitmap alpha or signed-distance data
  before writing pixels. Preserve the original texture channel semantics and
  material properties; do not paste raw alpha into an SDF atlas.
- For a bitmap-alpha atlas, copy rendered alpha values directly. Do not use the
  same alpha image as both source and paste mask: that computes approximately
  `alpha²/255`, weakens antialiasing, and can make small Thai strokes appear as
  dots even though every codepoint exists.
- Keep the recorded glyph rectangle aligned to the actual rendered bitmap.
  Do not include an extra blank border inside the rectangle and then scale that
  rectangle as if it were ink; small glyphs become artificially shrunken.
- When each glyph owns `m_AtlasPadding` on both sides, reserve at least twice
  that padding between packed rectangles. Verify the exact geometry rather
  than reusing a generic one-pixel packer gap.
- Patch every font route proved reachable by the target surfaces. For legacy
  Unity `Font` assets, update texture and metrics together. Skip a textureless
  duplicate only after proving it is not a separate rendered route.
- Prefer a Thai face whose weight and proportions survive the game's actual
  size and contrast. Broad Unicode coverage is not a readability criterion;
  compare candidate faces on the same native bright, dark, short, and long
  dialogue surfaces.

## Diagnose by symptom

| Symptom | Likely fault | Required check |
| --- | --- | --- |
| Thai exists but looks like dots or hairlines | alpha was multiplied twice, glyph rectangle includes blank padding, or face is too light | inspect atlas alpha values and glyph rectangles, then compare the same runtime line |
| Marks clip or bleed into neighbors | packing gap and atlas padding disagree | calculate rectangle spacing and run strict overlap checks |
| Menu works but dialogue does not | different TMP/legacy font route | trace the exact visible component to its external font/material/texture |
| Offline glyph coverage passes but text is unreadable | weight, scale, SDF/alpha, contrast, or mark placement fault | inspect current native frames; do not rewrite the translation |
| A rebuilt bundle passes while the game still shows the old result | the running process retained old assets | hash live files, relaunch the exact game, and capture a fresh frame |

## Gate each revision

1. Record pristine, candidate, and live bundle hashes and sizes.
2. Assert required Thai codepoint coverage, strict rectangle non-overlap,
   valid texture bounds, unchanged unrelated mappings, and deterministic
   second-build hashes.
3. Install transactionally and byte-compare every live bundle to the candidate.
4. Relaunch the exact executable after any bundle-byte change.
5. Revisit the same menu and dialogue lines, including upper/lower marks,
   punctuation, wrapping, and one long sentence.
6. Bind each capture path, dimensions, SHA-256, input route, executable state,
   and live bundle hashes to that revision only.
