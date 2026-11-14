# Claude setup refresh – plan

Source: the analysis of `CLAUDE.md`, `install.sh`, `README.md`, `settings.json` and `statusline-command.sh` against Claude Code 2.1.325, on 2026-11-14.

Status: done. Every task was answered before implementation started. A checked box means done; an unchecked box means skipped.

Tasks are ordered smallest and quickest first, except where a task depends on another one.

## Settings

- [ ] **T1 – Use one effort default.** Skipped: the three `high` entries are deliberate.
  - Problem: `/effort` reported xhigh as saved, but `settings.json` still says `high` in `effortLevel`, `modelSettings.opus` and `modelSettings.claude-opus-5-5`. The per-model entry wins over the top-level one, and `opus` is an alias that the lookup probably never matches.
  - The settings file shall hold one effort default, at the level the user chooses.
  - When the user runs `/effort <level>` and picks it as the default, the new level MUST appear in `settings.json`.
  - Check: start a new session and confirm the effort level it shows.

- [x] **T2 – Remove allow rules that auto mode sets aside.** Approved: remove all of them.
  - Rules: `Bash(python3 *)`, `Bash(python *)`, `Bash(bash *)`, `Bash(sh *)`, `Bash(node *)`, `Bash(perl *)`, `Bash(npx *)`, `Bash(uvx *)`, `Bash(*/bin/python *)`, `Bash(*/bin/python3 *)`, `Bash(*/bin/bash *)`, `Bash(*/bin/sh *)`.
  - Problem: auto mode strips these while it is on, so they do nothing in your default mode. Outside auto mode they allow any code to run without asking.
  - Before removal, the list MUST be checked against what auto mode actually strips.
  - Check: `jq` confirms the rules are gone and the file is valid JSON.

- [x] **T3 – Remove or narrow allow rules that skip the auto-mode classifier.** Approved: remove every rule listed.
  - Rules: `Bash(curl *)`, `Bash(gh api *)`, `Bash(git fetch *)`, `Bash(git pull *)`, `Bash(tee *)`, `Bash(npm *)`, `Bash(yarn *)`, `Bash(corepack yarn *)`, `Bash(poetry *)`, `Bash(kill *)`, `Bash(open *)`.
  - Problem: a rule that auto mode keeps lets every matching command skip the classifier. Claude Code's own guidance says never to allowlist curl, `gh api`, git fetch or pull, or package runners.
  - Narrow, local, read-only rules SHOULD stay, because each one saves a classifier call.

- [x] **T4 – Settle the auto memory conflict.** Approved: keep auto memory on, and drop the CLAUDE.md restriction.
  - Problem: CLAUDE.md says to use auto memory only when a project names it, but auto memory is on in every session.
  - Either `autoMemoryEnabled` shall be `false`, or CLAUDE.md shall drop the restriction.

## Status line

- [x] **T5 – Remove leftover status-line state.** Approved.
  - Remove the stale `statusline-spend.lock` directory in `~/.claude`, and any state files that later tasks make unused.

- [x] **T6 – Give each directory its own git cache, and stop taking git locks.** Approved: one cache per directory.
  - Problem: `/tmp/claude-statusline-git-cache` is shared by every session. A repo on branch `other-branch` rendered as `on main`.
  - The status line shall show the branch and file counts of its own directory only.
  - Every git command in the status line MUST use `--no-optional-locks`.
  - Check: render two repos on different branches within 5 seconds, and confirm each shows its own branch.

- [x] **T7 – Skip the spend branch before the first API response.** Approved.
  - Problem: `rate_limits` arrives only after the first response, so every new session on a subscription runs the spend branch: a Keychain read, a call to the usage endpoint, and possibly `ccusage`.
  - While `context_window.current_usage` is null, the status line MUST NOT read the Keychain, call the network or run `ccusage`.
  - Check: render with `current_usage: null` and no `rate_limits`, and confirm no process other than `git` and `jq` starts.

- [x] **T8 – Stop downloading ccusage during a render.** Approved: use an installed ccusage only, otherwise skip the estimate.
  - Problem: when ccusage is not installed, the script runs `npx --yes ccusage`, which downloads the latest unpinned package during a render.
  - The status line MUST NOT download a package during a render.

- [x] **T9 – Read the input with one jq call.** Approved.
  - Problem: each render runs nine `jq` calls and about 20 processes, for about 120 ms.
  - The status line shall read every input field with one `jq` call.
  - Check: 10 renders MUST take less time than the 1.2-second baseline, with the same output.

- [x] **T10 – Refresh the status line on a timer.** Changed: no new fields, because Claude Code shows them elsewhere. The token-count segment stays.
  - `statusLine.refreshInterval` shall be `30`, so the pacing marker updates while idle.

- [x] **T11 – Support subscription and token-based billing equally.** Approved: keep spend in the status line, as below. The config runs on several machines, so both kinds of billing need equal support.
  - The status line shall show quota pacing for a subscription and spend pacing for token-based billing, in the same segment and the same format.
  - Where the input carries `rate_limits.spend_limit` (a Claude gateway), the status line shall show that spend and its pacing, without a network call. Today it shows nothing in that case, because the script reads only `seven_day` when `rate_limits` is present.
  - Where `spend_limit` is absent and no rate-limit window is present, the status line shall use the usage endpoint, then an installed ccusage (T8).
  - Check: render sample inputs for a subscription, a gateway spend limit, and a token-based account with no limits, and confirm each shows its usage and pacing.

## CLAUDE.md

- [x] **T12 – Remove guidance that Claude Code already gives.** Approved.
  - Remove subagent bullets 1 and 4, because the Agent tool's description covers them and offers worktree isolation.
  - Shorten "Verification before done" to the part the built-in guidance lacks: say how you checked it.

- [x] **T13 – Load the Headroom section only when the proxy is on.** Approved.
  - Move "Compressed tool output" to its own file, and add it through a SessionStart hook.
  - When `ANTHROPIC_BASE_URL`, `ANTHROPIC_VERTEX_BASE_URL` or `ANTHROPIC_FOUNDRY_BASE_URL` points at `127.0.0.1` or `localhost`, the hook shall add the section to the session context. Changed from port 8787 during implementation, because `headroom wrap --port` can move the proxy and the Vertex and Foundry modes set other variables.
  - If the proxy is not configured, then the session MUST NOT receive the section.
  - `install.sh` shall link the new file, and `--check` shall report it.

- [ ] **T14 – Replace the `tasks/todo.md` workflow with plan mode.** Skipped: plans stay in `tasks/todo.md`.
  - Plan mode's approval step does the "Verify plan" job, and plans save to `~/.claude/plans`, which the accounts already share.
  - Trade-off: plans no longer sit in each repo.

- [x] **T15 – Move the less-used writing styles to a skill.** Approved.
  - The skill shall be a `SKILL.md` with a description, so it appears in the skill listing and Claude loads it without a CLAUDE.md lookup.
  - Move Structure, Requirements, Outward, Legal, Simplified Technical English and Creative to a `writing-standards` skill.
  - CLAUDE.md shall keep the routing table, Default and Mechanics, and name the skill for the other rows.

## Mod

- [ ] **T16 – Build a pacing mod.** Skipped: the status line already shows pacing, and a mod is a second thing to maintain on an early-access API.
  - A mod in this repo, served by a directory marketplace, using `session.measure`, `$.store` and `$.clock`.
  - When weekly pacing crosses a threshold the user picks, the mod shall show a toast.
  - Where T11 moves the spend branch here, the mod shall also show monthly spend.
  - Check: `claude plugin validate`, `tsc`, and a `claude plugin test` file.

## Documentation

- [x] **T17 – Bring the README up to date.** Approved. Runs last, because it describes the result of the other tasks.
  - Update the status-line example and segments.
  - Remove `todos/` from the list of shared folders.
  - Make the skill list match CLAUDE.md.
  - Describe whichever of T13, T14, T15 and T16 are done.

## Review

What changed:

- `settings.json`: 23 allow rules removed (T2, T3). `Skill(writing-standards)` added to the allow list, so the new skill loads without a prompt. A second SessionStart hook added (T13). `statusLine.refreshInterval` set to 30 (T10).
- `statusline-command.sh`: rewritten with the same output. One `jq` call; one `git status --porcelain=v2` per directory every 5 seconds, with `--no-optional-locks`; no `bc`, `sed`, `tr` or `date` in the render path. New: gateway `spend_limit`, a five-hour-only subscription, a short hash for a detached HEAD. The spend branch waits for the first API response, and ccusage runs only when installed.
- `CLAUDE.md`: the auto memory restriction, two subagent bullets, the Headroom section and six writing styles removed; verification shortened. CLAUDE.md went from 1,409 to 919 words.
- New files: `scripts/headroom-context.sh` and `scripts/headroom-context.md` (T13), `skills/writing-standards/SKILL.md` (T15). `install.sh` links `scripts/`, and both config dirs are linked.
- `README.md`: updated for all of the above (T17).
- T5: the stale lock directory had already cleared itself; the old shared git cache in `/tmp` was removed.

How each was checked:

- Same output: the old and new status line rendered 9 inputs (subscription, high context, home dir, outside home, outside a repo, and four token-billing cache states) byte for byte the same.
- T6: two repos on different branches, rendered within 5 seconds, each showed its own branch. Live sessions in other repos now write per-directory caches in `$TMPDIR`.
- T7: with shims that log calls, a first render (`current_usage: null`) called nothing; the old script called `security` and `ccusage`.
- T8: with no ccusage on the PATH, the new script called no `npx`; the old one did.
- T9: 10 renders took 0.19 seconds, against 1.42 seconds for the old script.
- T11: gateway monthly, weekly, daily and no-period inputs each showed the expected spend and pacing; the old script showed nothing for them. The month window was checked against `date` and at the Mar 31 to Feb 28 boundary.
- T13: the hook printed the section for `127.0.0.1:8787` and `127.0.0.1:9000/p/proj`, and nothing for a remote URL or no URL. It ran from both config dirs through the settings command.
- T15: the harness lists `writing-standards` and the skill loads.
- `settings.json` is valid JSON, the diff held only the intended lines, and `install.sh --check` exits 0 for both config dirs.

- Shellcheck 0.11.0, run with `mise exec shellcheck@0.11.0 --` because mise has no global version set, reports nothing for `statusline-command.sh`, `scripts/headroom-context.sh` and `install.sh`.
- T13 in a real session: two headless sessions (`claude -p`, Haiku) ran the hook with status 0. Through the proxy, the transcript holds the section body and the model saw the section. Without `ANTHROPIC_BASE_URL`, the transcript holds none of the body and the model did not see it.
