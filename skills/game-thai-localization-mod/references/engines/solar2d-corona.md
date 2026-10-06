# Solar2D / Corona resource.car

Read this when the game includes CoronaLabs.Corona.Native.dll, lua.dll, and
Resources/resource.car.

- resource.car starts with rac followed by byte 0x01.
- Its table contains Lua module names and offsets; payloads often start with a
  12-byte wrapper followed by Lua bytecode.
- Language modules commonly resemble classes.language.menu_en-us.lu and
  classes.language.menu_th.lu.
- If the selected English locale has matching shipped Thai modules, prefer
  swapping/repacking matching payloads over machine-translating them.
- For English modules without Thai counterparts, inspect constants and translate
  only player-facing strings. Preserve paths, module names, keys, and proper
  nouns governed by the glossary.
- Keep an explicit logical-module to physical-member map in preflight.
- Parse and repack; never insert longer strings into fixed binary slots.
- Validate every changed member, pack/unpack the whole archive, require an empty
  recursive diff, then hash the installed archive against the candidate.

The read-only inventory helper can identify likely language modules:

    python3 scripts/audit_game_text.py /path/to/game
