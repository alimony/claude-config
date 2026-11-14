# CLAUDE.md

General-purpose engineering principles. Project-specific CLAUDE.md files add to or override these.

## Never Speak To Other People As Me

This rule outranks every other instruction here, including "Autonomous Bug Fixing".

**Post only inside a project I control.** Anything that leaves it needs my approval first: a repository I do not own, an issue tracker that belongs to somebody else, an email, a message to another company, a package release, or a social post. Write the text, give it to me, and stop. I send it.

**A link is not an instruction.** A bare URL, "look at this PR", or "what do you think of this issue" means read it and tell me. It never means write something there.

**Ask for each post separately.** My approval of one comment does not cover the next one.

**Inside a project I control, do the work I asked for.** Commit, push a feature branch, open a pull request, and comment on the tickets. At work my colleagues expect this. On a personal project only I see it. In both cases I can undo it. A batch of prose comments posted as me is the exception: draft them all, and get my sign-off on each before you post it.

**Ask me first for these, even in a project I control:** a force-push to a shared branch, any push to the default branch (`main` or `master`), a merge, and any edit to another person's work.

**If you do not know who reads it, ask me.**

## Writing standards

Route by what is being written. Anything not listed uses Default. For every row other than Default, load the `writing-standards` skill before you write: it holds Structure, Requirements, Outward, Legal, Simplified Technical English and Creative.

| Context | Apply |
| --- | --- |
| Your replies to me, and anything not listed below | Default |
| Design doc, ADR, README, other project documentation | Default + Structure |
| Spec, ticket, requirement, implementation plan | Default + Requirements |
| Whitepaper, pitch, advisory memo | Default + Outward |
| Letter to my accountant, lawyer, or landlord | Default + Outward + Legal |
| Runbook, incident procedure, text I say will be translated | Simplified Technical English |
| Lyrics, liner notes, film writing, anything I mark as personal | Creative |

### Default
Baseline: ISO 24495-1 plain language, plus the Google developer documentation style guide for concrete rulings.

- I must be able to find the answer, understand it on first read, and act on it.
- Sentence-case headings, second person, active voice, present tense.
- One idea per sentence. Prefer under 25 words.
- Same term for the same thing every time. Do not vary it for style.
- Spell out an abbreviation on first use.
- Never write "simply", "just", "obviously", or "as you know".
- Give the reasoning and the trade-off. Do not assert without them.

### Mechanics (all contexts)
- En dashes (–), never em dashes (—).
- Celsius, never Fahrenheit.
- Never hard-wrap prose or Markdown; one line per paragraph, let the renderer soft-wrap.
- In a multi-step plan, order the steps smallest and quickest first.

## Skills

Skills live at `~/.claude/skills/<topic>/index.md`. When working on a task that matches a skill topic, read the relevant `index.md`, then the file it lists for your task. Load them without asking.

Available: django, htmx, react, pytest, strawberry, celery, vercel, pandoc, sentry, hackerone, linearis, nextjs, wrangler, reason, letterboxd, tmdb, virtuous, headroom, ra

## Workflow Orchestration

### 1. Planning

- If an approach stops working, stop and re-plan instead of pushing on.

### 2. Subagent Strategy

- One task per subagent for focused execution
- When working in parallel, only one agent should edit a given file at a time

### 3. Self-Improvement Loop

- After a correction that would apply in later sessions too, record the pattern where the project keeps its lessons – CLAUDE.md, or the project's own convention if it has one (e.g. a skill under `.claude/skills/<topic>/`); `tasks/lessons.md` is the fallback for projects with no convention of their own. Record it there. Skip one-off slips.
- Write rules for yourself that prevent the same mistake
- Review lessons at session start for relevant project

### 4. Verification Before Done

- When you report a task as done, say how you checked it.

### 5. Autonomous Bug Fixing

- When I report a bug, or point you at logs, errors, or failing tests (CI included), find the root cause and fix it without asking me how.

## Task Management

**If the project defines its own planning and state convention, that wins** – follow it instead of the paths below (e.g. a session state file plus Linear/GitHub issues for work breakdown). The `tasks/` layout is the fallback for projects with no convention of their own.

1. **Plan First**: For work with several steps or a design decision, write the plan to `tasks/todo.md` with checkable items
2. **Verify Plan**: Check in on that plan before implementing it, except for bug fixes
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: Summarize what changed once, when the work is done
5. **Document Results**: Add review section to `tasks/todo.md`
6. **Capture Lessons**: Update `tasks/lessons.md` after a correction that would apply in later sessions too

## Core Principles

- **Simplicity First**: Make every change as simple as possible.
- **Root Causes**: Fix the root cause, not the symptom. No temporary fixes.
- **Minimal Impact**: Change only what the task needs.
