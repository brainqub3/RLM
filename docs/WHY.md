# Why this exists

> Evidence dossier for rlm-mem. The README's "Why this exists"
> subsection cites the strongest 2-3 numbers; this file holds the
> full case with citations.

## The cost of unstructured AI coding

"Vibe coding" - describing a task to an LLM and accepting
generated code without manual review or structural constraints -
fails at scale in three measurable ways.

### 1. AI use does not automatically speed developers up

A controlled study on experienced open-source developers found
that AI tooling actually slowed task completion when used without
structure:

> Our early 2025 study found the use of AI causes tasks to take
> 19% longer, with a confidence interval between +2% and +39%.

- [METR study on AI tools and developer productivity][metr]

The follow-up in early 2026 saw selection bias (developers
unwilling to participate without AI dropped out), so the
original 19% slowdown stands as the strongest controlled signal
to date. Without scaffolding around the model, more AI does not
mean more output.

### 2. Failed agent attempts cost 4x more than successful ones

The SWE-Effi study analysed agent token economics and found
unstructured agents burn through compute on attempts that never
finish:

> An unresolved attempt consumes on average over 4 times more
> resources than a successful one. [...] a failed attempt consumes
> over 8.8 million tokens and 658 seconds.

- [SWE-Effi: Cost-Aware Evaluation of Agent Frameworks][sweeffi]

The mechanism is the **Token Snowball Effect**: every failed
tool call appends to the next prompt, the context bloats, the
model loses focus, and it loops without futility detection.

### 3. Long contexts degrade performance - "Lost in the Middle"

Stuffing a long monolithic prompt with PRD, tech-design, and
acceptance criteria does not work. Models exhibit a U-shaped
recall curve:

> GPT-3.5-Turbo's multi-document QA performance can drop by more
> than 20% - in the worst case, performance in 20- and 30-document
> settings is lower than performance without any input documents
> (i.e., closed-book performance; 56.1%).

- [Lost in the Middle: How Language Models Use Long Contexts][litm]

Critical instructions buried mid-prompt are reliably ignored.
The fix is not "make the prompt bigger"; the fix is structured
decomposition.


## What spec-driven workflows recover

The same models that fail at vibe coding succeed when given a
structured pipeline.

### TDFlow on SWE-bench

The TDFlow framework decouples patch proposing, debugging,
revision, and test generation into separately constrained
sub-agents. The numbers, on the standard SWE-bench benchmark:

> When provided human-written tests, TDFlow attains 88.8% pass
> rate on SWE-Bench Lite (an absolute improvement of 27.8% over
> the next best baseline) and 94.3% on SWE-Bench Verified.

- [TDFlow: Agentic Workflows for Test Driven Development][tdflow]

The same agent, on the same tasks, with no architectural
changes - just a forced decoupling into specs + tests + code +
review - moves from below-baseline to within touching distance
of human-level performance.

### Chain-of-thought is not optional for complex code

The pattern generalises. Decomposing the problem into stages
(intent -> architecture -> plan -> code) is not a stylistic
preference; it changes accuracy:

> Decomposing multi-step problems via natural language
> drastically improves the final coding accuracy. [...] Even with
> perfect initial context, an LLM cannot execute highly complex
> software development in one shot.

- [Architecting AI Software Engineering: Context, Cognition,
and Workflows][archai]

This is the core thesis behind PRD -> tech-design -> tasks -> impl.
It is not bureaucracy; it is the only configuration of the
problem that the model can actually solve.


## Where persistent memory fits

Spec-driven decomposition fixes the within-session problem.
Cross-session continuity is a separate problem with a
separate fix.

### The volume of lost context

> Six months of daily AI use = 19.5 million tokens. That's every
> decision, every debugging session, every architecture debate.
> Gone.

- [MemPalace project README][mempalace]

A default Claude Code session has no recall. Re-pasting prior
transcripts into new sessions is impossible (they don't fit any
context window) and LLM-summary-based memory APIs cost
~$507/year for a single developer.

### Token-efficient retrieval over history

claude-mem solves this with a layered retrieval pattern that
fetches identifiers first, then bodies only when needed:

> The 3-Layer Workflow: search - Get compact index with IDs
> (~50–100 tokens/result); timeline - Get chronological context
> around interesting results; get_observations - Fetch full
> details ONLY for filtered IDs (~500–1,000 tokens/result).
> ~10x token savings by filtering before fetching details.

- [claude-mem README][claudemem]

In rlm-mem, every session save and every observation captured
by the PostToolUse hook becomes searchable on the next
`/dev:start`. A correction made on Tuesday surfaces on Friday.
Architectural decisions made in February inform February's PRD
quality six months later.

### Why both RLM and claude-mem

RLM (the Recursive Language Model REPL) is the *spatial* axis:
it indexes the current state of a 1000+ file codebase. claude-mem
is the *temporal* axis: it remembers what was decided and why.
Either alone is incomplete. Together they let `/dev:prd`,
`/dev:tech-design`, and `/dev:impl` ground every claim in
concrete code references and historical context - which is
exactly the structured input the model needs to clear the
bars set in the previous section.


## Sources

[metr]: https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/
    "Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity"
[sweeffi]: https://arxiv.org/abs/2509.09853
    "SWE-Effi: Re-Evaluating Software AI Agent System Effectiveness Under Resource Constraints"
[litm]: https://arxiv.org/abs/2307.03172
    "Lost in the Middle: How Language Models Use Long Contexts"
[tdflow]: https://arxiv.org/abs/2510.23761
    "TDFlow: Agentic Workflows for Test Driven Development"
[archai]: #archai-note
    "Architecting AI Software Engineering: Context, Cognition, and Workflows (private NotebookLM source)"
[mempalace]: https://github.com/MemPalace/mempalace
    "MemPalace: open-source AI memory system"
[claudemem]: https://github.com/thedotmack/claude-mem
    "claude-mem: Claude Code plugin for persistent session memory"

- [METR - Measuring the Impact of Early-2025 AI on Experienced
  Open-Source Developer Productivity (METR blog, July 2025)][metr]
  | arXiv: <https://arxiv.org/abs/2507.09089>
- [SWE-Effi: Re-Evaluating Software AI Agent System
  Effectiveness Under Resource Constraints (Fan et al.,
  arXiv 2509.09853, 2025)][sweeffi]
- [Lost in the Middle: How Language Models Use Long Contexts
  (Liu et al., TACL 2024 / arXiv 2307.03172)][litm]
- [TDFlow: Agentic Workflows for Test Driven Development
  (Han et al., arXiv 2510.23761, 2025)][tdflow]
- Architecting AI Software Engineering: Context, Cognition, and
  Workflows - private synthesis sourced via NotebookLM during
  research; no public URL. <a id="archai-note"></a>
- [MemPalace - open-source AI memory system][mempalace]
- [claude-mem - Claude Code plugin for persistent session
  memory][claudemem]

