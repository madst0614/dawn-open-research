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

## Python verification on Windows

Use `.venv\Scripts\python.exe` for local final tests. Before final tests, run `.venv\Scripts\python.exe -c "import sys; print(sys.executable)"` and check required package imports. Do not use `python`, `py` or system Python for final tests. Report the actual Python path and test results.
