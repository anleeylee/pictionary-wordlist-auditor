# -*- coding: utf-8 -*-
"""Tests for the Pictionary Wordlist Auditor."""

import json
import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wordlist_auditor import (  # noqa: E402
    BRAND_BLACKLIST,
    SENSITIVE_BLACKLIST,
    audit_library,
    build_report,
    cross_library_duplicates,
    expected_difficulty,
    load_libraries,
    normalize,
    render_markdown,
)


def _lib(theme="test", entries=None):
    return {
        "theme": theme,
        "title": theme.title(),
        "entries": entries or [
            {"prompt": "Moon", "category": "Nature", "difficulty": "easy"},
            {"prompt": "Solar Eclipse", "category": "Nature", "difficulty": "medium"},
        ],
    }


class TestNormalize(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize("  Solar   Eclipse! "), "solar eclipse")


class TestDifficulty(unittest.TestCase):
    def test_easy_short(self):
        self.assertEqual(expected_difficulty("Cat"), "easy")
        self.assertEqual(expected_difficulty("Moon"), "easy")

    def test_medium_phrase(self):
        self.assertEqual(expected_difficulty("Solar Eclipse"), "medium")

    def test_hard_idiom(self):
        self.assertEqual(expected_difficulty("Butterfly Effect"), "hard")


class TestAuditLibrary(unittest.TestCase):
    def test_clean_library_passes(self):
        report = audit_library(Path("x.json"), _lib())
        self.assertEqual(report["checks"]["duplicates"], "pass")
        self.assertEqual(report["checks"]["brands"], "pass")
        self.assertEqual(report["checks"]["sensitive"], "pass")
        self.assertEqual(report["checks"]["length"], "pass")
        self.assertEqual(report["checks"]["difficulty"], "pass")

    def test_in_library_duplicate_detected(self):
        entries = [
            {"prompt": "Moon", "category": "Nature", "difficulty": "easy"},
            {"prompt": "moon", "category": "Nature", "difficulty": "easy"},
        ]
        report = audit_library(Path("x.json"), _lib(entries=entries))
        self.assertEqual(report["checks"]["duplicates"], "fail")
        self.assertIn("duplicates", report["stats"])

    def test_brand_detected(self):
        entries = [
            {"prompt": "Frisbee", "category": "Objects", "difficulty": "easy"},
        ]
        report = audit_library(Path("x.json"), _lib(entries=entries))
        self.assertEqual(report["checks"]["brands"], "fail")
        self.assertEqual(report["stats"]["brands"], 1)

    def test_sensitive_detected(self):
        entries = [
            {"prompt": "Beer Bottle", "category": "Objects", "difficulty": "medium"},
        ]
        report = audit_library(Path("x.json"), _lib(entries=entries))
        self.assertEqual(report["checks"]["sensitive"], "fail")
        self.assertEqual(report["stats"]["sensitive"], 1)

    def test_length_detected(self):
        entries = [
            {"prompt": "X", "category": "Objects", "difficulty": "easy"},
            {"prompt": "A" * 50, "category": "Abstract", "difficulty": "hard"},
        ]
        report = audit_library(Path("x.json"), _lib(entries=entries))
        self.assertEqual(report["checks"]["length"], "fail")
        self.assertEqual(report["stats"]["length"], 2)

    def test_difficulty_mismatch_detected(self):
        entries = [
            {"prompt": "Cat", "category": "Animals", "difficulty": "hard"},
        ]
        report = audit_library(Path("x.json"), _lib(entries=entries))
        self.assertEqual(report["checks"]["difficulty"], "warn")
        self.assertEqual(report["stats"]["difficulty"], 1)

    def test_unknown_difficulty_detected(self):
        entries = [
            {"prompt": "Moon", "category": "Nature", "difficulty": "weird"},
        ]
        report = audit_library(Path("x.json"), _lib(entries=entries))
        self.assertEqual(report["checks"]["difficulty"], "warn")

    def test_extra_blacklists_apply(self):
        entries = [{"prompt": "MyBrand", "category": "Objects", "difficulty": "easy"}]
        report = audit_library(Path("x.json"), _lib(entries=entries),
                               extra_blacklists={"brands": {"mybrand"}})
        self.assertEqual(report["checks"]["brands"], "fail")


class TestCrossLibrary(unittest.TestCase):
    def test_cross_duplicate_found(self):
        lib_a = _lib("a", [{"prompt": "Moon", "category": "Nature", "difficulty": "easy"}])
        lib_b = _lib("b", [{"prompt": "moon", "category": "Nature", "difficulty": "easy"}])
        dups = cross_library_duplicates([(Path("a.json"), lib_a), (Path("b.json"), lib_b)])
        self.assertEqual(len(dups), 1)

    def test_cross_duplicate_none(self):
        lib_a = _lib("a", [{"prompt": "Moon", "category": "Nature", "difficulty": "easy"}])
        lib_b = _lib("b", [{"prompt": "Mars", "category": "Nature", "difficulty": "easy"}])
        dups = cross_library_duplicates([(Path("a.json"), lib_a), (Path("b.json"), lib_b)])
        self.assertEqual(dups, [])


class TestBuildReport(unittest.TestCase):
    def test_verdict_fail_on_issues(self):
        with tempfile.TemporaryDirectory() as tmp:
            p1 = Path(tmp) / "a.json"
            p2 = Path(tmp) / "b.json"
            p1.write_text(json.dumps(_lib("a")), encoding="utf-8")
            entries = [{"prompt": "Frisbee", "category": "Objects", "difficulty": "easy"}]
            p2.write_text(json.dumps(_lib("b", entries)), encoding="utf-8")
            report = build_report([str(p1), str(p2)])
            self.assertEqual(report["verdict"], "fail")
            self.assertEqual(report["libraries"], 2)
            self.assertEqual(report["total_entries"], 3)

    def test_markdown_renders(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "a.json"
            out = Path(tmp) / "report.md"
            p.write_text(json.dumps(_lib("a")), encoding="utf-8")
            report = build_report([str(p)])
            render_markdown(report, str(out))
            self.assertTrue(out.exists())
            text = out.read_text(encoding="utf-8")
            self.assertIn("Pictionary Wordlist Audit Report", text)
            self.assertIn("Verdict", text)


if __name__ == "__main__":
    unittest.main()
