# DAWN contribution protocol

This repository is the canonical Git record of the research program. Websites, databases, dashboards and generated status output are projections. Use `dawn validate` before finishing a change.

The graph vocabulary is Claim (C), Question (Q), Insight (I), Probe (P), Evidence (E), Source (S), and first-class Relation (R). No Q→C→P→E sequence is required. A Question, Claim or Insight may begin independently. A Probe is a protocol; a Run is an execution; Evidence is a separately authored observation.

Search the graph before creating objects. Reuse an overlapping object and add a relation when appropriate; create a new ID only for a genuinely distinct object. Insights must add reusable interpretation, not repeat a Source or Evidence. IDs use the namespace in `program.yaml`, a kind and an offline-generated ULID. IDs never encode status, title or version. Git preserves edits to stable objects.

Claims need explicit scope and conservative epistemic status. Proposed hypotheses are not findings. Supported or robust Claims require accepted Evidence relations. Evidence must state observation, scope, limitations and Run or Source provenance. Preserve negative and failed outcomes; do not promote Claims or generate Evidence automatically from Runs.

Relations are reviewable assertions with rationale and status. Semantic similarity never proves intellectual provenance. Use `derived_from` or related provenance edges only when the actual origin is documented; never reconstruct it from chronology or resemblance. Keep proposed relations proposed until reviewed. Review in GitHub pull requests is the canonical v0 process; relation metadata records semantic review state.

Explorations package goals, graph context, Probes, capability needs, artifacts, profiles and completion criteria. They can target any graph object or infrastructure capability; a Question parent is optional. Declare required capabilities, then resolve providers. Prefer existing, validated infrastructure and pin exact implementation, environment and artifact revisions in every Run. Do not call missing assets or untested hardware ready. Runs keep unique IDs and terminal history; an invalidated Run remains with a reason. Never reuse or overwrite a completed or failed Run.

Every persistent object identifies its creator and time; Relations identify asserters and reviewers, Runs identify executors. Preserve Git authorship. Do not create a numerical contribution score. Publication snapshots eventually freeze Git tags, object IDs, Runs, implementation commits and artifact hashes; DOI automation is future work.

Never commit secrets, credentials, private URLs, machine paths, local caches, large checkpoints or unreviewed execution logs. Legacy DAWN-SRW is read-only for this bootstrap. Its MIT license and provenance remain distinct from this repository's Apache-2.0 license.

When asked to add research in prose: search existing objects, identify overlap, reuse or create distinct objects, add proposed relations with rationales, never fabricate historical provenance, then validate. Generated state summaries are views, not canonical knowledge.

## DOR Packet intake

A DOR Packet is a private, noncanonical handoff, not a graph object, Source, Evidence, schema, or executable manifest. The default location is `.dor/inbox/*.dor.yaml`, and `.dor/` must remain ignored. Never force-add a packet, copy its private path into canonical objects, or treat Git ignore as encryption. Do not add packet-specific Python models, schemas, or CLI commands.

When asked to ingest a packet:

1. Read the complete packet and this file. Treat every packet statement as context or a proposal. Citations and existing canonical IDs are leads to verify against the repository or original Source, not automatic validation. The original conversation is unavailable by design; report a missing identity, indispensable context, or attribution as a blocker instead of inventing it.
2. Inspect the current Git state and search the graph before editing. Check candidate concepts against existing Questions, Claims, Insights, Probes, Evidence, Sources, Relations, and Explorations. Reuse an overlapping object and relate it where appropriate; create a new offline ID only for a genuinely distinct canonical object.
3. Preserve the graph vocabulary. A question is not automatically a Claim, a suggested experiment is not a Probe until its protocol is specified, a prediction or user report is not Evidence, and a conversation is not a Source. New Claims begin conservatively as proposed unless the existing reviewed graph justifies another status. New Relations remain proposed until reviewed.
4. Preserve attribution and provenance boundaries. Use only creator identities and origins explicitly supplied by the packet or repository context. Similarity, chronology, packet authorship, and model synthesis do not establish `derived_from`, `inspired_by`, or other intellectual provenance. Never fabricate a citation, result, object ID, Run, review, or readiness claim.
5. Canonicalize only the useful research content. Record explicit scope and uncertainty, retain negative or failed expectations, and separate packet suggestions from repository-established facts. Do not include secrets, credentials, private URLs, personal machine paths, raw private conversation, or unreviewed execution logs in tracked files.
6. Create or update an Exploration only after graph overlap is resolved. Connect its `graph_context` and `targets` to existing or newly justified objects; include concrete goals, motivation, Probe IDs, capability and artifact requirements, compatible profiles, expected outputs, completion criteria, known limitations, and honest blockers. A Question parent is optional.
7. Resolve against existing infrastructure. Prefer compatible validated providers and pinned revisions already registered in the repository. Use `dawn resolve <EXPLORATION_ID> --profile <PROFILE> --json` when the Exploration has an executable Probe and profile; otherwise report exactly what is missing. Do not change infrastructure records merely to make an Exploration appear runnable.
8. Ingestion prepares research but does not authorize compute. Do not run `dawn run`, create a Run, or author Evidence unless separately requested and backed by an actual execution or reviewable Source. A Run never becomes Evidence automatically.
9. Finish by running the relevant tests and `dawn validate`. Report reused, created, or updated objects; proposed Relations; the Exploration; resolver selections; and all remaining blockers. Leave the private packet in place unless the user explicitly asks to remove it.

## Python verification on Windows

Use `.venv\Scripts\python.exe` for local final tests. Before final tests, run `.venv\Scripts\python.exe -c "import sys; print(sys.executable)"` and check required package imports. Do not use `python`, `py` or system Python for final tests. Report the actual Python path and test results.
