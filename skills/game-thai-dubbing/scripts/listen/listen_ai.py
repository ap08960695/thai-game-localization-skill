#!/usr/bin/env python3
"""Batch synthetic TTS takes through agy for a structured listening review."""

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


MODEL = os.environ.get("THAI_LISTENER_MODEL", "")
BATCH_SIZE = 1  # shortcut: serial review keeps replies attributable; batch after verifying JSON compliance.
FIELDS = {
    "file", "perceived_age_min", "perceived_age_max", "gender", "brightness",
    "energy", "emotion", "naturalness", "accent_issues", "fits_character", "changes",
}


def _json_value(text):
    decoder = json.JSONDecoder()
    fallback = None
    for pos, char in enumerate(text):
        if char not in "[{":
            continue
        try:
            value, _ = decoder.raw_decode(text, pos)
        except json.JSONDecodeError:
            continue
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            if any(key in value for key in ("results", "judgements", "judgments", "files", "status")):
                return value
            fallback = fallback or value
    if fallback is not None:
        return fallback
    raise ValueError("no JSON block found")


def parse_response(text, expected_files):
    value = _json_value(text)
    if isinstance(value, dict):
        value = next((value[key] for key in ("results", "judgements", "judgments", "files")
                      if isinstance(value.get(key), list)), [value])
    if not isinstance(value, list):
        raise ValueError("JSON must contain an array of file judgements")
    rows = {}
    for row in value:
        if not isinstance(row, dict) or set(row) != FIELDS:
            raise ValueError("judgement does not match required schema")
        name = row["file"]
        if not isinstance(name, str) or name not in expected_files or name in rows:
            raise ValueError("judgement has unknown or duplicate filename")
        for key in ("perceived_age_min", "perceived_age_max"):
            if type(row[key]) is not int or row[key] < 0:
                raise ValueError("perceived age must be a non-negative integer")
        for key in ("energy", "naturalness"):
            if type(row[key]) is not int or not 1 <= row[key] <= 5:
                raise ValueError(f"{key} must be an integer from 1 to 5")
        if row["perceived_age_min"] > row["perceived_age_max"]:
            raise ValueError("perceived age range is reversed")
        if row["brightness"] not in {"deep", "medium", "bright"}:
            raise ValueError("brightness must be deep, medium, or bright")
        if row["fits_character"] not in {"yes", "partly", "no"}:
            raise ValueError("fits_character must be yes, partly, or no")
        if not isinstance(row["gender"], str) or not isinstance(row["emotion"], str):
            raise ValueError("gender and emotion must be strings")
        if not isinstance(row["accent_issues"], list) or not all(isinstance(x, str) for x in row["accent_issues"]):
            raise ValueError("accent_issues must be an array of strings")
        if not isinstance(row["changes"], list) or not all(isinstance(x, str) for x in row["changes"]):
            raise ValueError("changes must be an array of strings")
        rows[name] = row
    if set(rows) != set(expected_files):
        raise ValueError("response is missing one or more requested files")
    return rows


def _line_for(path, line_text):
    for key in (str(path), path.name, path.stem):
        if key in line_text:
            return line_text[key]
    return ""


def _prompt(character, staged, line_text):
    items = [{"file": name, "line_text": _line_for(source, line_text)}
             for name, source in staged]
    return (
        "Listen to every supplied audio file with your local file/audio reader; read only these staged files "
        "in your current working directory. Do not run shell commands or code or take external actions. "
        "Judge the voice against this character sheet: " + character + "\n"
        "Return only a JSON array with exactly one object per file, in this exact schema and no extra keys: "
        '[{"file":"exact filename","perceived_age_min":0,"perceived_age_max":0,"gender":"unspecified",'
        '"brightness":"medium","energy":3,"emotion":"unspecified","naturalness":3,'
        '"accent_issues":[],"fits_character":"partly","changes":[]}]\n'
        "Brightness must be exactly deep, medium, or bright; fits_character must be yes, partly, or no. "
        "Use integers 1-5 for energy and naturalness; age values are non-negative integers. "
        "Use empty arrays when there are no accent issues or changes. Keep each file judgement independent. "
        "Requested files and optional Thai line text: " + json.dumps(items, ensure_ascii=False)
    )


def _safe_denied(value):
    if not isinstance(value, list):
        return []
    names = []
    for item in value:
        if isinstance(item, dict):
            item = next((item[k] for k in ("name", "action", "tool", "type") if item.get(k)), "denied action")
        if isinstance(item, str):
            names.append(re.sub(r"[\w.+-]+@[\w.-]+|(?:sk-|AIza)[A-Za-z0-9_-]{8,}", "[redacted]", item)[:120])
    return names


def _failure(path, status, reason, turns=0, denied=None, duration=0.0, attempts=0):
    return {"file": str(path), "status": status, "num_turns": turns,
            "denied_actions": denied or [], "duration_seconds": round(duration, 3),
            "attempts": attempts, "error": reason}


def _run_batch(staged, character, line_text):
    expected = [name for name, _ in staged]
    prompt = _prompt(character, staged, line_text)
    env = os.environ.copy()
    env.update(CUDA_VISIBLE_DEVICES="", HIP_VISIBLE_DEVICES="", ROCR_VISIBLE_DEVICES="")
    total_duration = 0.0
    total_turns = 0
    denied = []
    last_status = "AGY_FAILED"
    last_error = "agy did not return a valid judgement"
    for attempt in range(2):
        started = time.monotonic()
        try:
            proc = subprocess.run(
                ["agy", "-p", prompt, "--model", MODEL, "--output-format", "json",
                 "--print-timeout", "280s"],
                cwd=Path(staged[0][1]).parent, stdin=subprocess.DEVNULL,
                capture_output=True, text=True, timeout=300, check=False, env=env,
            )
        except (OSError, subprocess.TimeoutExpired):
            total_duration += time.monotonic() - started
            last_status, last_error = "AGY_FAILED", "agy could not complete within timeout"
            break
        total_duration += time.monotonic() - started
        if proc.returncode:
            last_status, last_error = "AGY_FAILED", f"agy exited with status {proc.returncode}"
            break
        try:
            envelope = _json_value(proc.stdout)
            if not isinstance(envelope, dict):
                raise ValueError("invalid agy envelope")
        except ValueError:
            last_status, last_error = "AGY_OUTPUT_INVALID", "agy output was not valid JSON"
            continue
        status = str(envelope.get("status", "UNKNOWN"))
        turns = envelope.get("num_turns", 0)
        turns = turns if type(turns) is int and turns >= 0 else 0
        total_turns += turns
        for action in _safe_denied(envelope.get("denied_actions")):
            if action not in denied:
                denied.append(action)
        response = envelope.get("response")
        if status != "SUCCESS" or turns <= 0 or not isinstance(response, str) or not response.strip():
            last_status, last_error = status if status != "SUCCESS" else "AGY_INCOMPLETE", "agy returned no usable response"
            break
        try:
            parsed = parse_response(response, expected)
        except ValueError as exc:
            last_status, last_error = "PARSE_FAILED", str(exc)
            continue
        return {name: {**parsed[name], "status": "SUCCESS", "num_turns": total_turns,
                       "denied_actions": denied, "duration_seconds": round(total_duration, 3),
                       "attempts": attempt + 1}
                for name in expected}
    return {name: _failure(source, last_status, last_error, total_turns, denied,
                           total_duration, min(attempt + 1, 2))
            for name, source in staged}


def run_listen_ai(audio_files, character, line_text=None, out_path="results.jsonl"):
    if not MODEL:
        raise ValueError("set THAI_LISTENER_MODEL to an available audio-capable model before hosted review")
    files = [Path(item).resolve() for item in audio_files]
    if len({p.name for p in files}) != len(files):
        raise ValueError("input filenames must be unique")
    if any(not p.is_file() for p in files):
        raise FileNotFoundError("one or more audio files do not exist")
    line_text = line_text or {}
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results = []
    with out_path.open("w", encoding="utf-8") as output:
        for offset in range(0, len(files), BATCH_SIZE):
            batch = files[offset:offset + BATCH_SIZE]
            with tempfile.TemporaryDirectory(prefix="listen-ai-") as temp:
                temp_dir = Path(temp)
                staged, failures = [], {}
                for source in batch:
                    stage_name = source.name
                    target = temp_dir / stage_name
                    if source.suffix.lower() == ".wav":
                        target = target.with_suffix(".mp3")
                        try:
                            converted = subprocess.run(
                                ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                                 "-i", str(source), "-codec:a", "libmp3lame", "-q:a", "2", str(target)],
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, timeout=180, check=False,
                            )
                        except (OSError, subprocess.TimeoutExpired):
                            failures[source] = _failure(source, "STAGING_FAILED", "audio conversion unavailable or timed out")
                            continue
                        if converted.returncode:
                            failures[source] = _failure(source, "STAGING_FAILED", "WAV to MP3 conversion failed")
                            continue
                    else:
                        shutil.copyfile(source, target)
                    staged.append((target.name, source))
                staged_lines = {name: _line_for(source, line_text) for name, source in staged}
                judged = _run_batch([(name, temp_dir / name) for name, _ in staged], character, staged_lines) if staged else {}
                batch_rows = {str(source): failures[source] for source in batch if source in failures}
                for staged_name, source in staged:
                    model_row = judged[staged_name]
                    model_row["file"] = str(source)
                    batch_rows[str(source)] = model_row
            for source in batch:
                row = batch_rows[str(source)]
                results.append(row)
                output.write(json.dumps(row, ensure_ascii=False) + "\n")
            output.flush()
    return results


def _load_line_text(path):
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
        raise ValueError("line-text JSON must map filenames to Thai text")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio_files", nargs="+")
    parser.add_argument("--character", required=True, help="short character sheet")
    parser.add_argument("--line-text", help="JSON map from filename to Thai line text")
    parser.add_argument("--out", default="results.jsonl")
    args = parser.parse_args()
    rows = run_listen_ai(args.audio_files, args.character, _load_line_text(args.line_text), args.out)
    counts = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    print(json.dumps({"files": len(rows), "statuses": counts, "out": str(Path(args.out))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
