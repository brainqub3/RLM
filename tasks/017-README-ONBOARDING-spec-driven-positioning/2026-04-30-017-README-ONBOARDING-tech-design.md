# 017-README-ONBOARDING — Technical Design

**Status**: Draft
**PRD**: [2026-04-30-017-README-ONBOARDING-prd.md](2026-04-30-017-README-ONBOARDING-prd.md)
**Created**: 2026-04-30
**Branch**: `feature/017-readme-onboarding`

---

## Overview

Restructure `README.md` in place. Replace the front 540 lines (TL;DR
through Quick Start) with a new top-of-file driven by spec-driven
positioning, a comparison table, and Claude-Design-generated PNG
architecture diagrams committed under `assets/`. Keep all existing
technical reference content (hooks, statusline, profiles, Docker,
Docker, contributing, license) in the same file under a single
`## Reference` heading at the bottom. No new docs/ files. No
screencast in V1. No video.

This is a **documentation-only** change — no code touched. Risk
profile: low for the workflow, high for first-impression quality
(the whole point of the rewrite).

## Current Architecture (RLM-verified)

This section resolves every PRD "Current State" claim against
current code/files, per the Step 1.5 rule.

### Verified anew

- **README size**: 809 lines — verified via:
  `wc -l README.md`, 2026-04-30. (PRD said "770+"; the file
  grew by ~39 lines since PRD draft due to the Excluding Vendor
  Paths subsection added in task 016. Claim still holds in
  spirit; PRD updated mentally.)
- **Section ordering**: 22 top-level `## ` headings — verified
  via: `grep -n '^## ' README.md`, 2026-04-30. Order matches PRD
  description (What → Prereqs → Install → Hooks → Statusline →
  Profiles → Hooks (duplicate header) → Quick Start → Available
  Commands → ...). Note the **two `## Hooks` headings** at lines
  258 and 379 — likely an accidental near-duplicate that should
  be consolidated during the rewrite.
- **First reader-facing description**: "RLM-Mem provides a
  complete workflow…" — verified via:
  `grep -n 'RLM-Mem provides' README.md`, 2026-04-30. Located
  inside `## 🎯 What Is This?` at line 5+.
- **Repo's own term "Hybrid Quality-First Development Workflow"**
  — verified via: NotebookLM cross-notebook query, citation
  `b44ca1d8-9815-49c0-82f6-3b1ffe03606c`, 2026-04-30. Confirmed.
- **Industry term "spec-driven development"** — verified via:
  NotebookLM query, citation `de833dd0-0a7a-4d2b-915a-233c749d5b81`,
  2026-04-30. Confirmed.

### Resolved assumption

PRD flagged: *"Claude Design API or MCP server: not documented
in the launch announcement [assumption, verify in tech-design]"*

**Resolution**: **Negative**. There is no public Claude Design API
or MCP server as of 2026-04-30 — verified via WebSearch
(`Claude Design Anthropic API MCP programmatic export 2026`)
and WebFetch on the Anthropic launch announcement. Anthropic
states integrations will land "over the coming weeks" but they
are not shipped today. No SVG/PNG/Mermaid native export.

**Implication for design**: We cannot script Claude Design
invocation from CI or `make` targets. User decision (locked):
generate diagrams interactively in Claude Design, export to
standalone HTML, take a PNG screenshot, commit the PNG.
Source prompts saved alongside as `.prompt.md` so a future
maintainer can regenerate. This is *not* fully reproducible —
acknowledged risk; mitigated by the prompt file.

## Past Decisions (Claude-Mem)

- Tasks 011–016 commit history shows a consistent pattern:
  README is edited in place across tasks; no prior task created
  a `docs/` directory. Sticking to single-file README aligns
  with this precedent.
- Task 014 added `/dev:git` to README's Available Commands
  table without restructuring — pattern reused here for the
  comparison table insertion.

## Proposed Design

### Structural plan

The README will be split conceptually into three zones; physical
layout is one file:

```
┌──────────────────────────────────────────────┐
│ Above-the-fold (target ≤ 120 lines)          │
│   - title + tagline                          │
│   - TL;DR block                              │
│   - 3-line install                           │
│   - 60-second Quick Start                    │
│   - Architecture diagram (PNG)               │
│   - Comparison table                         │
│   - Why this exists (≤ 200 words)            │
│   - link to docs/WHY.md                      │
├──────────────────────────────────────────────┤
│ Mid-section (≤ 250 lines)                    │
│   - What you get (commands list, briefly)    │
│   - Workflow walkthrough (PRD→tasks→impl)    │
│   - Profiles overview                        │
│   - Test subagents brief                     │
├──────────────────────────────────────────────┤
│ Reference (everything else, bottom)          │
│   - Detailed installation per platform       │
│   - Hooks (consolidated single section)      │
│   - Statusline                               │
│   - Profiles details                         │
│   - Test subagents details                   │
│   - Docker                                   │
│   - Configuration                            │
│   - Verification / Updating / Help           │
│   - Contributing / License                   │
│   - Acknowledgments                          │
└──────────────────────────────────────────────┘
```

Target final line count: ≤ 850 (current 809 + diagrams + new
content - removed duplication). Zero net deletion of factual
content (NFR check via diff audit before merge).

### Components

This is doc-only, but treating sections as components clarifies
ownership and verification:

**New sections**:

1. **TL;DR block**
   - Purpose: 5-line value proposition above the fold
   - Location: README, replaces existing "What Is This?" framing
   - Content contract:
     - one-sentence category positioning ("spec-driven Claude
       Code workflow")
     - one-sentence differentiator ("only framework with both
       persistent codebase index and cross-session memory")
     - one-line install command (or pointer to install block)
     - link to comparison table
     - link to WHY.md

2. **Comparison table**
   - Purpose: position vs named alternatives (Story 2)
   - Location: README, mid-section (~line 100)
   - Format: GitHub-flavoured markdown table
   - Source link per row to competitor repo

3. **Architecture diagram (PNG)**
   - Purpose: visual explanation (Story 3)
   - Location: README, above-the-fold zone, after TL;DR
   - Asset paths:
     - `assets/diagrams/architecture-overview.png` (rendered)
     - `assets/diagrams/architecture-overview.prompt.md` (the
       Claude Design prompt used to generate it, committed
       so future maintainers can regenerate without
       reverse-engineering)
   - Optionally a second diagram showing the workflow
     command sequence (PRD→tech-design→tasks→impl)

4. **"Why this exists" subsection**
   - Purpose: ROI evidence (Story 4)
   - Location: README, end of above-the-fold zone
   - Length: ≤ 200 words
   - Cites: 2–3 strongest stats from NotebookLM evidence pool
   - Links to: full `docs/WHY.md` dossier

5. **`docs/WHY.md`**
   - Purpose: full evidence dossier (Story 4)
   - Length: 600–1200 words
   - Sources: TDFlow SWE-bench numbers (88.8% / 94.3% / 27.8%
     improvement), METR study (19% slowdown for unstructured
     AI use), Token Snowball paper (4× resource cost on
     failed attempts), Lost-in-the-Middle (>20% accuracy
     drop), MemPalace 19.5M-token figure for 6 months of
     daily AI use
   - Each citation: full quote + source link, lifted from
     NotebookLM query results in this session

**Modified sections** (in-place edits only — no logical
restructure beyond reordering):

| Existing section | Action |
|---|---|
| `## 🎯 What Is This?` | Replace with TL;DR + Quick Pitch |
| `## 📋 Prerequisites` | Move to Reference |
| `## 🚀 Installation` | Keep a 3-line summary above the fold; full version moves to Reference |
| `## 📦 What Gets Installed` | Move to Reference |
| `## Hooks` (line 258) | Merge with `## 🛡️ Hooks` (line 379) under Reference |
| `## Statusline` | Move to Reference |
| `## ⚙️ Profiles` | Keep brief overview in mid-section, details to Reference |
| `## 🛡️ Hooks` (line 379) | Consolidate with the earlier Hooks section |
| `## 🎮 Quick Start` | Promote above the fold, condense to 60-second flavour |
| `## 📚 Available Commands` | Stay in mid-section |
| `## 🧪 Test Subagents` | Brief blurb in mid-section, details to Reference |
| `## 💡 Usage Tips` | Move to Reference |
| `## 🔧 Configuration` | Move to Reference |
| `## 📖 Documentation` | Move to Reference |
| `## 🔗 Related Projects` | **Replace** with new "Comparison" section (above the fold) |
| `## 🔍 Verification` | Move to Reference |
| `## 🆘 Getting Help` | Move to Reference |
| `## 🔄 Updating` | Move to Reference |
| `## 📝 License` | Move to Reference (unchanged) |
| `## 🐳 Docker Development & Testing` | Move to Reference |
| `## 🤝 Contributing` | Move to Reference |
| `## 🙏 Acknowledgments` | Move to Reference |
| `## 🚀 What's Next?` | Drop or fold into "Why this exists" |

### Data contracts

**Comparison table — column schema** (locked):

| Column | Type | Source-of-truth |
|---|---|---|
| Project | string + link | competitor repo URL |
| Spec-driven phases | ✅ / ❌ / partial | competitor README |
| Persistent codebase index | ✅ / ❌ | competitor README |
| Cross-session memory | ✅ (built-in) / ✅ (optional add-on) / ❌ | competitor README |
| TDD enforcement | ✅ / ❌ / partial | competitor README |
| Workflow profiles | ✅ / ❌ | competitor README |
| Subagent count | integer | competitor README |
| Git worktrees | ✅ / ❌ | competitor README |

**Comparison table — row set** (locked):

1. **rlm-mem** (this repo) — `https://github.com/povesma/claude_code_RLM_mem`
2. **Superpowers** — `https://github.com/obra/superpowers`
3. **BMAD-METHOD** (representative port:
   `aj-geddes/claude-code-bmad-skills`) —
   `https://github.com/aj-geddes/claude-code-bmad-skills`
4. **Oh-My-ClaudeCode (OMC)** — represented in NotebookLM
   citation; canonical repo URL to be confirmed during impl
5. **claude-code-workflows (shinpr)** —
   `https://github.com/shinpr/claude-code-workflows`
6. **claude-workflow-template (nicholasmartin)** —
   `https://github.com/nicholasmartin/claude-workflow-template`

Each cell value to be filled during impl by reading the
competitor's README. **Cell values are facts about competitors
— each must be sourced (link to the competitor's README line),
not asserted.** This is a direct application of the
PRD-evidence-discipline rule we deployed earlier this session.

**`docs/WHY.md` — section schema**:

```
# Why this exists
## The cost of unstructured AI coding
  - METR 19% slowdown stat
  - Token Snowball / SWE-Effi expensive-failure stat
  - Lost in the Middle stat
## What spec-driven workflows recover
  - TDFlow 88.8% / 94.3% / 27.8% improvement
  - Decomposition / Chain-of-Thought evidence
## Where persistent memory fits
  - MemPalace 19.5M-tokens / 6 months figure
  - claude-mem 3-layer search 10× token savings
## Sources
  - full citation list with URLs
```

### Diagram generation pipeline (since no API)

```
1. Open Claude Design (web)
2. Paste prompt from
   assets/diagrams/architecture-overview.prompt.md
3. Iterate via conversation until satisfied
4. Export to standalone HTML
5. Open HTML in headless Chrome / take screenshot
   (manual, one-off; no Playwright dependency)
6. Save PNG to assets/diagrams/architecture-overview.png
7. Commit BOTH the PNG and the .prompt.md file
8. Reference in README via standard markdown image syntax
```

The `.prompt.md` file is the source-of-truth for regeneration.
Without it the PNG is opaque; with it any maintainer can
re-prompt Claude Design to update the diagram.

### Verification approach

| Requirement | Method | Scope | Expected Evidence |
|---|---|---|---|
| FR-1: README structure refactor | `code-only` + `manual-run-user` | doc | first 100 lines contain TL;DR + install + comparison link; visual inspection |
| FR-2: Spec-driven category positioning | `code-only` | doc | `grep -c "spec-driven" README.md` ≥ 2 |
| FR-3: Comparison table | `code-only` + `manual-run-claude` | doc | grep finds 6+ rows; each row contains a link; each cell sourced via embedded link or footnote |
| FR-4: Architecture diagram | `manual-run-user` | doc | PNG exists at `assets/diagrams/architecture-overview.png`; `.prompt.md` exists; README references both |
| FR-5: Terminal screencast | — | — | **Out of scope** (user selected "skip in V1") |
| FR-6: Why-this-exists + WHY.md | `code-only` + `manual-run-claude` | doc | README section ≤ 200 words; `docs/WHY.md` exists; cites ≥ 2 sources with URLs |
| FR-7: Preserve technical reference | `auto-test` (grep diff) | doc | every old `## ` heading still findable somewhere in new README; no factual content silently deleted |
| NFR-1: Above-the-fold completeness | `manual-run-user` | doc | TL;DR + category + install + diff visible without scroll on 1080p |
| NFR-2: Maintenance cost | `code-only` | doc | every diagram has a paired `.prompt.md` |
| NFR-3: No video V1 | n/a | — | nothing to verify |
| NFR-4: Markdown-only | `code-only` | doc | no `<script>` tags in README |

## Trade-offs & Rejected Alternatives

1. **Headless Playwright render of Claude Design HTML →
   reproducible PNG** — rejected: adds a Playwright dev
   dependency for a one-off generation step. The committed
   `.prompt.md` + manual screenshot is good enough at this
   scale.

2. **Direct Claude Messages API → SVG/Mermaid** — rejected
   because user explicitly asked to *utilise Claude Design if
   possible*. We will use Claude Design (interactively) for the
   primary diagram. Mermaid stays in the toolkit as fallback if
   the Claude Design output is unusable for a given case.

3. **Single rendered SVG instead of PNG** — rejected: SVG from
   a screenshot tool tends to be raster-embedded anyway. PNG is
   honest about what it is.

4. **Splitting Reference into multiple `docs/*.md` files** —
   rejected (user pick). Keep all reference in README under one
   `## Reference` heading.

5. **VHS / asciinema screencast in V1** — rejected (user pick).
   Defer to V2.

6. **Restructuring as a website (mkdocs / Docusaurus)** — out
   of scope per PRD.

## Files to Create / Modify

**Create**:
- `assets/diagrams/architecture-overview.png` — primary
  architecture diagram
- `assets/diagrams/architecture-overview.prompt.md` — source
  prompt for the above
- `assets/diagrams/workflow-sequence.png` — optional second
  diagram showing the command flow PRD→tech-design→tasks→impl
  (decision deferred to impl: include only if it adds clarity
  beyond the overview diagram)
- `assets/diagrams/workflow-sequence.prompt.md` — companion if
  the above is created
- `docs/WHY.md` — full evidence dossier

**Modify**:
- `README.md` — full structural refactor as described

## Dependencies

**External**:
- Anthropic Claude Design (subscription access required for
  diagram generation; user-driven, not in CI)

**Internal**: None. Doc-only change.

**Test-time**: None. No test suite for documentation.

## Security Considerations

- Claude Design diagrams may bake in secrets if the prompt
  references env vars or paths. **Diagram prompts must not
  contain credentials, API keys, or private hostnames.** Audit
  before commit.
- No `<script>` tags in README (NFR-4) — defends against any
  rendered-HTML XSS surface on GitHub.
- Competitor links must be HTTPS and to official repos only —
  no shortened URLs, no tracker links.

## Performance Considerations

- README rendered size: PNG diagrams should be ≤ 200 KB each
  (compress with `pngquant` or similar before commit). Don't
  commit a 5 MB raw screenshot.
- Total `assets/` overhead: target ≤ 500 KB total for the
  diagrams.
- No GIFs in V1 (screencast deferred), so no large binary
  blobs beyond the PNGs.

## Rollback Plan

Single-file revert of `README.md` plus `git rm` on the new
`assets/` and `docs/WHY.md` files. The change is contained to
documentation; no behaviour change to ship/revert.

## Constraints Carried from PRD

- `README.md` stays at repo root, single file (NFR/structural)
- All current factual content preserved (FR-7)
- Markdown-only, no JS embeds (NFR-4)
- No produced video in V1 (out of scope)
- "Spec-driven Claude Code workflow" is the canonical category
  name (FR-2)

## PRD Deltas (small)

1. **PRD said README is "770+ lines"; actually 809 today** —
   note added in Current Architecture; no requirement change.
2. **PRD assumed Claude Design might have an API/MCP** —
   verified false. Diagram generation pipeline is now manual
   (user-driven Claude Design session → screenshot → commit).
   Source prompt committed alongside for regenerability.
3. **PRD allowed Claude Design with mermaid fallback for
   FR-4** — keep the fallback explicit: if a specific diagram
   doesn't render usably from Claude Design, fall back to a
   ```mermaid``` block in README for that diagram only.
4. **Screencast (FR-5) deferred to V2** — user selection.

---

## Next Steps

1. Review and approve this design.
2. Run `/dev:tasks` to break down into:
   - Asset prep tasks (Claude Design prompts, exports,
     screenshot, compress, commit)
   - README refactor tasks (TL;DR draft, comparison table fill,
     section moves, link audit)
   - `docs/WHY.md` draft tasks
   - Verification tasks (line-count, grep checks, link audit,
     visual inspection)
