# architecture-overview - Claude Design source prompt

This file is the source of truth for `architecture-overview.png`.
To regenerate the diagram:

1. Open Claude Design (`https://claude.ai/design`)
2. Paste the prompt below
3. Iterate via conversation until the layout reads cleanly
4. Export to standalone HTML
5. Open the HTML, take a clean screenshot of the diagram area
6. Compress with `pngquant --quality=65-80` to keep file
   under ~200 KB
7. Save as `assets/diagrams/architecture-overview.png`
8. Commit the new PNG together with any prompt edits made
   during iteration

## Prompt

```
Create a clean technical architecture diagram for a developer
tool called "rlm-mem" - a spec-driven Claude Code workflow.

Show three horizontal layers, top to bottom:

LAYER 1 - User-facing commands (top):
  Boxes labeled in this order:
    /dev:init -> /dev:start -> /dev:prd ->
    /dev:tech-design -> /dev:tasks -> /dev:impl
  Arrows between boxes are left-to-right showing the workflow.
  Caption above this layer: "Commands (Claude Code)"

LAYER 2 - Two parallel context engines (middle):
  Two large boxes side by side:
    Left box: "RLM (Recursive Language Model)"
      sub-bullets: "Indexes 1000+ files into a single state.pkl.
      Spatial axis: where is code?"
    Right box: "claude-mem (semantic memory)"
      sub-bullets: "SQLite + ChromaDB. Captures every session's
      decisions and corrections. Temporal axis: why did we
      decide this?"

LAYER 3 - Outputs (bottom):
  Three boxes labeled:
    "PRDs (sourced)" | "Tech designs (verified)" | "Tasks
    (TDD-ready)"
  These boxes feed back into LAYER 1's /dev:impl through a
  dotted upward arrow.

Connections between LAYER 1 and LAYER 2:
- Draw a SINGLE labeled bus from the whole commands row down
  to each engine box (not per-command arrows). All commands
  consult both engines.
- Bus label to RLM box: "all commands -> reads RLM index"
- Bus to claude-mem box has TWO labeled paths:
    - "all commands -> queries via MCP" (read path)
    - "Claude Code PostToolUse hook -> writes observations"
      (write path; this is automatic, not invoked by commands)

Footer / tagline (centered, small caps, neutral color):
  "layered specs -> verified context -> code"
  (do NOT use "spec -> memory -> code"; "spec" is too flat
  and "memory" is not a destination)

Style:
- Minimal. No gradients, no drop shadows.
- Monospace labels for command names (/dev:*).
- Two accent colors max - one for RLM (e.g. teal), one for
  claude-mem (e.g. amber). Everything else neutral.
- 16:9 aspect ratio, optimised for embedding in a GitHub
  README at ~800px wide.

Do NOT include:
- Any logos or branded marks
- Marketing copy or value-prop text
- Anyone's credentials, API keys, hostnames, or paths
- Pricing or subscription info
```

## Iteration notes

- v1 (initial): per-command colored arrows from /dev:prd and
  /dev:tasks were misleading (every command uses both engines);
  tagline "spec -> memory -> code" implied memory is between
  spec and code. Revised v2 uses a single bus per engine, splits
  claude-mem into hook-write + MCP-read paths, and changes the
  tagline to "layered specs -> verified context -> code".
