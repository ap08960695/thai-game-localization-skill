# Unreal cooked PAK localization

Use this reference for cooked Unreal games whose runtime content includes
`.pak`, `.uasset`, `.uexp`, `.ubulk`, or serialized font assets.

## Inventory every override layer

- Inspect base locale data, `L10N`, platform/device trees such as `Platform/PC`,
  DLC, patches, and cooked UI overrides separately.
- Record duplicate IDs and archive priority. A complete generic English corpus
  does not cover a higher-priority PC-only table.
- Keep every companion file required by the cooked asset. Never distribute a
  patched `.uexp` while silently omitting its `.uasset` or `.ubulk`.
- Classify texture-baked text and platform-only prompts explicitly instead of
  allowing generic-table coverage to hide them.

## Patch serialized assets coherently

- Derive string encoding and length rules from the actual asset. Unreal
  `FString` commonly uses positive ANSI lengths and negative UTF-16 code-unit
  lengths, including the terminator; do not assume one representation.
- When replacement bytes change size, propagate the delta through every
  enclosing property/row/struct length plus export `SerialSize`,
  `SerialOffset`, `BulkDataStartOffset` or equivalent bulk-data offsets, and
  any asset-specific boundaries.
- Validate nested rows individually. A top-level export that parses does not
  prove hundreds of inner struct properties still end at the correct offsets.
- Assert the expected row/property counts, final boundaries, companion metadata,
  and exact translated values. Rebuild twice and require identical bytes.
- Treat an Unreal “corrupt data” dialog as a serialization failure first. Find
  the earliest bad boundary instead of deleting translated rows until it boots.

## Rebuild and verify the PAK

- Preserve the observed PAK version, mount point, path-hash seed, compression
  support, case, and relative member paths.
- Pack once, unpack to a fresh tree, recursively diff against intended staging,
  and byte-compare every member. Record member count and candidate hash.
- Inspect shipped engine configuration and current logs for PAK signing or
  encryption. `_P.pak` naming changes priority; it does not bypass a signature
  policy.
- A signed base can ignore an unsigned overlay without a visible error. Discover
  the build's supported loader option/plugin from local evidence. Do not
  generalize a switch such as `-fileopenlog` to another game or build.

## Prove the actual loader path

- Installed path and SHA-256 prove bytes only. Require the exact final executable
  to open the overlay through `fuser`, `lsof`, `/proc/<pid>/fd`, or a loader log.
- Use an injected loader option only as a diagnostic experiment. Final runtime
  proof must start normally through the intended launcher without adding the
  option to that test command, then show the persisted option in the final
  process command line.
- Bind proof to runner, account, config root, AppID, executable, installed PAK
  hash, and visible Thai frame. Host Steam and Playbeam may share the same game
  library while keeping different `localconfig.vdf` files and launch options.
- If one runner shows Thai and another shows English, compare active Steam
  process ownership, `HOME`, userdata account, recent `LastPlayed`/autocloud
  timestamps, final command line, and overlay handles before changing the PAK.

## Package and clean up honestly

- Put required launch options or plugins in the manifest and exact README flow;
  explain how to preserve existing options and remove only the mod's setting.
- Do not label the final archive runtime-proven merely because an equivalent
  development PAK worked. Install or stream-verify the payload from the final
  archive through the intended runner's normal launch.
- Use `zip -T` or read-only `unzip -t` for ZIP integrity. Uppercase
  `unzip -T` changes the archive timestamp and mutates evidence.
- If documentation or proof files change the archive after payload testing,
  report payload runtime proof and archive integrity separately until the final
  archive is retested.
- Delay delivery-only workspace deletion until the intended runner passes, or
  explicitly retain enough source/evidence to diagnose a failed user handoff.
