# claude-config

Version-controlled [Claude Code](https://docs.anthropic.com/en/docs/claude-code) configuration. Keeps settings, instructions, and customizations in a Git repo and symlinks them into `~/.claude/`.

## What's included

| Path | Purpose |
|---|---|
| `CLAUDE.md` | Global instructions that apply to all projects — engineering principles, coding standards, and workflow preferences |
| `settings.json` | Claude Code settings: model, effort level, statusline config |
| `statusline-command.sh` | Custom statusline showing model, directory, git state, context usage, token counts, and weekly quota pacing |
| `commands/` | Slash commands (e.g. `/i-know-kung-fu` to generate skills from docs sites) |
| `skills/` | Documentation-derived skill files for Django, htmx, React, pytest, Strawberry, Celery, Vercel, Pandoc, Sentry, HackerOne, Linearis, Next.js, and Wrangler |
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

Edit the files in this repo, not in `~/.claude/` directly. Since the installer creates symlinks, changes here are picked up immediately (no need to re-run the installer unless you add new files).

## Statusline

The custom statusline displays two lines:

```
Claude Opus 4.7  ~/my-project on main +1~2?3
██████░░░░ 58% | 45.2K in 12.1K out | 42%w △5 · 18%s
```

**Line 1 — model, directory, git:**
- Model display name
- Working directory (with `$HOME` abbreviated to `~`)
- Git branch, plus file status: `+N` staged (green), `~N` modified (yellow), `?N` untracked (red)
- Git state is cached for 5 seconds in `/tmp/claude-statusline-git-cache` to keep the statusline snappy in large repos

**Line 2 — context and quota:**
- Context-window usage bar + percentage (green < 70%, yellow < 90%, red ≥ 90%)
- Input / output token counts formatted as `K` / `M`
- `N%w` — weekly quota used (same color thresholds as context bar)
- Pacing indicator — delta between weekly usage % and calendar % of the week elapsed:
  - `▲N` red: over-pacing by ≥ 10 points (burning faster than time)
  - `△N` yellow: over-pacing by 3–9 points
  - `•N` dim: on track (within ±2 points)
  - `▽N` cyan: under-pacing by 3–9 points (banking)
  - `▼N` green: under-pacing by ≥ 10 points
- `N%s` — current 5-hour session quota used

The quota and pacing segments only appear when the host sends rate-limit data.

## Slash commands

- **`/i-know-kung-fu <docs-url>`** — crawl a documentation site and generate a Claude Code skill from it. Output lands in `skills/<project>/`.
