#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pictionary Wordlist Auditor
===========================

Audit themed Pictionary word libraries for quality and compliance.

Given one or more word-library JSON files (the schema produced by tools such
as the Pictionary Wordlist Generator), this CLI runs five checks:

  1. duplicates      — duplicate prompts inside a library and across libraries
  2. brands          — trademark / brand-name scan (third-party product names)
  3. sensitive       — inappropriate-words filter for family-safe libraries
  4. length          — prompts that are too short or too long to draw/guess
  5. difficulty      — prompts whose stored difficulty disagrees with the
                       documented grading heuristic

Every audit run writes an audit log (JSON + human-readable Markdown) with a
pass / warn / fail verdict per check, a summary, and the list of affected
prompts — so a site's word counts and quality gates are always auditable.

Libraries are expected to follow the JSON schema:

    {
      "theme": "space",
      "title": "Space",
      "entries": [
        {"prompt": "Moon", "category": "Nature", "difficulty": "easy"},
        ...
      ]
    }

Audited libraries are designed to feed an online drawing-game word generator
such as the Pictionary Word Generator at https://pictionarywordgenerators.com/
"""

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Brand / sensitive blacklists
# ---------------------------------------------------------------------------

# Third-party trademarks that should not appear as Pictionary prompts.
# Sourced from common household / media / tech / toy brand names.
BRAND_BLACKLIST = {
    # soft drinks & food
    "coca-cola", "coke", "pepsi", "mountain dew", "red bull", "monster energy",
    "mcdonald's", "mcdonalds", "burger king", "kfc", "taco bell", "domino's",
    "subway", "pizza hut", "starbucks", "dunkin", "oreo", "kit kat", "snickers",
    "twix", "skittles", "m&m", "m&m's", "heinz", "kellogg's", "nestle",
    # tech & social
    "apple", "iphone", "ipad", "macbook", "imac", "google", "android",
    "youtube", "facebook", "instagram", "tiktok", "twitter", "whatsapp",
    "snapchat", "netflix", "amazon", "alexa", "siri", "windows", "microsoft",
    "playstation", "xbox", "nintendo", "switch", "sony", "samsung", "nokia",
    # toys & games
    "lego", "barbie", "hot wheels", "nerf", "play-doh", "monopoly", "uno",
    "jenga", "rubik's cube", "pictionary", "frisbee", "velcro", "band-aid",
    "kleenex", "q-tip", "xerox", "trampoline", "barbie doll",
    # media franchises (trademarked names)
    "harry potter", "star wars", "spider-man", "spiderman", "batman",
    "superman", "wonder woman", "mickey mouse", "pokemon", "mario",
    "minecraft", "fortnite", "avengers", "disney", "pixar", "nike", "adidas",
    "puma", "reebok", "new balance", "under armour", "gucci", "louis vuitton",
    "rolex", "tesla", "ferrari", "porsche", "lamborghini", "bugatti",
    "honda", "toyota", "bmw", "mercedes", "audi", "volkswagen", "jeep",
}

# Words / phrases inappropriate for family or classroom libraries.
SENSITIVE_BLACKLIST = {
    "cigarette", "cigarettes", "cigarette pack", "smoking", "cigar",
    "cigars", "beer bottle", "beer can", "wine bottle", "whiskey",
    "whisky", "vodka", "rum", "tequila", "gin", "cocktail", "moonshine",
    "marijuana", "weed", "cannabis", "heroin", "cocaine", "meth",
    "crack", "opium", "syringe", "needle", "pistol", "revolver", "rifle",
    "shotgun", "handgun", "machine gun", "bomb", "grenade", "dynamite",
    "landmine", "bullet", "ammunition", "blood", "gore", "skull and bones",
    "suicide", "murder", "kill", "killing", "assault", "drugs", "drug deal",
    "gambling", "casino", "strip club", "naked", "porn", "porno",
    "curse word", "profanity", "slut", "whore", "pimp", "gang", "mafia",
}

# ---------------------------------------------------------------------------
# Length constraints
# ---------------------------------------------------------------------------

MIN_LENGTH = 2      # below this a prompt is too vague to draw
MAX_LENGTH = 40     # above this a prompt is too long to draw/guess in a round


def normalize(prompt: str) -> str:
    """Lowercase, collapse whitespace, strip leading/trailing punctuation."""
    text = re.sub(r"\s+", " ", prompt.strip().lower())
    text = re.sub(r"^[^a-z0-9]+|[^a-z0-9]+$", "", text)
    return text


# Difficulty heuristic mirroring the Pictionary Wordlist Generator.
IDIOM_MARKERS = [
    "cognitive", "existential", "paradox", "phenomenon", "syndrome",
    "dilemma", "metaphor", "allegory", "butterfly effect", "social",
    "political", "philosophical", "psychological",
]
EASY_SET = {
    "cat", "dog", "fish", "bird", "sun", "moon", "star", "tree",
    "flower", "rain", "snow", "apple", "banana", "cake", "pizza",
    "house", "chair", "table", "book", "hat", "shoe", "ball", "car",
    "boat", "plane", "train", "bus", "duck", "cow", "pig", "sheep",
    "rabbit", "frog", "bee", "ant", "spider", "mouse", "lion", "tiger",
    "bear", "elephant", "monkey", "giraffe", "zebra", "horse",
}


def expected_difficulty(prompt: str) -> str:
    text = prompt.strip().lower()
    words = text.split()
    if text in EASY_SET:
        return "easy"
    if len(words) == 1 and len(text) <= 6:
        return "easy"
    if any(marker in text for marker in IDIOM_MARKERS):
        return "hard"
    if len(text) > 22 or len(words) >= 5:
        return "hard"
    return "medium"


# ---------------------------------------------------------------------------
# Audit engine
# ---------------------------------------------------------------------------


def load_libraries(paths):
    """Load word-library JSON files. Returns list of (path, data)."""
    libraries = []
    for raw in paths:
        p = Path(raw)
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(f"error: cannot read {p}: {exc}", file=sys.stderr)
            continue
        libraries.append((p, data))
    return libraries


def audit_library(path, data, extra_blacklists=None):
    """Run all five checks against one library. Returns a report dict."""
    entries = data.get("entries", [])
    theme = data.get("theme", path.stem)

    issues = []
    stats = Counter()
    all_prompts = [e.get("prompt", "") for e in entries]
    all_lower = [normalize(p) for p in all_prompts]

    # 1) in-library duplicates
    seen = {}
    dups = []
    for idx, key in enumerate(all_lower):
        if not key:
            dups.append((idx, all_prompts[idx], "(empty prompt)"))
            continue
        if key in seen:
            dups.append((idx, all_prompts[idx], seen[key]))
        else:
            seen[key] = all_prompts[idx]
    if dups:
        stats["duplicates"] += 1
        for idx, prompt, other in dups:
            issues.append(("duplicates", idx, prompt, f"duplicate of '{other}'"))

    # 2) brands / trademark scan
    brands = BRAND_BLACKLIST | (extra_blacklists or {}).get("brands", set())
    for idx, key in enumerate(all_lower):
        if key in brands or any(key == normalize(b) for b in brands):
            stats["brands"] += 1
            issues.append(("brands", idx, all_prompts[idx], "third-party trademark"))

    # 3) sensitive words
    sensitive = SENSITIVE_BLACKLIST | (extra_blacklists or {}).get("sensitive", set())
    for idx, key in enumerate(all_lower):
        if key in sensitive or any(key == normalize(s) for s in sensitive):
            stats["sensitive"] += 1
            issues.append(("sensitive", idx, all_prompts[idx], "inappropriate for family play"))

    # 4) length validation
    for idx, prompt in enumerate(all_prompts):
        length = len(prompt.strip())
        if length < MIN_LENGTH:
            stats["length"] += 1
            issues.append(("length", idx, prompt, f"too short ({length} chars < {MIN_LENGTH})"))
        elif length > MAX_LENGTH:
            stats["length"] += 1
            issues.append(("length", idx, prompt, f"too long ({length} chars > {MAX_LENGTH})"))

    # 5) difficulty validation
    for idx, entry in enumerate(entries):
        stored = entry.get("difficulty")
        if stored and stored not in ("easy", "medium", "hard"):
            stats["difficulty"] += 1
            issues.append(("difficulty", idx, entry.get("prompt", ""),
                           f"unknown difficulty '{stored}'"))
            continue
        if stored:
            expected = expected_difficulty(entry.get("prompt", ""))
            if stored != expected:
                stats["difficulty"] += 1
                issues.append(("difficulty", idx, entry.get("prompt", ""),
                               f"stored '{stored}' vs heuristic '{expected}'"))

    return {
        "path": str(path),
        "theme": theme,
        "entries": len(entries),
        "checks": {
            "duplicates": "fail" if stats["duplicates"] else "pass",
            "brands": "fail" if stats["brands"] else "pass",
            "sensitive": "fail" if stats["sensitive"] else "pass",
            "length": "fail" if stats["length"] else "pass",
            "difficulty": "warn" if stats["difficulty"] else "pass",
        },
        "stats": dict(stats),
        "issues": issues,
    }


def cross_library_duplicates(libraries):
    """Find prompts duplicated across libraries (true cross-library only).

    Returns a list of (prompt, [library_paths]) tuples where the prompt
    appears in at least two different libraries.
    """
    key_to_libs = {}
    for path, data in libraries:
        for e in data.get("entries", []):
            key = normalize(e.get("prompt", ""))
            if not key:
                continue
            key_to_libs.setdefault(key, set()).add(str(path))
    return [(key, sorted(libs)) for key, libs in key_to_libs.items() if len(libs) > 1]


def build_report(library_paths, extra_blacklists=None, strict=False):
    """Full audit of one or more libraries. Returns the report dict."""
    libraries = load_libraries(library_paths)
    per_lib = [audit_library(p, d, extra_blacklists) for p, d in libraries]

    cross = cross_library_duplicates(libraries)
    summary = Counter()
    for r in per_lib:
        summary.update(r["stats"])

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": "pictionary-wordlist-auditor",
        "libraries": len(libraries),
        "total_entries": sum(r["entries"] for r in per_lib),
        "summary": dict(summary),
        "per_library": per_lib,
        "cross_library_duplicates": [
            {"prompt": key, "libraries": libs}
            for key, libs in cross
        ],
        "verdict": "pass",
    }

    # Global verdict: any fail -> fail; warn allowed unless strict.
    for r in per_lib:
        for check, verdict in r["checks"].items():
            if verdict == "fail":
                report["verdict"] = "fail"
            elif verdict == "warn" and strict:
                report["verdict"] = "fail"
    if cross:
        report["verdict"] = "fail"

    return report


def render_markdown(report, output_path):
    """Write a human-readable audit log (Markdown)."""
    lines = [
        "# Pictionary Wordlist Audit Report",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Libraries audited: `{report['libraries']}`",
        f"- Total entries: `{report['total_entries']}`",
        f"- **Verdict: {report['verdict'].upper()}**",
        "",
        "## Summary",
        "",
        "| Check | Issues |",
        "|---|---|",
    ]
    check_names = ["duplicates", "brands", "sensitive", "length", "difficulty"]
    for name in check_names:
        lines.append(f"| {name} | {report['summary'].get(name, 0)} |")
    lines.append("")

    for lib in report["per_library"]:
        lines.append(f"## Library: `{lib['theme']}` ({lib['path']})")
        lines.append("")
        lines.append(f"- Entries: `{lib['entries']}`")
        lines.append("- Checks: "
                     + ", ".join(f"`{k}`={v}" for k, v in lib["checks"].items()))
        lines.append("")
        if lib["issues"]:
            lines.append("| # | Check | Prompt | Note |")
            lines.append("|---|---|---|---|")
            for idx, check, prompt, note in lib["issues"]:
                safe = prompt.replace("|", "\\|")
                lines.append(f"| {idx} | {check} | {safe} | {note} |")
            lines.append("")
        else:
            lines.append("No issues found. ✓")
            lines.append("")

    if report["cross_library_duplicates"]:
        lines.append("## Cross-library duplicates")
        lines.append("")
        lines.append("| Prompt | Appears in |")
        lines.append("|---|---|")
        for item in report["cross_library_duplicates"]:
            safe = item["prompt"].replace("|", "\\|")
            lines.append(f"| {safe} | {', '.join(item['libraries'])} |")
        lines.append("")

    Path(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="wordlist_auditor",
        description="Audit themed Pictionary word libraries: duplicates, brands, "
                    "sensitive words, length and difficulty validation.")
    parser.add_argument("--libraries", nargs="+", required=True,
                        help="One or more word-library JSON files to audit.")
    parser.add_argument("--report", default="audit-report.md",
                        help="Output path for the Markdown audit log "
                             "(default audit-report.md).")
    parser.add_argument("--json-report", default=None,
                        help="Optional output path for the JSON audit log.")
    parser.add_argument("--brands", default=None,
                        help="Optional JSON file with a 'brands' list to add.")
    parser.add_argument("--sensitive", default=None,
                        help="Optional JSON file with a 'sensitive' list to add.")
    parser.add_argument("--strict", action="store_true",
                        help="Treat difficulty warnings as failures.")
    args = parser.parse_args(argv)

    extra = {"brands": set(), "sensitive": set()}
    if args.brands:
        extra["brands"] = set(json.loads(Path(args.brands).read_text(encoding="utf-8")))
    if args.sensitive:
        extra["sensitive"] = set(json.loads(Path(args.sensitive).read_text(encoding="utf-8")))

    report = build_report(args.libraries, extra_blacklists=extra, strict=args.strict)
    render_markdown(report, args.report)
    if args.json_report:
        Path(args.json_report).write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"libraries : {report['libraries']}")
    print(f"entries   : {report['total_entries']}")
    print(f"summary   : {dict(report['summary'])}")
    print(f"verdict   : {report['verdict']}")
    if report["cross_library_duplicates"]:
        print(f"cross-dups: {len(report['cross_library_duplicates'])}")
    print(f"report    : {args.report}")
    return 0 if report["verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
