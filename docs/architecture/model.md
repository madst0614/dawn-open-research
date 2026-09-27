# DOR research grammar v1

Git stores one YAML file per persistent object. `program.yaml` defines the namespace and review convention; strict Pydantic models define canonical shapes; generated JSON Schemas are projections. The catalog validator checks identity, references, scholarly Relation endpoints, Result grounding, Claim maturity, Method-specific execution compatibility, and fail-closed infrastructure rules. No database or generated view is authoritative.

## Four separate layers

### Research activity

**Study** is one bounded unit of research activity. It organizes any relevant Questions, Claims, Methods, Results, and Artifacts around a goal, motivation, completion criteria, limitations, and blockers. It is not itself a knowledge assertion and need not begin with a Question or Claim.

### Epistemic core

- **Question** is a structured uncertainty that research can meaningfully investigate. Its inquiry, rationale, scope, and status define what is being sought and what progress means.
- **Claim** is a reviewable proposition, interpretation, or definition. `claim_type` and epistemic `status` are independent.
- **Method** is a reusable way of investigating, deriving, testing, analyzing, or constructing knowledge. It is not one execution.
- **Result** is an outcome that actually occurred or was derived. It has scope, limitations, authors, and one or more valid grounding IDs.
- **Relation** is a reviewable scholarly assertion about how two research objects bear on one another. It carries an asserter, time, rationale, status, and review metadata.

### Grounding and research products

- **Source** is an external provenance anchor such as a paper, book, dataset, repository, documentation, benchmark publication, or historical record. The Source record does not turn its contents into DOR Claims.
- **Artifact** is a first-class research product or identifiable input: a dataset, model, checkpoint, proof object, implementation, kernel, engineered system, benchmark suite, or corpus. It is not confined to execution output.
- **Run** is one historical execution of one Method in one Study. It freezes implementation, environment, profile, Artifact, configuration, command, time, output, and failure or invalidation provenance.

A Result's `grounding_ids` may resolve to Runs, Sources, or Artifacts. Grounding is explicit plumbing, not a scholarly Relation.

### Execution infrastructure

`RepositoryRef`, `InfrastructureProvider`, `Environment`, `ResourceProfile`, and related frozen runtime metadata describe how computational work can run. They do not belong to the epistemic graph merely because research uses them.

## Graph, not pipeline

DOR does not require `Question → Claim → Method → Result`. Research histories may include:

- `Question → Claim → Method → Result`;
- `Method → Result → Question`;
- `Result → Question → Claim`;
- `Source → Question`;
- `Artifact → Question`; or
- `Claim → Question`.

Question resolution is a reviewed epistemic judgment. It does not follow automatically from one supported Claim.

## Evidential role

Evidence is not a canonical object. An accepted evidential Relation makes its source play an evidential role for a Claim:

- `Result --supports/weakens/contradicts--> Claim`;
- `Source --supports/weakens/contradicts--> Claim`; or
- `Claim --supports/weakens/contradicts--> Claim`.

A Result has no automatic bearing on a Claim. A `supported` or `robust` Claim requires an accepted `supports` Relation from one of those allowed scholarly sources. This rule does not auto-promote Claims.

## Minimal scholarly Relation vocabulary

Semantic Relations use closed endpoint rules:

| Family | Relation and valid endpoints |
|---|---|
| Question/answer | Claim or Result `answers` Question |
| Question generation | Claim or Result `raises` Question; Source `motivates` Question; Method or Artifact `enables` Question; Question `refines` Question |
| Inquiry | Method `investigates` Question; Method `tests` Claim |
| Evidential/argumentative | Result, Source, or Claim `supports`, `weakens`, or `contradicts` Claim |
| Knowledge development | Claim `refines`, `generalizes`, `specializes`, or `depends_on` Claim |

Intellectual or historical provenance is a separate Relation class with `derived_from`, `informed_by`, `inspired_by`, and `independently_convergent_with`. It is never inferred from similarity, chronology, shared Packet authorship, or model synthesis.

Relation is not execution plumbing. Study membership, Run provider use, environment selection, Artifact input/output, and Result grounding use explicit fields.

## Study semantics and execution plans

A Study's semantic side is:

```text
id, title, lifecycle
goal, motivation
question_ids, claim_ids, method_ids, result_ids, artifact_ids
completion_criteria, known_limitations, blockers
```

Its execution side is structurally separate:

```yaml
execution:
  plans:
    - method_id: <METHOD_ID>
      entrypoint: <adapter or null>
      requires:
        capabilities: []
        artifacts: []
      profile_ids: []
      expected_outputs: []
      blockers: []
      declared_readiness: draft | local | public | blocked | null
```

Each plan names a Method already listed by the Study. A Study may have zero plans, one plan, or several plans. The resolver targets `Study + Method + Profile`; Method omission is allowed only when exactly one plan has an executable entrypoint. Ambiguity fails closed.

## Run and resolver boundary

The resolver remains the single authority for computational readiness. For the selected Method plan it checks capabilities, deterministic provider selection, provider verification claims, environment/profile compatibility, lockfile digest, required Artifacts, local/public availability, and declared blockers.

A Run references the Study and selected Method, and validation confirms that the matching execution plan exists. It freezes provider interface and repository revision, environment lock digest, resource profile, input Artifact digests, configuration digest, command, executor, timestamps, outputs, and terminal history. A terminal Run is never overwritten. A Run never creates a Result automatically.

The current runner supports only `dawn_srw.zero_shot_eval_jax@1`. The architecture permits several Method plans without turning the runner into a generic plugin system.

## Read-only projections

`dawn view` and `dawn export` validate first, derive bounded state, and never mutate canonical files. Compact Study view answers what, why, which research objects and products matter, what is blocked, and what may execute. Research view follows explicit Study references, one-hop scholarly Relations, Result grounding, and related Runs. Execution view obtains each readiness decision from the resolver.

Exports include Git identity, deterministic ordering, and redaction of private locators and local paths. They never read or include `.dor/`.
