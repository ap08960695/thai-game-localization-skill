# Klei / Don't Starve

Read this when the game includes Klei Lua scripts, data/scripts/languages/*.po,
strings.pot, or ~/.klei/DoNotStarve/log.txt.

- Treat PO files as one runtime source, not the only source. Inspect Lua such as
  frontend.lua, constants, event/promo UI, and downloaded panels visible in
  evidence.
- Validate PO with msgfmt -c or an equivalent parser. Header warnings are
  reportable; placeholder errors are blockers.
- Font archives such as data/fonts/buttonfont.zip and thaiui50.zip may contain
  .fnt metrics and .tex atlases. Boxes or blank Thai can mean an atlas
  orientation/metrics mismatch rather than missing translations.
- Prefer the game's existing .tex toolchain. A prior Don't Starve repair used
  ktools/ktech and DXT5 repacking to correct a flipped atlas/metrics mismatch;
  treat that as a format clue, not a universal command.
- Test every font zip with unzip -t. When runtime testing is permitted, inspect
  ~/.klei/DoNotStarve/log.txt for language/font errors and capture current
  screenshot evidence.
- Do not call a static menu screenshot a hang. Check process state, log movement,
  screenshot changes, and the actual input path.
- Event/news/promo text such as More Info may be remote or image-baked. Trace
  it before adding speculative PO entries.

Font acceptance still follows the generic art-direction and line-fit bar in the
main skill; rendering glyphs alone is insufficient.
