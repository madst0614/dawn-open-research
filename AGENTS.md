# DAWN contribution protocol

This repository is the canonical Git record of the research program. Websites, databases, dashboards, and generated status output are projections. Run the full test suite and `dawn validate` before finishing a change.

The universal research grammar has four distinct layers:

- **Research activity:** Study.
- **Epistemic core:** Question, Claim, Method, Result, and Relation.
- **Grounding and research products:** Source, Artifact, and Run.
- **Execution infrastructure:** RepositoryRef, InfrastructureProvider, Environment, ResourceProfile, and related runtime metadata.

The contributor vocabulary is:

- **Question — What is unresolved?** An open knowledge target.
- **Study — What bounded research is underway?** A unit that connects a goal, explicit research references, requirements, and execution.
- **Claim — What is asserted, interpreted, or defined?** A proposition, reusable interpretation, or definition with explicit scope and epistemic status.
- **Method — How is it investigated?** A reusable research protocol, not a concrete execution.
- **Result — What actually occurred?** An observed or derived outcome with explicit provenance, scope, and limitations.
- **Connections — How does this research bear on existing knowledge?** Reviewable semantic or intellectual-provenance assertions stored internally as Relation records.
- **References — Where did external information come from?** Source records for papers, datasets, repositories, documentation, benchmarks, and similar material.
- **Execution provenance — What exact code, data, environment, and configuration produced a Run?**

This is a graph, not a mandatory tree or pipeline. A Question, Claim, Method, or unexpected Result may begin the work. Claims and Methods may be reused across Studies. Results may bear on several Claims. A Study may address several Questions or Claims.

Do not flatten the grammar into generic Node, Statement, or Event objects, and do not create generic records merely to avoid a semantic decision. Use Relation only for scholarly meaning that a researcher may review, dispute, or reinterpret. Study membership, Run infrastructure, Artifact flow, and Result grounding belong in explicit fields rather than scholarly Relations.

Search the graph before creating objects. Reuse an overlapping object and connect it where appropriate; create a new ID only for a genuinely distinct object. IDs use the namespace in `program.yaml`, an object kind, and an offline-generated ULID. IDs never encode status, title, or version. Git preserves edits to stable objects.

Questions need an explicit inquiry, rationale, scope, and reviewed resolution status; they are not topic labels or todo items. Claims need explicit scope and conservative epistemic status. Claim type is `proposition`, `interpretation`, or `definition`; maturity is tracked separately. Proposed hypotheses, interpretations, and definitions are not findings. A `supported` or `robust` Claim requires an accepted scholarly `supports` Relation from a Result, Source, or Claim. A Result never promotes a Claim automatically, and Question status never changes automatically because one Claim is supported.

A Result must state what occurred or was derived, where it applies, its limitations, its authors, and at least one grounding ID resolving to a Run, Source, or Artifact. Conversation statements, expectations, predictions, and unexecuted procedures are not Results. Preserve negative outcomes. A Run remains execution provenance until a Result is separately authored.

Connections are first-class internal records with an asserter, time, rationale, status, and review metadata. Contributors normally reason in human terms such as “this Result weakens that Claim”; they do not need to manipulate internal YAML unless implementing the connection. Semantic similarity never proves intellectual provenance. Use `derived_from` or related provenance types only when actual origin is documented, never from chronology or resemblance. New Connections remain proposed until reviewed.

Studies use explicit `question_ids`, `claim_ids`, `method_ids`, `result_ids`, and `artifact_ids`; do not replace them with an untyped target bag. A Study may begin without a Question or Claim. Method-specific capabilities, artifacts, profiles, entrypoints, outputs, and execution blockers belong under `execution.plans`, not in the semantic fields. A Study may contain several executable Methods; resolve and run the explicit `Study + Method + Profile` target, omitting Method only when exactly one executable plan is unambiguous. Prefer existing, validated infrastructure and pin exact implementation, environment, profile, configuration, and artifact revisions in every Run. Do not call missing assets, incomplete environments, or untested hardware ready.

A Method describes how research is performed. A Run is one historical execution of one Method-specific execution plan within one Study. Runs keep unique IDs and terminal history; a failed or invalidated Run remains with its reason. Never reuse or overwrite a terminal Run.

Every persistent object identifies its creator and time. Connections identify asserters and reviewers; Results identify authors and reviewers; Runs identify executors. Preserve Git authorship. Do not create numerical contribution scores. Publication snapshots may freeze Git tags, object IDs, Runs, implementation commits, environment locks, and artifact hashes; DOI automation remains future work.

Never commit secrets, credentials, private URLs, machine paths, local caches, large checkpoints, or unreviewed execution logs. DAWN-SRW is read-only for this bootstrap. Its MIT license and provenance remain distinct from this repository's Apache-2.0 license.

When asked to add research in prose: search current objects, identify overlap, reuse or create distinct objects, add only justified proposed Connections, preserve bounded uncertainty and negative expectations, prepare or update a Study, then validate. Generated views are not canonical knowledge.

## DOR Packet intake

A DOR Packet is a private, noncanonical handoff. It is not a research object, schema, executable manifest, Reference, or Result. It may retain conversational distinctions including questions, candidate propositions, interpretations, definitions, experimental ideas, alternative explanations, predicted outcomes, failure modes, references, artifacts, and execution context.

The private workspace is `.dor/inbox/`, `.dor/archive/`, and `.dor/maps/`; `.dor/` must remain ignored. Never force-add a Packet or intake trace, copy its private path into canonical objects, or treat Git ignore as encryption. Do not add Packet-specific Python models, schemas, or CLI commands.

Successful intake preserves a private transformation trace. Read the original Packet as bytes without modifying it, compute SHA-256 over those exact bytes, and archive an exact copy as `.dor/archive/<sha256>.dor.yaml`. If that archive already exists, verify identical bytes rather than overwriting it. Before canonical edits, record the current Git commit and dirty state.

Write `.dor/maps/<YYYYMMDDTHHMMSSZ>-<packet-slug>.intake.yaml` with `dor_intake_trace_version: 1`. Record original and archived paths, digest, base revision and dirty state, validation outcomes, related Studies, and mapping groups named `reused`, `created`, `updated`, `deferred`, and `unresolved`. Every item names the Packet idea, canonical IDs if any, and a rationale. `deferred` means useful context intentionally remains only in the archived Packet. Archive and trace are private process provenance, not scientific state.

When asked to ingest a Packet:

1. Read the complete Packet and this file. Preserve its exact-byte archive, digest, and pre-edit repository identity before canonicalization. Treat every statement as context or a proposal. Citations and supplied IDs are leads to verify, not automatic validation. Report missing identity, indispensable context, or attribution as a blocker instead of inventing it.
2. Inspect current Git state and search Questions, Studies, Claims, Methods, Results, Connections, References, Runs, and infrastructure before editing. Reuse overlapping objects; create a new offline ID only for a distinct object.
3. Preserve the vocabulary. An open question is not automatically a Claim; an experimental idea becomes a Method only when its protocol is adequately specified; a prediction is not a Result; a conversation is not a Reference. New Claims and Connections begin conservatively unless reviewed repository state justifies otherwise.
4. Preserve attribution and provenance boundaries. Use only identities and origins explicitly supplied by the Packet or repository context. Similarity, chronology, Packet authorship, and model synthesis do not establish intellectual provenance. Never fabricate a citation, outcome, ID, Run, review, or readiness claim.
5. Canonicalize only useful research content. Record scope and uncertainty, retain negative and failed expectations, and separate Packet suggestions from repository-established facts. Exclude secrets, credentials, private URLs, personal machine paths, raw private conversation, and unreviewed execution logs from tracked files.
6. Map candidate propositions to `Claim(claim_type=proposition)`, reusable interpretations to `Claim(claim_type=interpretation)`, candidate formal definitions to `Claim(claim_type=definition)`, specified procedures to Methods, and actual observations or derivations with verified Run, Source, or Artifact grounding to Results. Predicted and hypothetical outcomes stay outside Results.
7. Create or update a Study only after overlap is resolved. Use explicit Question, Claim, Method, Result, and Artifact references; include goals, motivation, completion criteria, limitations, and honest blockers. Keep Method-specific execution requirements and readiness in `execution.plans`. A Question parent is optional.
8. Resolve against registered infrastructure. Prefer compatible validated providers and pinned revisions. Use `dawn resolve <STUDY_ID> --method <METHOD_ID> --profile <PROFILE> --json` when a Study has multiple executable Methods; omit `--method` only when selection is unambiguous. Otherwise report exactly what is missing. Never change infrastructure records merely to make a Study appear runnable.
9. Intake prepares research but does not authorize compute. Do not run `dawn run`, create a Run, or author a Result unless separately requested and backed by actual execution or a reviewable Reference.
10. Run relevant tests and `dawn validate`, complete the private trace with exact outcomes, and report reused, created, updated, deferred, and unresolved material; proposed Connections; related Studies; resolver selections; and remaining blockers. Leave the Packet, archive, and trace in place unless explicitly asked to remove them.

## Python verification on Windows

Use `.venv\Scripts\python.exe` for local final tests. Before final tests, run `.venv\Scripts\python.exe -c "import sys; print(sys.executable)"` and check required package imports. Do not use `python`, `py`, or system Python for final tests. Report the actual Python path and test results.
