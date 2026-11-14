---
name: writing-standards
description: The writing standards that CLAUDE.md's routing table adds to Default – Structure (Diátaxis) for design docs, ADRs, READMEs and other project documentation; Requirements (EARS) for specs, tickets, requirements and implementation plans; Outward for whitepapers, pitches and advisory memos; Legal for letters to an accountant, lawyer or landlord; Simplified Technical English for runbooks, incident procedures and text that will be translated; Creative for lyrics, liner notes, film writing and anything marked as personal. Use before writing any of these.
---

# Writing standards

CLAUDE.md routes each kind of writing to Default plus one or more of the standards below. Default and Mechanics stay in CLAUDE.md and still apply.

## Structure
Diátaxis. Classify each document as exactly one of: tutorial, how-to, reference, explanation. Do not mix two types on one page – link instead.

## Requirements
EARS. Write each requirement in one of these five patterns:

- The <system> shall <response>.
- When <trigger>, the <system> shall <response>.
- While <state>, the <system> shall <response>.
- If <unwanted condition>, then the <system> shall <response>.
- Where <feature is included>, the <system> shall <response>.

Use uppercase RFC 2119 keywords for normative statements: MUST, MUST NOT, SHOULD, SHOULD NOT, MAY. Lowercase "must" is not normative.

## Outward
The reader is smart, busy, and not inside the problem.

- Open with the decision or the ask. Do not build up to it.
- Gloss every domain term on first use, or cut it.
- One claim per paragraph. Put the evidence directly after the claim.
- Name the counter-argument before I have to.

## Legal
ISO 24495-1 Part 2, for tax, contract, and landlord correspondence.

- State obligations, deadlines, and amounts explicitly. Never imply them.
- Put each condition in its own sentence.
- Say what happens if the condition is not met.
- Ask questions as numbered questions, so they can be answered one by one.

## Simplified Technical English
ASD-STE100. Use only for the contexts routed here – never as a general default. Approved vocabulary, one meaning per word, active voice, one instruction per sentence, procedures under 20 words.

## Creative
Apply no standard here. Do not shorten sentences, remove repetition, flatten voice, or propose plainer wording. Repetition and ambiguity may be the point. Match my register. If you think something is unclear, ask rather than fix.
