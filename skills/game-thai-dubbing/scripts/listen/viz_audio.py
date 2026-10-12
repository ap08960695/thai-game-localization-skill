#!/usr/bin/env python3
"""Render CPU audio features as compact per-take and comparison PNGs."""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def _libraries():
    os.environ.update(CUDA_VISIBLE_DEVICES="", HIP_VISIBLE_DEVICES="", ROCR_VISIBLE_DEVICES="")
    os.environ["NUMBA_NUM_THREADS"] = "1"
    import librosa
    import numpy as np
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        base = Path(sys.base_prefix) / "lib/python3/dist-packages"
        if base.is_dir():
            sys.path.append(str(base))
        from PIL import Image, ImageDraw, ImageFont
    return librosa, np, Image, ImageDraw, ImageFont


def _analyse(path, text=""):
    librosa, np, *_ = _libraries()
    y, sr = librosa.load(str(path), sr=22050, mono=True)
    if not len(y):
        raise ValueError("audio is empty")
    duration = len(y) / sr
    frame, hop = 2048, 256
    audio = np.pad(y, (0, max(0, frame - len(y))))
    mel = librosa.feature.melspectrogram(y=audio, sr=sr, n_fft=frame, hop_length=hop, n_mels=96)
    mel_db = librosa.power_to_db(mel, ref=np.max)
    f0, _, _ = librosa.pyin(audio, sr=sr, fmin=60, fmax=500,
                            frame_length=frame, hop_length=hop)
    f0_times = librosa.times_like(f0, sr=sr, hop_length=hop)
    rms = librosa.feature.rms(y=audio, frame_length=frame, hop_length=hop)[0]
    rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    centroid = librosa.feature.spectral_centroid(y=audio, sr=sr, n_fft=frame, hop_length=hop)[0]
    voiced = f0[np.isfinite(f0)]
    median = float(np.median(voiced)) if len(voiced) else None
    f0_range = float(12 * np.log2(np.max(voiced) / np.min(voiced))) if len(voiced) and np.min(voiced) > 0 else None
    return {
        "duration_seconds": duration,
        "f0_median_hz": median,
        "f0_range_semitones": f0_range,
        "spectral_centroid_hz": float(np.mean(centroid)) if len(centroid) else None,
        "text_chars_per_second": sum(ch.isalpha() for ch in text) / duration if text and duration else None,
        "mel_db": mel_db,
        "mel_freqs": librosa.mel_frequencies(n_mels=mel.shape[0], fmin=0, fmax=sr / 2),
        "f0": f0,
        "f0_times": f0_times,
        "rms": rms,
        "rms_times": rms_times,
    }


def _palette(values):
    _, np, *_ = _libraries()
    stops = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    colors = np.array([[18, 20, 45], [55, 83, 160], [40, 150, 145], [245, 175, 65], [250, 245, 145]])
    return np.stack([np.interp(values, stops, colors[:, channel]) for channel in range(3)], axis=-1).astype("uint8")


def _base_canvas(width=1440, height=980):
    _, _, Image, ImageDraw, ImageFont = _libraries()
    image = Image.new("RGB", (width, height), "white")
    return image, ImageDraw.Draw(image), ImageFont.load_default()


def _line(draw, points, fill, width=2):
    clean = [(int(x), int(y)) for x, y in points]
    if len(clean) > 1:
        draw.line(clean, fill=fill, width=width)


def _failed_png(path, error, out_path):
    image, draw, font = _base_canvas(1440, 420)
    draw.text((36, 32), f"{Path(path).name} - analysis failed", fill="#182238", font=font)
    draw.text((36, 90), str(error)[:220], fill="#9b2532", font=font)
    image.save(out_path, format="PNG", optimize=True)


def _render_one(path, data, text, out_path):
    librosa, np, Image, ImageDraw, ImageFont = _libraries()
    width, height = 1440, 980
    image, draw, font = _base_canvas(width, height)
    title_stats = [
        f"F0 median {data['f0_median_hz']:.1f} Hz" if data["f0_median_hz"] is not None else "F0 median n/a",
        f"range {data['f0_range_semitones']:.1f} st" if data["f0_range_semitones"] is not None else "range n/a",
        f"centroid {data['spectral_centroid_hz']:.0f} Hz" if data["spectral_centroid_hz"] is not None else "centroid n/a",
        f"Thai chars/s {data['text_chars_per_second']:.1f}" if data["text_chars_per_second"] is not None else "Thai chars/s n/a",
    ]
    draw.text((35, 25), f"{Path(path).name} | {data['duration_seconds']:.2f}s | " + " | ".join(title_stats),
              fill="#182238", font=font)
    plot_x, plot_w = 115, 1265
    sections = [(82, 330, "Mel spectrogram", "mel frequency"),
                (452, 205, "F0 contour", "Hz (60–500)"),
                (725, 170, "RMS energy", "amplitude")]
    mel_y, mel_h, mel_name, mel_axis = sections[0]
    db = np.clip((data["mel_db"][::-1] + 75) / 75, 0, 1)
    mel_rgb = _palette(db)
    mel_img = Image.fromarray(mel_rgb, "RGB").resize((plot_w, mel_h), Image.Resampling.LANCZOS)
    image.paste(mel_img, (plot_x, mel_y))
    draw.rectangle((plot_x, mel_y, plot_x + plot_w, mel_y + mel_h), outline="#607080")
    for hz in (250, 500, 1000, 2000, 4000, 8000):
        bins = np.where(data["mel_freqs"] <= hz)[0]
        if len(bins):
            y = mel_y + int((1 - bins[-1] / max(1, len(data["mel_freqs"]) - 1)) * mel_h)
            draw.text((30, y - 5), f"{hz} Hz", fill="#253246", font=font)
            draw.line((plot_x, y, plot_x + plot_w, y), fill="#ffffff", width=1)
    draw.text((plot_x, mel_y - 20), mel_name, fill="#182238", font=font)
    for start, panel_h, label, ylabel in sections[1:]:
        draw.rectangle((plot_x, start, plot_x + plot_w, start + panel_h), outline="#91a0ad")
        draw.text((30, start + 4), ylabel, fill="#253246", font=font)
        draw.text((plot_x, start - 20), label, fill="#182238", font=font)
        for frac in (0.25, 0.5, 0.75):
            y = start + int(panel_h * frac)
            draw.line((plot_x, y, plot_x + plot_w, y), fill="#e2e7eb", width=1)
    f0_y, f0_h = sections[1][:2]
    points, last = [], None
    for t, value in zip(data["f0_times"], data["f0"]):
        if np.isfinite(value) and 0 <= t <= data["duration_seconds"]:
            x = plot_x + int(t / data["duration_seconds"] * plot_w)
            y = f0_y + int((1 - (value - 60) / 440) * f0_h)
            if last is not None and x - last[0] <= 3:
                _line(draw, [last, (x, y)], "#b53054", 3)
            last = (x, y)
        else:
            last = None
    rms_y, rms_h = sections[2][:2]
    peak = max(float(np.max(data["rms"])), 1e-9)
    rms_points = [(plot_x + int(t / data["duration_seconds"] * plot_w),
                   rms_y + rms_h - int(float(v) / peak * (rms_h - 8)))
                  for t, v in zip(data["rms_times"], data["rms"])
                  if 0 <= t <= data["duration_seconds"]]
    for left, right in zip(rms_points, rms_points[1:]):
        _line(draw, [left, right], "#267b63", 2)
    for x in (plot_x, plot_x + plot_w // 2, plot_x + plot_w):
        seconds = (x - plot_x) / plot_w * data["duration_seconds"]
        draw.text((x - 10, 920), f"{seconds:.1f}s", fill="#253246", font=font)
    image.save(out_path, format="PNG", optimize=True)


def _band(profile, key):
    aliases = {"f0_median_hz": ("f0_median_hz", "f0_median"),
               "f0_range_semitones": ("f0_range_semitones", "f0_range"),
               "spectral_centroid_hz": ("spectral_centroid_hz", "centroid_hz", "centroid")}
    value = next((profile[name] for name in aliases[key] if name in profile), None)
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return float(value[0]), float(value[1])
    if isinstance(value, dict) and "min" in value and "max" in value:
        return float(value["min"]), float(value["max"])
    return None


def _render_comparison(rows, profile, out_path):
    _, np, Image, ImageDraw, ImageFont = _libraries()
    width, height = 1440, 780
    image, draw, font = _base_canvas(width, height)
    draw.text((36, 25), "Listening panel — acoustic comparison", fill="#182238", font=font)
    metrics = [("F0 median (Hz)", "f0_median_hz"),
               ("F0 range (semitones)", "f0_range_semitones"),
               ("Spectral centroid (Hz)", "spectral_centroid_hz")]
    x0, plot_w = 165, 1210
    for index, (label, key) in enumerate(metrics):
        top = 80 + index * 225
        plot_y, plot_h = top + 26, 145
        values = [row.get(key) for row in rows]
        finite = [float(v) for v in values if isinstance(v, (int, float)) and np.isfinite(v)]
        band = _band(profile, key)
        limits = finite + (list(band) if band else [])
        low, high = (min(limits), max(limits)) if limits else (0.0, 1.0)
        pad = max((high - low) * 0.12, abs(high) * 0.04, 1.0)
        low, high = low - pad, high + pad
        draw.text((36, top), label, fill="#182238", font=font)
        draw.rectangle((x0, plot_y, x0 + plot_w, plot_y + plot_h), outline="#91a0ad")
        if band:
            y_hi = plot_y + int((high - band[1]) / (high - low) * plot_h)
            y_lo = plot_y + int((high - band[0]) / (high - low) * plot_h)
            draw.rectangle((x0, min(y_hi, y_lo), x0 + plot_w, max(y_hi, y_lo)), fill="#e3efff")
            draw.text((x0 + 5, min(y_hi, y_lo) + 2), "target band", fill="#315a8d", font=font)
        for fraction in (0, 0.5, 1):
            y = plot_y + int(fraction * plot_h)
            draw.line((x0, y, x0 + plot_w, y), fill="#e2e7eb", width=1)
            draw.text((36, y - 5), f"{high - fraction * (high - low):.1f}", fill="#253246", font=font)
        slot = plot_w / max(1, len(rows))
        for i, (row, value) in enumerate(zip(rows, values)):
            x = x0 + int((i + 0.5) * slot)
            if isinstance(value, (int, float)) and np.isfinite(value):
                y = plot_y + int((high - value) / (high - low) * plot_h)
                draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill="#bd365a", outline="white")
            name = Path(row["file"]).name
            draw.text((x - min(22, len(name) * 3), plot_y + plot_h + 5), name, fill="#253246", font=font)
    image.save(out_path, format="PNG", optimize=True)


def generate_viz(audio_files, out_dir, target_profile=None, line_text=None):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    profile = target_profile or {}
    line_text = line_text or {}
    results = []
    used_names = set()
    for index, item in enumerate(audio_files):
        path = Path(item).resolve()
        stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", path.stem).strip("._") or f"take-{index + 1}"
        if stem in used_names:
            stem = f"{index + 1:02d}-{stem}"
        used_names.add(stem)
        png = out_dir / f"{stem}.png"
        text = line_text.get(str(path), line_text.get(path.name, line_text.get(path.stem, "")))
        try:
            data = _analyse(path, text)
            _render_one(path, data, text, png)
            results.append({"file": str(path), "png": str(png),
                            **{key: round(value, 4) if isinstance(value, float) else value
                               for key, value in data.items() if key not in {"mel_db", "mel_freqs", "f0", "f0_times", "rms", "rms_times"}}})
        except Exception as exc:
            _failed_png(path, type(exc).__name__, png)
            results.append({"file": str(path), "png": str(png), "error": f"{type(exc).__name__}: {str(exc)[:180]}"})
    comparison = out_dir / "comparison.png"
    _render_comparison(results, profile, comparison)
    return results, str(comparison)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio_files", nargs="+")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--target-profile", help="optional target metric bands in JSON")
    parser.add_argument("--line-text", help="optional JSON map from filename to Thai text")
    args = parser.parse_args()
    profile = json.loads(Path(args.target_profile).read_text(encoding="utf-8")) if args.target_profile else {}
    lines = json.loads(Path(args.line_text).read_text(encoding="utf-8")) if args.line_text else {}
    results, comparison = generate_viz(args.audio_files, args.out_dir, profile, lines)
    print(json.dumps({"files": len(results), "pngs": sum(Path(x["png"]).is_file() for x in results),
                      "comparison": comparison}, ensure_ascii=False))


if __name__ == "__main__":
    main()
