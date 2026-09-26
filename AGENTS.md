# DAWN contribution protocol

This repository is the canonical Git record of the research program. Websites, databases, dashboards, and generated status output are projections. Run the full test suite and `dawn validate` before finishing a change.

The universal research vocabulary is:

- **Question — What is unresolved?** An open knowledge target.
- **Study — What bounded research is underway?** A unit that connects a goal, explicit research references, requirements, and execution.
- **Claim — What is asserted or interpreted?** A proposition or reusable interpretation with explicit scope and epistemic status.
- **Method — How is it investigated?** A reusable research protocol, not a concrete execution.
- **Result — What actually occurred?** An observed or derived outcome with explicit provenance, scope, and limitations.
- **Connections — How does this research bear on existing knowledge?** Reviewable semantic or intellectual-provenance assertions stored internally as Relation records.
- **References — Where did external information come from?** Source records for papers, datasets, repositories, documentation, benchmarks, and similar material.
- **Execution provenance — What exact code, data, environment, and configuration produced a Run?**

This is a graph, not a mandatory tree or pipeline. A Question, Claim, Method, or unexpected Result may begin the work. Claims and Methods may be reused across Studies. Results may bear on several Claims. A Study may address several Questions or Claims.

Search the graph before creating objects. Reuse an overlapping object and connect it where appropriate; create a new ID only for a genuinely distinct object. IDs use the namespace in `program.yaml`, an object kind, and an offline-generated ULID. IDs never encode status, title, or version. Git preserves edits to stable objects.

Claims need explicit scope and conservative epistemic status. Claim type is only `proposition` or `interpretation`; maturity is tracked separately. Proposed hypotheses and interpretations are not findings. A `supported` or `robust` Claim requires an accepted `Result --supports--> Claim` Connection. A Result never promotes a Claim automatically.

A Result must state what occurred, where it applies, its limitations, its authors, and at least one Run or Reference. Conversation statements, expectations, predictions, and unexecuted procedures are not Results. Preserve negative outcomes. A Run remains execution provenance until a Result is separately authored.

Connections are first-class internal records with an asserter, time, rationale, status, and review metadata. Contributors normally reason in human terms such as “this Result weakens that Claim”; they do not need to manipulate internal YAML unless implementing the connection. Semantic similarity never proves intellectual provenance. Use `derived_from` or related provenance types only when actual origin is documented, never from chronology or resemblance. New Connections remain proposed until reviewed.

Studies use explicit `question_ids`, `claim_ids`, and `method_ids`; do not replace them with an untyped target bag. A Study declares capabilities and artifacts before provider resolution. Prefer existing, validated infrastructure and pin exact implementation, environment, profile, configuration, and artifact revisions in every Run. Do not call missing assets, incomplete environments, or untested hardware ready.

A Method describes how research is performed. A Run is one historical execution of one Method within one Study. Runs keep unique IDs and terminal history; a failed or invalidated Run remains with its reason. Never reuse or overwrite a terminal Run.

Every persistent object identifies its creator and time. Connections identify asserters and reviewers; Results identify authors and reviewers; Runs identify executors. Preserve Git authorship. Do not create numerical contribution scores. Publication snapshots may freeze Git tags, object IDs, Runs, implementation commits, environment locks, and artifact hashes; DOI automation remains future work.

Never commit secrets, credentials, private URLs, machine paths, local caches, large checkpoints, or unreviewed execution logs. DAWN-SRW is read-only for this bootstrap. Its MIT license and provenance remain distinct from this repository's Apache-2.0 license.

When asked to add research in prose: search current objects, identify overlap, reuse or create distinct objects, add only justified proposed Connections, preserve bounded uncertainty and negative expectations, prepare or update a Study, then validate. Generated views are not canonical knowledge.

## DOR Packet intake

A DOR Packet is a private, noncanonical handoff. It is not a research object, schema, executable manifest, Reference, or Result. It may retain conversational distinctions including questions, candidate propositions, interpretations, experimental ideas, alternative explanations, predicted outcomes, failure modes, references, and execution context.

The private workspace is `.dor/inbox/`, `.dor/archive/`, and `.dor/maps/`; `.dor/` must remain ignored. Never force-add a Packet or intake trace, copy its private path into canonical objects, or treat Git ignore as encryption. Do not add Packet-specific Python models, schemas, or CLI commands.

Successful intake preserves a private transformation trace. Read the original Packet as bytes without modifying it, compute SHA-256 over those exact bytes, and archive an exact copy as `.dor/archive/<sha256>.dor.yaml`. If that archive already exists, verify identical bytes rather than overwriting it. Before canonical edits, record the current Git commit and dirty state.

Write `.dor/maps/<YYYYMMDDTHHMMSSZ>-<packet-slug>.intake.yaml` with `dor_intake_trace_version: 1`. Record original and archived paths, digest, base revision and dirty state, validation outcomes, related Studies, and mapping groups named `reused`, `created`, `updated`, `deferred`, and `unresolved`. Every item names the Packet idea, canonical IDs if any, and a rationale. `deferred` means useful context intentionally remains only in the archived Packet. Archive and trace are private process provenance, not scientific state.

When asked to ingest a Packet:

1. Read the complete Packet and this file. Preserve its exact-byte archive, digest, and pre-edit repository identity before canonicalization. Treat every statement as context or a proposal. Citations and supplied IDs are leads to verify, not automatic validation. Report missing identity, indispensable context, or attribution as a blocker instead of inventing it.
2. Inspect current Git state and search Questions, Studies, Claims, Methods, Results, Connections, References, Runs, and infrastructure before editing. Reuse overlapping objects; create a new offline ID only for a distinct object.
3. Preserve the vocabulary. An open question is not automatically a Claim; an experimental idea becomes a Method only when its protocol is adequately specified; a prediction is not a Result; a conversation is not a Reference. New Claims and Connections begin conservatively unless reviewed repository state justifies otherwise.
4. Preserve attribution and provenance boundaries. Use only identities and origins explicitly supplied by the Packet or repository context. Similarity, chronology, Packet authorship, and model synthesis do not establish intellectual provenance. Never fabricate a citation, outcome, ID, Run, review, or readiness claim.
5. Canonicalize only useful research content. Record scope and uncertainty, retain negative and failed expectations, and separate Packet suggestions from repository-established facts. Exclude secrets, credentials, private URLs, personal machine paths, raw private conversation, and unreviewed execution logs from tracked files.
6. Map candidate propositions to `Claim(claim_type=proposition)`, reusable interpretations to `Claim(claim_type=interpretation)`, specified procedures to Methods, and actual observations with verified Run or Reference provenance to Results. Predicted and hypothetical outcomes stay outside Results.
7. Create or update a Study only after overlap is resolved. Use explicit Question, Claim, and Method references; include goals, motivation, requirements, profiles, expected outputs, completion criteria, limitations, readiness, and honest blockers. A Question parent is optional.
8. Resolve against registered infrastructure. Prefer compatible validated providers and pinned revisions. Use `dawn resolve <STUDY_ID> --profile <PROFILE> --json` only when a Study has an executable Method and profile; otherwise report exactly what is missing. Never change infrastructure records merely to make a Study appear runnable.
9. Intake prepares research but does not authorize compute. Do not run `dawn run`, create a Run, or author a Result unless separately requested and backed by actual execution or a reviewable Reference.
10. Run relevant tests and `dawn validate`, complete the private trace with exact outcomes, and report reused, created, updated, deferred, and unresolved material; proposed Connections; related Studies; resolver selections; and remaining blockers. Leave the Packet, archive, and trace in place unless explicitly asked to remove them.

## Python verification on Windows

Use `.venv\Scripts\python.exe` for local final tests. Before final tests, run `.venv\Scripts\python.exe -c "import sys; print(sys.executable)"` and check required package imports. Do not use `python`, `py`, or system Python for final tests. Report the actual Python path and test results.
