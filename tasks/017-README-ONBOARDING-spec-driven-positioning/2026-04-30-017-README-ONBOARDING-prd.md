# 017-README-ONBOARDING: README Rewrite for Spec-Driven Positioning — PRD

**Status**: Draft
**Created**: 2026-04-30
**Author**: Claude (via /dev:prd, dpovesma@artec3d.com directing)
**Branch**: `feature/017-readme-onboarding`

---

## Context

The current `README.md` is 770+ lines and front-loads installation
prerequisites, hooks, statusline configuration, and Docker before the
reader learns what the project actually does or why they should care.
Newcomers landing on the GitHub page see ceremony, not value. Engineers
shopping for a Claude Code workflow plugin need to know in 60 seconds:
"what category is this, what does it do that the alternatives don't,
how do I try it." Today they don't.

This PRD scopes a rewrite that puts a TL;DR + comparison table + simple
install above the fold, demotes technical reference to later sections,
and adds AI-generated diagrams to communicate the architecture
visually. A produced explainer video is deferred to V2.

### Current State (observed)

- `README.md` is 770 lines — verified via:
  `wc -l README.md` → 770, 2026-04-30
- Section ordering today is What → Prerequisites → Installation →
  Hooks → Statusline → Profiles → Hooks (duplicate?) → Quick Start →
  Available Commands — verified via: `grep -n '^## ' README.md`,
  2026-04-30
- The first reader-facing description is "RLM-Mem provides a complete
  workflow for working with large codebases" — verified via:
  `grep -n 'RLM-Mem provides' README.md`, 2026-04-30
- The repo's own term for the workflow is **"Hybrid Quality-First
  Development Workflow"** — verified via NotebookLM
  cross-notebook query against the AI Agentic Workflows notebook,
  citation `b44ca1d8-9815-49c0-82f6-3b1ffe03606c`, 2026-04-30
- The community-recognised industry term for the PRD → tech-design
  → tasks → impl pattern is **"spec-driven development"** —
  verified via NotebookLM query (notebook `a9782dcd`,
  citation `de833dd0-0a7a-4d2b-915a-233c749d5b81`), 2026-04-30
- Claude Design (Anthropic Labs) launched 2026-04-17, generates
  interactive HTML/SVG/PNG/PPTX prototypes from prompts; supports
  handoff to Claude Code; pricing tied to Pro/Max/Team/Enterprise
  subscriptions — verified via WebFetch
  `https://www.anthropic.com/news/claude-design-anthropic-labs`,
  2026-04-30. Programmatic API or MCP server: not documented in the
  launch announcement [assumption, verify in tech-design]
- HeyGen has an official MCP connector and Claude Code Skills for
  programmatic video generation — verified via WebSearch and
  `https://www.heygen.com/blog/generate-ai-videos-with-claude`,
  2026-04-30. Synthesia, Runway are alternatives with REST APIs

### Past Similar Features (from claude-mem + NotebookLM)

- The same notebook (`a9782dcd`) already contains a detailed
  source for rlm-mem itself, providing canonical phrasings we can
  reuse: "Hybrid Quality-First Development Workflow", "RLM
  (Recursive Language Model)", "9 Commands cover the complete
  development lifecycle"
- Prior README edits in this repo (commits `0069f16`,
  `d988027`) were tactical — fixed counts, added the `/dev:git`
  command — never restructured. This PRD is the first holistic
  rewrite

## Problem Statement

**Who**: Engineers evaluating Claude Code workflow plugins (primary);
existing users + engineering managers (secondary)

**What**: Cannot answer "what is this and should I use it" in under
60 seconds from the README. Cannot tell how rlm-mem differs from
Superpowers, BMAD, OMC, or claude-workflow-template without reading
all of them. Cannot show a teammate a 30-second pitch

**Why**: First impressions on GitHub determine adoption. The market
has at least 6 named competitors as of April 2026 (see References),
and the category is consolidating around "spec-driven development".
A README that doesn't position rlm-mem in that category by name and
show its differentiator (only framework with both persistent
codebase index AND cross-session memory) will lose evaluators by
default

**When**: Triggered by user request 2026-04-30 after observing
README friction during real onboarding

## Goals

### Primary Goal

A README that lets a developer go from "found this on GitHub" to
"installed and running" in under 5 minutes and to "I understand
what differentiates this from Superpowers" in under 60 seconds.

### Secondary Goals

- Establish the category name **"spec-driven Claude Code workflow"**
  as the canonical descriptor in repo docs
- Make the "only framework with persistent codebase index +
  cross-session memory" differentiator visible above the fold
- Provide visual artefacts (architecture diagram, terminal
  screencast) so non-readers can grasp the system
- Keep technical depth available — relocated, not removed

## User Stories

### Epic

As a developer, I want to land on the rlm-mem README and decide
whether to try it within 60 seconds, so that I can evaluate it
honestly against alternatives without committing to a 30-minute
read.

### User Stories

1. **As a developer evaluating Claude Code workflow plugins**
   **I want** the first screen of the README to tell me the
   category, the one-sentence pitch, the differentiator, and a
   3-line install
   **So that** I can decide in under 60 seconds whether to keep
   reading

   **Acceptance Criteria**:
   - [ ] First non-title content is a TL;DR block ≤ 5 lines
   - [ ] Category name appears in the first paragraph
   - [ ] Install fits in ≤ 5 shell lines, copy-pasteable
   - [ ] A "vs Superpowers / BMAD / OMC" comparison table appears
         within the first 25% of the file

2. **As a developer comparing rlm-mem to Superpowers**
   **I want** a comparison table that names alternatives and shows
   the differentiator
   **So that** I don't have to read three other repos to make a
   decision

   **Acceptance Criteria**:
   - [ ] Comparison table covers at least 4 named competitors
   - [ ] Table includes columns for: persistent codebase index,
         cross-session memory, spec-driven phases, TDD
         enforcement, workflow profiles
   - [ ] Each row links to the competitor's repo

3. **As a visual learner**
   **I want** an architecture diagram and a terminal screencast
   **So that** I can grasp how RLM, claude-mem, and the workflow
   commands fit together without reading prose

   **Acceptance Criteria**:
   - [ ] At least one architecture diagram embedded in the README
   - [ ] Diagram shows the three layers: RLM (file index),
         claude-mem (memory), commands (workflow)
   - [ ] At least one asciinema-style terminal screencast or
         animated GIF shows a real session (e.g.
         `/dev:start` → `/dev:prd` flow)

4. **As an engineering manager evaluating ROI**
   **I want** a brief "Why this exists" section with citable
   evidence
   **So that** I can justify adoption to my team or skip the tool

   **Acceptance Criteria**:
   - [ ] README contains a "Why this exists" section ≤ 200 words
   - [ ] Section cites at least 2 external sources (e.g. SWE-bench
         numbers, METR study, Token Snowball paper)
   - [ ] A linked `docs/WHY.md` carries the full evidence dossier
         for readers who want depth

5. **As an existing user**
   **I want** technical reference (hooks, settings, profiles,
   Docker) preserved and findable
   **So that** my workflows don't break

   **Acceptance Criteria**:
   - [ ] All technical content from the current README either
         remains in README under a "Reference" section or moves to
         a linked `docs/` file with a clear pointer
   - [ ] No content is silently deleted

6. **As a contributor adding a new feature**
   **I want** a competitors section that's easy to extend when a
   new framework appears
   **So that** the comparison stays current

   **Acceptance Criteria**:
   - [ ] Competitors section sits at the bottom of the README
   - [ ] Comparison table is markdown (not an image), so any
         contributor can add a row

## Requirements

**Describe by class and sensitivity, not by concrete identifier.**
Concrete diagram contents, exact section ordering, prose drafts,
and competitor row contents belong in the tech-design.

### Functional Requirements

1. **FR-1: README structure refactor** — Reorder the README so
   that TL;DR, category positioning, install, and quickstart
   appear above the fold (within first 100 lines). Demote prereq
   tables, statusline, hooks reference, and Docker to a Reference
   section.
   - Priority: High
   - Rationale: Story 1 (60-second eval), Story 5 (preserve depth)
   - Dependencies: None

2. **FR-2: Spec-driven category positioning** — Use "spec-driven
   Claude Code workflow" as the canonical descriptor in the
   README first paragraph and tagline. Retain "Hybrid
   Quality-First Development Workflow" as the named methodology
   inside.
   - Priority: High
   - Rationale: Industry-term alignment per NotebookLM research

3. **FR-3: Comparison table** — A markdown table comparing
   rlm-mem against named alternatives (at least 4) along
   distinguishing dimensions. Located in the bottom third of the
   README under a clearly labelled section.
   - Priority: High
   - Rationale: Stories 2 and 6
   - Note: Concrete competitor list and column headers go in
     tech-design

4. **FR-4: Architecture diagram(s) generated by Claude Design** —
   At least one diagram showing the system architecture, embedded
   in the README. Generated through Anthropic Claude Design and
   exported as a static format the README can display
   (PNG/SVG/standalone HTML).
   - Priority: High
   - Rationale: Story 3
   - Dependency: Anthropic Claude Design subscription access
     [assumption: user has Claude Pro/Max/Team/Enterprise — verify
     in tech-design]
   - Constraint: If Claude Design lacks export to a format git can
     reasonably store (i.e. only outputs Canva/PPTX), fall back to
     mermaid syntax in markdown

5. **FR-5: Terminal screencast** — At least one asciinema
   recording or animated GIF showing a real `/dev:*` command
   flow. Linked or embedded in the README.
   - Priority: Medium
   - Rationale: Story 3
   - Constraint: Must work without autoplay (GIFs autoplay; that's
     acceptable). No audio.

6. **FR-6: "Why this exists" section + linked WHY.md** — A
   ≤ 200-word section in the README citing 2–3 external evidence
   points. Full dossier lives in `docs/WHY.md`.
   - Priority: Medium
   - Rationale: Story 4
   - Source pool: NotebookLM-verified citations (TDFlow SWE-bench
     numbers, METR study, Token Snowball, MemPalace, Lost in the
     Middle)

7. **FR-7: Preserve existing technical reference** — All current
   sections covering installation steps, hooks, statusline,
   profiles, Docker either stay in the README under a Reference
   heading or move to dedicated `docs/*.md` files with a clear
   pointer from README.
   - Priority: High (no-regression)
   - Rationale: Story 5

### Non-Functional Requirements

1. **NFR-1: Readability** — TL;DR + category + install fit on a
   single 1080p screen at default GitHub render width. Verified by
   visual inspection in tech-design / impl phase
2. **NFR-2: Maintenance cost** — Diagrams must be regenerable from
   their source prompt or definition file. No hand-edited PNGs
   without a recorded source
3. **NFR-3: No produced video in V1** — Out of scope this round.
   See "Out of Scope"
4. **NFR-4: Markdown-only** — README itself stays plain markdown;
   no HTML embeds beyond what GitHub renders natively (`<img>` and
   `<details>` are fine, `<script>` is not)

### Technical Constraints

- Must remain a single `README.md` at repo root (GitHub convention)
- Diagram source(s) must be committed alongside generated assets
- No new build step — generation tools (Claude Design, asciinema,
  HeyGen) run out-of-band; their outputs are committed
- Must not break existing links from the install script,
  TROUBLESHOOTING.md, or task files referencing README sections
  (audit before merge)

## Out of Scope

- **Produced explainer video** — deferred to V2. The HeyGen MCP
  integration is *researched* in this PRD but the video itself
  ships in a follow-up PRD (e.g. 018) once V1 metrics justify it
- **i18n / non-English README** — V1 is English-only
- **Generating a website / docs site** — README + linked
  `docs/*.md` only. No mkdocs, Docusaurus, etc.
- **Restructuring CLAUDE.md** — separate concern; CLAUDE.md is
  developer-facing
- **Renaming the project** — "RLM-Mem" stays. Category descriptor
  is what changes, not the product name
- **Comparing against non-Claude-Code tools** — Cursor rules,
  Aider workflows, GitHub Copilot extensions out of scope.
  Comparison stays within the Claude Code plugin/skill ecosystem

## Success Metrics

1. **Above-the-fold completeness** — TL;DR, category, install,
   differentiator all visible without scrolling on a 1080p screen
   (binary check)
2. **Readability** — README first 100 lines contain ≥ 4 of the
   following: tagline, category name, comparison link, install
   commands, quickstart commands, "Why this exists" pointer,
   architecture diagram or its anchor
3. **Comparison breadth** — Comparison table covers ≥ 4 named
   competitors (Superpowers, BMAD, OMC, claude-workflow-template
   minimum)
4. **Reference preservation** — `git diff README.md` between
   pre/post rewrite shows zero pure deletions of factual content
   (audit step in tech-design / impl)
5. **Onboarding friction** — Validate qualitatively by asking
   one developer unfamiliar with the project to install + run
   `/dev:start` from the new README; target ≤ 5 minutes

## References

### Industry Sources (NotebookLM + Web)

- NotebookLM: notebook `a9782dcd-d629-4c62-9445-aeba00425437`
  "AI Agentic Workflows and Claude Developer Tools" — confirms
  "spec-driven development" as community term and inventories
  competitors
- NotebookLM: notebook `b040f36c-f7db-4e54-9fe1-048f52c21aaa`
  "Architecting AI Software Engineering" — provides quotable
  evidence on context engineering vs one-shot prompts
- NotebookLM: notebook `63a17be3-0de7-44df-ac67-47d0cce4021d`
  "The Future of AI-Assisted Software Development and Agentic
  Coding" — provides SWE-bench/TDFlow/Token-Snowball evidence
- NotebookLM: notebook `81d16e4c-6347-4e7b-b066-59bf9c2a88e2`
  "Persistent AI Memory Systems" — claude-mem vs MemPalace
  positioning and benchmarks
- Anthropic Claude Design launch:
  https://www.anthropic.com/news/claude-design-anthropic-labs
- Superpowers plugin: https://github.com/obra/superpowers
- BMAD ports:
  https://github.com/24601/BMAD-AT-CLAUDE,
  https://github.com/aj-geddes/claude-code-bmad-skills
- shinpr workflows: https://github.com/shinpr/claude-code-workflows
- HeyGen MCP: https://www.heygen.com/blog/generate-ai-videos-with-claude

### From Codebase (RLM)

- `README.md` — target file
- `CLAUDE.md` — siblings, not edited by this PRD
- `.claude/commands/dev/*.md` — referenced by README, not edited
- `tasks/016-RLM-PATH-EXCLUSION-init-repo-exclude-include/` — most
  recent feature, structurally similar PRD/tech-design pair to
  use as template

### From History (Claude-Mem)

- Past README edits (commits `0069f16`, `d988027`) — were
  tactical, never restructured
- Task 014 added `/dev:git` to Available Commands — pattern for
  inserting new sections without breaking flow

---

**Next Steps**:

1. Review and refine this PRD
2. Run `/dev:tech-design` to:
   - Confirm Claude Design API/export feasibility (resolve the
     `[assumption, verify in tech-design]` flag in Current State)
   - Specify the concrete competitor table (rows + columns)
   - Decide diagram format (PNG vs SVG vs mermaid fallback)
   - Specify section ordering and word-counts
3. Run `/dev:tasks` to break down into implementation subtasks
