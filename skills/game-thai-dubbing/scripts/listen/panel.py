#!/usr/bin/env python3
"""Run Gemini listening review and CPU acoustic plots for a set of takes."""

import argparse
import json
import os
from pathlib import Path


os.environ.update(CUDA_VISIBLE_DEVICES="", HIP_VISIBLE_DEVICES="", ROCR_VISIBLE_DEVICES="")

from listen_ai import _load_line_text, run_listen_ai
from viz_audio import generate_viz


AUDIO_SUFFIXES = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"}


def _collect(inputs):
    files = []
    for item in inputs:
        path = Path(item).expanduser()
        if path.is_dir():
            files.extend(sorted(p for p in path.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_SUFFIXES))
        else:
            files.append(path)
    files = list(dict.fromkeys(p.resolve() for p in files))
    if not files:
        raise ValueError("no audio files found")
    if any(p.suffix.lower() not in AUDIO_SUFFIXES for p in files):
        raise ValueError("input list contains an unsupported audio extension")
    return files


def _cell(value):
    return str(value if value not in (None, "") else "—").replace("|", "\\|").replace("\n", " ")


def run_panel(inputs, character, out_dir, line_text=None, target_profile=None):
    files = _collect(inputs)
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    ai_rows = run_listen_ai(files, character, line_text, out_dir / "results.jsonl")
    analyses, comparison = generate_viz(files, out_dir / "plots", target_profile, line_text)
    ai_by_file = {row["file"]: row for row in ai_rows}
    analysis_by_file = {row["file"]: row for row in analyses}
    entries = []
    for path in files:
        key = str(path)
        entries.append({"file": key, "listening": ai_by_file.get(key, {}),
                        "analysis": analysis_by_file.get(key, {})})
    report = {"character": character, "files": entries, "comparison_png": comparison}
    (out_dir / "panel.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Listening panel", "", f"Character: {_cell(character)}", "",
             "| Take | AI status | Fit | Naturalness | Perceived voice | Acoustic summary | Notes |",
             "|---|---|---|---:|---|---|---|"]
    for entry in entries:
        ai, analysis = entry["listening"], entry["analysis"]
        age = ""
        if "perceived_age_min" in ai:
            age = f"{ai['perceived_age_min']}–{ai['perceived_age_max']} / {ai.get('gender', '')} / {ai.get('brightness', '')}"
        stats = []
        for key, label, unit in (("f0_median_hz", "F0", "Hz"),
                                 ("f0_range_semitones", "range", "st"),
                                 ("spectral_centroid_hz", "centroid", "Hz"),
                                 ("text_chars_per_second", "Thai chars/s", "")):
            value = analysis.get(key)
            if isinstance(value, (int, float)):
                stats.append(f"{label} {value:.1f}{unit}")
        notes = ai.get("error") or analysis.get("error") or "; ".join(ai.get("changes", []))
        if ai.get("accent_issues"):
            notes = (notes + "; " if notes else "") + "accent: " + ", ".join(ai["accent_issues"])
        lines.append("| " + " | ".join(_cell(value) for value in (
            Path(entry["file"]).name, ai.get("status", "MISSING"), ai.get("fits_character"),
            ai.get("naturalness"), age, ", ".join(stats), notes,
        )) + " |")
    lines.extend(["", f"Comparison: `plots/{Path(comparison).name}`", ""])
    (out_dir / "panel.md").write_text("\n".join(lines), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", help="take directory or audio file list")
    parser.add_argument("--character", required=True)
    parser.add_argument("--line-text", help="optional JSON map from filename to Thai line text")
    parser.add_argument("--target-profile", help="optional JSON target metric bands")
    parser.add_argument("--out-dir")
    args = parser.parse_args()
    files = _collect(args.inputs)
    if args.out_dir:
        out_dir = Path(args.out_dir)
    elif len(args.inputs) == 1 and Path(args.inputs[0]).is_dir():
        source_dir = Path(args.inputs[0]).resolve()
        out_dir = source_dir.parent / "listen-panel"
    else:
        out_dir = files[0].parent / "listen-panel"
    line_text = _load_line_text(args.line_text)
    target_profile = json.loads(Path(args.target_profile).read_text(encoding="utf-8")) if args.target_profile else {}
    report = run_panel(args.inputs, args.character, out_dir, line_text, target_profile)
    statuses = {}
    for row in report["files"]:
        status = row["listening"].get("status", "MISSING")
        statuses[status] = statuses.get(status, 0) + 1
    print(json.dumps({"files": len(report["files"]), "statuses": statuses,
                      "panel": str(Path(out_dir) / "panel.md"), "comparison": report["comparison_png"]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
