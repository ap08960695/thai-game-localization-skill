# Static Validation Contract

Use scripts/validate_localization.py as the central JSON/CSV gate. It uses only
the Python standard library and writes one machine-readable JSON document to
stdout.

## Commands

    python3 scripts/validate_localization.py --self-check --pretty
    python3 scripts/validate_localization.py /path/to/validation-manifest.json --pretty

Exit 0 means the declared scope is eligible for static-valid. Exit 1 means the
report contains blocking findings. Run the self-check after changing the script.

For syntax-only checks of other JSON release files, use
`jq -e '.' file >/dev/null`. Do not use `jq -e empty`: `empty` deliberately
emits no value, so `-e` returns status 4 even for valid JSON.

## Manifest

Version 1 uses this shape:

    {
      "version": 1,
      "glossary": "glossary.json",
      "coverage": {
        "ledger": "coverage.json",
        "required_runtime_sources": ["dialogue", "menu"]
      },
      "font_gate": {
        "mode": "metrics",
        "metrics": "fonts/ui.fnt",
        "pairs": ["dialogue", "menu"],
        "max_widths": {"menu.text": 420, "dialogue.text": 760},
        "max_lines": {"menu.text": 2, "dialogue.text": 4},
        "fit_exemptions": {
          "dialogue.speaker_name": "Auto-sized by the engine"
        }
      },
      "pairs": [
        {
          "name": "dialogue",
          "source": "source/dialogue.csv",
          "target": "thai/dialogue.csv",
          "format": "csv",
          "encoding": "utf-8",
          "id_fields": ["UID"],
          "locked_fields": ["speaker"],
          "text_fields": ["text"],
          "byte_limits": {"text": 1024}
        }
      ]
    }

Paths are relative to the manifest. For JSON, records may be a top-level list,
an object keyed by ID, or a list selected with records_path. Dot paths are
accepted for nested JSON fields. Encoding must be pinned; auto detection alone
is not static-valid evidence.

The glossary may be inline or a JSON path:

    {
      "case_sensitive": true,
      "preserve": ["HP", "SP", "Coromon"],
      "translations": {
        "Save": ["บันทึก", "เซฟ"],
        "Cancel": "ยกเลิก"
      },
      "allowed_unchanged": ["Coromon"]
    }

preserve requires the same occurrence count. translations requires an approved
target term whenever its source term occurs. allowed_unchanged applies only to
an entire unchanged field; prefer a row-level coverage reason for exceptions.

The coverage ledger uses:

    {
      "runtime_sources": [
        {
          "name": "dialogue",
          "status": "translated",
          "evidence": ["12,408 reviewed records"]
        },
        {
          "name": "news-panel",
          "status": "remote",
          "reason": "Downloaded after launch"
        }
      ],
      "entries": [
        {
          "pair": "dialogue",
          "id": "npc_001",
          "field": "text",
          "status": "intentionally-unchanged",
          "reason": "Character name"
        }
      ]
    }

Every required runtime source needs one classification and evidence or reason.
Row-level entries are for meaningful source text deliberately left identical.

## Encoding and Thai shaping gate

The validator detects UTF-8, UTF-8 BOM, CP874, and TIS-620 candidates, requires
decode/encode byte round-trip, and rejects a configured encoding that does not
match. CP874 and TIS-620 can be byte-ambiguous; pin the encoding from format or
engine evidence rather than guessing from bytes alone.

It also blocks replacement characters, embedded BOMs, orphaned Thai combining
marks, duplicate adjacent combining marks, encoding failures, and configured
per-field byte-limit overflow. This is a sanity gate, not a full shaping-engine
emulator; engine rendering still needs runtime proof when allowed.

## Font coverage and fit

font_gate must use one mode:

- metrics: validate glyph coverage and configured line/width limits from BMFont
  text/XML or the JSON metrics shape below;
- external-evidence: provide non-empty evidence from an engine/font inspection
  tool when metrics cannot be represented here;
- not-applicable: provide a reason why the declared pass renders no Thai text.

JSON font metrics:

    {
      "line_height": 48,
      "glyphs": {
        "32": 12,
        "3585": {"advance": 28}
      }
    }

Glyph keys are Unicode code points; advances use the same units as max_widths.
For bitmap fonts, verify that the metrics match the actual atlas candidate.
Width checks remove preserved control tokens and measure each declared line.
Use real UI box limits, not an arbitrary desktop width. Every checked text field
needs a width/line constraint or a non-empty fit_exemptions reason. Because
dynamic placeholder values are not present in the file, separately test their
worst-case rendered substitutions when they can affect fit.

The validator checks source/target record parity, ID order, locked fields,
placeholder multisets, literal and escaped newlines, glossary drift,
untranslated rows, coverage, hashes, encoding, byte limits, Thai mark sanity,
font glyphs, and configured width/line fit. Pack/unpack/archive integrity and
installed-byte verification remain separate required gates.

## Per-pass delta audit

Before packing, compare pristine source data with the working target for every
target archive. Assert the exact changed member, row IDs, and fields and reject
any other change. Keep the resulting JSON or equivalent with the validation
report. The central validator may not know a game's paired fields: if a field
such as `EnglishCensored` intentionally mirrors Thai, declare that policy in the
ledger/manifest and include the field in the expected delta rather than calling
it a regression. After full-archive packing, unpack to a fresh tree, recursively
diff against the intended candidate tree, and byte-compare every changed binary
member.
