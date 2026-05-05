# workflow-sequence - Claude Design source prompt

This file is the source of truth for `workflow-sequence.png`.
To regenerate the diagram:

1. Open Claude Design (`https://claude.ai/design`)
2. Paste the prompt below
3. Iterate via conversation until the layout reads cleanly
4. Export to standalone HTML
5. Open the HTML, take a clean screenshot of the diagram area
6. Compress with `pngquant --quality=65-80` to keep file
   under ~200 KB
7. Save as `assets/diagrams/workflow-sequence.png`
8. Commit the new PNG together with any prompt edits made
   during iteration

## Prompt

```
Create a workflow-sequence diagram for the rlm-mem developer
tool, showing how its commands chain together and how feedback
loops back to earlier specs when inconsistencies are found.

OVERALL LAYOUT
==============
Three vertical columns, equal-or-near-equal heights, separated
by generous whitespace:

  COLUMN 1 (LEFT):    "FEEDBACK"
  COLUMN 2 (CENTER):  "MAIN FLOW"
  COLUMN 3 (RIGHT):   "AUXILIARY COMMANDS"

Each column has its caption rendered as a small-caps monospace
label at the top, neutral gray, with a thin horizontal rule
beneath.

The whole diagram is square-ish (~1:1 aspect ratio) when
exported. Target ~1300-1500 px wide for GitHub README use.

TITLE BLOCK (top-left, spanning above the FEEDBACK column)
==========================================================
Three-line stack, left-aligned:

  Line 1 (kicker, small caps, monospace, ~14px, neutral):
    "RLM-MEM · SPEC-DRIVEN WORKFLOW"

  Line 2 (title, serif, bold, ~32px, near-black):
    "Waterfall, with self-correction."

  Line 3 (subtitle, sans-serif or serif, regular, ~16px,
   muted gray):
    "Feedback flows back when reality contradicts the spec."

COLUMN 1 - FEEDBACK
===================
Top of column: a single highlighted panel called the
"Docs-first principle" panel. Below it: 6 stacked legend
cards.

Docs-first panel:
- Background: warm cream / beige tint (~#FBF5E8) so it stands
  apart from the white legend cards beneath.
- Tag chip at top: "SELF-CORRECTION" in small-caps, amber
  text on the cream background, ~11px.
- Heading: "Docs-first principle" (serif bold, ~22px)
- Body: short copy, total 20-25 words. Suggested:
    "When downstream contradicts the spec, edit the doc, not
     the code. /dev:impl pauses, then resumes when the doc
     is corrected."
- Body font: ~13-14px regular, neutral dark gray, line-height
  ~1.5 for readability.

Legend cards (6, stacked vertically below the Docs-first panel):
Each card represents one feedback arrow. Card structure:
- Thick colored left border (~6px) matching the arrow color
- Top of card: small pill/chip showing the TARGET command,
  color-matched to the border:
    "PRD"          (red border + red chip)
    "TECH-DESIGN"  (purple border + purple chip)
    "TASKS"        (teal border + teal chip)
- Below the chip: bold inline title in the format
  "<symptom> · <action>", e.g. "PRD gap or factual error ·
  Fix PRD". The "Fix X" half is colored to match the border.
- Below: 1-2 short sentences (~13px regular) describing the
  trigger.

The 6 cards in order, top to bottom:

  (1) PRD          - "PRD gap or factual error · Fix PRD"
       "Tech-design exposed a missing assumption. Patch the
        PRD before re-running design."

  (2) PRD          - "Missing requirement · Revise PRD"
       "A requirement only became visible while breaking
        work down. PRD must own it."

  (3) TECH-DESIGN  - "Design inconsistency · Fix tech-design"
       "Tasks broke down only because the design contradicted
        itself. Reconcile design first."

  (4) PRD          - "Requirement was wrong · Rewrite PRD"
       "Running code contradicted the PRD. Rewrite the spec -
        never let code become the source of truth."

  (5) TECH-DESIGN  - "Interface mismatch · Revise design"
       "Code revealed an API shape the design got wrong.
        Update the design."

  (6) TASKS        - "Scope drift in code · Update tasks"
       "Implementation discovered work the task list never
        named. Record it as tasks."

Color mapping: cards 1, 2, 4 use red (PRD-bound). Cards 3, 5
use purple (tech-design-bound). Card 6 uses teal
(tasks-bound). This way the viewer can scan by color and
group "all things that revise PRD" instantly.

COLUMN 2 - MAIN FLOW
====================
6 stacked step cards, top to bottom, with downward solid blue
arrows between them. Each card structure:
- Thin teal vertical bar on the left edge
- Top of card: small step badge "STEP 1" (teal, monospace)
- Command name (monospace, bold, ~22px)
- Verb-phrase (~15px, regular)
- Skip-rule below (~13px, italic, muted gray)

The 6 main-flow cards in order:

  STEP 1  /dev:init
           "Index repo, bootstrap memory."
           skip: "Initially - or major changes only."

  STEP 2  /dev:start
           "Load full session context."
           skip: "Every session; never skip."

  STEP 3  /dev:prd
           "Draft layered requirements."
           skip: "Skip for trivial fixes; reuse if PRD exists."

  STEP 4  /dev:tech-design
           "Map architecture and interfaces."
           skip: "Skip if change maps directly to tasks."

  STEP 5  /dev:tasks
           "Break work into TDD-ready subtasks."
           skip: "Skip for exploratory POCs."

  STEP 6  /dev:impl
           "Execute one subtask at a time, TDD."
           skip: "Do not skip; this is the execution step."

Step 6 (impl) has an "EXECUTE" badge as a small orange-tinted
pill anchored to the TOP-LEFT corner of the card (left of
or just below the "STEP 6" badge). Not top-right. Not inline
with the step number; a distinct chip in its own corner so
that "STEP 6" and "EXECUTE" read as two adjacent badges.

Step 6 also has a thicker outline (~2px navy) to visually
distinguish it as the active execution box.

After Step 6, a downward arrow leads to:

TERMINAL ARTIFACT BOX (below Step 6, in MAIN FLOW column):
- Styled as a stylized terminal/console window:
  dark near-black background, three traffic-light dots in
  the top-left, monospace text inside.
- Header bar: "OUTPUT - committed to git" (centered)
- A small green "ARTIFACT" pill chip
- Body shows a sample run, e.g.:
    $ /dev:impl - subtask 3/7
    ✓ tests/auth.spec.ts  (14 passed)
    ✓ src/auth/session.ts (implementation)
    $ /dev:git - commit & PR
    commit 8a4c... feat(auth)
- This box anchors the diagram: the workflow's terminal
  artifact is COMMITTED CODE, not a doc.

COLUMN 3 - AUXILIARY COMMANDS
=============================
4 stacked cards, lighter / more muted styling than main flow.
These commands are NOT part of the main flow - they are helper
commands a developer can invoke any time. Some have explicit
"naturally invoked after step X" relationships rendered as
thin dotted lines into the MAIN FLOW column; others are
entirely standalone (no dotted line at all).

Card style:
- No step badges (these are not numbered steps)
- Lighter or no left-border accent
- Command name (monospace, bold) + 1-line verb-phrase

Render EXACTLY these dotted-line connections - no more,
no less:

  /dev:health     NO dotted line at all. Standalone helper;
                  can be invoked any time, independent of
                  flow state. Render the card with no line
                  attached.

  /dev:check      TWO dotted lines, both running sideways
                  from this card's left edge into the right
                  edge of the corresponding main-flow card:
                    - one line ending at /dev:start (Step 2)
                    - one line ending at /dev:tasks (Step 5)
                  Indicates /dev:check is naturally invoked
                  after each of those two steps to audit
                  status.

  /dev:test-plan  ONE dotted line, running sideways from
                  this card's left edge into the right edge
                  of /dev:tech-design (Step 4).
                  Test plans are derived from the tech
                  design, so this helper sits next to that
                  step.

  /dev:git        ONE dotted line, running sideways from
                  this card's left edge into the right edge
                  of /dev:impl (Step 6). Used after
                  implementation to commit and open a PR.

Vertical placement of the auxiliary cards (top-to-bottom in
the right column): /dev:health, /dev:check, /dev:test-plan,
/dev:git. The cards are positioned near the main-flow step
they connect to (or, for /dev:health, near the top of the
column with no connection at all).

The dotted lines are subtle (gray, ~1px), have NO arrowheads,
and imply NO flow direction. They mark a positional /
relationship hint only ("this helper is naturally invoked
near this step"), not an execution edge.

The 4 auxiliary cards, in order:

  /dev:health     "Check workflow parts status."
                  Standalone, no dotted line.

  /dev:check      "Audit task list status."
                  Connected by dotted lines to /dev:start
                  and /dev:tasks.

  /dev:test-plan  "Derive tests from design."
                  Connected by a dotted line to
                  /dev:tech-design.

  /dev:git        "Commit & PR after impl."
                  Connected by a dotted line to /dev:impl.

DO NOT include /dev:improve. It is not implemented yet.

FEEDBACK ARROWS (the central visual element)
=============================================
6 curved dashed arrows flow from the COLUMN 1 legend cards
into the COLUMN 2 main-flow cards (left-to-right, with
some downward sweep). Each arrow:

- Originates near the right edge of its corresponding legend
  card (Column 1)
- Terminates with an arrowhead at the left edge of its
  TARGET main-flow card (Column 2):

    Arrow 1 (PRD,   from card 1) -> STEP 3 /dev:prd
    Arrow 2 (PRD,   from card 2) -> STEP 3 /dev:prd
    Arrow 3 (TECH,  from card 3) -> STEP 4 /dev:tech-design
    Arrow 4 (PRD,   from card 4) -> STEP 3 /dev:prd
    Arrow 5 (TECH,  from card 5) -> STEP 4 /dev:tech-design
    Arrow 6 (TASKS, from card 6) -> STEP 5 /dev:tasks

Visual rules for the feedback arrows:
- Stroke style: dashed
- Color matches the legend card's left border / chip
  (red / purple / teal). Use a third warm-orange or red for
  PRD-bound; muted purple for tech-design-bound; teal for
  tasks-bound.
- Stroke weight: ~1.5-2px. Long arrows (e.g. card 6 ->
  STEP 5) can be slightly thicker if needed for emphasis.
- Origin and target points are STAGGERED vertically so 6
  arcs don't bundle into shared points.
- Origin dots: each arrow starts with a small filled dot
  on the right edge of its legend card, in the arrow's
  color, so the start is visibly distinct from the curve.
- Arrowheads: simple filled triangle in the arrow's color.
- DO NOT label the arrows themselves. The legend cards
  carry all label content. Arrows are clean curves only.
- Arrow paths can cross each other - that is fine and
  expected. The differentiated colors keep them readable.

This combination (color-coded cards + matching colored arrows
+ no labels on the curves) is the central design principle.
It lets a viewer answer "what feedback paths exist?" by
scanning Column 1, and "where does this feedback go?" by
following an arrow's color to its target step.

TYPOGRAPHY
==========
- Title (line 2 of title block): serif, bold, ~32px
- Section captions (FEEDBACK / MAIN FLOW / AUXILIARY
  COMMANDS): small-caps, monospace, ~14px, neutral gray
- Step badges (STEP 1 etc.): monospace, ~12px, teal
- Command names (/dev:*): monospace, bold, ~20-22px
- Verb-phrases inside cards: regular, ~14-15px
- Skip-rules: italic, ~12-13px, muted gray
- Docs-first body, legend card body: regular, ~13-14px,
  line-height ~1.5
- Tag chips (SELF-CORRECTION, PRD, TECH-DESIGN, TASKS,
  EXECUTE): small-caps, ~10-11px, color-on-tinted-background
- Terminal box body: monospace, ~12-13px, light-on-dark

PALETTE
=======
- Backgrounds: white / very light gray for cards, cream
  (~#FBF5E8) for the Docs-first panel, near-black
  (~#1A1A1A) for the terminal artifact box
- Accents:
    teal     (~#0E8478) - main-flow step bars, badges,
                          tasks-bound feedback (card 6)
    red/coral (~#C24E3A) - PRD-bound feedback (cards 1, 2, 4)
    purple   (~#5B3F9A) - tech-design-bound feedback
                          (cards 3, 5)
    amber    (~#B27E1F) - SELF-CORRECTION tag, EXECUTE pill
    navy     (~#2A3654) - Step 6 thicker outline
- All other UI: neutral grays.

DO NOT include:
- /dev:improve (not implemented yet)
- Any logos or branded marks
- Marketing copy or value-prop text
- Credentials, API keys, hostnames, or paths
- Pricing or subscription info
```

## Iteration notes

- v1 (initial draft, 2026-05-04): created to complement
  architecture-overview.png. Architecture diagram shows WHAT
  the system is (commands + two engines + outputs); this one
  shows HOW commands chain in time, when each can be skipped,
  and how feedback loops back when a downstream step reveals
  upstream inconsistency. /dev:improve intentionally excluded
  because the command is not implemented yet (see story 8.0
  in the 017 task list for the broader cleanup).

- v2 (2026-05-04): user-requested revisions:
  1. Larger, more legible text - v1 body text was too small.
  2. Separated origin/destination points of feedback arrows -
     v1 bundled them at shared points.
  3. Expanded feedback to all-to-all upstream: every
     downstream command can revise EVERY upstream spec
     (6 arrows total, not 3).
  4. Added terminal artifact: "code in git" box after
     /dev:impl, since the workflow's output is committed
     code, not a doc.
  5. Switched preferred orientation to vertical for room.
  6. Tagline corrected: this IS waterfall (sequential gated
     phases), just with feedback. "Iterative, not waterfall"
     was rhetorical; "waterfall with self-correction" is
     accurate. Honest framing turns "waterfall" from a
     stigma into the actual feature being claimed.

- v3 (2026-05-04): user-requested revisions after v2 render:
  1. Differentiate the 6 feedback arrows by weight + dash
     pattern + color shade. v2 had them all the same orange
     dashed and they merged visually.
  2. Strip labels off the arcs. Move them into a numbered
     legend in a left-side annotation panel.
  3. Annotation panel heading: "Docs-first principle".
     Adds a short justification ("specs come before code,
     but specs are never finished; fix the spec first when
     downstream surfaces a gap") so the diagram explains
     WHY the feedback exists, not just that it does.

- v4 (2026-05-05): user re-designed the diagram in Claude
  Design directly, then provided a final PNG. This prompt
  was rewritten to be a faithful spec OF the v4 image, not a
  forward-looking brief. Concrete details captured from the
  rendered PNG:
  1. Three-column layout (FEEDBACK | MAIN FLOW | AUXILIARY),
     square aspect (~1:1), not the earlier two-lane scheme.
  2. Step badges read "STEP 1" through "STEP 6" - single
     digit, no leading zero.
  3. Docs-first panel body trimmed to ~20-25 words; the
     verbose justification from v3 was rejected as too
     marketing-flavored.
  4. EXECUTE pill is anchored to the TOP-LEFT corner of
     /dev:impl (left of or just below the STEP 6 badge),
     not top-right or inline.
  5. Auxiliary connections are precisely:
       /dev:health     standalone, no dotted line
       /dev:check      dotted lines to /dev:start AND
                       /dev:tasks
       /dev:test-plan  dotted line to /dev:tech-design
       /dev:git        dotted line to /dev:impl
     Earlier prompt had vague "paired with" language and
     was wrong about /dev:check (which has TWO connections,
     not one).
  6. Feedback arrow targets in v4: arrows 1, 2, 4 land at
     /dev:prd (Step 3); arrows 3, 5 land at /dev:tech-design
     (Step 4); arrow 6 lands at /dev:tasks (Step 5). No
     impl-bound feedback (impl is the source of feedback,
     never a target).
