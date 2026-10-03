---
description: Diff a saved LinkedIn connections HTML page against macOS Contacts and emit a CSV of missing entries
argument-hint: [path/to/connections.html]
---

# LinkedIn → Contacts

Compare connections in a saved LinkedIn HTML page to the macOS Contacts address book and produce a CSV of LinkedIn connections that are not yet in Contacts.

## Input

**HTML file**: $ARGUMENTS

If no path was given, look in `~/Downloads/` and `~/Desktop/` for `.html`/`.htm` files modified within the last 90 days whose content contains `linkedin.com/in/`. If exactly one match exists, use it. If multiple, list them with modification times (most recent first) and ask which to use. If there are none, ask the user where the file is.

## One-time setup

The work is done by a Python script at `~/.claude/scripts/linkedin-contacts.py` (symlinked from this repo via `install.sh`). It uses PEP 723 inline metadata; `uv` fetches `beautifulsoup4` and `pyobjc-framework-Contacts` into a cached venv on first run.

If `~/.claude/scripts/` does not yet exist, run `~/Documents/claude-config/install.sh` once. As a fallback, the script can be invoked at its repo path: `~/Documents/claude-config/scripts/linkedin-contacts.py`.

The first run triggers a macOS permission prompt for Contacts access (System Settings → Privacy & Security → Contacts → enable for the terminal). Approving it once is enough.

## Run

```bash
~/.claude/scripts/linkedin-contacts.py "<HTML_PATH>"
```

The script:
1. Parses every `linkedin.com/in/<username>/` from the HTML and its display name. The name comes from the profile-picture label (`<img alt>` / SVG `aria-label` ending in `'s profile picture`), which holds it verbatim, even when lower-case. Without that label, the script takes the most name-like adjacent text (child `<p>` / `<span>` / `<strong>`, then sibling anchors pointing to the same profile). Emoji are stripped from names.
2. For each connection, runs `CNContact.predicateForContactsMatchingName:` to ask Contacts.app for candidates by name — no full address-book enumeration. Punctuation and post-nominals (e.g. ", MOL", " - PhD") are stripped from the search before querying.
3. Treats a connection as already-known if any returned candidate has a URL or social-profile value containing the LinkedIn username, or matching first+last names case-insensitively.
4. Writes the missing entries to `~/Downloads/linkedin-missing-YYYY-MM-DD.csv` (override with `--output PATH`), encoded as **Mac Roman** – the encoding Contacts.app assumes when importing a CSV.

If the page header states a larger total (for example, "738 connections") than the HTML contains, the script prints a `warning:` line. LinkedIn loads the list in batches as you scroll, so the page was saved before every batch loaded.

CSV columns: `First Name`, `Last Name`, `LinkedIn Username` (the slug only — e.g. `adriano-backes-pilla`, not the full URL).

Mac Roman covers Western European accents (ü, ö, ç, ñ, é) natively. Anything outside it (ł, ș, Cyrillic, CJK) is folded to the closest ASCII form – combining marks stripped, a small transliteration table for letters like `ł → l`, and `?` as a last resort. Each fold is reported on stderr as a `note:` line; relay those to the user, since a folded name may want a manual fix before import.

Relay the script's summary to the user (total parsed, already in Contacts, missing, output path), and any `warning:` line.

## Troubleshooting

**Zero connections parsed.** Grep the HTML for `/in/` — if there are no hits, the saved file is a login wall or unrendered SPA shell. If there are hits but the script extracts nothing, inspect the structure around those anchors and adjust `parse_html` in `linkedin-contacts.py` (the candidate-gathering loop and `is_name_like` / `is_plausible_name`).

**Fewer connections parsed than the page lists.** The script warns about this. Ask the user to open the connections page, scroll to the end of the list until no more cards load, and save the page again the same way (in Chrome: File → Save Page As → "Webpage, Complete"). Then re-run.

**Contacts query fails with `authorizationStatus` denied or restricted.** Approve Contacts access for the terminal in System Settings → Privacy & Security → Contacts, then retry.

**Names look wrong (split badly, headline included).** The script takes the profile-picture label, or else the first name-like candidate per profile. Middle names go into the last-name column (e.g., "John Q Public" → `John` / `Q Public`); fix in the CSV before import or adjust the split in `parse_html`.

**A connection is reported missing but is in Contacts.** Most likely the Contacts entry's name diverges from LinkedIn's display name (nicknames, different transliteration) and has no LinkedIn URL stored. The per-connection name predicate won't find it. Workaround: add the LinkedIn URL to the Contacts entry, or accept the false positive and skip that row at import time.

**Accented names import as mojibake (`BengÃ¼su`).** Contacts.app read the file as something other than Mac Roman. The script writes Mac Roman by default; confirm with `file` / `xxd` that ü is a single `0x9F` byte rather than the two-byte UTF-8 `0xC3 0xBC`. If a CSV was produced with `--encoding utf-8`, re-run without the flag.

**Importing the CSV into Contacts.app.** Contacts.app imports the CSV directly: File → Import (or drag the file onto the app), then map the columns to fields in the dialog it shows. It also reads vCard (.vcf) and LDIF. If a ready-to-import vCard is preferred instead, ask and I'll convert the CSV (one `BEGIN:VCARD … END:VCARD` block per row with `URL;type=LinkedIn:` for the profile).

## Useful flags

- `--output PATH` — write CSV somewhere other than the default.
- `--encoding NAME` – override the CSV encoding (default `mac_roman`). Use `utf-8` only when the file is headed somewhere other than Contacts.app; it also disables the ASCII folding, since UTF-8 can represent everything.
