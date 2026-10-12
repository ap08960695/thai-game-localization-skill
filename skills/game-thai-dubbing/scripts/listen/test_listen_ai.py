import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import listen_ai
from listen_ai import parse_response, run_listen_ai


def row(file):
    return {
        "file": file,
        "perceived_age_min": 13,
        "perceived_age_max": 16,
        "gender": "male",
        "brightness": "medium",
        "energy": 4,
        "emotion": "startled and breathless",
        "naturalness": 4,
        "accent_issues": [],
        "fits_character": "yes",
        "changes": ["raise urgency on the names"],
    }


class ParseResponseTests(unittest.TestCase):
    def test_extracts_fenced_json_and_matches_expected_files(self):
        response = "Judgements follow:\n```json\n" + json.dumps([row("A-0001.mp3")]) + "\n```"
        parsed = parse_response(response, ["A-0001.mp3"])
        self.assertEqual(parsed["A-0001.mp3"]["brightness"], "medium")

    def test_rejects_missing_required_file(self):
        with self.assertRaises(ValueError):
            parse_response(json.dumps([row("A-0001.mp3")]), ["A-0001.mp3", "B-0001.mp3"])

    def test_rejects_invalid_or_unattributed_judgements(self):
        for change in ({"energy": True}, {"perceived_age_min": 20},
                       {"file": "unexpected.mp3"}, {"extra": "field"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                parse_response(json.dumps([{**row("A-0001.mp3"), **change}]), ["A-0001.mp3"])

    def test_preserves_text_when_wav_is_staged_as_mp3(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "take.wav"
            source.write_bytes(b"synthetic staging fixture")
            with patch.object(listen_ai, "MODEL", "test-model"), \
                 patch.object(listen_ai.subprocess, "run") as convert, \
                 patch.object(listen_ai, "_run_batch") as review:
                convert.return_value.returncode = 0
                review.return_value = {"take.mp3": {**row("take.mp3"), "status": "SUCCESS"}}
                result = run_listen_ai([source], "test sheet", {str(source): "synthetic text"},
                                      Path(folder) / "results.jsonl")
                self.assertEqual(review.call_args.args[2], {"take.mp3": "synthetic text"})
                self.assertEqual(result[0]["file"], str(source.resolve()))

    def test_records_conversion_failure_without_review(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "take.wav"
            source.write_bytes(b"synthetic staging fixture")
            with patch.object(listen_ai, "MODEL", "test-model"), \
                 patch.object(listen_ai.subprocess, "run", side_effect=FileNotFoundError), \
                 patch.object(listen_ai, "_run_batch") as review:
                result = run_listen_ai([source], "test sheet", out_path=Path(folder) / "results.jsonl")
                self.assertEqual(result[0]["status"], "STAGING_FAILED")
                review.assert_not_called()

    def test_unconfigured_model_stops_before_upload(self):
        with patch.object(listen_ai, "MODEL", ""), self.assertRaises(ValueError):
            run_listen_ai([], "test sheet")


if __name__ == "__main__":
    unittest.main()
