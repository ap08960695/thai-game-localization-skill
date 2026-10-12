#!/usr/bin/env python3
"""Validate the loose-WAV loader's PCM16 contract; no third-party dependencies."""

import argparse
import array
import json
import math
from pathlib import Path
import struct
import sys


MAX_BYTES = 64 * 1024 * 1024


def inspect_pcm16(blob):
    if not 12 <= len(blob) <= MAX_BYTES:
        raise ValueError("WAV must be 12 bytes to 64 MiB")
    if blob[:4] != b"RIFF" or blob[8:12] != b"WAVE":
        raise ValueError("require RIFF/WAVE")
    if struct.unpack_from("<I", blob, 4)[0] + 8 != len(blob):
        raise ValueError("RIFF size must equal file size")
    fmt, pcm, pos = None, None, 12
    while pos < len(blob):
        if pos + 8 > len(blob):
            raise ValueError("truncated chunk header")
        tag, size = struct.unpack_from("<4sI", blob, pos)
        start = pos + 8
        pos = start + size + (size & 1)
        if pos > len(blob):
            raise ValueError("truncated chunk or odd-chunk padding")
        if tag == b"fmt ":
            if fmt is not None or size < 16:
                raise ValueError("invalid or duplicate fmt chunk")
            fmt = struct.unpack_from("<HHIIHH", blob, start)
        elif tag == b"data":
            if pcm is not None:
                raise ValueError("duplicate data chunk")
            pcm = blob[start:start + size]
    if fmt is None or not pcm:
        raise ValueError("missing fmt or nonempty data chunk")
    encoding, channels, rate, byte_rate, align, bits = fmt
    if (encoding != 1 or bits != 16 or channels not in (1, 2)
            or not 8000 <= rate <= 192000 or align != channels * 2
            or byte_rate != rate * align or len(pcm) % align):
        raise ValueError("require aligned PCM16 mono/stereo, 8–192 kHz, consistent byte/block rates")
    samples = array.array("h")
    samples.frombytes(pcm)
    if sys.byteorder != "little":
        samples.byteswap()
    peak = max(abs(x) for x in samples)
    frames = len(pcm) // align
    return {"sample_rate": rate, "channels": channels, "frames": frames,
            "duration_s": frames / rate, "peak_dbfs": 20 * math.log10(peak / 32768) if peak else None,
            "rail_samples": sum(x in (-32768, 32767) for x in samples), "silent": peak == 0}


def validate(path, sample_rate=None, channels=None, duration=None):
    path = Path(path)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("WAV exceeds 64 MiB loader limit")
    result = inspect_pcm16(path.read_bytes())
    if sample_rate is not None and result["sample_rate"] != sample_rate:
        raise ValueError("sample rate differs from expected")
    if channels is not None and result["channels"] != channels:
        raise ValueError("channels differ from expected")
    if duration is not None:
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError("expected duration must be positive and finite")
        if abs(result["duration_s"] - duration) > 1 / result["sample_rate"]:
            raise ValueError("duration differs by more than one frame")
    # shortcut: sample rails are warnings; use an external true-peak/loudness gate before delivery.
    result["warnings"] = (["silent"] if result["silent"] else []) + (
        ["sample rails: inspect clipping"] if result["rail_samples"] else [])
    return result


def self_check():
    import tempfile

    def chunk(tag, data):
        return tag + struct.pack("<I", len(data)) + data + b"\0" * (len(data) & 1)

    def riff(body):
        return b"RIFF" + struct.pack("<I", len(body) + 4) + b"WAVE" + body

    def fixture(channels=1, fmt=None, pcm=None, extra=b""):
        fmt = fmt or struct.pack("<HHIIHH", 1, channels, 48000, 48000 * channels * 2, channels * 2, 16)
        pcm = pcm if pcm is not None else struct.pack("<hhhh", 0, 100, -100, 0) * channels
        return riff(chunk(b"fmt ", fmt) + extra + chunk(b"data", pcm))

    valid = fixture(extra=chunk(b"JUNK", b"x"))
    assert inspect_pcm16(valid)["frames"] == 4
    assert inspect_pcm16(fixture(2))["channels"] == 2
    assert inspect_pcm16(fixture(pcm=b"\0\0"))["silent"]
    bad = [valid[:-1], valid + b"x", b"NOPE" + valid[4:],
           fixture(pcm=b"x"), fixture(pcm=b""),
           fixture(fmt=struct.pack("<HHIIHH", 3, 1, 48000, 96000, 2, 16)),
           fixture(fmt=struct.pack("<HHIIHH", 1, 1, 48000, 1, 2, 16)),
           fixture(extra=chunk(b"fmt ", b"x" * 16)),
           fixture(extra=chunk(b"data", b"\0\0")), riff(b"short")]
    for blob in bad:
        try:
            inspect_pcm16(blob)
        except ValueError:
            continue
        raise AssertionError("malformed WAV accepted")
    with tempfile.TemporaryDirectory(prefix="wav-check-") as folder:
        path = Path(folder) / "fixture.wav"
        path.write_bytes(valid)
        assert validate(path, 48000, 1, 4 / 48000)["warnings"] == []
        for args in [(44100, None, None), (None, 2, None), (None, None, 1.0),
                     (None, None, float("nan"))]:
            try:
                validate(path, *args)
            except ValueError:
                continue
            raise AssertionError("mismatched expectation accepted")
    return {"ok": True, "self_check": "valid mono/stereo/padding and 14 malformed/mismatch cases passed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?")
    parser.add_argument("--sample-rate", type=int)
    parser.add_argument("--channels", type=int, choices=(1, 2))
    parser.add_argument("--duration", type=float, help="expected duration, tolerance one delivery frame")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if not args.self_check and not args.file:
        parser.error("provide a WAV file or --self-check")
    try:
        result = self_check() if args.self_check else {
            "ok": True, "file": args.file,
            **validate(args.file, args.sample_rate, args.channels, args.duration)}
    except (OSError, ValueError, struct.error) as error:
        result = {"ok": False, "error": str(error)}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
