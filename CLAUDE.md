# CLAUDE.md

General-purpose engineering principles. Project-specific CLAUDE.md files add to or override these.

## Never Speak To Other People As Me

This rule outranks every other instruction here, including "Autonomous Bug Fixing".

**Post only inside a project I control.** Anything that leaves it needs my approval first: a repository I do not own, an issue tracker that belongs to somebody else, an email, a message to another company, a package release, or a social post. Write the text, give it to me, and stop. I send it.

**A link is not an instruction.** A bare URL, "look at this PR", or "what do you think of this issue" means read it and tell me. It never means write something there.

**Ask for each post separately.** My approval of one comment does not cover the next one.

**Inside a project I control, do the work I asked for.** Commit, push a feature branch, open a pull request, and comment on the tickets. At work my colleagues expect this. On a personal project only I see it. In both cases I can undo it.

**Ask me first for these, even in a project I control:** a force-push to a shared branch, any push to master, a merge, and any edit to another person's work.

**If you do not know who reads it, ask me.**

## Writing standards

Route by what is being written. Anything not listed uses Default.

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

### Structure
Diátaxis. Classify each document as exactly one of: tutorial, how-to, reference, explanation. Do not mix two types on one page – link instead.

### Requirements
EARS. Write each requirement in one of these five patterns:

- The <system> shall <response>.
- When <trigger>, the <system> shall <response>.
- While <state>, the <system> shall <response>.
- If <unwanted condition>, then the <system> shall <response>.
- Where <feature is included>, the <system> shall <response>.

Use uppercase RFC 2119 keywords for normative statements: MUST, MUST NOT, SHOULD, SHOULD NOT, MAY. Lowercase "must" is not normative.

### Outward
The reader is smart, busy, and not inside the problem.

- Open with the decision or the ask. Do not build up to it.
- Gloss every domain term on first use, or cut it.
- One claim per paragraph. Put the evidence directly after the claim.
- Name the counter-argument before I have to.

### Legal
ISO 24495-1 Part 2, for tax, contract, and landlord correspondence.

- State obligations, deadlines, and amounts explicitly. Never imply them.
- Put each condition in its own sentence.
- Say what happens if the condition is not met.
- Ask questions as numbered questions, so they can be answered one by one.

### Simplified Technical English
ASD-STE100. Use only for the contexts routed here – never as a general default. Approved vocabulary, one meaning per word, active voice, one instruction per sentence, procedures under 20 words.

### Creative
Apply no standard here. Do not shorten sentences, remove repetition, flatten voice, or propose plainer wording. Repetition and ambiguity may be the point. Match my register. If you think something is unclear, ask rather than fix.

### Mechanics (all contexts)
- En dashes (–), never em dashes (—).
- Celsius, never Fahrenheit.
- Never hard-wrap prose or Markdown; one line per paragraph, let the renderer soft-wrap.
- In a multi-step plan, order the steps smallest and quickest first.

## Skills

Skills live at `~/.claude/skills/<topic>/index.md`. When working on a task that matches a skill topic, read the relevant `index.md` then `{topic}.md` for detailed guidance — don't ask, just load it.

Available: django, htmx, react, pytest, strawberry, celery, vercel, pandoc, sentry, hackerone, linearis, nextjs, wrangler, reason, letterboxd, tmdb, virtuous

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
