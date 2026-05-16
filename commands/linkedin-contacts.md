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
1. Parses every `linkedin.com/in/<username>/` from the HTML and the most name-like adjacent text (looks at child `<p>` / `<span>` / `<strong>`, `<img alt>`, SVG `aria-label`, then sibling anchors pointing to the same profile, stripping LinkedIn's `'s profile picture` suffix).
2. For each connection, runs `CNContact.predicateForContactsMatchingName:` to ask Contacts.app for candidates by name — no full address-book enumeration. Punctuation and post-nominals (e.g. ", MOL", " - PhD") are stripped from the search before querying.
3. Treats a connection as already-known if any returned candidate has a URL or social-profile value containing the LinkedIn username, or matching first+last names case-insensitively.
4. Writes the missing entries to `~/Downloads/linkedin-missing-YYYY-MM-DD.csv` (override with `--output PATH`).

CSV columns: `First Name`, `Last Name`, `LinkedIn Username` (the slug only — e.g. `adriano-backes-pilla`, not the full URL).

Relay the script's summary to the user (total parsed, already in Contacts, missing, output path).

## Troubleshooting

**Zero connections parsed.** Grep the HTML for `/in/` — if there are no hits, the saved file is a login wall or unrendered SPA shell. If there are hits but the script extracts nothing, inspect the structure around those anchors and adjust `parse_html` in `linkedin-contacts.py` (the candidate-gathering loop and `is_name_like` / `is_plausible_name`).

**Contacts query fails with `authorizationStatus` denied or restricted.** Approve Contacts access for the terminal in System Settings → Privacy & Security → Contacts, then retry.

**Names look wrong (split badly, headline included).** The script picks the first name-like candidate per profile. Middle names go into the last-name column (e.g., "John Q Public" → `John` / `Q Public`); fix in the CSV before import or adjust the split in `parse_html`.

**A connection is reported missing but is in Contacts.** Most likely the Contacts entry's name diverges from LinkedIn's display name (nicknames, different transliteration) and has no LinkedIn URL stored. The per-connection name predicate won't find it. Workaround: add the LinkedIn URL to the Contacts entry, or accept the false positive and skip that row at import time.

**The CSV won't import directly into Contacts.app.** Contacts.app reads vCard (.vcf), tab-separated text, or LDIF — not generic CSV. If a vCard is needed instead, ask and I'll convert the CSV (one `BEGIN:VCARD … END:VCARD` block per row with `URL;type=LinkedIn:` for the profile).

## Useful flags

- `--output PATH` — write CSV somewhere other than the default.
