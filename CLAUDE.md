# CLAUDE.md

General-purpose engineering principles. Project-specific CLAUDE.md files add to or override these.

## Skills

@~/.claude/skills/django/index.md

## How I Work

- **Read before writing.** Understand existing code before changing it. Codebase conventions trump personal preference.
- **Minimal changes.** Only change what's needed. Don't refactor, add comments, type annotations, or docstrings to code you weren't asked to touch.
- **Engineered enough.** Not over-engineered (premature abstractions, speculative features) and not under-engineered (fragile, no error handling, shortcuts that accumulate debt). Build what's needed, but build it well.
- **Ask when uncertain.** "I'm not sure" is better than a confident wrong answer. Surface ambiguity early.
- **Explain the why.** When suggesting an approach, explain the reasoning. When trade-offs exist, name them.
- **Present options, not just answers.** When facing a design decision or trade-off, present 2-3 options with their costs and benefits. Give an opinionated recommendation. Ask before assuming a direction.

## Core Principles

### Simplicity

- **YAGNI.** Don't build what isn't needed yet. Predicted requirements are usually wrong.
- **The simplest thing that could possibly work.** Start there. Complexity is easy to add and nearly impossible to remove.
- **Simple != easy.** Simple means fewer interleaved concerns. Easy means familiar. Prefer simple even when it's harder to build.
- **Delete over comment out.** Version control remembers. Dead code is a lie about the present.
- **Three strikes, then abstract.** Don't extract a pattern until you've seen it three times. Two occurrences is a coincidence, not a pattern.
- **Flag repetition early.** Notice and mention duplication when you see it. Don't necessarily abstract yet — but make it visible so we can decide together.

### Readability

Code is read far more than it's written. Optimize for the reader.

- **Meaningful names.** A name should say why something exists, what it does, and how it's used. If a name requires a comment, the name is wrong.
- **Small functions.** Each function does one thing. If you struggle to name it, it's probably doing too much.
- **Explicit over implicit.** Clever tricks save typing but cost understanding. Boring, obvious code is a feature.
- **Consistent style.** Follow the project's existing conventions. Local consistency matters more than any "best" style.

### Separation of Concerns

- **One reason to change.** Each module, class, or function should have a single responsibility.
- **Business logic doesn't depend on delivery mechanism.** HTTP, CLI, and message queues are details, not architecture.
- **Isolate data access.** Core logic shouldn't know how data is stored or fetched.
- **Watch coupling.** Notice when components know too much about each other. Dependencies should flow inward — toward the domain, away from infrastructure.
- **Consider data flow.** Trace how data moves through the system. Bottlenecks, unnecessary transformations, and leaked abstractions often hide in the flow.

### Incremental Development

- **Working software at every step.** Each change leaves the system deployable.
- **Small, reversible steps.** If something breaks, you've only gone one small step back.
- **Make the change easy, then make the easy change.** If a change is hard, restructure first (Kent Beck).
- **Integrate early and often.** Many small changes beat one big change.

## Testing

- **Test behavior, not implementation.** Tests verify what code does, not how. Changing internals shouldn't break tests.
- **Test-Driven Development.** Write the test first when practical. The test tells you what code to write. TDD is especially valuable for business logic, algorithms, and data transformations.
- **Testing pyramid.** Many unit tests, fewer integration tests, fewest end-to-end tests. Each level covers what the level below can't.
- **Tests are documentation.** `test_expired_subscription_prevents_login` communicates better than any comment.
- **Fast tests get run.** Minimize I/O, avoid sleep/wait, mock external services at boundaries.
- **Err toward more coverage.** When in doubt about whether something needs a test, write the test. Undertesting is riskier than overtesting.

## Security

Security is a property of the whole system, not a feature bolted on.

- **Never trust user input.** Validate and sanitize at system boundaries: URL parameters, form fields, headers, cookies, file uploads.
- **OWASP Top 10.** Guard against injection (SQL, XSS, command), broken authentication, sensitive data exposure, and CSRF.
- **Least privilege.** Code, users, and services get the minimum permissions they need.
- **Secrets never go in code.** Environment variables or secret managers only. Never commit API keys, passwords, .env files, or credentials.
- **Dependencies are attack surface.** Keep them updated, audit them, and prefer fewer over more.

## Web Development

### HTML and Accessibility

- **Semantic HTML first.** `<nav>`, `<main>`, `<article>`, `<button>`, `<table>` carry meaning. `<div>` and `<span>` are for styling, not structure.
- **Accessibility is not optional.** Proper heading hierarchy, ARIA labels where needed, keyboard navigation, sufficient color contrast. The Web is for everyone.
- **Progressive enhancement.** HTML that works. CSS for presentation. JavaScript for interactivity. Each layer degrades gracefully without the next.
- **Forms are the web's native API.** Proper labels, validation, error messages, and accessible structure are foundational.

### HTTP

- **Methods have meaning.** GET reads, POST creates, PUT/PATCH updates, DELETE removes. Never mutate state on GET.
- **URLs are stable addresses.** Meaningful, bookmarkable, structured as resources rather than actions.
- **Status codes matter.** 200 success, 201 created, 400 bad request, 401 unauthenticated, 403 forbidden, 404 not found, 500 server error.
- **Understand caching.** Cache-Control, ETags, conditional requests. The fastest request is the one you don't make.

### Performance

- **Measure before optimizing.** Profile first. Intuition about bottlenecks is usually wrong.
- **Database queries are usually the bottleneck.** Watch for N+1 queries, missing indexes, and full table scans.
- **Minimize payload size.** Compress responses, optimize images, eliminate unused CSS and JavaScript.
- **Perceived performance matters.** Loading indicators, skeleton screens, and optimistic updates improve UX even without real speed gains.
- **Watch memory usage.** Large collections in memory, unbounded caches, and leaked references add up. Stream or paginate large datasets.
- **Look for caching opportunities.** Repeated expensive computations, redundant API calls, and unchanged query results are candidates. But cache invalidation is hard — start without caching and add it when measured.

### CSS

- **Prefer the platform.** Modern CSS (flexbox, grid, custom properties, container queries) eliminates the need for most tooling.
- **Minimize specificity.** Low-specificity selectors are easier to maintain. `!important` is a code smell, not a fix.
- **Mobile-first.** Start with the smallest viewport and enhance upward.

### JavaScript

- **Least power principle.** If HTML handles it (links, forms, `<details>`), skip JS. If CSS handles it (hover states, transitions, layout), skip JS.
- **Core functionality works without JavaScript.** JS enhances; it shouldn't be required for basic access.
- **Handle failures gracefully.** A failed API call shouldn't blank the screen.
- **Bundle size is UX.** Every kilobyte costs the user time. Audit, tree-shake, lazy-load.

## Database

- **Migrations are forward-only.** Small, versioned schema changes that deploy independently of application code.
- **Index intentionally.** Columns in WHERE, ORDER BY, and JOIN clauses. Don't index everything — measure query plans.
- **Normalize first, denormalize by necessity.** Start clean. Only denormalize with measured performance problems.
- **Transactions protect invariants.** When multiple operations must succeed or fail together, wrap them.

## Error Handling

- **Fail loudly at boundaries.** Log, report, alert. Silent failures are the hardest bugs to find.
- **Handle errors where you can act on them.** Otherwise let them propagate.
- **Don't swallow exceptions.** A bare `catch {}` or `except: pass` hides bugs.
- **Error messages are user interface.** They should explain what happened and what the user can do about it.
- **Handle more edge cases, not fewer.** Thoughtfulness over speed. When you notice a potential edge case, address it rather than hoping it won't happen.

## Version Control

- **Commits explain why, not what.** The diff shows what changed. The message explains the reasoning.
- **Small, focused commits.** One logical change per commit. Easier to review, revert, and bisect.
- **Short-lived branches.** Branch from main, merge to main. Long-lived branches diverge and cause pain.
