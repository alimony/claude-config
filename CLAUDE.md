# CLAUDE.md

General-purpose engineering principles. Project-specific CLAUDE.md files add to or override these.

## Output Style

- **Always use an en dash (–), never an em dash (—)** in all output – prose, chat messages, code comments, and report text alike. Wherever an em dash would conventionally mark a parenthetical break or a range, use an en dash instead.
- **Never hard-wrap Markdown or prose.** Write one line per paragraph and let the editor/renderer soft-wrap – no manual line breaks in the middle of a paragraph, in files or in messages. (The only exception is a platform-specific report format that genuinely requires hard breaks, and only where a project-level rule explicitly says so.)

## Skills

Skills live at `~/.claude/skills/<topic>/index.md`. When working on a task that matches a skill topic, read the relevant `index.md` then `{topic}.md` for detailed guidance — don't ask, just load it.

Available: django, htmx, react, pytest, strawberry, celery, vercel, pandoc, sentry, hackerone, linearis, nextjs, wrangler, reason

## Workflow Orchestration

### 1. Plan Mode Default

- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately — don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity
- Once the plan is solid, switch to auto-accept edits — Claude can usually one-shot it

### 2. Subagent Strategy

- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution
- When working in parallel, only one agent should edit a given file at a time
- For fully parallel workstreams, use git worktrees

### 3. Self-Improvement Loop

- After ANY correction from the user: record the pattern where the project keeps its lessons — CLAUDE.md, or the project's own convention if it has one (e.g. a skill under `.claude/skills/<topic>/`); `tasks/lessons.md` is the fallback for projects with no convention of their own
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 4. Verification Before Done

- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness
- Give Claude a way to verify its work — this 2-3x the quality of the final result

### 5. Demand Elegance (Balanced)

- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes — don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing

- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests — then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

## Task Management

**If the project defines its own planning and state convention, that wins** — follow it instead of
the paths below (e.g. a session state file plus Linear/GitHub issues for work breakdown). The
`tasks/` layout is the fallback for projects with no convention of their own.

1. **Plan First**: Write plan to `tasks/todo.md` with checkable items
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review section to `tasks/todo.md`
6. **Capture Lessons**: Update `tasks/lessons.md` after corrections

## Core Principles

- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Changes should only touch what's necessary. Avoid introducing bugs.
