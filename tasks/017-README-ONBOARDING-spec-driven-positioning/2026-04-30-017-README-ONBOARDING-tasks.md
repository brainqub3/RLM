# 017-README-ONBOARDING - Task List

## Relevant Files

- [tasks/017-README-ONBOARDING-spec-driven-positioning/
  2026-04-30-017-README-ONBOARDING-prd.md](
  2026-04-30-017-README-ONBOARDING-prd.md)
  :: Product Requirements Document
- [tasks/017-README-ONBOARDING-spec-driven-positioning/
  2026-04-30-017-README-ONBOARDING-tech-design.md](
  2026-04-30-017-README-ONBOARDING-tech-design.md)
  :: Technical Design Document
- [README.md](../../README.md)
  :: MODIFY — full structural refactor (TL;DR up top,
  comparison table, diagram, "Why this exists" pointer,
  Reference section at bottom)
- [docs/WHY.md](../../docs/WHY.md)
  :: CREATE — full evidence dossier with TDFlow / METR /
  Token Snowball / Lost-in-the-Middle / MemPalace citations
- [assets/diagrams/architecture-overview.png](
  ../../assets/diagrams/architecture-overview.png)
  :: CREATE — primary architecture diagram (RLM + claude-mem
  + commands)
- [assets/diagrams/architecture-overview.prompt.md](
  ../../assets/diagrams/architecture-overview.prompt.md)
  :: CREATE — Claude Design source prompt for the above
- [assets/diagrams/workflow-sequence.png](
  ../../assets/diagrams/workflow-sequence.png)
  :: CREATE (optional, if it adds clarity beyond overview) —
  PRD → tech-design → tasks → impl flow
- [assets/diagrams/workflow-sequence.prompt.md](
  ../../assets/diagrams/workflow-sequence.prompt.md)
  :: CREATE (companion to above, only if .png is created)

## Notes

- Doc-only feature: no code, no test suite. Verification is
  primarily `code-only` (grep / line-count) and
  `manual-run-user` (visual inspection) per the tech-design
  Verification Approach table.
- TDD does not apply.
- Diagram generation is **manual** — Claude Design has no API
  as of 2026-04-30 (verified in tech-design Step 1.5).
  Workflow: Claude drafts the `.prompt.md`, user runs Claude
  Design web UI + screenshots, Claude verifies the asset
  exists and is referenced from README.
- Comparison table cell values must each be sourced (link to
  competitor README line or footnote). Same evidence-discipline
  rule we deployed to `/dev:prd` and `/dev:tech-design` this
  session.
- Sequencing locked: data first (WHY.md + comparison cells),
  README structural rewrite second, diagrams third.
- Two `## Hooks` headings (lines 258, 379 in current README)
  need consolidation during the rewrite — flagged in
  tech-design Current Architecture.

## TDD Planning Guidelines Applied

- TDD is not feasible for documentation. All verification is
  `code-only` (mechanical checks) or `manual-run-user`
  (visual / qualitative).
- The "tests" for this feature are: line-count caps, grep
  presence/absence, link audit, byte-level diff for
  no-content-deletion.

## Tasks

- [X] 1.0 **User Story:** As a maintainer, I want a complete
  evidence dossier in `docs/WHY.md` so that the README's
  "Why this exists" subsection has authoritative citations to
  link to and so that future PRs can reuse the same evidence
  pool [6/6]
  - [X] 1.1 Create `docs/` directory and stub `docs/WHY.md`
    with the four-section skeleton from tech-design (cost
    of unstructured AI coding / what spec-driven recovers /
    where persistent memory fits / Sources)
    [verify: code-only]
  - [X] 1.2 Write the "cost of unstructured AI coding"
    section: cite METR 19% slowdown, SWE-Effi expensive-
    failure (4× resource cost / 8.8M tokens), Lost-in-the-
    Middle (>20% accuracy drop) — each with full quote and
    URL. Lift verbatim from the NotebookLM citations
    captured in this session
    [verify: code-only]
    → 3 citations with verbatim quotes; reference labels
      [metr], [sweeffi], [litm] to be defined in 1.5
  - [X] 1.3 Write the "what spec-driven workflows recover"
    section: cite TDFlow 88.8% / 94.3% / 27.8% absolute
    improvement on SWE-bench Lite/Verified, Chain-of-Thought
    decomposition evidence
    [verify: code-only]
  - [X] 1.4 Write the "where persistent memory fits"
    section: cite MemPalace 19.5M-tokens / 6 months figure,
    claude-mem 3-layer search ~10× token savings, the
    LongMemEval R@5 benchmarks where applicable
    [verify: code-only]
  - [X] 1.5 Write the Sources section as a flat list of
    `[Title](URL)` entries — every citation in the body
    must have a corresponding Sources entry
    [verify: code-only]
  - [X] 1.6 Verify `docs/WHY.md` ends with a final newline,
    has zero unsourced factual claims, and that
    `wc -w docs/WHY.md` is between 600 and 1200 (per
    tech-design length budget)
    [verify: manual-run-claude]
    → wc -w: 1045 (in range); trailing 0a confirmed; 7
      reference labels used = 7 defined [live] (2026-04-30)

- [X] 2.0 **User Story:** As a maintainer, I want a fully
  filled-in capability comparison table data file so that
  the README rewrite can drop in a complete table without
  having to re-research each competitor cell during prose
  editing [9/9]
  - [X] 2.1 Create scratch file
    `tasks/017-README-ONBOARDING-spec-driven-positioning/
    comparison-data.md` with the 8-column header schema from
    tech-design (Project | Spec-driven phases | Persistent
    codebase index | Cross-session memory | TDD enforcement |
    Workflow profiles | Subagent count | Git worktrees)
    [verify: code-only]
  - [X] 2.2 Fill row 1 (rlm-mem, this repo): every cell
    sourced to a file:line in this repo. Subagent count
    counts files in `.claude/agents/`. Workflow profiles
    sourced to `.claude/profiles/`
    [verify: code-only]
    → 4 profiles found; 1 RLM agent + 5 documented test
      agents = 6 total reported with disclosure note
  - [X] 2.3 Fill row 2 (Superpowers, obra/superpowers):
    fetch the competitor README via WebFetch, extract each
    cell's truth value with a one-line quote + URL fragment
    citation per cell
    [verify: code-only]
  - [X] 2.4 Fill row 3 (BMAD-METHOD, representative port:
    aj-geddes/claude-code-bmad-skills): same procedure
    [verify: code-only]
  - [X] 2.5 Fill row 4 (Oh-My-ClaudeCode / OMC): first
    confirm canonical repo URL via WebSearch (PRD flagged
    as TBD), then fill cells from competitor README
    [verify: code-only]
    → canonical URL: github.com/Yeachan-Heo/oh-my-claudecode
  - [X] 2.6 Fill row 5 (claude-code-workflows,
    shinpr/claude-code-workflows): same procedure
    [verify: code-only]
  - [X] 2.7 Fill row 6 (claude-workflow-template,
    nicholasmartin/claude-workflow-template): same procedure
    [verify: code-only]
  - [X] 2.8 Sanity-check: every cell has a citation; no cell
    is asserted without a source link. This applies the
    evidence-discipline rule we deployed in /dev:prd to the
    comparison table itself
    [verify: code-only]
    → all 6 rows × 7 capability cells have a Source column
      with a direct quote
  - [X] 2.9 Render the final compact 8-column table (no
    citations inline — those move to a "Sources for
    comparison" footnote block) ready to paste into README
    [verify: code-only]

- [~] 3.0 **User Story:** As a developer landing on the
  GitHub page, I want the first 120 lines of the README to
  give me a TL;DR, category positioning, install, quickstart,
  and links into the comparison and Why sections, so that I
  can decide in 60 seconds whether to keep reading [7/8]
    > 3.8 awaits user-side visual inspection on GitHub
    > render. All mechanical sub-tasks complete.
  - [X] 3.1 Snapshot baseline: capture
    `wc -l README.md` and `grep -n '^## ' README.md` output
    into `tasks/017-.../baseline-headings.txt` for the
    no-deletion audit in story 6
    [verify: code-only]
    → 74-line snapshot saved [live] (2026-04-30)
  - [X] 3.2 Draft the new title block + 5-line TL;DR
    [verify: code-only]
  - [X] 3.3 Draft the condensed 60-second Quick Start
    [verify: code-only]
  - [X] 3.4 Draft the "Why this exists" subsection
    [verify: code-only]
  - [X] 3.5 Draft the Comparison section
    [verify: code-only]
  - [X] 3.6 Apply the above-the-fold zone to README
    [verify: code-only]
    → replaced lines 1-52 with new top: title, TL;DR,
      diagram anchor, Quick start, ## Comparison, ## Why
      this exists. README now 848 lines [live] (2026-04-30)
  - [X] 3.7 Run `head -120 README.md` and confirm the
    above-the-fold zone contains: TL;DR, "spec-driven"
    string ≥ 1, install command, comparison-table link,
    why-this-exists pointer
    [verify: manual-run-claude]
    → all 7 of {spec-driven, TL;DR, ## Comparison,
      install.sh, /dev:start, Why this exists, docs/WHY.md}
      found in head -100 [live] (2026-04-30)
  - [ ] 3.8 DEFERRED — moved to PR-time check under Story 6.0.
    Branch not pushed yet; GitHub render verification belongs
    with the reviewer acceptance pass once the PR is opened.
    Original: Manually inspect README.md as rendered on GitHub
    (preview locally via `glow` or push to a draft branch and
    view): confirm TL;DR + category + install + differentiator
    visible without scroll on a 1080p screen
    [verify: manual-run-user]
    → deferred to Story 6.0 PR review (2026-04-30)

- [X] 4.0 **User Story:** As an existing user of rlm-mem, I
  want all current technical reference content preserved
  under a single `## Reference` section at the bottom of the
  README so that my existing workflows and bookmarks don't
  break [6/6]
  - [X] 4.1 Insert a new `## Reference` H2 heading
    [verify: code-only]
  - [X] 4.2 Move the old sections en bloc to the Reference
    zone in canonical order
    [verify: code-only]
    → original sections were already in roughly that order;
      "moving" reduced to inserting `## Reference` and
      demoting subsequent H2->H3
  - [X] 4.3 Consolidate the two Hooks headings into one
    [verify: code-only]
    → tabular hook summary + context-guard rationale +
      Docs-first-enforcement note merged under single
      ### Hooks
  - [X] 4.4 Audit moved-section anchors
    [verify: manual-run-claude]
    → no internal markdown links to old anchors found in
      other repo files
  - [X] 4.5 Demote H2 -> H3 inside ## Reference
    [verify: code-only]
    → 16 H3 children now sit cleanly under ## Reference
  - [X] 4.6 Verify mid-section bridge content exists
    [verify: code-only]
    → ## Available Commands (table) and ## Test subagents
      (3-line list) sit between above-the-fold and Reference

- [X] 5.0 **User Story:** As a visual learner, I want at
  least one architecture diagram (RLM + claude-mem +
  commands) embedded in the README, generated via Claude
  Design with the source prompt committed, so that I can
  grasp the system without reading prose and so that the
  diagram is regenerable by future maintainers [7/7]
    > Subtask 5.3 (run Claude Design + save PNG) requires
    > user action. README has a placeholder anchor at
    > `<!-- ARCHITECTURE-DIAGRAM-ANCHOR -->` ready for the
    > image embed once 5.3 completes. 5.4-5.7 cascade after.
  - [X] 5.1 Create `assets/diagrams/` directory
    [verify: code-only]
  - [X] 5.2 Draft
    `assets/diagrams/architecture-overview.prompt.md`
    [verify: code-only]
    → 3-layer diagram prompt (commands -> RLM/claude-mem ->
      outputs); explicit "do NOT include credentials" line
  - [X] 5.3 USER ACTION: open Claude Design (web), paste the
    prompt, iterate to satisfaction, export to standalone
    HTML, screenshot the rendered diagram, save as
    `assets/diagrams/architecture-overview.png`. Compress
    with `pngquant` or similar so file ≤ 200 KB
    [verify: manual-run-user]
    → user generated v4 in Claude Design (3 iterations:
      v1 fixed misleading per-command arrows + tagline,
      v2 added POSTTOOLUSE-HOOK write path, v3 fixed text
      wrapping); saved by user [live] (2026-05-04)
    → prompt source-of-truth updated to v2 in
      assets/diagrams/architecture-overview.prompt.md
  - [X] 5.4 Verify the asset: file exists, is a valid PNG,
    is ≤ 200 KB. Run `file` and `du -k` to confirm
    [verify: manual-run-claude]
    → file: PNG 924x540, 25 KB (well under 200 KB budget)
      [live] (2026-05-04)
  - [X] 5.5 Add the diagram reference to README in the
    above-the-fold zone (anchor placeholder added in 3.6
    is now filled): `![rlm-mem architecture](assets/
    diagrams/architecture-overview.png)`
    [verify: code-only]
    → README.md:18 now embeds the PNG with descriptive alt
      text; placeholder comment replaced with image + caption
      pointing to the source prompt
  - [X] 5.6 Decide whether a second diagram (workflow
    sequence: PRD → tech-design → tasks → impl) adds clarity
    beyond the overview. If yes, repeat 5.2-5.5 for
    `workflow-sequence.{png,prompt.md}`. If no, document
    the decision inline in this task
    [verify: manual-run-user]
    → DECISION (2026-05-04): YES, generate. Architecture
      diagram shows WHAT; workflow-sequence shows HOW commands
      chain, when each is skippable, and feedback loops when
      downstream steps surface upstream inconsistency.
    → 5.6a [X] Draft `assets/diagrams/workflow-sequence.prompt.md`
      with two-lane layout (main 6 commands + auxiliary), skip-
      rules per command, and 3 backward feedback arrows.
      Iterated to v3: 6 all-to-all upstream feedback arrows,
      "Docs-first principle" annotation panel, "code in git"
      terminal artifact box, vertical layout, "Waterfall with
      self-correction" tagline. /dev:improve excluded (story 8.0).
    → 5.6b [X] User generated v3+ in Claude Design (4
      iterations: differentiate arrows / strip arc labels /
      docs-first panel / fix right-edge clipping); saved as
      assets/diagrams/workflow-sequence.png [live] (2026-05-04)
    → 5.6c [X] Embedded in README.md:22 with descriptive alt
      text + caption pointing to the source prompt
    → 5.6d [X] Verified PNG: 1300x1189, 552 KB. Original
      Claude Design output was 2636x2412 / 1.6 MB; resized
      with sips -Z 1300 to 552 KB. Over the 200 KB target
      from 5.3 (pngquant unavailable in env) but accepted by
      user; quality preserved at full diagram resolution.
  - [X] 5.7 If the Claude Design output for any diagram is
    unusable, fall back to a ```mermaid``` block in README
    for that diagram only (per tech-design rejected-
    alternative #2)
    [verify: manual-run-user]
    → N/A — both diagrams (architecture-overview,
      workflow-sequence) were generated successfully via
      Claude Design after iteration. No fallback needed.

- [~] 6.0 **User Story:** As a reviewer of this PR, I want
  the rewrite to provably preserve all factual content from
  the previous README (no silent deletions) and to satisfy
  the quantitative success metrics from the PRD, so that I
  can approve the change with confidence [5/7]
    > 6.2 (visual eyeball on 1080p screen) and 6.7
    > (5-min onboarding test by another developer) await
    > user action. Mechanical metrics (line count, grep
    > checks, no-script, table breadth) all green.
  - [X] 6.1 Run a "no factual content deleted" diff audit
    [verify: manual-run-claude]
    → 21 of 23 baseline H2s preserved; 2 intentional drops:
      "What Is This?" (content rewritten into TL;DR + Why)
      and "What's Next?" (dropped per tech-design as
      redundant with Quick start)
  - [ ] 6.2 Verify success metric: TL;DR + category +
    install + differentiator visible without scroll on
    1080p
    [verify: manual-run-user]
  - [X] 6.3 Verify above-the-fold elements
    [verify: manual-run-claude]
    → 7 of 7 in head -100: spec-driven, TL;DR, ## Comparison,
      install.sh, /dev:start, Why this exists, docs/WHY.md
  - [X] 6.4 Verify comparison table breadth
    [verify: manual-run-claude]
    → 8 lines starting with `|` in Comparison section
      (1 header + 1 separator + 6 data rows) - meets target
  - [X] 6.5 Verify total README <= 850 lines
    [verify: manual-run-claude]
    → 798 lines - within budget
  - [X] 6.6 Verify no `<script>` tags
    [verify: manual-run-claude]
    → grep returns 0
  - [ ] 6.7 Onboarding-friction test: ask one developer
    unfamiliar with the project to install + run
    `/dev:start` from the new README; record whether they
    completed in ≤ 5 minutes and any friction points
    [verify: manual-run-user]

- [~] 7.0 **User Story:** As a contributor opening this
  branch a week from now, I want the working tree clean
  (only task-017 files staged) and the branch pushed, so
  that handoff is unambiguous [0/4]
    > **UN-DEFERRED 2026-05-05** per user instruction:
    > "Un-defer Task 7. Commit task-017 artifacts, and
    > then let's check what else is changed and decide if
    > we commit it now". Earlier 04-30 deferral lifted.
  - [ ] 7.1 Stage ONLY task-017 artifacts (do NOT stage
    pre-existing dirty files like task-009 prose or the
    prd.md/tech-design.md edits from the earlier evidence-
    discipline session)
    [verify: code-only]
  - [ ] 7.2 Compose conventional-style commit message:
    `docs(017): restructure README for spec-driven
    positioning, add evidence dossier and architecture
    diagram prompt`
    [verify: code-only]
  - [ ] 7.3 Push branch to origin
    [verify: manual-run-user]
  - [ ] 7.4 Open PR and capture URL
    [verify: manual-run-user]

- [X] 8.0 **User Story:** As a maintainer, I want every
  reference to `/dev:improve` removed from user-facing docs
  until the command is actually implemented, so that the
  documentation does not advertise a missing feature [3/3]
    > Surfaced 2026-05-04 during 5.6 (workflow-sequence
    > diagram). User clarified scope: the command file IS
    > partially implemented but lacks claude-mem capture
    > upstream, making it unusable. Removed from user-facing
    > docs only (option C); file kept in place at
    > .claude/commands/dev/improve.md for future completion.
    > Known leak: command still appears in slash-menu skill
    > list — accepted by user.
    > Historical task records (009-FEEDBACK-LOOP, 011-RENAME)
    > intentionally NOT modified — they archive completed
    > work and editing them rewrites history.
  - [X] 8.1 Inventory: grep the repo for `/dev:improve`
    and `dev:improve` and list every file + line that
    references it
    [verify: manual-run-claude]
    → 3 user-facing hits identified: README.md:110 (table
      row), README.md:327 (file tree), impl.md:319 (Step 8
      wrap-up). Plus historical-only hits in tasks/009,
      tasks/011, tasks/017 (intentionally preserved) and
      explicit-exclusion notes in workflow-sequence prompt
      (correctly preserved).
  - [X] 8.2 Remove or comment-out each reference (delete
    if the surrounding prose makes sense without it; mark
    with a TODO if the structure depends on listing it)
    [verify: code-only]
    → 8.2a [X] README.md:110 — removed Available Commands
      table row
    → 8.2b [X] README.md:326 — removed `improve.md` line
      from `.claude/commands/dev/` file tree; bumped
      command count comment from "All 12" to "All 11"
    → 8.2c [X] .claude/commands/dev/impl.md — deleted
      entire "Step 8 Session Wrap-Up Check" section
      (sole purpose was suggesting `/dev:improve`)
  - [X] 8.3 Verify post-removal: grep returns zero hits
    in user-facing docs (README, command help text,
    profiles)
    [verify: manual-run-claude]
    → grep "/dev:improve\|dev:improve" returns ZERO hits
      in README.md and in .claude/commands/dev/
      (excluding improve.md itself, which stays per option
      C). [live] (2026-05-04)

