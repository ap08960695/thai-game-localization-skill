#!/usr/bin/env python3
"""Read-only audit for likely game localization surfaces."""

from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import struct
from pathlib import Path


TEXT_EXTS = {".json", ".csv", ".txt", ".xml", ".ini", ".lua", ".lu"}
PLAYER_KEYS = {
    "name",
    "description",
    "shortDescription",
    "description1",
    "description2",
    "description3",
    "text",
    "message",
    "label",
    "title",
    "value",
}
TOKEN_RE = re.compile(r"<[^>]+>|\[[^\]]+\]|\{[^}]+\}|%[sdif]")
INTERNAL_RE = re.compile(
    r"^([A-Z0-9_]+|[a-z][A-Za-z0-9_]*(\.[a-zA-Z0-9_]+)*|[a-z]+_[A-Za-z0-9_]+|level \d+)$"
)


def has_english(text: str) -> bool:
    return bool(re.search(r"[A-Za-z]{3,}", text))


def has_thai(text: str) -> bool:
    return any("\u0e00" <= ch <= "\u0e7f" for ch in text)


def is_pathlike(text: str) -> bool:
    return bool(re.search(r"\.(png|jpg|json|lua|lu|wav|ogg|mp3|xml)$", text, re.I))


def looks_internal(text: str) -> bool:
    if TOKEN_RE.fullmatch(text.strip()):
        return True
    if INTERNAL_RE.fullmatch(text.strip()):
        return True
    return False


def print_top_files(root: Path) -> None:
    files = [p for p in root.rglob("*") if p.is_file()]
    print("== largest files ==")
    for p in sorted(files, key=lambda p: p.stat().st_size, reverse=True)[:30]:
        print(f"{p.stat().st_size:>12}  {p.relative_to(root)}")
    print()


def scan_structured_text(root: Path) -> None:
    print("== structured text candidates ==")
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in TEXT_EXTS:
            continue
        rel = p.relative_to(root)
        try:
            if p.suffix.lower() == ".json":
                scan_json_file(p, rel)
            elif p.suffix.lower() == ".csv":
                scan_csv_file(p, rel)
        except Exception as exc:
            print(f"{rel}: unreadable ({exc})")
    print()


def scan_json_file(path: Path, rel: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    hits: list[tuple[str, str]] = []

    def walk(value, key: str = "", trail: str = "") -> None:
        if isinstance(value, dict):
            for k, v in value.items():
                walk(v, str(k), f"{trail}.{k}" if trail else str(k))
        elif isinstance(value, list):
            for i, v in enumerate(value):
                walk(v, key, f"{trail}[{i}]")
        elif isinstance(value, str):
            if (
                key in PLAYER_KEYS
                and has_english(value)
                and not is_pathlike(value)
                and not looks_internal(value)
            ):
                hits.append((trail, value[:180]))

    walk(data)
    if hits:
        thai = sum(has_thai(v) for _, v in hits)
        print(f"{rel}: {len(hits)} candidate strings, {thai} already contain Thai")
        for trail, value in hits[:8]:
            print(f"  {trail}: {value}")


def scan_csv_file(path: Path, rel: Path) -> None:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = [f for f in (reader.fieldnames or []) if f in PLAYER_KEYS]
        hits: list[tuple[str, str, str]] = []
        for row in reader:
            uid = row.get("UID") or row.get("id") or "?"
            for field in fields:
                value = row.get(field) or ""
                if has_english(value) and not is_pathlike(value) and not looks_internal(value):
                    hits.append((uid, field, value[:180]))
    if hits:
        thai = sum(has_thai(v) for _, _, v in hits)
        print(f"{rel}: {len(hits)} candidate strings, {thai} already contain Thai")
        for uid, field, value in hits[:8]:
            print(f"  {uid}.{field}: {value}")


def parse_corona_car(path: Path):
    data = path.read_bytes()
    if not data.startswith(b"rac\x01") or len(data) < 16:
        return None
    count = struct.unpack_from("<I", data, 12)[0]
    pos = 16
    entries = []

    def align4(n: int) -> int:
        return (n + 3) & ~3

    for _ in range(count):
        if pos + 12 > len(data):
            return None
        flag, off, name_len = struct.unpack_from("<III", data, pos)
        name = data[pos + 12 : pos + 12 + name_len].decode("utf-8", "replace")
        entries.append({"name": name, "flag": flag, "off": off, "table_pos": pos})
        pos += 12 + align4(name_len + 1)
    if not all(a["off"] < b["off"] for a, b in zip(entries, entries[1:])):
        print(f"{path}: warning offsets are not strictly sorted")
    return data, entries


def scan_corona_archives(root: Path) -> None:
    print("== Solar2D/Corona resource.car ==")
    for car in sorted(root.rglob("resource.car")):
        parsed = parse_corona_car(car)
        if not parsed:
            print(f"{car.relative_to(root)}: not parsed")
            continue
        _, entries = parsed
        names = {e["name"] for e in entries}
        lang = [n for n in names if n.startswith("classes.language.") and n.endswith(".lu")]
        missing = []
        for suffix in ("en-us", "en-uk"):
            tail = f"_{suffix}.lu"
            for name in sorted(lang):
                if name.endswith(tail) and name[: -len(tail)] + "_th.lu" not in names:
                    missing.append(name)
        print(f"{car.relative_to(root)}: {len(entries)} entries, {len(lang)} language modules")
        print(f"  English language modules without Thai counterpart: {len(missing)}")
        for name in missing[:30]:
            print(f"  - {name}")
        ext_counts = collections.Counter(Path(e["name"]).suffix.lower() or "<none>" for e in entries)
        print("  top embedded extensions:", ", ".join(f"{k}:{v}" for k, v in ext_counts.most_common(8)))
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game_dir", type=Path)
    args = parser.parse_args()
    root = args.game_dir.expanduser().resolve()
    if not root.exists():
        parser.error(f"not found: {root}")
    print(f"game_dir: {root}")
    print_top_files(root)
    scan_structured_text(root)
    scan_corona_archives(root)
    print("audit complete: inspect candidates manually before patching; this script is read-only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
