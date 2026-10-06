#!/usr/bin/env python3
"""Validate JSON/CSV game-localization pairs and emit a JSON report.

The validator is intentionally Python-standard-library only. Configure it with a
manifest described in references/validation.md, or run --self-check to exercise
both a passing fixture and a deliberately broken token fixture.
"""

from __future__ import annotations

import argparse
import codecs
import collections
import csv
import hashlib
import io
import json
import re
import tempfile
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(
    r"<[^>\n]+>|\[f\d+[^\]\n]*\]|\{[^{}\n]+\}|"
    # A space after a prose percentage (for example, "counterattack % is")
    # is not a printf space flag. Keep real printf placeholders such as %s,
    # %d, and %1$s protected without classifying natural-language percentages.
    r"(?<![\d}])%(?:\([^)]+\))?(?:\d+\$)?[-+#0']*\d*(?:\.\d+)?[diouxXeEfFgGcrsaqp%]"
)
FONT_PAYLOAD_RE = re.compile(r"\[f(\d+).+\]")
NEWLINE_RE = re.compile(r"\\r\\n|\\n|\\r|\r\n|\n|\r")
THAI_COMBINING = {
    "\u0e31",
    *map(chr, range(0x0E34, 0x0E3B)),
    *map(chr, range(0x0E47, 0x0E4F)),
}
SOURCE_COVERAGE_STATUSES = {
    "translated",
    "intentionally-unchanged",
    "image-baked",
    "remote",
    "out-of-scope",
}
MAX_ISSUE_DETAILS = 500


class ValidationFailure(Exception):
    """Raised for a manifest or input that cannot be validated safely."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def new_report(manifest: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "manifest": str(manifest),
        "ok": False,
        "eligible_stage": None,
        "summary": {
            "pairs": 0,
            "source_records": 0,
            "target_records": 0,
            "text_cells": 0,
            "translated_cells": 0,
            "intentionally_unchanged_cells": 0,
            "errors": 0,
            "warnings": 0,
        },
        "pairs": [],
        "files": [],
        "coverage": {},
        "font_gate": {},
        "issues": [],
        "issue_details_truncated": 0,
    }


def add_issue(
    report: dict[str, Any],
    severity: str,
    code: str,
    message: str,
    *,
    pair: str | None = None,
    record_id: str | None = None,
    field: str | None = None,
) -> None:
    key = "errors" if severity == "error" else "warnings"
    report["summary"][key] += 1
    issue = {"severity": severity, "code": code, "message": message}
    if pair is not None:
        issue["pair"] = pair
    if record_id is not None:
        issue["record_id"] = record_id
    if field is not None:
        issue["field"] = field
    if len(report["issues"]) < MAX_ISSUE_DETAILS:
        report["issues"].append(issue)
    else:
        report["issue_details_truncated"] += 1


def canonical_encoding(name: str) -> str:
    aliases = {
        "utf8": "utf-8",
        "utf_8": "utf-8",
        "utf-8-bom": "utf-8-sig",
        "utf8-bom": "utf-8-sig",
        "windows-874": "cp874",
        "windows874": "cp874",
        "tis620": "tis-620",
    }
    normalized = aliases.get(name.strip().lower(), name.strip().lower())
    try:
        codecs.lookup(normalized)
    except LookupError as exc:
        raise ValidationFailure(f"unsupported encoding: {name}") from exc
    return normalized


def encoding_candidates(raw: bytes) -> list[str]:
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return ["unsupported-utf16-bom"]
    candidates: list[str] = []
    if raw.startswith(codecs.BOM_UTF8):
        try:
            if raw.decode("utf-8-sig").encode("utf-8-sig") == raw:
                candidates.append("utf-8-sig")
        except UnicodeError:
            pass
    else:
        for encoding in ("utf-8", "cp874", "tis-620"):
            try:
                if raw.decode(encoding).encode(encoding) == raw:
                    candidates.append(encoding)
            except UnicodeError:
                pass
    if raw and all(byte < 0x80 for byte in raw):
        return ["ascii", "utf-8", "cp874", "tis-620"]
    return candidates


def decode_file(path: Path, configured: str) -> tuple[str, dict[str, Any]]:
    raw = path.read_bytes()
    candidates = encoding_candidates(raw)
    if "unsupported-utf16-bom" in candidates:
        raise ValidationFailure(f"{path}: UTF-16 BOM is outside the supported gate")
    if not candidates:
        raise ValidationFailure(
            f"{path}: bytes do not round-trip as UTF-8, CP874, or TIS-620"
        )
    selected = canonical_encoding(configured)
    if selected == "auto":
        selected = "utf-8-sig" if "utf-8-sig" in candidates else candidates[0]
    comparable = [candidate for candidate in candidates if candidate != "ascii"]
    if selected not in comparable:
        raise ValidationFailure(
            f"{path}: configured {selected}, detected candidates {', '.join(candidates)}"
        )
    try:
        text = raw.decode(selected)
    except UnicodeError as exc:
        raise ValidationFailure(f"{path}: cannot decode as {selected}: {exc}") from exc
    round_trip = text.encode(selected) == raw
    if not round_trip:
        raise ValidationFailure(f"{path}: {selected} decode/encode round-trip changed bytes")
    detected = "ascii" if candidates[0] == "ascii" else candidates[0]
    return text, {
        "configured_encoding": configured,
        "used_encoding": selected,
        "detected_encoding": detected,
        "encoding_candidates": candidates,
        "bom": "utf-8" if raw.startswith(codecs.BOM_UTF8) else None,
        "round_trip": round_trip,
        "bytes": len(raw),
    }


def resolve_path(base: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (base / path).resolve()


def field_get(value: Any, path: str) -> Any:
    current = value
    if path == "":
        return current
    for segment in path.split("."):
        if isinstance(current, dict) and segment in current:
            current = current[segment]
        elif isinstance(current, list) and segment.isdigit():
            index = int(segment)
            if index >= len(current):
                raise KeyError(path)
            current = current[index]
        else:
            raise KeyError(path)
    return current


def json_records(data: Any, records_path: str | None) -> list[dict[str, Any]]:
    container = field_get(data, records_path) if records_path else data
    if isinstance(container, list):
        if not all(isinstance(row, dict) for row in container):
            raise ValidationFailure("JSON record list contains a non-object value")
        return list(container)
    if isinstance(container, dict) and all(
        isinstance(row, dict) for row in container.values()
    ):
        records = []
        for key, row in container.items():
            copied = dict(row)
            copied.setdefault("__key__", key)
            records.append(copied)
        return records
    raise ValidationFailure(
        "JSON records must be a list of objects or an object keyed by record ID"
    )


def load_records(
    path: Path,
    file_format: str,
    encoding: str,
    records_path: str | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    text, metadata = decode_file(path, encoding)
    if file_format == "json":
        try:
            records = json_records(json.loads(text), records_path)
        except json.JSONDecodeError as exc:
            raise ValidationFailure(f"{path}: invalid JSON: {exc}") from exc
    elif file_format == "csv":
        if records_path:
            raise ValidationFailure("records_path is only valid for JSON pairs")
        try:
            reader = csv.DictReader(io.StringIO(text, newline=""))
            if not reader.fieldnames:
                raise ValidationFailure(f"{path}: CSV has no header")
            records = list(reader)
        except csv.Error as exc:
            raise ValidationFailure(f"{path}: invalid CSV: {exc}") from exc
    else:
        raise ValidationFailure(f"unsupported pair format: {file_format}")
    metadata.update({"path": str(path), "sha256": sha256_file(path), "format": file_format})
    return records, metadata


def record_identifier(record: dict[str, Any], id_fields: list[str]) -> str:
    values = []
    for field in id_fields:
        try:
            value = field_get(record, field)
        except KeyError as exc:
            raise ValidationFailure(f"record is missing ID field {field}") from exc
        if value is None or value == "":
            raise ValidationFailure(f"record has an empty ID field {field}")
        values.append(str(value))
    return "|".join(values)


def token_counter(text: str) -> collections.Counter[str]:
    tokens = []
    for token in TOKEN_RE.findall(text):
        font_payload = FONT_PAYLOAD_RE.fullmatch(token)
        tokens.append(f"[f{font_payload.group(1)}]" if font_payload else token)
    return collections.Counter(tokens)


def newline_counter(text: str) -> collections.Counter[str]:
    return collections.Counter(NEWLINE_RE.findall(text))


def meaningful_text(text: str) -> bool:
    stripped = TOKEN_RE.sub("", text)
    stripped = NEWLINE_RE.sub("", stripped)
    return bool(re.search(r"[A-Za-z0-9\u0e00-\u0e7f]", stripped))


def thai_sanity_issues(text: str) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    if "\ufffd" in text:
        issues.append(("replacement_character", "contains Unicode replacement character U+FFFD"))
    if "\ufeff" in text:
        issues.append(("embedded_bom", "contains an embedded byte-order mark"))
    cluster_has_thai = False
    previous = ""
    for index, char in enumerate(text):
        if char in THAI_COMBINING:
            if not cluster_has_thai:
                issues.append(
                    (
                        "thai_orphan_combining_mark",
                        f"Thai combining mark U+{ord(char):04X} has no preceding Thai base at character {index}",
                    )
                )
            if previous == char:
                issues.append(
                    (
                        "thai_duplicate_combining_mark",
                        f"duplicate Thai combining mark U+{ord(char):04X} at character {index}",
                    )
                )
        elif "\u0e00" <= char <= "\u0e7f":
            cluster_has_thai = True
        elif char.isspace() or unicodedata.category(char)[0] in {"P", "C", "S"}:
            cluster_has_thai = False
        else:
            cluster_has_thai = False
        previous = char
    return issues


def load_json_reference(base: Path, value: Any, label: str) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        raise ValidationFailure(f"{label} must be an object or JSON file path")
    path = resolve_path(base, value)
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationFailure(f"cannot load {label} {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValidationFailure(f"{label} root must be a JSON object")
    return data


def glossary_contains(text: str, term: str, case_sensitive: bool) -> bool:
    # Proper names must not match as prefixes inside unrelated English words
    # (for example, Haru must not match Harumph).
    if term and term[0].isascii() and term[0].isupper():
        flags = 0 if case_sensitive else re.IGNORECASE
        return re.search(
            rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])",
            text,
            flags,
        ) is not None
    if case_sensitive:
        return term in text
    return term.casefold() in text.casefold()


def glossary_count(text: str, term: str, case_sensitive: bool) -> int:
    if case_sensitive:
        return text.count(term)
    return text.casefold().count(term.casefold())


def unchanged_allowed_by_preserve(text: str, preserve: list[str]) -> bool:
    remainder = text
    for term in sorted(preserve, key=len, reverse=True):
        remainder = remainder.replace(term, "")
    remainder = TOKEN_RE.sub("", remainder)
    remainder = NEWLINE_RE.sub("", remainder)
    return not re.search(r"[A-Za-z0-9\u0e00-\u0e7f]", remainder)


def load_coverage(
    manifest: dict[str, Any],
    base: Path,
    pair_names: list[str],
    report: dict[str, Any],
) -> dict[tuple[str, str, str], dict[str, Any]]:
    config = manifest.get("coverage")
    if not isinstance(config, dict) or "ledger" not in config:
        add_issue(
            report,
            "error",
            "coverage_contract_missing",
            "manifest.coverage.ledger is required",
        )
        return {}
    try:
        ledger = load_json_reference(base, config["ledger"], "coverage ledger")
    except ValidationFailure as exc:
        add_issue(report, "error", "coverage_ledger_unreadable", str(exc))
        return {}

    sources = ledger.get("runtime_sources", [])
    if not isinstance(sources, list):
        add_issue(report, "error", "coverage_sources_invalid", "runtime_sources must be a list")
        sources = []
    source_map: dict[str, dict[str, Any]] = {}
    for source in sources:
        if not isinstance(source, dict) or not isinstance(source.get("name"), str):
            add_issue(report, "error", "coverage_source_invalid", "each runtime source needs a name")
            continue
        name = source["name"]
        if name in source_map:
            add_issue(report, "error", "coverage_source_duplicate", f"duplicate runtime source: {name}")
            continue
        status = source.get("status")
        if status not in SOURCE_COVERAGE_STATUSES:
            add_issue(
                report,
                "error",
                "coverage_status_invalid",
                f"runtime source {name} has invalid status {status!r}",
            )
        if not source.get("reason") and not source.get("evidence"):
            add_issue(
                report,
                "error",
                "coverage_evidence_missing",
                f"runtime source {name} needs reason or evidence",
            )
        source_map[name] = source

    required = config.get("required_runtime_sources", pair_names)
    if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
        add_issue(
            report,
            "error",
            "coverage_required_sources_invalid",
            "required_runtime_sources must be a string list",
        )
        required = pair_names
    for name in required:
        if name not in source_map:
            add_issue(
                report,
                "error",
                "coverage_source_missing",
                f"runtime source has no coverage classification: {name}",
            )

    entry_map: dict[tuple[str, str, str], dict[str, Any]] = {}
    entries = ledger.get("entries", [])
    if not isinstance(entries, list):
        add_issue(report, "error", "coverage_entries_invalid", "coverage entries must be a list")
        entries = []
    for entry in entries:
        if not isinstance(entry, dict):
            add_issue(report, "error", "coverage_entry_invalid", "coverage entry must be an object")
            continue
        try:
            key = (str(entry["pair"]), str(entry["id"]), str(entry["field"]))
        except KeyError:
            add_issue(
                report,
                "error",
                "coverage_entry_invalid",
                "coverage entry needs pair, id, and field",
            )
            continue
        if key in entry_map:
            add_issue(report, "error", "coverage_entry_duplicate", f"duplicate coverage entry: {key}")
            continue
        if entry.get("status") != "intentionally-unchanged":
            add_issue(
                report,
                "error",
                "coverage_entry_status_invalid",
                f"row-level entry {key} must use intentionally-unchanged",
            )
        if not entry.get("reason"):
            add_issue(
                report,
                "error",
                "coverage_entry_reason_missing",
                f"row-level entry {key} needs a reason",
            )
        entry_map[key] = entry

    report["coverage"] = {
        "required_runtime_sources": required,
        "classified_runtime_sources": len(source_map),
        "row_exceptions": len(entry_map),
    }
    return entry_map


def encoding_for_pair(pair: dict[str, Any], side: str) -> str:
    configured = pair.get("encoding")
    if isinstance(configured, str):
        return configured
    if isinstance(configured, dict) and isinstance(configured.get(side), str):
        return configured[side]
    raise ValidationFailure(
        f"pair {pair.get('name', '<unnamed>')} must pin encoding as a string or source/target object"
    )


def infer_format(pair: dict[str, Any], source: Path) -> str:
    configured = pair.get("format")
    if configured:
        return str(configured).lower()
    suffix = source.suffix.lower().lstrip(".")
    if suffix in {"json", "csv"}:
        return suffix
    raise ValidationFailure(f"cannot infer JSON/CSV format from {source}")


def pair_ids(
    records: list[dict[str, Any]],
    id_fields: list[str],
    report: dict[str, Any],
    pair_name: str,
    side: str,
) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for index, record in enumerate(records):
        try:
            identifier = record_identifier(record, id_fields)
        except ValidationFailure as exc:
            add_issue(
                report,
                "error",
                "record_id_invalid",
                f"{side} row {index}: {exc}",
                pair=pair_name,
            )
            identifier = f"__invalid_{side}_{index}"
        if identifier in seen:
            add_issue(
                report,
                "error",
                "record_id_duplicate",
                f"duplicate {side} record ID: {identifier}",
                pair=pair_name,
                record_id=identifier,
            )
        seen.add(identifier)
        result.append(identifier)
    return result


def compare_glossary(
    source: str,
    target: str,
    glossary: dict[str, Any],
    report: dict[str, Any],
    pair: str,
    record_id: str,
    field: str,
) -> None:
    case_sensitive = bool(glossary.get("case_sensitive", True))
    preserve = glossary.get("preserve", [])
    if not isinstance(preserve, list):
        add_issue(report, "error", "glossary_preserve_invalid", "glossary.preserve must be a list")
        preserve = []
    for term in preserve:
        if not isinstance(term, str):
            continue
        source_count = glossary_count(source, term, case_sensitive)
        if source_count and glossary_count(target, term, case_sensitive) != source_count:
            add_issue(
                report,
                "error",
                "glossary_preserve_drift",
                f"preserved term {term!r} count changed",
                pair=pair,
                record_id=record_id,
                field=field,
            )
    translations = glossary.get("translations", {})
    if not isinstance(translations, dict):
        add_issue(
            report,
            "error",
            "glossary_translations_invalid",
            "glossary.translations must be an object",
        )
        return
    for source_term, expected in translations.items():
        if not isinstance(source_term, str) or not glossary_contains(source, source_term, case_sensitive):
            continue
        expected_terms = [expected] if isinstance(expected, str) else expected
        if not isinstance(expected_terms, list) or not all(
            isinstance(item, str) for item in expected_terms
        ):
            add_issue(
                report,
                "error",
                "glossary_translation_invalid",
                f"translation for {source_term!r} must be a string or string list",
            )
            continue
        if not any(glossary_contains(target, item, case_sensitive) for item in expected_terms):
            add_issue(
                report,
                "error",
                "glossary_translation_drift",
                f"{source_term!r} does not use an approved target term",
                pair=pair,
                record_id=record_id,
                field=field,
            )


def validate_pair(
    pair: dict[str, Any],
    manifest_base: Path,
    glossary: dict[str, Any],
    coverage_entries: dict[tuple[str, str, str], dict[str, Any]],
    report: dict[str, Any],
    render_samples: list[dict[str, str]],
) -> None:
    name = pair.get("name")
    if not isinstance(name, str) or not name:
        add_issue(report, "error", "pair_name_missing", "each pair needs a non-empty name")
        return
    try:
        source_path = resolve_path(manifest_base, pair["source"])
        target_path = resolve_path(manifest_base, pair["target"])
        file_format = infer_format(pair, source_path)
        source_encoding = encoding_for_pair(pair, "source")
        target_encoding = encoding_for_pair(pair, "target")
        if source_encoding.lower() == "auto" or target_encoding.lower() == "auto":
            raise ValidationFailure("encoding must be pinned; auto is not static-valid evidence")
        records_path = pair.get("records_path")
        source_records, source_meta = load_records(
            source_path, file_format, source_encoding, records_path
        )
        target_records, target_meta = load_records(
            target_path, file_format, target_encoding, records_path
        )
    except (KeyError, OSError, ValidationFailure) as exc:
        add_issue(report, "error", "pair_load_failed", str(exc), pair=name)
        return

    report["files"].extend([source_meta, target_meta])
    report["summary"]["source_records"] += len(source_records)
    report["summary"]["target_records"] += len(target_records)
    pair_report = {
        "name": name,
        "format": file_format,
        "source_records": len(source_records),
        "target_records": len(target_records),
        "source_sha256": source_meta["sha256"],
        "target_sha256": target_meta["sha256"],
    }
    report["pairs"].append(pair_report)

    id_fields = pair.get("id_fields")
    text_fields = pair.get("text_fields")
    locked_fields = pair.get("locked_fields", [])
    if not isinstance(id_fields, list) or not id_fields or not all(
        isinstance(item, str) for item in id_fields
    ):
        add_issue(report, "error", "id_fields_invalid", "id_fields must be a non-empty string list", pair=name)
        return
    if not isinstance(text_fields, list) or not text_fields or not all(
        isinstance(item, str) for item in text_fields
    ):
        add_issue(
            report,
            "error",
            "text_fields_invalid",
            "text_fields must be a non-empty string list",
            pair=name,
        )
        return
    if not isinstance(locked_fields, list) or not all(
        isinstance(item, str) for item in locked_fields
    ):
        add_issue(
            report,
            "error",
            "locked_fields_invalid",
            "locked_fields must be a string list",
            pair=name,
        )
        return

    source_ids = pair_ids(source_records, id_fields, report, name, "source")
    target_ids = pair_ids(target_records, id_fields, report, name, "target")
    if len(source_records) != len(target_records):
        add_issue(
            report,
            "error",
            "record_count_mismatch",
            f"source has {len(source_records)} records; target has {len(target_records)}",
            pair=name,
        )
    if source_ids != target_ids:
        add_issue(
            report,
            "error",
            "record_id_order_mismatch",
            "record IDs or row order differ between source and target",
            pair=name,
        )

    source_map = dict(zip(source_ids, source_records))
    target_map = dict(zip(target_ids, target_records))
    byte_limits = pair.get("byte_limits", {})
    if not isinstance(byte_limits, dict):
        add_issue(report, "error", "byte_limits_invalid", "byte_limits must be an object", pair=name)
        byte_limits = {}
    byte_encoding = target_meta["used_encoding"]
    if byte_encoding == "utf-8-sig":
        byte_encoding = "utf-8"
    allowed_unchanged = glossary.get("allowed_unchanged", [])
    if not isinstance(allowed_unchanged, list):
        add_issue(
            report,
            "error",
            "glossary_allowed_unchanged_invalid",
            "glossary.allowed_unchanged must be a list",
        )
        allowed_unchanged = []
    preserve = [term for term in glossary.get("preserve", []) if isinstance(term, str)]

    for identifier in source_ids:
        if identifier not in target_map:
            continue
        source_record = source_map[identifier]
        target_record = target_map[identifier]
        for field in [*id_fields, *locked_fields]:
            try:
                source_value = field_get(source_record, field)
                target_value = field_get(target_record, field)
            except KeyError:
                add_issue(
                    report,
                    "error",
                    "locked_field_missing",
                    f"locked field is absent: {field}",
                    pair=name,
                    record_id=identifier,
                    field=field,
                )
                continue
            if source_value != target_value:
                add_issue(
                    report,
                    "error",
                    "locked_field_changed",
                    "locked source/target values differ",
                    pair=name,
                    record_id=identifier,
                    field=field,
                )

        for field in text_fields:
            try:
                source_value = field_get(source_record, field)
                target_value = field_get(target_record, field)
            except KeyError:
                add_issue(
                    report,
                    "error",
                    "text_field_missing",
                    f"text field is absent: {field}",
                    pair=name,
                    record_id=identifier,
                    field=field,
                )
                continue
            if not isinstance(source_value, str) or not isinstance(target_value, str):
                add_issue(
                    report,
                    "error",
                    "text_field_not_string",
                    "source and target text fields must be strings",
                    pair=name,
                    record_id=identifier,
                    field=field,
                )
                continue

            source_text = source_value
            target_text = target_value
            render_samples.append(
                {"pair": name, "id": identifier, "field": field, "text": target_text}
            )
            if meaningful_text(source_text):
                report["summary"]["text_cells"] += 1
            if token_counter(source_text) != token_counter(target_text):
                add_issue(
                    report,
                    "error",
                    "token_mismatch",
                    "placeholder/control-token multiset changed",
                    pair=name,
                    record_id=identifier,
                    field=field,
                )
            if newline_counter(source_text) != newline_counter(target_text):
                add_issue(
                    report,
                    "error",
                    "newline_mismatch",
                    "literal or escaped newline multiset changed",
                    pair=name,
                    record_id=identifier,
                    field=field,
                )
            for code, message in thai_sanity_issues(target_text):
                add_issue(
                    report,
                    "error",
                    code,
                    message,
                    pair=name,
                    record_id=identifier,
                    field=field,
                )
            compare_glossary(
                source_text, target_text, glossary, report, name, identifier, field
            )

            if field in byte_limits:
                limit = byte_limits[field]
                if not isinstance(limit, int) or limit < 1:
                    add_issue(
                        report,
                        "error",
                        "byte_limit_invalid",
                        f"byte limit for {field} must be a positive integer",
                        pair=name,
                    )
                else:
                    try:
                        byte_count = len(target_text.encode(byte_encoding))
                    except UnicodeEncodeError as exc:
                        add_issue(
                            report,
                            "error",
                            "field_encoding_failed",
                            str(exc),
                            pair=name,
                            record_id=identifier,
                            field=field,
                        )
                    else:
                        if byte_count > limit:
                            add_issue(
                                report,
                                "error",
                                "byte_limit_exceeded",
                                f"target uses {byte_count} bytes; limit is {limit}",
                                pair=name,
                                record_id=identifier,
                                field=field,
                            )

            if meaningful_text(source_text):
                if source_text != target_text:
                    report["summary"]["translated_cells"] += 1
                else:
                    coverage_entry = coverage_entries.get((name, identifier, field))
                    allowed = (
                        source_text in allowed_unchanged
                        or unchanged_allowed_by_preserve(source_text, preserve)
                        or bool(
                            coverage_entry
                            and coverage_entry.get("status") == "intentionally-unchanged"
                            and coverage_entry.get("reason")
                        )
                    )
                    if allowed:
                        report["summary"]["intentionally_unchanged_cells"] += 1
                    else:
                        add_issue(
                            report,
                            "error",
                            "untranslated_text",
                            "meaningful source and target text are identical without an approved exception",
                            pair=name,
                            record_id=identifier,
                            field=field,
                        )


def parse_bmfont_text(text: str) -> tuple[dict[int, float], float | None]:
    glyphs: dict[int, float] = {}
    line_height: float | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("common "):
            flat: dict[str, str] = {}
            for quoted_key, quoted_value, key, value in re.findall(
                r"(\w+)=\"([^\"]*)\"|(\w+)=([^\s]+)", stripped
            ):
                flat[quoted_key or key] = quoted_value or value
            if "lineHeight" in flat:
                line_height = float(flat["lineHeight"])
        elif stripped.startswith("char "):
            flat = {}
            for quoted_key, quoted_value, key, value in re.findall(
                r"(\w+)=\"([^\"]*)\"|(\w+)=([^\s]+)", stripped
            ):
                flat[quoted_key or key] = quoted_value or value
            if "id" in flat and "xadvance" in flat:
                codepoint = int(flat["id"])
                if codepoint >= 0:
                    glyphs[codepoint] = float(flat["xadvance"])
    return glyphs, line_height


def load_font_metrics(path: Path) -> tuple[dict[int, float], float | None]:
    raw = path.read_bytes()
    if raw.startswith(b"BMF"):
        raise ValidationFailure(
            f"{path}: binary BMFont is unsupported; export text/XML/JSON metrics"
        )
    text = raw.decode("utf-8-sig")
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValidationFailure(f"{path}: invalid font metrics JSON: {exc}") from exc
        glyph_data = data.get("glyphs", {})
        if not isinstance(glyph_data, dict):
            raise ValidationFailure(f"{path}: glyphs must be an object")
        glyphs: dict[int, float] = {}
        for key, value in glyph_data.items():
            advance = value.get("advance") if isinstance(value, dict) else value
            glyphs[int(key)] = float(advance)
        line_height = data.get("line_height")
        return glyphs, float(line_height) if line_height is not None else None
    if text.lstrip().startswith("<"):
        try:
            root = ET.fromstring(text)
        except ET.ParseError as exc:
            raise ValidationFailure(f"{path}: invalid BMFont XML: {exc}") from exc
        common = root.find("common")
        line_height = (
            float(common.attrib["lineHeight"])
            if common is not None and "lineHeight" in common.attrib
            else None
        )
        glyphs = {
            int(node.attrib["id"]): float(node.attrib["xadvance"])
            for node in root.findall("./chars/char")
            if "id" in node.attrib and "xadvance" in node.attrib
        }
        return glyphs, line_height
    return parse_bmfont_text(text)


def renderable_text(text: str) -> str:
    text = TOKEN_RE.sub("", text)
    return text.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\n")


def constraint_for(mapping: dict[str, Any], pair: str, field: str) -> Any:
    for key in (f"{pair}.{field}", f"*.{field}", field):
        if key in mapping:
            return mapping[key]
    return None


def validate_font_gate(
    manifest: dict[str, Any],
    base: Path,
    render_samples: list[dict[str, str]],
    report: dict[str, Any],
) -> None:
    gate = manifest.get("font_gate")
    if not isinstance(gate, dict):
        add_issue(
            report,
            "error",
            "font_gate_missing",
            "font_gate must record metrics, external evidence, or a justified not-applicable decision",
        )
        return
    mode = gate.get("mode")
    report["font_gate"] = {"mode": mode}
    if mode in {"external-evidence", "not-applicable"}:
        evidence = gate.get("evidence", [])
        reason = gate.get("reason")
        if mode == "external-evidence" and (
            not isinstance(evidence, list) or not evidence
        ):
            add_issue(
                report,
                "error",
                "font_evidence_missing",
                "external-evidence mode needs a non-empty evidence list",
            )
        if mode == "not-applicable" and not reason:
            add_issue(
                report,
                "error",
                "font_not_applicable_unjustified",
                "not-applicable mode needs a reason",
            )
        if mode == "not-applicable" and any(
            re.search(r"[\u0e00-\u0e7f]", sample["text"]) for sample in render_samples
        ):
            add_issue(
                report,
                "error",
                "font_not_applicable_has_thai",
                "not-applicable is invalid because declared target text contains Thai",
            )
        return
    if mode != "metrics":
        add_issue(
            report,
            "error",
            "font_gate_mode_invalid",
            "font_gate.mode must be metrics, external-evidence, or not-applicable",
        )
        return
    metrics_value = gate.get("metrics")
    if not isinstance(metrics_value, str):
        add_issue(report, "error", "font_metrics_missing", "metrics mode needs a metrics path")
        return
    metrics_path = resolve_path(base, metrics_value)
    try:
        glyphs, line_height = load_font_metrics(metrics_path)
    except (OSError, UnicodeError, ValueError, ValidationFailure) as exc:
        add_issue(report, "error", "font_metrics_unreadable", str(exc))
        return
    if not glyphs:
        add_issue(report, "error", "font_metrics_empty", "font metrics contain no glyphs")
        return
    max_widths = gate.get("max_widths", {})
    max_lines = gate.get("max_lines", {})
    fit_exemptions = gate.get("fit_exemptions", {})
    if (
        not isinstance(max_widths, dict)
        or not isinstance(max_lines, dict)
        or not isinstance(fit_exemptions, dict)
    ):
        add_issue(
            report,
            "error",
            "font_constraints_invalid",
            "max_widths, max_lines, and fit_exemptions must be objects",
        )
        return
    if not max_widths and not max_lines and not fit_exemptions:
        add_issue(
            report,
            "error",
            "font_fit_constraints_missing",
            "metrics mode needs width/line constraints or justified field exemptions",
        )
    pair_filter = gate.get("pairs")
    if pair_filter is not None and (
        not isinstance(pair_filter, list) or not all(isinstance(item, str) for item in pair_filter)
    ):
        add_issue(report, "error", "font_pair_filter_invalid", "font_gate.pairs must be a string list")
        pair_filter = None
    ignored = set(gate.get("ignore_characters", ""))
    missing: dict[str, set[str]] = collections.defaultdict(set)
    checked = 0
    checked_fields: set[tuple[str, str]] = set()
    for sample in render_samples:
        if pair_filter is not None and sample["pair"] not in pair_filter:
            continue
        checked += 1
        checked_fields.add((sample["pair"], sample["field"]))
        text = renderable_text(sample["text"])
        key = f"{sample['pair']}.{sample['field']}"
        for char in text:
            if char in "\r\n\t" or char in ignored:
                continue
            if ord(char) not in glyphs:
                missing[key].add(char)
        lines = text.splitlines() or [""]
        line_limit = constraint_for(max_lines, sample["pair"], sample["field"])
        if line_limit is not None:
            if not isinstance(line_limit, int) or line_limit < 1:
                add_issue(report, "error", "font_line_limit_invalid", f"invalid max_lines for {key}")
            elif len(lines) > line_limit:
                add_issue(
                    report,
                    "error",
                    "font_line_limit_exceeded",
                    f"text uses {len(lines)} lines; limit is {line_limit}",
                    pair=sample["pair"],
                    record_id=sample["id"],
                    field=sample["field"],
                )
        width_limit = constraint_for(max_widths, sample["pair"], sample["field"])
        if width_limit is not None:
            try:
                numeric_limit = float(width_limit)
            except (TypeError, ValueError):
                add_issue(report, "error", "font_width_limit_invalid", f"invalid max_widths for {key}")
            else:
                for line_number, line in enumerate(lines, start=1):
                    width = sum(glyphs.get(ord(char), 0.0) for char in line if char not in ignored)
                    if width > numeric_limit:
                        add_issue(
                            report,
                            "error",
                            "font_width_exceeded",
                            f"line {line_number} width is {width:g}; limit is {numeric_limit:g}",
                            pair=sample["pair"],
                            record_id=sample["id"],
                            field=sample["field"],
                        )
    for pair, field in sorted(checked_fields):
        key = f"{pair}.{field}"
        has_width = constraint_for(max_widths, pair, field) is not None
        has_lines = constraint_for(max_lines, pair, field) is not None
        exemption = constraint_for(fit_exemptions, pair, field)
        if not has_width and not has_lines and not (
            isinstance(exemption, str) and exemption.strip()
        ):
            add_issue(
                report,
                "error",
                "font_fit_constraint_missing",
                f"{key} needs a width/line constraint or a non-empty fit exemption",
                pair=pair,
                field=field,
            )
    for key, characters in missing.items():
        detail = ", ".join(f"{char} (U+{ord(char):04X})" for char in sorted(characters))
        pair, field = key.split(".", 1)
        add_issue(
            report,
            "error",
            "font_glyph_missing",
            f"font lacks required glyphs: {detail}",
            pair=pair,
            field=field,
        )
    if checked == 0:
        add_issue(
            report,
            "error",
            "font_no_text_checked",
            "metrics mode did not select any target text cells",
        )
    report["font_gate"].update(
        {
            "metrics": str(metrics_path),
            "metrics_sha256": sha256_file(metrics_path),
            "glyphs": len(glyphs),
            "line_height": line_height,
            "text_cells_checked": checked,
        }
    )


def validate_manifest(manifest_path: Path) -> dict[str, Any]:
    manifest_path = manifest_path.expanduser().resolve()
    report = new_report(manifest_path)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        add_issue(report, "error", "manifest_unreadable", str(exc))
        return report
    if not isinstance(manifest, dict):
        add_issue(report, "error", "manifest_invalid", "manifest root must be an object")
        return report
    if manifest.get("version") != 1:
        add_issue(report, "error", "manifest_version_invalid", "manifest.version must equal 1")
    pairs = manifest.get("pairs")
    if not isinstance(pairs, list) or not pairs:
        add_issue(report, "error", "pairs_missing", "manifest.pairs must be a non-empty list")
        return report
    pair_names = [
        pair.get("name")
        for pair in pairs
        if isinstance(pair, dict) and isinstance(pair.get("name"), str)
    ]
    for name, count in collections.Counter(pair_names).items():
        if count > 1:
            add_issue(
                report,
                "error",
                "pair_name_duplicate",
                f"pair name is duplicated: {name}",
            )
    report["summary"]["pairs"] = len(pairs)
    base = manifest_path.parent
    try:
        glossary = load_json_reference(base, manifest.get("glossary", {}), "glossary")
    except ValidationFailure as exc:
        add_issue(report, "error", "glossary_unreadable", str(exc))
        glossary = {}
    coverage_entries = load_coverage(manifest, base, pair_names, report)
    render_samples: list[dict[str, str]] = []
    for pair in pairs:
        if not isinstance(pair, dict):
            add_issue(report, "error", "pair_invalid", "each pair must be an object")
            continue
        validate_pair(
            pair,
            base,
            glossary,
            coverage_entries,
            report,
            render_samples,
        )
    validate_font_gate(manifest, base, render_samples, report)
    handled = (
        report["summary"]["translated_cells"]
        + report["summary"]["intentionally_unchanged_cells"]
    )
    total = report["summary"]["text_cells"]
    report["coverage"]["handled_text_cells"] = handled
    report["coverage"]["total_text_cells"] = total
    report["coverage"]["percent"] = round(100.0 * handled / total, 2) if total else 100.0
    report["ok"] = report["summary"]["errors"] == 0
    report["eligible_stage"] = "static-valid" if report["ok"] else None
    return report


def write_csv(path: Path, rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerows(rows)


def run_self_check() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="thai-localization-validator-") as temp:
        root = Path(temp)
        source = root / "source.csv"
        target = root / "target.csv"
        coverage = root / "coverage.json"
        metrics = root / "font.json"
        manifest = root / "manifest.json"
        source_rows = [
            ["UID", "speaker", "text"],
            ["1", "hero", "Hello {name}\nHP"],
            ["2", "system", "Coromon"],
        ]
        target_rows = [
            ["UID", "speaker", "text"],
            ["1", "hero", "สวัสดี {name}\nHP"],
            ["2", "system", "Coromon"],
        ]
        write_csv(source, source_rows)
        write_csv(target, target_rows)
        coverage.write_text(
            json.dumps(
                {
                    "runtime_sources": [
                        {
                            "name": "dialogue",
                            "status": "translated",
                            "evidence": ["validator fixture"],
                        }
                    ],
                    "entries": [
                        {
                            "pair": "dialogue",
                            "id": "2",
                            "field": "text",
                            "status": "intentionally-unchanged",
                            "reason": "proper noun",
                        }
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        rendered = "สวัสดี HPCoromon"
        metrics.write_text(
            json.dumps(
                {
                    "line_height": 32,
                    "glyphs": {str(ord(char)): 10 for char in set(rendered)},
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        manifest.write_text(
            json.dumps(
                {
                    "version": 1,
                    "glossary": {
                        "preserve": ["HP"],
                        "translations": {"Hello": "สวัสดี"},
                        "allowed_unchanged": ["Coromon"],
                    },
                    "coverage": {
                        "ledger": "coverage.json",
                        "required_runtime_sources": ["dialogue"],
                    },
                    "font_gate": {
                        "mode": "metrics",
                        "metrics": "font.json",
                        "pairs": ["dialogue"],
                        "max_widths": {"dialogue.text": 200},
                        "max_lines": {"dialogue.text": 2},
                    },
                    "pairs": [
                        {
                            "name": "dialogue",
                            "source": "source.csv",
                            "target": "target.csv",
                            "format": "csv",
                            "encoding": "utf-8",
                            "id_fields": ["UID"],
                            "locked_fields": ["speaker"],
                            "text_fields": ["text"],
                            "byte_limits": {"text": 128},
                        }
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        valid = validate_manifest(manifest)
        if not valid["ok"]:
            return {
                "ok": False,
                "self_check": "valid fixture failed",
                "report": valid,
            }
        if token_counter("[f1source payload]") != token_counter("[f1คำแปล]"):
            return {"ok": False, "self_check": "font-payload token normalization failed"}
        if token_counter("100% complete"):
            return {"ok": False, "self_check": "percentage text was parsed as a printf token"}
        target_rows[1][2] = "สวัสดี {player}\nHP"
        write_csv(target, target_rows)
        invalid = validate_manifest(manifest)
        negative_codes = {issue["code"] for issue in invalid["issues"]}
        if invalid["ok"] or "token_mismatch" not in negative_codes:
            return {
                "ok": False,
                "self_check": "negative fixture did not detect token_mismatch",
                "report": invalid,
            }
        return {
            "ok": True,
            "self_check": {
                "valid_fixture": "passed",
                "negative_fixture": "token_mismatch detected",
            },
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", type=Path)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        result = run_self_check()
    elif args.manifest:
        result = validate_manifest(args.manifest)
    else:
        parser.error("provide a manifest or --self-check")
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
