# thai-game-localization-skill

An agent skill (for Claude Code, Codex and other `SKILL.md`-compatible agents)
plus stdlib-only Python checkers for building **context-aware Thai localization
mods** for installed games.

> ชุดเครื่องมือสำหรับทำม็อดแปลเกมเป็นภาษาไทยอย่างเป็นระบบ: หาแหล่งข้อความจริงตอนรันเกม,
> แปลตามบริบทฉาก, รักษา placeholder/control token ให้ครบ, ปรับฟอนต์ไทย,
> แพ็กและติดตั้งแบบ transactional และตรวจก่อนปล่อยด้วยสคริปต์

## What is inside

| Path | Purpose |
|------|---------|
| `skills/game-thai-localization-mod/SKILL.md` | The workflow: trace runtime text, translate in context, preserve format invariants, install transactionally, prove only what you are allowed to prove |
| `skills/game-thai-localization-mod/references/` | Validation gates, install recovery, overlay refinement, batch translation, Thai font cluster spacing, release-gate lessons |
| `skills/game-thai-localization-mod/references/engines/` | Engine notes: Unity (Addressables/fonts), Unreal (cooked pak), Larian DOS2, Klei, Solar2D/Corona |
| `skills/game-thai-localization-mod/scripts/validate_localization.py` | Locale-pack validator: ID/order parity, placeholder and control-token multisets, newlines, Thai combining marks, line width. Run `--self-check` to see it pass a good fixture and catch a broken one |
| `skills/game-thai-localization-mod/scripts/audit_game_text.py` | Audit a game tree for text sources |
| `skills/game-thai-localization-mod/evals/evals.json` | Behavioural evals for the skill |

Python 3.9+, standard library only.

## Use

Copy or symlink the skill directory into your agent's skills folder, e.g.

```bash
cp -r skills/game-thai-localization-mod ~/.claude/skills/
```

Validate a locale pack:

```bash
python3 skills/game-thai-localization-mod/scripts/validate_localization.py --self-check
python3 skills/game-thai-localization-mod/scripts/validate_localization.py manifest.json --pretty
```

The manifest format is described in
`skills/game-thai-localization-mod/references/validation.md`.

## Scope and legal

This repo contains **workflow and tooling only**. It does not contain game
assets, game text, or translated game text. Only translate and distribute text
for games you own and in ways the game's license and the rights holders allow.
Most games' text is copyrighted: share patches or tools, not extracted game
files.

## License

MIT. See [LICENSE](LICENSE).
