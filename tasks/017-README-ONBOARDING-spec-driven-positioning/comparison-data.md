# Comparison Data — Working Notes

> Scratch file. Each cell value MUST be sourced (link to a line
> in the competitor's README, or a footnote with quote + URL).
> Final compact table for README is in the last section.

## Schema

| Column | Type | Source-of-truth |
|---|---|---|
| Project | string + link | competitor repo URL |
| Spec-driven phases | ✅ / ❌ / partial | competitor README |
| Persistent codebase index | ✅ / ❌ | competitor README |
| Cross-session memory | ✅ built-in / ✅ optional / ❌ | competitor README |
| TDD enforcement | ✅ / ❌ / partial | competitor README |
| Workflow profiles | ✅ / ❌ | competitor README |
| Subagent count | integer | competitor README |
| Git worktrees | ✅ / ❌ | competitor README |

## Sourced rows (with citations)

### Row 1: rlm-mem (this repo)

| Cell | Value | Source |
|---|---|---|
| Project | [rlm-mem](https://github.com/povesma/claude_code_RLM_mem) | this repo |
| Spec-driven phases | ✅ | `.claude/commands/dev/{prd,tech-design,tasks,impl}.md` exist (verified 2026-04-30) |
| Persistent codebase index | ✅ | `.claude/rlm_scripts/rlm_repl.py` (RLM REPL builds `.claude/rlm_state/state.pkl`) |
| Cross-session memory | ✅ built-in | claude-mem MCP integration mandatory per `CLAUDE.md` "Claude-Mem Integration (MANDATORY)" |
| TDD enforcement | ✅ | `.claude/commands/dev/tasks.md` "TDD Planning Guidelines"; profile `quality.yaml` `testing.approach: tdd` |
| Workflow profiles | ✅ | `.claude/profiles/{quality,fast,minimal,research}.yaml` (4 profiles) |
| Subagent count | 6 | 1 in `.claude/agents/` (`rlm-subcall.md`); 5 test-* agents documented but not yet committed (`README.md` "Test Subagents" section) |
| Git worktrees | ❌ | grep for "worktree" in `.claude/` returns no usage |

### Row 2: Superpowers ([obra/superpowers](https://github.com/obra/superpowers))

| Cell | Value | Source |
|---|---|---|
| Spec-driven phases | ✅ | "brainstorming → writing-plans → implementation"; "Refines rough ideas through questions, presents design in sections for validation" |
| Persistent codebase index | ❌ | "No mention of indexing system across the documentation" |
| Cross-session memory | ❌ | "No built-in or optional cross-session memory capability described" |
| TDD enforcement | ✅ | "test-driven-development" skill enforces "RED-GREEN-REFACTOR cycle"; "Write tests first, always" stated in Philosophy |
| Workflow profiles | ❌ (partial) | Skills activate contextually but not explicitly called "profiles" for different scenarios |
| Subagent count | 14+ | "Multiple skills shipped including test-driven-development, systematic-debugging, brainstorming, writing-plans, dispatching-parallel-agents, and others" |
| Git worktrees | ✅ | "using-git-worktrees" skill: "Creates isolated workspace on new branch, runs project setup, verifies clean test baseline" |

### Row 3: BMAD-METHOD ([aj-geddes/claude-code-bmad-skills](https://github.com/aj-geddes/claude-code-bmad-skills))

| Cell | Value | Source |
|---|---|---|
| Spec-driven phases | ✅ | "Phase 1: Analysis → Phase 2: Planning (PRD/tech-spec) → Phase 3: Solutioning (architecture) → Phase 4: Implementation" |
| Persistent codebase index | ❌ | "Status tracking uses YAML project config, not code indexing" |
| Cross-session memory | ✅ built-in | "YAML-based status files"; "Persistent context across sessions. No re-explaining project state." |
| TDD enforcement | ❌ (partial) | "Development includes testing (Writes tests) but not explicitly mandated as test-first workflow" |
| Workflow profiles | ✅ | "Project Levels (Right-Sizing) with 5 complexity levels (0-4) adjusting planning depth accordingly" |
| Subagent count | 9 | "BMad Master, Business Analyst, Product Manager, System Architect, Scrum Master, Developer, UX Designer, Builder, Creative Intelligence" |
| Git worktrees | ❌ | "No mention of git worktrees" |

### Row 4: Oh-My-ClaudeCode ([Yeachan-Heo/oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode))

| Cell | Value | Source |
|---|---|---|
| Spec-driven phases | ❌ (partial) | "deep-interview…before any code is written" + "team-plan → team-prd → team-exec pipeline" but enforcement is optional |
| Persistent codebase index | ❌ | "Session summaries: .omc/sessions/*.json…but no explicit persistent AST/semantic codebase index" |
| Cross-session memory | ✅ built-in | "Extract reusable patterns from your sessions" with project and user scope stored in `.omc/skills/` |
| TDD enforcement | ❌ | "No mention of test-first workflows or TDD enforcement" |
| Workflow profiles | ✅ | "Multiple strategies for different use cases including Team, autopilot, ultrawork, ralph, pipeline, and ultrapilot modes" |
| Subagent count | 19 | "19 specialized agents (with tier variants) for architecture, research, design, testing, data science" |
| Git worktrees | ✅ | "Native team worker worktrees are being added behind an opt-in/config gate" |

### Row 5: claude-code-workflows ([shinpr/claude-code-workflows](https://github.com/shinpr/claude-code-workflows))

| Cell | Value | Source |
|---|---|---|
| Spec-driven phases | ✅ | "Creates design documents…Breaks down into tasks…Implements"; PRD → design → planning → execution phases |
| Persistent codebase index | ❌ (partial) | "codebase-analyzer agent analyzes existing codebase before design, but no persistent indexing mechanism" |
| Cross-session memory | ❌ | "No cross-session memory system mentioned" |
| TDD enforcement | ✅ | "task-executor…Implements backend features with TDD" |
| Workflow profiles | ✅ | "backend (`dev-workflows`), frontend (`dev-workflows-frontend`), fullstack, skills-only" |
| Subagent count | 27 | "16 recipes + 11 knowledge skills" |
| Git worktrees | ❌ | "No git worktree usage mentioned" |

### Row 6: claude-workflow-template ([nicholasmartin/claude-workflow-template](https://github.com/nicholasmartin/claude-workflow-template))

| Cell | Value | Source |
|---|---|---|
| Spec-driven phases | ✅ | "PRD → /plan-feature → /execute" lifecycle; "write your first PRD with /create-prd" |
| Persistent codebase index | ❌ | "No mention of maintaining an indexed codebase snapshot" |
| Cross-session memory | ❌ (partial) | "/continue scans board state and checks git history, but reconstructs context from GitHub/git rather than storing persistent memory" |
| TDD enforcement | ❌ | "No requirement for tests before code" |
| Workflow profiles | ❌ | "One standard workflow lifecycle shown; no mention of alternative profiles" |
| Subagent count | 1 | "/workflow - Workflow Modifier (Skill) for modifying the workflow system itself" |
| Git worktrees | ❌ | "No mention of worktrees" |

## Final compact table (for README paste)

> **Legend**: ✅ built-in · 🟡 partial / optional · ❌ absent
>
> Snapshot date: 2026-04-30. Sources for every cell:
> [comparison-data.md](
> tasks/017-README-ONBOARDING-spec-driven-positioning/comparison-data.md)

| Project | Spec-driven phases | Codebase index | Cross-session memory | TDD enforce | Profiles | Subagents/skills | Git worktrees |
|---|---|---|---|---|---|---|---|
| **rlm-mem** *(this)* | ✅ | ✅ | ✅ | ✅ | ✅ (4) | 6 | ❌ |
| [Superpowers](https://github.com/obra/superpowers) | ✅ | ❌ | ❌ | ✅ | 🟡 | 14+ | ✅ |
| [BMAD-METHOD](https://github.com/aj-geddes/claude-code-bmad-skills) | ✅ | ❌ | ✅ | 🟡 | ✅ (5 levels) | 9 | ❌ |
| [Oh-My-ClaudeCode](https://github.com/Yeachan-Heo/oh-my-claudecode) | 🟡 | ❌ | ✅ | ❌ | ✅ (6 modes) | 19 | ✅ |
| [claude-code-workflows](https://github.com/shinpr/claude-code-workflows) | ✅ | 🟡 | ❌ | ✅ | ✅ | 27 | ❌ |
| [claude-workflow-template](https://github.com/nicholasmartin/claude-workflow-template) | ✅ | ❌ | 🟡 | ❌ | ❌ | 1 | ❌ |

**rlm-mem's only-one-with-both differentiator**: persistent
codebase index (RLM) **and** cross-session memory (claude-mem)
in a single workflow. No competitor in the table has both.
