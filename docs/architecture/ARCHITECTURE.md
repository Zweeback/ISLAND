# ISLAND Architecture Contract

## Status

This document is a human-readable projection of the canonical model in
`workspace/system-model.yaml`. If this document conflicts with the model, the
model wins. Human prose is helpful; human prose is also how architecture slowly
turns into folklore.

## 1. System purpose

ISLAND is a governed consolidation workspace for multiple projects, tools,
agents, knowledge sources, and integrations. It is not itself one application
and it is not a generic production platform.

The architecture must make five things explicit:

1. what components exist;
2. which component owns each responsibility;
3. which actor may perform an action;
4. which approvals and invariants constrain that action;
5. what evidence proves the action completed correctly.

## 2. Source-of-truth hierarchy

1. `workspace/system-model.yaml` defines architecture and governance facts.
2. `workspace/projects.yaml` defines project inventory and lifecycle facts.
3. project-local `AGENTS.md` files define narrower operating constraints.
4. root `AGENTS.md` and `.github/copilot-instructions.md` are runtime-specific
   policy projections.
5. documentation explains the system but must not introduce new authority.

This removes the previous ambiguity where similar rules appeared in multiple
files without a declared precedence or derivation relationship.

## 3. Layer boundaries

### Governance

Owns policy, routing, schemas, approval gates, and validation. It must not own
product behavior or runtime business logic.

### Platform

Owns shared orchestration, connectors, health checks, and reusable operational
tools. Platform components expose capabilities to domain projects through
explicit interfaces rather than filesystem assumptions.

### Domains

Own product-specific behavior and user-facing applications. Domain projects may
consume platform capabilities but must not silently become shared infrastructure.

### Knowledge

Owns catalogs, manifests, retrieval sources, and durable task state. Knowledge
artifacts require schemas or documented record formats.

### Integration

Owns external feeds, gateways, and live interfaces. Network access is treated as
a security boundary, not merely another helper function.

### Archive

Contains immutable reference material. Automated actors have read-only access.

## 4. Agent execution model

Every material task is represented by an execution contract.

Required input:

- task identifier;
- target project resolved through `workspace/projects.yaml`;
- objective;
- allowed write scopes;
- acceptance criteria.

Required output:

- change summary;
- files changed;
- validation evidence;
- unresolved risks.

Valid lifecycle:

`proposed -> approved -> executing -> validating -> completed`

A task may enter `blocked` or `failed` from any active state. No agent may call a
task complete merely because files changed. Completion is a validation state,
not an emotional impression.

## 5. Deterministic routing

Routing decisions use five dimensions:

- target project;
- required capability;
- risk level;
- data sensitivity;
- external side effects.

High-risk work routes to the human owner. Repository maintenance routes to
Jules, schema validation to Codex, code generation to GitHub Copilot, and local
privileged execution to Antigravity. A future orchestrator may automate this
routing only by consuming the canonical model.

## 6. Security invariants

The following are architectural invariants, not recommendations:

- no tracked secret material;
- archive paths remain immutable;
- every project action resolves a catalog entry first;
- executable changes require automated validation;
- completion requires evidence;
- authentication, command execution, network fetching, secrets, workflow
  permissions, destructive operations, and paid deployments require explicit
  risk handling and, where declared, human approval.

## 7. Interfaces and ownership

Components own capabilities, not arbitrary folders. Folder paths are deployment
and repository projections of component boundaries.

A component may call another component only through a declared interface. New
cross-layer dependencies must document:

- provider component;
- consumer component;
- input and output contract;
- failure behavior;
- security classification;
- test strategy.

Direct imports across unrelated domain projects are prohibited unless promoted
to a shared platform component.

## 8. Change protocol

Architecture changes must update the canonical model first. A change is
architecture-significant when it adds or changes:

- a layer;
- a component or ownership boundary;
- an actor capability;
- a routing rule;
- an approval gate;
- an invariant;
- an execution state;
- a cross-component interface.

Such changes require:

1. schema-valid model changes;
2. an architecture decision record in `docs/architecture/decisions/`;
3. updated policy projections where runtime behavior changes;
4. CI validation.

## 9. Definition of architectural done

An architecture change is complete only when:

- the canonical model validates;
- referenced paths and actors resolve;
- identifiers are unique;
- component layers exist;
- policy projections do not contradict the model;
- validation evidence is attached to the pull request;
- unresolved risks are explicit.
