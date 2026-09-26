# Universal research model v1

Git stores one YAML file per persistent object. `program.yaml` provides the program namespace and review convention. `src/open_research/models.py` defines strict v1 shapes; JSON Schemas in `schemas/` are generated projections. `store.py` validates identity, fields, reference integrity, Connection types, conservative Claim maturity, and fail-closed infrastructure rules. The CLI reads the tree and derives views. No database is authoritative.

## Research concepts

The public model is Question, Study, Claim, Method, and Result.

- A Question is an unresolved knowledge target.
- A Study is a bounded unit of research with explicit Question, Claim, and Method references.
- A Claim is either a proposition or an interpretation; its type is independent of its epistemic status.
- A Method is a reusable protocol.
- A Result is an observed or derived outcome with at least one Run or Reference, explicit scope, and limitations.

The canonical representation is a graph. Study fields express simple membership directly. Internal Relation records hold scholarly Connections only when the connection itself carries meaning or review state. Source records provide external References.

A Result has no automatic effect on a Claim. Only an explicit `supports`, `weakens`, or `contradicts` Connection states how that Result bears on the Claim. A `supported` or `robust` Claim requires an accepted supporting Result Connection.

## Study and execution boundary

A Study names `question_ids`, `claim_ids`, and `method_ids`, plus its goal, motivation, requirements, resource profiles, optional entrypoint, expected outputs, completion criteria, limitations, blockers, and declared readiness. `entrypoint_method_id` identifies the one Method executed by the entrypoint. Methods that require distinct entrypoints belong in separate Studies rather than a multi-entrypoint execution model.

Infrastructure providers advertise capabilities. The resolver compares compatible environments and providers deterministically, preferring validated, then available, then experimental providers. It verifies profile compatibility, the environment lock, and artifact availability, reports blockers, and exposes each selected repository commit. A provider's stable identity and interface version remain separate from the implementation commit.

A Run identifies exactly one Study and one Method. It freezes selected provider revisions, environment and profile identity, configuration digest, input artifact digests, command template, timestamps, executor, outputs, and terminal status. A Method is reusable; a Run is historical. A Result is authored separately after an actual outcome is reviewable.

The current executor delegates to `scripts/zero_shot_eval_jax.py` in the pinned DAWN-SRW repository. Implementation code is not copied. A local checkpoint path is supplied at execution time, hashed, and represented in the Run by artifact ID and digest rather than personal path. Failed and interrupted Runs retain their manifests.

The executable Study remains blocked because no concrete checkpoint or complete TPU environment lock is registered. The schema, resolver, views, and CLI remain testable on CPU without pretending that a scientific execution occurred.

## Projections

`dawn view` and `dawn export` are deterministic, read-only projections of a successfully validated Catalog. Neither reads `.dor/` or creates canonical state.

- Compact Study views answer what is being studied, which Questions and Claims are in scope, which Methods are used, which Results exist, what is blocked, and what completion requires.
- Research views use a bounded one-hop graph closure from explicit Study references, Connections, Result provenance, and directly related Runs.
- Execution views delegate every per-profile plan to the resolver; no second readiness calculation exists.

Exports add the current research Git commit and dirty flag. They redact local paths, private locators, and local artifact locations. A dirty tree is reported rather than rejected; Run creation retains its stricter clean-tree requirement. Every collection is ordered by stable ID.
