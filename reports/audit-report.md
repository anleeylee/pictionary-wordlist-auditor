# Pictionary Wordlist Audit Report

- Generated: `2026-10-12T21:06:23+00:00`
- Libraries audited: `2`
- Total entries: `29`
- **Verdict: FAIL**

## Summary

| Check | Issues |
|---|---|
| duplicates | 1 |
| brands | 1 |
| sensitive | 1 |
| length | 2 |
| difficulty | 5 |

## Library: `space` (examples\libs\space.json)

- Entries: `20`
- Checks: `duplicates`=pass, `brands`=pass, `sensitive`=pass, `length`=pass, `difficulty`=pass

No issues found. ✓

## Library: `with-issues` (examples\libs\with-issues.json)

- Entries: `9`
- Checks: `duplicates`=fail, `brands`=fail, `sensitive`=fail, `length`=fail, `difficulty`=warn

| # | Check | Prompt | Note |
|---|---|---|---|
| duplicates | 1 | cat | duplicate of 'Cat' |
| brands | 2 | Frisbee | third-party trademark |
| sensitive | 3 | Beer Bottle | inappropriate for family play |
| length | 4 | X | too short (1 chars < 2) |
| length | 5 | The extraordinarily complicated geopolitical phenomenon known as the butterfly effect in modern science | too long (103 chars > 40) |
| difficulty | 2 | Frisbee | stored 'easy' vs heuristic 'medium' |
| difficulty | 5 | The extraordinarily complicated geopolitical phenomenon known as the butterfly effect in modern science | stored 'easy' vs heuristic 'hard' |
| difficulty | 6 | Moon | stored 'hard' vs heuristic 'easy' |
| difficulty | 7 | Pizza | stored 'hard' vs heuristic 'easy' |
| difficulty | 8 | Asteroid Belt | unknown difficulty 'weird' |

## Cross-library duplicates

| Prompt | Appears in |
|---|---|
| moon | examples\libs\space.json, examples\libs\with-issues.json |

