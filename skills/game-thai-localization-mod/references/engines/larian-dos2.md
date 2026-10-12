# Larian DOS2 PAK, Nexus Merge, and Release

## Contents

- Freeze the DOS2 identity and path map
- Audit every upstream payload root
- Build the locale archive
- Separate rendering from wording QA
- Package and clean up safely

Use this reference for Divinity: Original Sin 2 Definitive Edition, Larian PAK
work, or a Nexus overlay that combines an `English.pak` with loose font assets.

## Freeze the DOS2 identity and path map

- Allow only AppID `435150`, final executable `EoCApp.exe`, launcher helper
  `SupportTool.exe`, and the verified `DefEd/Data` targets.
- Record host and stream-runtime/container paths separately. Resolve their mounts and
  hashes before treating `<host-home>/...` and `<runtime-home>/...` as the same
  install; a process command line can expose a container alias, not a safe host
  deletion target.
- Use Norbyte LSLib/Divine for Larian PAKs. Do not infer PAK validity from `7z`;
  pack, list, extract to a fresh tree, and recursively compare the result.

## Audit every upstream payload root

- Hash and safely list the complete third-party archive before extracting it.
  DOS2 Nexus archives can store Windows separators literally, so do not assume
  `unzip -Z1` names are normalized POSIX paths. Reject traversal, absolute,
  duplicate, case-colliding, link, and executable surprises.
- Map every functional payload, not only the primary PAK:
  - merge reviewed Thai rows from `Localization/English.pak` into the final
    dedicated locale PAK and mark the raw `English.pak` as superseded;
  - include required `Public/Game/GUI/fonts` assets byte-identically when they
    are not already inside the final release payload;
  - include the locale selector and every story/mod override required by the
    running install.
- Record each upstream member as `included-byte-identical`, `merged`,
  `superseded`, or `excluded` with a reason. Record archive hash, imported-row
  counts, font hashes, and local-use/publication authority in package-relative
  provenance.
- Do not let a patched development install prove package completeness. A game
  can render Thai because a prior pass put fonts in `Game.pak` even when the
  release ZIP omitted the original loose-font dependency. Compare the release
  against the full upstream member map and, when authorized, a fresh official
  baseline.

## Build the locale archive

- Freshly extract the live locale PAK for each revision and keep pristine
  English, the Nexus reference, and current Thai as separate inputs.
- Parse bilingual `English (Thai)` rows defensively. Import only reviewed rows
  whose IDs, source text, markup, tokens, and line structure are safe; preserve
  unresolved control tokens and untranslated/unsafe rows explicitly.
- Prefer a dedicated `Localization/Thai.pak` plus `language.lsx` selector when
  runtime evidence shows an edited English slot remains fallback English.
- Audit the exact expected content IDs, XML validity, member count, and
  pack-unpack semantic equality before atomic installation.

## Separate rendering from wording QA

- Classify findings independently as glyph/render failure, readability/layout
  failure, or lexical/mixed-language residue. Correct Thai rendering does not
  make labels such as `Hotbar`, `Journal`, or parenthetical English complete.
- Prove title/menu, dialogue, HUD, pause, journal/radial, and item-context
  surfaces separately. A real gameplay dialogue/HUD frame is required when the
  user asks for gameplay evidence; a menu, setup screen, or cinematic is not a
  substitute.
- Bind runtime proof to the exact installed PAK hash and only the surfaces
  reopened after that revision. Keep unreachable post-restart panels at
  source-and-package-verified rather than promoting them from older captures.

## Package and clean up safely

- Make one private, self-contained release containing the merged locale PAK,
  byte-identical upstream fonts, selector, required overrides, README,
  manifest, provenance, QA evidence, and `SHA256SUMS`. Explain why a superseded
  raw `English.pak` is not installed beside the final locale PAK.
- Build and independently extract a candidate ZIP outside every deletion root.
  Keep the previous final ZIP until the candidate passes integrity, JSON,
  manifest-member, checksum, font-byte, and README gates; replace the final ZIP
  atomically only after those checks.
- For JSON syntax validation use `jq -e '.' file >/dev/null`; `jq -e empty`
  exits 4 because it emits no value. When reading archive members whose stored
  names contain backslashes, normalize through safe extraction or verify an
  exact single match before hashing.
- Before stopping DOS2, verify the exact PID and `/proc/<pid>/cmdline`, send
  `TERM` only to `EoCApp.exe`, wait, then handle `SupportTool.exe` only if its
  exact process remains. Avoid full-command `ps | rg` gates that match the
  scanner itself; prefer `comm`, known PIDs, and independent handle checks.
- Treat “delete the game folder” as ambiguous among workspace, live Steam
  install, and sibling-game workspace. Resolve the literal target after the
  latest user message, recheck mount/handles, keep the verified package
  outside it, delete only that exact path, and re-hash the package afterward.
