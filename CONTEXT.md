# Agent Eval Lab Context

## Project Purpose

Agent Eval Lab is a local evaluation harness for coding agents. It runs realistic
software engineering tasks against pinned repository commits, captures the trial
trace and outcome, applies graders, and summarizes reliability across repeated
trials.

The project is evaluation infrastructure, not a general coding assistant or IDE.

## Intended Readers

- **Technical evaluators and model-quality engineers**: use the lab to understand
  where a coding-agent harness is reliable, brittle, or worth improving next.
- **Solo developers choosing an AI coding tool**: use the lab's reports to see
  which agent harness fits their project style and risk tolerance.

## Domain Vocabulary

- **UL**: shorthand for Ubiquitous Language, the canonical project vocabulary
  in this file. Public docs, issues, reports, and code should prefer UL terms
  when a concept has one.
- **Task**: a single eval case with repository, commit, prompt, environment, and
  success criteria.
- **Task bundle**: the canonical on-disk unit for a task: a directory containing
  `task.yaml`, generated `task-card.md`, and any reference artifacts.
- **Task card**: generated Markdown summary of a task bundle for humans and AI
  assistants. It is committed next to `task.yaml` but regenerated from task
  metadata rather than hand-edited.
- **Task-card drift**: mismatch between `task.yaml` and generated task cards.
  The repo-local pre-commit hook should catch drift before commits.
- **Task candidate issue**: a GitHub Issue that records a possible future task
  or task-curation slice. Use issue labels for workflow state: `needs-triage`
  for candidates needing curator judgment, `ready-for-human` for human-led
  curation/design work, and `ready-for-agent` only when the task is fully
  specified for an AFK agent. Do not maintain local task-candidate backlog
  documents.
- **Prompt ambiguity**: realistic user-level imprecision in a task prompt. It is
  acceptable only when the task's expected behavior, graders, reference solution,
  and human-review rubric remain unambiguous.
- **Non-interactive task**: a task intended to be attempted from a fixed prompt
  without a clarification loop. The first Solo Dev Starter Suite uses
  non-interactive tasks.
- **Interactive task**: a future task type where the agent harness may ask
  follow-up questions, and the quality of those questions can be graded.
- **Trial**: one attempt at a task by an agent harness. Prefer "trial" in new
  docs and result metadata. Use "run" only for CLI compatibility and historical
  artifact paths.
- **Evaluation suite**: a group of tasks designed to measure a capability or
  regression surface.
- **Harness**: a system that surrounds another system to run, constrain,
  observe, or improve it. Use qualified terms in public docs: **evaluation
  harness** for Agent Eval Lab and **agent harness** for the product or scaffold
  being evaluated.
- **Evaluation (eval) harness**: Agent Eval Lab itself. It prepares isolated
  environments, invokes agent harnesses through adapters, captures
  transcripts/traces and outcomes, runs graders, records human review metadata,
  and aggregates trial results.
- **Solo Dev Starter Suite**: the first serious evaluation suite for this
  project, focused on small realistic maintenance tasks a solo developer faces
  when starting or stabilizing an AI-assisted project. It should be a curated
  mixed-language suite rather than a single-language suite or random sample.
  Include one UI/visual task in the first version, graded conservatively with
  deterministic checks plus human visual review.
- **Agent harness**: the product or scaffold being evaluated, such as Codex CLI,
  Claude Code, Cursor Agent, or the manual adapter. Prefer this term over
  "agent", "agent tool", or "agent application" when naming comparison targets.
- **Tool**: an intentionally generic word. Avoid unqualified "tool" when a UL
  term is available. Use **evaluation harness** for Agent Eval Lab, **agent
  harness** for systems such as Codex CLI or Cursor Agent, and "tool call",
  "shell command", or "dependency" for lower-level actions inside a trial.
- **Agent harness configuration**: a comparable setup of an agent harness plus
  its explicit model, permissions, sandbox, project rules, and runtime options
  when known.
- **Run surface metadata**: vendor-neutral trial metadata that describes the
  runtime surface used by an agent harness, including execution surface,
  runtime version, model identity source, sandbox or permission mode, tool and
  memory policy, network policy, timeout or step budget, stop reason, and
  recorded human interventions. Unsupported facts should appear as `unknown`
  rather than being omitted.
- **Agent harness operability evidence**: side-by-side evidence about how an
  agent harness can be run, bounded, inspected, and audited from currently
  stored artifacts. It can use run surface metadata, agent harness
  configuration, verifier state, resource usage fields, transcripts, diffs,
  review overlays, and report/result links. It belongs in the same
  task-to-trial-to-result-to-evidence-to-report flow as capability evidence,
  while remaining distinct from task-performance metrics: operability evidence
  describes runtime controls and receipts, not whether the final patch solved
  the task. Use explicit `unknown` values for unsupported facts rather than
  inferring a complete control-plane model from partial artifacts.
- **Agent adapter**: the local Python integration that invokes an agent harness
  through Agent Eval Lab.
- **Underlying model**: the model selected by an agent harness. Do not collapse
  agent harness and model into one comparison dimension.
- **Grader**: scoring logic for a trial. Code-based graders are the default for
  coding tasks.
- **Assertion**: one check inside a grader, usually a command that must exit
  successfully.
- **Transcript / trace**: the record of an agent trial, including agent output,
  tool events, command output, and intermediate state when available.
- **Outcome**: the final workspace state after a trial, especially the patch,
  changed files, and grader results.
- **Grader outcome**: the deterministic pass/fail result produced by configured
  graders and assertions.
- **Human review outcome**: the human-approved quality judgment for a trial,
  recorded with review labels, notes, and evidence. It can disagree with or add
  nuance to the grader outcome.
- **Verified result**: a valid trial whose deterministic grader outcome passes.
  Verified means the configured graders accepted the final workspace state; it
  does not by itself mean a human reviewer accepted patch quality.
- **Accepted result**: a valid, grader-passing trial with a primary human review
  label that counts as accepted quality. The initial accepted label is
  `success_clean`; `success_messy` remains a verified but not accepted result.
- **Trial validity**: human-review metadata indicating whether a trial is fair to
  count in capability summaries. Valid trials count toward pass rate, pass@k,
  pass^k, and median outcome metrics.
- **Excluded trial**: a stored trial whose raw artifacts remain inspectable but
  whose result is omitted from fair capability metrics because the attempt was
  invalidated by setup, eval-harness, operator, task-definition, or dependency
  problems. Eval-harness failures use the exclusion reason
  `eval_harness_error`.
- **Outcome evidence**: structured facts used to support an outcome or human
  review, such as changed files, lines added/deleted, commands run, duration,
  token usage, cost, diff excerpts, transcript/trace excerpts, and grader output.
- **Capability evidence digest**: generated, AI-readable Markdown that
  summarizes a selected set of trial artifacts for later hand-authored agent
  capability reports. It reports aggregate metrics, fair/excluded trial counts,
  review labels, outcome evidence, resource usage, and artifact links without
  making final interpretive claims.
- **Edit size metrics**: structured evidence about patch size, especially files
  changed and lines added/deleted.
- **Resource usage metrics**: structured evidence about runtime cost, especially
  duration, input/output tokens, and estimated dollar cost when available.
- **Token-normalized outcome metrics**: aggregate resource usage metrics that
  divide reported token spend by verified or accepted results. Failed valid
  trials count in the token numerator so retries and wasted attempts remain
  visible. Use input-plus-output tokens as the primary portable bucket, and keep
  cached-input and reasoning-output token buckets separate because harnesses
  expose them differently.
- **resource_inefficient**: review/failure label for trials that use
  disproportionate runtime, token budget, cost, or command churn relative to the
  task complexity and outcome quality. Prefer as a secondary label unless
  resource waste is the dominant result. Initially judged by human reviewers
  using structured metrics; explicit thresholds should wait until enough trial
  history exists.
- **Reference solution**: proof that a real task is solvable and that its graders
  can accept a known-good fix.
- **Reference artifact**: a verified reference patch or commit for a task. It may
  be authored with AI assistance, but it must be reviewed and validated against
  the task graders before the task is publishable.
- **Reference verification**: positive-control execution of a task's reference
  artifact. It writes report/result artifacts shaped like agent trial outputs,
  marked with `trial_kind: reference_verification`.
- **Fixture repo**: a purpose-built repository used when a capability is hard to
  cover with a natural external project. Avoid relying on fixture repos for the
  main credibility of a suite.
- **Human review label**: a failure-taxonomy or success label attached after
  inspecting a trial.
- **Agent capability report**: the lab's primary summary artifact. It explains
  what an agent harness does well, poorly, and inconsistently across an
  evaluation suite in AI-readable Markdown, backed by trials, graders, outcomes,
  transcripts/traces, human review labels, and aggregate metrics.
- **Hand-authored interpretation**: report prose whose claims are selected and
  approved by a human reviewer, even when drafted with AI assistance.
- **Evidence-based claim**: a report statement scoped to the evaluated tasks,
  agent harness configuration, runtime conditions, graders, and observed trials.
  Avoid global capability claims that exceed the evidence.
- **Evidence-scoped recommendation**: practical guidance whose scope is limited
  to the evidence behind it. Use recommendations to help readers act, but do not
  imply broader certainty than the trials support.
- **Agent harness baseline**: repeated fair trials for one agent harness
  configuration across an evaluation suite, collected before making
  multi-harness comparison claims. A baseline is scoped to the suite, runtime
  conditions, model identity when known, permissions, graders, and human-review
  protocol.
- **Codex deep baseline**: the first agent capability report for the Solo Dev
  Starter Suite, focused on evaluating one Codex CLI agent harness configuration
  deeply before comparing multiple harnesses. Initial depth target: six task
  categories, one task per category, five independent trials per task using the
  same prompt and same agent harness configuration.
- **Claude Code baseline**: the next agent harness baseline for the Solo Dev
  Starter Suite, focused on evaluating one Claude Code agent harness
  configuration before comparing Claude Code against the existing Codex evidence
  set.
- **Solo developer**: an individual choosing an AI coding tool for a project
  based on task fit, reliability, risk tolerance, validation quality, runtime,
  and cost.

## Documentation Conventions

- Use `docs/adr/` for architectural decisions.
- Use `docs/design.md` for the current system overview, not as the primary home
  for new decisions.
- Use `docs/anthropic-eval-principles.md` for eval terminology and practice
  conventions.
- Use `docs/runtime-accountability.md` for open questions around model identity,
  token usage, billing context, and cost.
- Use `docs/agents/` for project-local instructions consumed by agent skills and
  referenced from `AGENTS.md`. Use `.agents/` for executable skill bundles and
  other agent runtime assets.
- Use `docs/retrospectives/` for historical notes about completed pilots,
  first attempts, and operating lessons.
- Use `reports/<report-slug>/` for published capability-report bundles. Keep the
  hand-authored `report.md`, generated `digest.md`, and supporting notes such as
  `model-attribution.md` together when they describe the same evidence set.

## Current Architectural Shape

- The CLI entrypoint is `python3 -m agentlab`.
- Task files are human-editable YAML or JSON and live under `tasks/`.
- Task bundles live under `tasks/<suite>/<task-id>/` and contain `task.yaml`,
  generated `task-card.md`, and reference artifacts.
- Task smoke tests verify the reference artifact, then run exactly one agent
  trial with one job before repeated or parallel trials are interpreted.
- Each trial gets an isolated cloned workspace under `runs/<trial-id>/workspace`.
- Agent adapters implement the `AgentAdapter` protocol in `agentlab.agents`.
- Trial artifacts include `report.md`, `result.json`, `diff.patch`, and an
  adapter-specific transcript or trace. New `result.json` artifacts include
  neutral run surface metadata as a sibling to adapter-specific
  `agent_harness_config`.
- Multi-trial summaries group by suite, eval type, task, agent harness, and
  model, then report fair-trial pass rate, pass@k, pass^k, accepted-result
  counts, token-normalized outcome metrics, and excluded-trial counts.
- Capability evidence digests provide AI-readable Markdown tables for capability
  reports; human-authored interpretation remains separate.
