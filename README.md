# claude-config

Version-controlled [Claude Code](https://docs.anthropic.com/en/docs/claude-code) configuration. Keeps settings, instructions, and customizations in a Git repo and symlinks them into `~/.claude/`.

## What's included

| Path | Purpose |
|---|---|
| `CLAUDE.md` | Global instructions that apply to all projects – engineering principles, coding standards, and workflow preferences |
| `settings.json` | Claude Code settings: permission rules (allow, ask, deny), two `SessionStart` hooks (the link check and the Headroom instructions), model, effort level, plugins, and statusline config |
| `statusline-command.sh` | Custom statusline showing model, directory, git state, context usage, token counts, and quota or spend pacing |
| `scripts/` | `headroom-context.sh`, the `SessionStart` hook that adds `headroom-context.md` to a session while Claude Code runs through a local Headroom proxy |
| `skills/` | Documentation-derived skill files for Django, htmx, React, pytest, Strawberry, Celery, Vercel, Pandoc, Sentry, HackerOne, Linearis, Next.js, Wrangler, Reason, Letterboxd, TMDB, Virtuous CRM+, Headroom, and Resident Advisor (`ra`), plus `sentry-cli`, a guide to the Sentry command-line tool; `writing-standards`, the writing standards that `CLAUDE.md` routes to beyond Default; and `test-suite-audit` (`/test-suite-audit`), which audits a project's test suite and writes a prioritised, evidence-backed report |
| `install.sh` | Installer that symlinks everything into `~/.claude/` |

## Setup

```bash
git clone <this-repo> ~/Documents/claude-config
cd ~/Documents/claude-config
./install.sh
```

The installer will:
- Create `~/.claude/` if it doesn't exist
- Symlink each config file and directory into `~/.claude/`
- Back up any existing files to `*.bak` before replacing them
- Skip files or directories that don't exist in the repo

Restart Claude Code after installing to pick up changes.

## Making changes

Edit the files in this repo, not in `~/.claude/` directly. Since the installer creates symlinks, changes here are picked up immediately (no need to re-run the installer unless you add a top-level file or folder, such as `agents/`).

`./install.sh --check` prints each link a run would create or change, changes no link, and exits 1 if there is any. It does create a missing shared folder in `~/.claude` (such as `tasks` or `plans`) without a report. Claude Code's startup cleanup removes those folders when they are empty, so a missing one is not drift.

## Second account

A second Claude account runs from its own config dir, which Claude Code uses when `CLAUDE_CONFIG_DIR` is set. Login credentials stay separate: Claude Code keeps `.claude.json` inside the config dir, and on macOS it names the Keychain entry after a hash of the dir path.

1. Run the installer against the new dir:

   ```bash
   CLAUDE_CONFIG_DIR="$HOME/.claude-2" ./install.sh
   ```

2. Add an alias to your shell profile:

   ```bash
   alias claude2='CLAUDE_CONFIG_DIR="$HOME/.claude-2" claude'
   ```

3. Run `claude2` and log in with `/login`.

For a second config dir, the installer does two things beyond linking the repo files:

- It links `projects/` (transcripts and auto memory), `file-history/`, `plans/`, `tasks/`, `plugins/`, and `history.jsonl` back to `~/.claude`. Either account can then resume the other's sessions and use the same memory.
- If the dir has no `.claude.json`, it creates one from your `~/.claude.json`. It copies project trust and UI state, but never the account, the user ID, or cached server data.

The `SessionStart` hooks check and read whichever config dir the session runs from, because `install.sh` and the hook command read `CLAUDE_CONFIG_DIR`. The status line also reads it, so each account shows its own spend.

## Headroom instructions

When `ANTHROPIC_BASE_URL`, `ANTHROPIC_VERTEX_BASE_URL` or `ANTHROPIC_FOUNDRY_BASE_URL` points at `127.0.0.1` or `localhost`, the `SessionStart` hook adds `scripts/headroom-context.md` to the session. It tells Claude how to read the markers that the Headroom proxy leaves in compressed tool output. Without a local proxy, a session gets nothing. To change the instructions, edit `scripts/headroom-context.md`.

## Statusline

The custom statusline displays two lines:

```
Claude Opus 5.5  ~/my-project on main +1~2?3
██████░░░░ 58% | 45.2K in 12.1K out | 42%w △5 · 18%s
```

It runs on every session event, and also every 30 seconds (`statusLine.refreshInterval`), so the pacing marker keeps moving while you are idle. It needs macOS, `jq` and `git`.

**Line 1 – model, directory, git:**
- Model display name
- Working directory (with `$HOME` abbreviated to `~`)
- Git branch, or the short commit hash when detached, plus file status: `+N` staged (green), `~N` modified (yellow), `?N` untracked (red)
- Git state is cached for 5 seconds per directory in `$TMPDIR`, to keep the statusline fast in large repos. Git runs with `--no-optional-locks`, so it never takes the index lock that a commit needs.

**Line 2 – context, then quota or spend:**
- Context-window usage bar + percentage (green < 70%, yellow < 90%, red ≥ 90%)
- Input / output token counts formatted as `K` / `M`
- A quota or spend segment, which depends on how the account is billed:

| Billing | Segment | Source |
| --- | --- | --- |
| Subscription (Pro, Max) | `42%w △5 · 18%s`: weekly quota used, pacing, five-hour quota used. `18%s` alone when only the five-hour window is reported. | Rate limits that Claude Code sends |
| Claude gateway spend limit | `$261/$500 52% △7 · $1.23s`: spend and limit, pacing over the limit's period (daily, weekly or monthly), this session's spend. `52%$` in place of the amounts when the gateway sends none. | Rate limits that Claude Code sends; no network call |
| Token-based, no gateway (API, Enterprise, spend-limit account) | `$123/$500 25% ▽4 · $1.23s`: month-to-date spend and limit, pacing over the month in UTC, this session's spend | `GET /api/oauth/usage` with the account's OAuth token, refreshed in the background every 5 minutes |
| Token-based, usage endpoint unavailable | `~$88mo · $1.23s`, or `~$88/$200 44% ▼3 · $1.23s` with a budget: a list-price estimate, marked `~` | An installed `ccusage`, refreshed every 15 minutes. It is never downloaded during a render. For a budget, put a dollar number in `monthly-budget` in the account's config dir, such as `~/.claude/monthly-budget`. The estimate is gross: it does not subtract prepaid credit. |

Quota uses the context bar's colors. Spend is green below 80%, yellow below 100%, and red at 100% or more.

The pacing marker is the usage percentage minus the calendar percentage of the window elapsed:
- `▲N` red: over-pacing by ≥ 10 points (burning faster than time)
- `△N` yellow: over-pacing by 3–9 points
- `•N` dim: on track (within ±2 points)
- `▽N` cyan: under-pacing by 3–9 points (banking)
- `▼N` green: under-pacing by ≥ 10 points

The segment appears after the session's first API response, because Claude Code sends rate limits only from then on. Before that, every account looks token-based, so the status line waits instead of calling the usage endpoint.

## Slash commands

Each command is a skill folder, `skills/<name>/SKILL.md`, and any script it runs lives inside that folder.

- **`/i-know-kung-fu <docs-url>`** – crawl a documentation site and generate a Claude Code skill from it. Output lands in `skills/<project>/`.
- **`/linkedin-contacts [connections.html]`** – diff a saved LinkedIn connections page against macOS Contacts and write a CSV of the connections missing from Contacts.
- **`/test-suite-audit [path] [focus]`** – audit a project's test suite and write a prioritised, evidence-backed improvement plan.
