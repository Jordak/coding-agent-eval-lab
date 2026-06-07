# ADR 0010: Use Base-Only Agent Workspaces

Status: Accepted

Date: 2026-06-04

## Context

Agent Eval Lab evaluates coding-agent outcomes against pinned repository commits. The evaluation harness currently prepares trial workspaces by cloning a task repository and checking out the pinned base commit. That gives each trial an isolated checkout, but the agent-facing `.git` directory may still contain upstream branches, tags, or later commits.

For issue-derived or public-regression tasks, that local git history can expose the fix the task is supposed to measure. DeepSWE highlighted this benchmark integrity risk while motivating original tasks and shallow/base-only workspace practice; see the [DeepSWE benchmark](https://deepswe.datacurve.ai/), [DeepSWE repository](https://github.com/datacurve-ai/deep-swe), and [DeepSWE methodology notes](https://deepswe.datacurve.ai/blog). The same risk applies here: Agent Eval Lab should measure whether an agent harness solves the requested task from the pinned base tree, not whether it can discover a hidden answer in local repository history.

The lab also relies on repeated trials and evidence-scoped reports. Workspace history policy is therefore part of the run surface: mixing full-history and base-only trials inside one baseline would make evidence harder to compare.

## Decision

Agent-facing trial and reference-verification workspaces use a base-only git history.

The evaluation harness may use a private temporary prep checkout with full repository history to fetch and materialize the requested base tree. That prep checkout is outside the trial artifact tree and is removed after workspace materialization.

The agent-facing workspace is created by materializing the pinned base tree from Git object data, initializing a fresh git repository from an empty template, staging the pinned tree directly into the synthetic index, and creating one synthetic base commit with Git plumbing. Materialization preserves tracked blob bytes as stored in the pinned commit; it does not use `git archive`, checkout smudge filters, LFS hydration, or local git hooks. The synthetic repository has no upstream remotes, branches, tags, or later commits. Synthetic commits use a fixed local identity such as `Agent Eval Lab <agentlab@example.com>` and a generic commit message. They do not embed the upstream commit SHA in the agent-facing git history.

Diff capture is performed explicitly against the synthetic base commit. Run surface metadata records the workspace history policy and synthetic base ref. Result metadata also records the original task repository and pinned task commit separately from the synthetic base ref.

Base-only workspaces are the only supported agent-facing workspace shape. Do not add task-level workspace history modes. If a task requires tags, richer git history, submodule initialization, Git LFS hydration, checkout filters, or other repository features beyond the materialized base tree, treat that as a task/environment design problem to resolve explicitly rather than falling back to a full-history workspace.

Reference verification uses the same base-only workspace policy as agent trials. Patch reference artifacts are applied to the synthetic base workspace. Commit reference artifacts may remain supported, but the evaluation harness must convert the commit difference into a patch in the private prep checkout before applying it to the base-only workspace.

Setup commands remain outside the synthetic base commit. The base commit represents only the pinned task repository tree. Untracked-file capture semantics are unchanged by this decision and are deferred to [issue #92](https://github.com/Jordak/coding-agent-eval-lab/issues/92).

## Alternatives Considered

- Keep full clone workspaces: rejected because local git history can leak later fixes and makes benchmark evidence less trustworthy.
- Add task-level `history_mode` options: rejected because multiple agent-facing workspace modes would create an avoidable comparability and maintenance burden.
- Delete or rewrite `.git` after cloning: rejected because it is less explicit than materializing a fresh repository from the pinned tree, and it is easier to leave stray remotes or history behind.
- Use shallow clone/fetch directly as the trial workspace: rejected for v1 because server support for fetching arbitrary pinned commits varies, while a private full clone followed by object-level materialization preserves current task compatibility.
- Use a durable shared clone cache: deferred. A temporary prep checkout keeps the first integrity slice simple and avoids cache invalidation, concurrency, and artifact-surface questions.
- Add special submodule or Git LFS behavior in v1: rejected. Preserve tracked `.gitmodules` and pointer files as normal files, and design richer task environments only when a publishable task requires them.

## Consequences

- Agents cannot inspect local `.git` history to find later upstream fixes.
- All new trials and reference verifications share one workspace history policy, improving baseline comparability.
- Reports and result JSON can distinguish the original task base commit from the synthetic workspace base ref used for diffing.
- Tasks whose setup or graders depend on tags, full history, submodules, or hydrated LFS objects may need task-specific redesign before they are publishable.
- The implementation must update workspace preparation, reference verification, run-surface metadata, reports, and focused tests while avoiding churn in existing checked-in reference result artifacts.
