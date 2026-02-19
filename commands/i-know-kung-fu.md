---
description: Read an entire documentation site and create skills from it
argument-hint: <docs-base-url>
---

# I Know Kung Fu

Read every page of a documentation website and create Claude Code skills that teach how to do things properly according to that documentation.

## Input

**Documentation URL**: $ARGUMENTS

If no URL was provided, ask the user for one. The URL should be the root of a documentation site (e.g., `https://docs.djangoproject.com/en/stable/`, `https://docs.djangoproject.com/en/6.0/`, `https://htmx.org/docs/`).

## Phase 1: Discovery — Map the Documentation

### 1.1 Identify the Project

Fetch the base URL with WebFetch. From the page content, determine:
- **Project name** (e.g., "django", "htmx", "react") — this becomes the skill namespace
- **Version** — extract from the URL or page content (see below)
- **Documentation structure type** (single page, multi-page with sidebar, API reference, tutorial-based, etc.)

**Version detection:** Many documentation sites encode the version in the URL path (e.g., `/en/6.0/`, `/v3/`, `/2.x/`). When the URL contains a specific version:
- Extract it from the URL path segment (e.g., `https://docs.djangoproject.com/en/6.0/` → version `6.0`)
- Include the version in the project slug: `{name}-{version}` (e.g., `django-6.0`)
- This allows multiple versions to coexist as separate skill sets

When the URL uses `stable`, `latest`, or has no version indicator, omit the version from the slug (e.g., just `django`).

Create a slug from the project name and optional version (lowercase, hyphens). This is `{project}` in all paths below. Record the **base path prefix** from the input URL (e.g., `/en/6.0/`) — this is used in Phase 1.2 to scope discovery.

### 1.2 Find All Documentation Pages

Try these strategies in order until one yields a comprehensive page list:

**URL scoping:** All strategies below must filter discovered URLs to stay within the **base path prefix** identified in Phase 1.1. For example, if the input URL is `https://docs.djangoproject.com/en/6.0/`, only include URLs whose path starts with `/en/6.0/`. This prevents pulling in pages from other versions (e.g., `/en/5.1/`) or unrelated sections of the site.

**Strategy A — Sitemap:**
```
{base_url}/sitemap.xml
{base_url}/../sitemap.xml
{domain}/sitemap.xml
```
Fetch with WebFetch. Parse all `<loc>` URLs. Filter to documentation pages within the base path prefix (exclude blog, changelog, marketing pages, and other versions).

**Strategy B — Table of Contents / Navigation:**
Fetch the base URL. Look for a table of contents, sidebar navigation, or "all topics" page. Follow those links to build the full page list. Many doc sites have an index or contents page — check for links like:
- `/contents/`, `/genindex/`, `/all/`, `/api/`, `/reference/`
- Sidebar navigation with nested sections

**Strategy C — Crawl from base:**
If A and B fail, start from the base URL and extract all internal links that stay within the base path prefix. Follow links one level deep to discover the full documentation tree. Deduplicate by URL.

### 1.3 Present the Map to the User

Before reading everything, present a summary:
- Total number of pages discovered
- Grouped by section/topic (from URL structure or headings)
- Estimated number of skill files to create
- Ask for confirmation before proceeding (this will use many API calls)

**Let the user adjust** — they might want to skip certain sections (e.g., "skip the tutorial, focus on reference docs") or focus on specific areas.

## Phase 2: Organize — Plan the Skill Files

### 2.1 Group Pages into Topics

Analyze the URL structure and page titles to group pages into coherent topics. Each topic becomes one skill file. Aim for:
- **5-20 skill files** depending on documentation size
- Each skill file covers a coherent theme (e.g., "models", "views", "forms", "testing")
- Each skill file synthesizes 3-30 documentation pages

**Grouping heuristics:**
- URL path segments often indicate sections (e.g., `/topics/db/`, `/ref/models/`)
- Documentation with chapters/sections map naturally to skill files
- API reference sections can be grouped by module/package
- Tutorials and how-to guides can be merged into topical skill files

### 2.2 Plan the Output

Output directory: `~/.claude/skills/{project}/`

Files to create:
- `~/.claude/skills/{project}/index.md` — Master index listing all skills
- `~/.claude/skills/{project}/{topic}.md` — One per topic group

Present the planned structure to the user and get approval.

## Phase 3: Read & Synthesize — The Heavy Lifting

### 3.1 Launch Parallel Agents

For each topic group, launch a background `general-purpose` agent using the Task tool. **Launch as many as possible in parallel** (6-10 agents at a time).

Each agent receives:
- The list of URLs to read for its topic
- The project name and topic name
- Instructions on what to extract and how to format the skill file

**Agent prompt template:**

```
You are reading documentation pages for the "{project}" project, specifically the "{topic}" section.

Read each of these URLs using WebFetch and synthesize them into a single, practical skill file.

URLs to read:
{url_list}

Create a skill file at: ~/.claude/skills/{project}/{topic}.md

## What to Include

The skill file should teach someone HOW TO DO THINGS PROPERLY with this technology. Focus on:

1. **Core Concepts** — What are the key ideas? (brief, not exhaustive)
2. **How-To Patterns** — The RIGHT way to do common tasks. Show code examples.
3. **Best Practices** — What the docs recommend. Anti-patterns to avoid.
4. **Common Pitfalls** — Gotchas, foot-guns, things that trip people up
5. **Key APIs** — The most important functions/classes/methods with usage examples
6. **Relationships** — How this topic connects to other parts of the framework

## What NOT to Include

- Don't dump the entire documentation text
- Don't include installation/setup instructions (unless that IS the topic)
- Don't include changelog or version history
- Don't include the tutorial walkthrough step-by-step (extract the PATTERNS from it instead)
- Don't include every single API method — focus on the important ones

## Format

Use clear markdown with:
- Short, scannable sections
- Code examples for every pattern
- "Do this / Don't do this" comparisons where relevant
- Quick-reference tables for common operations

## Size Target

Aim for 200-500 lines per skill file. Dense and practical, not sprawling.

After creating the file, report back what you covered and any pages that had errors or were inaccessible.
```

### 3.2 Monitor Progress

After launching all agents, wait for them to complete. Use TaskOutput to check on background agents periodically. Report progress to the user as agents finish.

### 3.3 Handle Failures

If an agent fails or a URL is inaccessible:
- Note which URLs failed
- Try once more with a fresh agent for failed pages
- If still failing, note the gap in the index file

## Phase 4: Index & Wire Up

### 4.1 Create the Master Index

After all agents complete, create `~/.claude/skills/{project}/index.md`:

```markdown
# {Project Name} Skills

Generated from {base_url} on {date}.

## Available Skills

| Skill | Topics Covered | Source Pages |
|-------|---------------|--------------|
| [{topic}](./{topic}.md) | Brief description | N pages |
| ... | ... | ... |

## How to Use

Reference individual skills in your project's CLAUDE.md:

    @~/.claude/skills/{project}/{topic}.md

Or reference this index to see all available skills:

    @~/.claude/skills/{project}/index.md

## Coverage

- Total documentation pages: {N}
- Pages read: {M}
- Pages failed: {F} (list if any)
```

### 4.2 Review the Output

Read each created skill file to verify quality. Check for:
- Files that are too short (agent may have failed to read pages)
- Files that are just raw dumps instead of synthesized guidance
- Missing cross-references between skill files

Present a summary to the user:
- List all created skill files with their sizes
- Note any gaps or quality issues
- Suggest how to reference them in their projects

### 4.3 Offer to Wire Up

Ask the user if they want to:
1. **Add to current project** — Add `@~/.claude/skills/{project}/index.md` to the project CLAUDE.md
2. **Add to global config** — Add reference to `~/.claude/CLAUDE.md`
3. **Leave standalone** — Just have the files available for manual reference

## Guidelines

### Quality Over Quantity
It's better to have 8 excellent skill files than 20 mediocre ones. If a documentation section is thin or not useful for "how to do things", merge it into a broader topic or skip it.

### Practical Over Theoretical
Every skill file should help someone WRITE BETTER CODE. If a section of documentation is purely conceptual with no actionable guidance, summarize it briefly rather than expanding it.

### Respect Context Limits
Each agent can reasonably read ~15-20 documentation pages and synthesize them. If a topic group has more pages, split it into sub-topics (e.g., "django-models-fields" and "django-models-queries" instead of one giant "django-models").

### Idempotent
If skills already exist for this project in `~/.claude/skills/{project}/`, ask the user whether to:
- **Overwrite** — Replace all existing skills
- **Merge** — Only create missing skills, skip existing ones
- **Cancel** — Don't proceed
