# Pictionary Wordlist Auditor

> **Audit themed Pictionary word libraries — in-library & cross-library de-duplication, trademark / brand-name scanning, sensitive-word filtering, length & difficulty validation, with an automatic audit log.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![CLI](https://img.shields.io/badge/CLI-ready-4B8BBE)](wordlist_auditor.py)
[![No dependencies](https://img.shields.io/badge/deps-stdlib%20only-blueviolet)](requirements.txt)

---

## Links

- 🎲 **Try the live tool:** [Pictionary Word Generator — 7,000+ free drawing prompts](https://pictionarywordgenerators.com/)
- 📄 **Easy words page:** [Easy Pictionary Words — fun & simple drawing prompts](https://pictionarywordgenerators.com/easy-pictionary-words)
- Read the Chinese version: [README.zh-CN.md](README.zh-CN.md)

---

## What it does

A Pictionary word library is only as good as its hygiene. Duplicate prompts,
stray brand names, borderline words, one-character placeholders and
inconsistent difficulty labels quietly ruin game nights and — when the library
is published on a site — embarrass the numbers you claim.

**The Pictionary Wordlist Auditor is the quality gate between a word library
and production.** Point it at one or more word-library JSON files and it runs
five checks, then writes a timestamped audit log (JSON + readable Markdown):

1. **Duplicates** — repeated prompts inside a library and **across libraries**
   (a theme should not quietly ship the same 40 prompts twice).
2. **Brands** — trademark / brand-name scan against a ~110-entry blacklist of
   soft drinks, tech, toys, cars, fast food and media franchises, so a library
   never ships "Frisbee", "Lego" or "Star Wars" as drawable prompts.
3. **Sensitive** — inappropriate-words filter for family-safe and classroom
   libraries (alcohol, drugs, weapons, adult content, profanity).
4. **Length** — prompts too short to draw (`X`) or too long for a round
   (50-character essays).
5. **Difficulty** — stored easy/medium/hard labels are re-checked against the
   documented grading heuristic; mismatches are flagged.

Every run produces an **audit log** (JSON + Markdown) with per-check
pass / warn / fail verdicts and the exact list of affected prompts — so a
site's published word counts and quality gates are always auditable.

## Why it matters

When you publish word libraries on a site such as the
[Pictionary Word Generator](https://pictionarywordgenerators.com/), the numbers
people see ("7,000+ prompts", "24 themed libraries") become claims that get
checked. An auditor makes the pipeline repeatable: the same five checks run
identically on every library, every time, and the report is the evidence.

It also catches the *quiet* mistakes a hand-curated list hides for months:

- the same prompt duplicated in two themes (players see repeats across rounds),
- a trademarked toy name that a lawyer will flag,
- a one-character placeholder that slipped past review,
- a "hard" label on a word every child knows.

## Install

```bash
git clone https://github.com/anleeylee/pictionary-wordlist-auditor.git
cd pictionary-wordlist-auditor

# no pip install needed — standard library only
python wordlist_auditor.py --help
```

## Usage

```bash
# audit one library
python wordlist_auditor.py --libraries examples/libs/space.json

# audit several libraries at once (cross-library duplicate check included)
python wordlist_auditor.py \
  --libraries examples/libs/space.json examples/libs/with-issues.json \
  --report reports/audit-report.md \
  --json-report reports/audit-report.json
```

Output paths default to `audit-report.md`; add `--json-report` for the
structured log. Extra blacklists can be supplied per run:

```bash
python wordlist_auditor.py --libraries my-lib.json \
  --brands my-brands.json \
  --sensitive my-sensitive.json
```

where each file is a plain JSON array of strings.

### Options

| Option | Default | Meaning |
|---|---|---|
| `--libraries` | (required) | One or more word-library JSON files |
| `--report` | `audit-report.md` | Markdown audit log output |
| `--json-report` | — | Optional JSON audit log output |
| `--brands` | built-in list | Extra brand-name blacklist file |
| `--sensitive` | built-in list | Extra sensitive-word blacklist file |
| `--strict` | off | Treat difficulty warnings as failures |

## Audit log example

```
# Pictionary Wordlist Audit Report
- Libraries audited: `2`
- Total entries: `29`
- **Verdict: FAIL**

| Check | Issues |
|---|---|
| duplicates | 1 |
| brands | 1 |
| sensitive | 1 |
| length | 2 |
| difficulty | 5 |
```

The full log lists every affected prompt with its index, check and note.

## Expected library schema

```json
{
  "theme": "space",
  "title": "Space",
  "entries": [
    {"prompt": "Moon", "category": "Nature", "difficulty": "easy"}
  ]
}
```

This is exactly the schema produced by the
[Pictionary Wordlist Generator](https://github.com/anleeylee/pictionary-wordlist-generator).

## Tests

```bash
python -m unittest discover -s tests -v
```

Covers: normalization, difficulty heuristics, in-library and cross-library
duplicates, brand / sensitive filtering, length validation, extra blacklists,
global verdicts and Markdown rendering.

## License

MIT — use it, extend it, and keep the attribution. The audit logs you generate
are your evidence; the tool just makes them repeatable.
