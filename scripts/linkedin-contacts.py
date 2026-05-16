#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "beautifulsoup4",
#     "pyobjc-framework-Contacts",
# ]
# ///
"""Diff connections in a saved LinkedIn HTML page against macOS Contacts.

Emits a CSV of LinkedIn connections that are not yet in Contacts so they can
be reviewed and imported.

Usage:
    linkedin-contacts.py PATH_TO_HTML [--output PATH]

For each connection parsed from the HTML, the script asks Contacts.app for
candidates matching the connection's name (via CNContactStore's name
predicate — fast, indexed lookup). A connection is considered "already in
Contacts" when any candidate either:
  * has a URL or social-profile value containing the LinkedIn username, or
  * has a (first, last) name matching the connection's, case-insensitive.

Missing connections are written as CSV with header:
    First Name,Last Name,LinkedIn Username
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import re
import sys
from pathlib import Path
from typing import NamedTuple

from bs4 import BeautifulSoup

import Contacts  # type: ignore[import-not-found]

IN_URL_RE = re.compile(r"(?:^|/)in/([^/?#\s\"']+)/?", re.IGNORECASE)

NON_NAME_TOKENS = {
    "view", "connect", "message", "follow", "profile", "linkedin",
    "connection", "connections", "member", "members",
    "status", "reachable", "remove", "send", "see", "all",
}

NAME_LIKE_RE = re.compile(
    r"^[A-ZÀ-ÖØ-Ý][\wÀ-ÿ'\-\.]*"
    r"(?:\s+[A-ZÀ-ÖØ-Ý][\wÀ-ÿ'\-\.]*){1,4}$",
    re.UNICODE,
)


class Connection(NamedTuple):
    username: str
    first: str
    last: str
    raw_name: str


def clean(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def is_name_like(text: str) -> bool:
    if not text or len(text) > 80:
        return False
    if any(tok in text.lower().split() for tok in NON_NAME_TOKENS):
        return False
    return bool(NAME_LIKE_RE.match(text))


def is_plausible_name(text: str) -> bool:
    if not text or len(text) > 60 or "\n" in text:
        return False
    if re.search(r"\d", text):
        return False
    tokens = text.split()
    if not (1 <= len(tokens) <= 5):
        return False
    if not all(t[:1].isalpha() and t[:1].isupper() for t in tokens):
        return False
    if any(tok in text.lower().split() for tok in NON_NAME_TOKENS):
        return False
    return True


def parse_html(path: Path) -> dict[str, Connection]:
    soup = BeautifulSoup(
        path.read_text(encoding="utf-8", errors="replace"),
        "html.parser",
    )
    results: dict[str, Connection] = {}
    for anchor in soup.find_all("a", href=True):
        m = IN_URL_RE.search(anchor["href"])
        if not m:
            continue
        username = m.group(1).lower().rstrip("/")
        if not username or username in {"me", "edit"}:
            continue

        candidates: list[str] = []
        for el in anchor.find_all(["p", "span", "strong"]):
            t = clean(el.get_text(" "))
            if t and t not in candidates:
                candidates.append(t)
        img = anchor.find("img")
        if img and img.get("alt"):
            candidates.append(clean(img["alt"]))
        for svg in anchor.find_all("svg"):
            if svg.get("aria-label"):
                candidates.append(clean(svg["aria-label"]))
        candidates.append(clean(anchor.get_text(" ")))

        parent = anchor.find_parent(["li", "article", "div", "section"])
        if parent:
            href = anchor["href"]
            for sibling_anchor in parent.find_all("a", href=True):
                if sibling_anchor is anchor or href not in sibling_anchor["href"]:
                    continue
                for el in sibling_anchor.find_all(["p", "span", "strong"]):
                    t = clean(el.get_text(" "))
                    if t and t not in candidates:
                        candidates.append(t)

        # Strip the trailing "'s profile picture" suffix LinkedIn appends to
        # image alts and accessibility labels (handles straight + curly apostrophes).
        cleaned: list[str] = []
        for c in candidates:
            stripped = re.sub(
                r"['‘’][sS]\s+(?:profile(?:\s+picture)?|profile\s+image)\s*$",
                "",
                c,
            ).strip()
            if stripped and stripped not in cleaned:
                cleaned.append(stripped)
        candidates = cleaned

        name = next((c for c in candidates if is_name_like(c)), "")
        if not name:
            plausible = [c for c in candidates if is_plausible_name(c)]
            if plausible:
                name = min(plausible, key=len)

        first, last = "", ""
        if name:
            parts = name.split(None, 1)
            first = parts[0]
            last = parts[1] if len(parts) > 1 else ""

        prev = results.get(username)
        if prev is None or (not prev.raw_name and name):
            results[username] = Connection(username, first, last, name)
    return results


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().casefold()


_CONTACT_KEYS = [
    Contacts.CNContactGivenNameKey,
    Contacts.CNContactFamilyNameKey,
    Contacts.CNContactUrlAddressesKey,
    Contacts.CNContactSocialProfilesKey,
]


def ensure_contacts_access() -> "Contacts.CNContactStore":
    status = Contacts.CNContactStore.authorizationStatusForEntityType_(
        Contacts.CNEntityTypeContacts
    )
    # 0 = not determined, 1 = restricted, 2 = denied, 3 = authorized,
    # 4 = limited (macOS 14+, user picked specific contacts)
    if status in (1, 2):
        sys.stderr.write(
            "Contacts access is denied or restricted. "
            "Approve it in System Settings → Privacy & Security → Contacts "
            "for the terminal running this script.\n"
        )
        sys.exit(2)
    return Contacts.CNContactStore.alloc().init()


def lookup_candidates(
    store: "Contacts.CNContactStore", name: str
) -> list:
    if not name:
        return []
    predicate = Contacts.CNContact.predicateForContactsMatchingName_(name)
    result, error = store.unifiedContactsMatchingPredicate_keysToFetch_error_(
        predicate, _CONTACT_KEYS, None
    )
    if error is not None:
        raise RuntimeError(f"Contacts query failed for {name!r}: {error}")
    return list(result or [])


def contact_urls(contact) -> list[str]:
    urls: list[str] = []
    for labeled in contact.urlAddresses() or []:
        v = labeled.value()
        if v:
            urls.append(str(v))
    for labeled in contact.socialProfiles() or []:
        sp = labeled.value()
        if sp is None:
            continue
        u = sp.urlString()
        if u:
            urls.append(str(u))
        un = sp.username()
        if un:
            urls.append(str(un))
    return urls


def candidate_matches(conn: Connection, contact) -> bool:
    user_l = conn.username.lower()
    for u in contact_urls(contact):
        ul = u.lower()
        if user_l in ul:
            return True
        m = IN_URL_RE.search(u)
        if m and m.group(1).lower().rstrip("/") == user_l:
            return True
    first = str(contact.givenName() or "")
    last = str(contact.familyName() or "")
    conn_first = _strip_suffix(conn.first)
    conn_last = _strip_suffix(conn.last)
    if (
        conn_first and conn_last
        and norm(first) == norm(conn_first)
        and norm(last) == norm(conn_last)
    ):
        return True
    return False


def _strip_suffix(s: str) -> str:
    """Drop trailing post-nominals like ", MOL" / " - PhD" / "/ MD"."""
    if not s:
        return ""
    s = re.split(r"\s*[,/]\s*", s, maxsplit=1)[0]
    s = re.split(r"\s+[-–—]\s+", s, maxsplit=1)[0]
    return s.strip()


def build_search_queries(conn: Connection) -> list[str]:
    first = _strip_suffix(conn.first)
    last = _strip_suffix(conn.last)
    queries: list[str] = []
    if first and last:
        queries.append(f"{first} {last}")
    if last and last not in queries:
        queries.append(last)
    if first and first not in queries and not last:
        queries.append(first)
    return queries


def find_missing(
    linkedin: dict[str, Connection],
    store: "Contacts.CNContactStore",
) -> list[Connection]:
    missing: list[Connection] = []
    for conn in linkedin.values():
        matched = False
        seen_ids: set[str] = set()
        for q in build_search_queries(conn):
            for cand in lookup_candidates(store, q):
                ident = str(cand.identifier())
                if ident in seen_ids:
                    continue
                seen_ids.add(ident)
                if candidate_matches(conn, cand):
                    matched = True
                    break
            if matched:
                break
        if not matched:
            missing.append(conn)
    return missing


def write_csv(missing: list[Connection], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["First Name", "Last Name", "LinkedIn Username"])
        for c in sorted(
            missing, key=lambda x: (x.last.casefold(), x.first.casefold(), x.username)
        ):
            w.writerow([c.first, c.last, c.username])


def default_output_path() -> Path:
    today = _dt.date.today().isoformat()
    return Path.home() / "Downloads" / f"linkedin-missing-{today}.csv"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("html", type=Path,
                   help="Saved LinkedIn connections HTML file")
    p.add_argument("--output", type=Path, default=None,
                   help="CSV output path (default: ~/Downloads/linkedin-missing-YYYY-MM-DD.csv)")
    args = p.parse_args(argv)

    if not args.html.exists():
        sys.stderr.write(f"error: HTML file not found: {args.html}\n")
        return 1

    print(f"Parsing {args.html} ...", file=sys.stderr)
    linkedin = parse_html(args.html)
    print(f"  found {len(linkedin)} LinkedIn connections", file=sys.stderr)
    if not linkedin:
        sys.stderr.write(
            "No /in/<username>/ URLs found in the HTML. "
            "Verify the saved page is a connections page (not a login redirect).\n"
        )
        return 3

    print("Querying Contacts.app per connection ...", file=sys.stderr)
    store = ensure_contacts_access()
    missing = find_missing(linkedin, store)
    already = len(linkedin) - len(missing)
    print(f"  {already} already in Contacts, {len(missing)} missing",
          file=sys.stderr)

    output_path = args.output or default_output_path()
    write_csv(missing, output_path)
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
