# KB-First RLM — MCP Knowledge Base Integration Pattern

## What This Is

An alternative to the file-based REPL pattern for systems that have an MCP-connected knowledge base. Instead of externalizing context to a Python REPL with a pickle state file, context is stored in a persistent knowledge graph and queried via MCP tools.

This eliminates the REPL script entirely while preserving the core RLM primitive: the root model never loads full context — it queries surgically and delegates chunk-level synthesis to a sub-LM.

## Primitive Mapping

| RLM Paper | File-Based (brainqub3) | KB-First (MCP) |
|-----------|----------------------|----------------|
| External context variable | `rlm_repl.py` pickle state | MCP KB search tool |
| `find_relevant(content, query)` | `grep()` / `search()` helpers | `knowledge_search(query)` via MCP |
| `peek(start, end)` | `peek()` helper | `fetch(atom_id)` via MCP |
| `llm_query(chunk, query)` | `rlm-subcall` subagent | `rlm-subcall` subagent (same) |
| `map_reduce(content, ...)` | skill loop over chunk files | skill loop over chunk files (same) |
| Persistent REPL state | `state.pkl` | KB atoms (already persistent) |

## When to Use KB-First

- You have an MCP server exposing a knowledge base (Willow, any vector/graph DB via MCP)
- Context is already indexed — atoms, embeddings, or structured records
- You want zero extra infrastructure: no REPL script, no state files, no pickle

## When to Use File-Based REPL

- Context is raw and unindexed (logs, scraped pages, git output, arbitrary text)
- You need `grep()`, `chunk_indices()`, `write_chunks()` over unstructured text
- No MCP knowledge server is available

## Two-File Skill Structure

### `.claude/skills/rlm.md` — orchestrator

```markdown
---
name: rlm
description: KB-first RLM loop. Searches MCP knowledge base first, chunks file context only if KB gap remains.
---

## Arguments

| Arg | Required | Default | Purpose |
|-----|----------|---------|---------|
| `query=<question>` | yes | — | What to answer |
| `context=<path>` | no | — | Path to large context file (fallback) |
| `limit=<int>` | no | 10 | Max KB results |
| `chunk_chars=<int>` | no | 200000 | Characters per chunk |

## Procedure

1. Call `knowledge_search(query, limit)` via MCP — collect results
2. Assess: do results answer the query fully? If yes, synthesize and stop.
3. If gap and no context file → surface what's missing, request file
4. If context file → chunk into 200K char segments, write to `.claude/rlm_state/chunks/`
5. Per chunk → dispatch `rlm-subcall` (Haiku) → collect structured JSON
6. Synthesize KB results + chunk results → final answer. Quote only cited evidence.
7. Clean up `.claude/rlm_state/chunks/`

## Guards

- Never load raw chunk content into the main session context.
- Subagents cannot spawn further subagents (Claude Code depth limit).
- Verify `.claude/rlm_state/` is in `.gitignore`; add it if missing.
```

### `.claude/agents/rlm-subcall.md` — sub-LM

```markdown
---
name: rlm-subcall
description: Sub-LM for RLM chunk analysis. Reads a chunk file, extracts relevant content, returns compact JSON.
tools:
  - Read
model: haiku
---

Read the chunk file at the provided path. Return JSON only:

{
  "chunk_id": "chunk_NNNN",
  "relevant": [{"point": "...", "evidence": "<25 words>", "confidence": "high|medium|low"}],
  "missing": ["what this chunk could not answer"],
  "answer_if_complete": "full answer or null"
}

Rules: no speculation beyond the chunk, evidence max 25 words, no further subagents.
```

## Generalizing Beyond Willow

This pattern works with any MCP server that exposes two primitives:

- **search tool** — `search(query, limit)` → list of results with id + summary
- **fetch tool** — `fetch(id)` → full record content

Replace the MCP tool names in the skill body. The subagent and `.claude/rlm_state/` directory are unchanged.

Examples: Willow (`willow_knowledge_search` + `store_get`), any vector database with an MCP adapter, any graph KB with search+fetch endpoints.

## Reference Implementation

[rudi193-cmd/willow-1.9](https://github.com/rudi193-cmd/willow-1.9) — `.claude/skills/rlm.md` + `.claude/agents/rlm-subcall.md`

The Willow implementation uses `willow_knowledge_search` (search) and `store_get` (fetch) as the MCP primitives. KB atoms serve as the persistent external memory store — no REPL state file needed.
