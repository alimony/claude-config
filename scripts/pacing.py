#!/usr/bin/env python3
"""Compare Claude /usage percentages against calendar time elapsed."""

import sys
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

MONTHS = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}


def month_num(s):
    return MONTHS[s[:3].lower()]


def to_24h(hour, ampm):
    if ampm == 'am':
        return 0 if hour == 12 else hour
    return hour if hour == 12 else hour + 12


def parse_sections(text):
    sections = []
    cur = {}
    for line in text.split('\n'):
        s = line.strip()
        if not s:
            if cur.get('label'):
                sections.append(cur)
                cur = {}
            continue
        pct = re.search(r'(\d+)%\s*used', s)
        if pct:
            cur['pct'] = int(pct.group(1))
        reset = re.search(r'Resets\s+(.+?)\s*\(([^)]+)\)', s)
        if reset:
            cur['reset_text'] = reset.group(1).strip()
            cur['tz'] = reset.group(2)
            spend = re.search(r'\$([\d.]+)\s*/\s*\$([\d.]+)\s*spent', s)
            if spend:
                cur['spend'] = (float(spend.group(1)), float(spend.group(2)))
        if pct or reset:
            continue
        if not any(c in s for c in '\u2588\u258c\u258f\u258e\u258d\u258b\u258a\u2589$'):
            if cur.get('label'):
                sections.append(cur)
                cur = {}
            cur['label'] = s
    if cur.get('label'):
        sections.append(cur)
    return [s for s in sections if s.get('pct') is not None and s.get('reset_text')]


def parse_reset(text, tz_name, now, fallback_date=None):
    tz = ZoneInfo(tz_name)
    now_l = now.astimezone(tz)
    year = now_l.year

    # "Apr 19 at 9am" / "Apr 20 at 1:59pm"
    m = re.match(r'(\w+)\s+(\d+)\s+at\s+(\d+)(?::(\d+))?\s*(am|pm)', text)
    if m:
        month = month_num(m.group(1))
        day = int(m.group(2))
        hour = to_24h(int(m.group(3)), m.group(5))
        minute = int(m.group(4)) if m.group(4) else 0
        if month < now_l.month - 6:
            year += 1
        return datetime(year, month, day, hour, minute, tzinfo=tz)

    # "May 1"
    m = re.match(r'(\w+)\s+(\d+)$', text)
    if m:
        month, day = month_num(m.group(1)), int(m.group(2))
        if month < now_l.month - 6:
            year += 1
        return datetime(year, month, day, 0, 0, tzinfo=tz)

    # "9am" / "2pm" / "9:59am" / "2:30pm"
    m = re.match(r'(\d+)(?::(\d+))?\s*(am|pm)$', text)
    if m:
        hour = to_24h(int(m.group(1)), m.group(3))
        minute = int(m.group(2)) if m.group(2) else 0
        if fallback_date:
            return datetime(fallback_date.year, fallback_date.month,
                            fallback_date.day, hour, minute, tzinfo=ZoneInfo(tz_name))
        dt = now_l.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if dt <= now_l:
            dt += timedelta(days=1)
        return dt

    return None


def fmt_remaining(td):
    total_h = max(0, int(td.total_seconds() / 3600))
    d, h = divmod(total_h, 24)
    return f"{d}d {h}h" if d else f"{h}h"


def main():
    text = sys.stdin.read()
    if not text.strip():
        print("No input. Pipe /usage output into this script.")
        sys.exit(1)

    now = datetime.now().astimezone()
    sections = parse_sections(text)
    sections = [s for s in sections if 'session' not in s['label'].lower()]

    if not sections:
        print("No parseable sections found.")
        sys.exit(1)

    # Collect week reset date for fallback (time-only resets)
    week_date = None
    for s in sections:
        if 'week' in s['label'].lower() and re.search(r'[A-Za-z]+\s+\d+', s['reset_text']):
            dt = parse_reset(s['reset_text'], s['tz'], now)
            if dt:
                week_date = dt.date()
                break

    for s in sections:
        fb = week_date if 'week' in s['label'].lower() else None
        reset_dt = parse_reset(s['reset_text'], s['tz'], now, fallback_date=fb)
        if not reset_dt:
            print(f"{s['label']}: could not parse reset '{s['reset_text']}'")
            print()
            continue

        tz = ZoneInfo(s['tz'])
        now_l = now.astimezone(tz)

        if 'week' in s['label'].lower():
            period = timedelta(days=7)
            start = reset_dt - period
        else:
            sm = reset_dt.month - 1 or 12
            sy = reset_dt.year - (1 if sm == 12 else 0)
            try:
                start = reset_dt.replace(year=sy, month=sm)
            except ValueError:
                start = reset_dt.replace(year=sy, month=sm, day=1)
            period = reset_dt - start

        elapsed = max(timedelta(0), now_l - start)
        remaining = max(timedelta(0), reset_dt - now_l)
        time_pct = min(100.0, elapsed / period * 100)
        usage_pct = s['pct']
        diff = usage_pct - time_pct

        spend_str = ""
        if 'spend' in s:
            u, t = s['spend']
            spend_str = f" (${u:.2f}/${t:.2f})"

        if abs(diff) <= 2:
            status = "ON TRACK"
        elif diff > 0:
            status = f"OVER by {diff:.0f}pp"
        else:
            status = f"{-diff:.0f}pp headroom"

        print(f"{s['label']}{spend_str}")
        print(f"  {usage_pct}% used  /  {time_pct:.0f}% elapsed  /  {fmt_remaining(remaining)} left")
        print(f"  {status}")

        if diff > 10 and time_pct >= 5:
            proj = usage_pct / time_pct * 100
            print(f"  !! At current rate, projected to use ~{min(proj, 999):.0f}% of quota")

        print()


if __name__ == '__main__':
    main()
