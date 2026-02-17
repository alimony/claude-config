# claude-config

Version-controlled [Claude Code](https://docs.anthropic.com/en/docs/claude-code) configuration. Keeps settings, instructions, and customizations in a Git repo and symlinks them into `~/.claude/`.

## What's included

| File | Purpose |
|---|---|
| `CLAUDE.md` | Global instructions that apply to all projects -- engineering principles, coding standards, and workflow preferences |
| `settings.json` | Claude Code settings (effort level, statusline config) |
| `statusline-command.sh` | Custom statusline showing model, directory, git branch/status, context usage, and token counts |
| `install.sh` | Installer that symlinks everything into `~/.claude/` |

The installer also supports optional `commands/`, `skills/`, and `agents/` directories if you add them later.

## Setup

```bash
git clone <this-repo> ~/Documents/claude-config
cd ~/Documents/claude-config
./install.sh
```

The installer will:
- Create `~/.claude/` if it doesn't exist
- Symlink each config file into `~/.claude/`
- Back up any existing files to `*.bak` before replacing them
- Skip files or directories that don't exist in the repo

Restart Claude Code after installing to pick up changes.

## Making changes

Edit the files in this repo, not in `~/.claude/` directly. Since the installer creates symlinks, changes here are picked up immediately (no need to re-run the installer unless you add new files).

## Statusline

The custom statusline displays two lines:

```
Claude Opus 4.6  ~/my-project on main +1~2?3
██████░░░░ 58% | 45.2K in 12.1K out
```

- **Line 1:** Model name, working directory, git branch, and file status (staged/modified/untracked)
- **Line 2:** Context window usage bar with color thresholds (green < 70%, yellow < 90%, red >= 90%) and token counts
