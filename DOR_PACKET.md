# DOR Packet handoff

A DOR Packet carries a research idea from a free-form conversation into DAWN Open Research without requiring the recipient to see the original conversation. It is a self-contained intake document: enough context to search the graph, decide what overlaps, prepare an Exploration, and state what is runnable or blocked.

A packet is deliberately **not** a canonical DAWN object. It does not change the meaning of Claim (C), Question (Q), Insight (I), Probe (P), Evidence (E), Source (S), Relation (R), Exploration, Run, or resolver records. There is no packet parser, Python model, JSON Schema, or `dawn ingest` command. Codex performs a reviewable canonicalization using [AGENTS.md](AGENTS.md).

## Privacy boundary

Save packets under `.dor/`, normally `.dor/inbox/<slug>.dor.yaml`. The repository ignores the entire directory, so a normal Git add does not publish a packet. This is an accident-prevention boundary, not encryption or access control: anyone with filesystem access can read it, and `git add -f` can override the ignore rule. Do not put credentials, tokens, private keys, restricted data, private URLs, or unnecessary personal information in a packet.

After intake, keep the packet local for continuity or delete it according to your own retention policy. Canonical files must stand on their own and must not depend on the packet remaining present.

## Authoring rules

A useful packet:

- summarizes the research idea and motivation without referring to “the discussion above”;
- separates known observations, external sources, hypotheses, interpretations, and open questions;
- states scope, uncertainty, assumptions, constraints, and decisions already made;
- gives source locators only when they are real, and marks whether they were actually checked;
- names canonical DAWN IDs only when they were explicitly verified;
- describes proposed Probes as protocols, including expected, negative, and failed outcomes;
- records compute, environment, implementation, data, and artifact requirements without claiming they are available;
- includes enough acceptance criteria for another researcher to judge completion; and
- uses `null`, `unknown`, or an explicit open question instead of inventing missing facts.

Packet contents are proposals. A candidate Claim is not a finding, a proposed Probe is not an execution, and a reported result is not Evidence until it has appropriate Run or Source provenance and review.

## Packet format

The format is a human-authored YAML convention rather than a machine-enforced schema. Keep the top-level keys below so another person or agent can navigate the handoff consistently. Empty lists are preferable to omitted context when absence matters.

```yaml
dor_packet_version: 1
title: "Short, specific research handoff title"
created_at: "2026-09-26T00:00:00+09:00"
created_by: "github:<username>"
privacy: private-local

handoff:
  summary: |-
    A standalone account of the idea and the important reasoning that led to it.
    The recipient must not need the original conversation.
  motivation: "Why this is worth investigating."
  requested_outcome: "What useful research state should exist after intake."
  decisions_already_made: []
  constraints: []
  out_of_scope: []

research:
  background: []
  known_observations:
    - statement: "What is believed to have been observed."
      basis: "Where that belief comes from, or unknown."
      scope: "Where it may apply."
      limitations: "Why it is not yet a general finding."
  open_questions:
    - "A concrete unresolved question."
  candidate_claims:
    - statement: "A falsifiable proposed proposition."
      scope: "The bounded domain of the proposition."
      basis: "Reasoning, prior observation, or source; never invented."
      epistemic_status: proposed
  candidate_insights:
    - interpretation: "A reusable interpretation, not a repeated observation."
      scope: "Where the interpretation may be useful."
  sources:
    - title: "Exact source title, if known"
      locator: "DOI, public URL, repository revision, or other stable locator"
      relevance: "What the source contributes."
      checked: false
  candidate_relations:
    - source: "Verified DAWN ID or an unambiguous packet-local label"
      relation: "Suggested semantic or provenance relation"
      target: "Verified DAWN ID or an unambiguous packet-local label"
      rationale: "Why the relation is suggested."
      provenance_basis: "Explicit origin evidence, or none."

exploration:
  goal: "The concrete research goal."
  graph_targets: []
  proposed_probes:
    - title: "Probe title"
      method: "What is varied or compared."
      protocol: "Enough procedural detail to specify the test."
      expected_observations: []
      negative_or_failure_outcomes: []
  requirements:
    capabilities: []
    artifacts: []
    environment: []
    compute: []
  implementation_refs: []
  data_refs: []
  expected_outputs: []
  completion_criteria: "A reviewable definition of done."
  known_limitations: []

canonicalization:
  graph_search_terms: []
  possible_existing_ids: []
  explicit_provenance_assertions: []
  assumptions: []
  unresolved_ambiguities: []
  intake_notes: []
```

`created_by` should identify the human responsible for the handoff using the repository convention when known. If identity or time is unavailable, use `null` and list the gap under `unresolved_ambiguities`; Codex must not guess required canonical attribution. Packet-local labels are descriptive handles, not DAWN IDs.

## Copy-paste ChatGPT prompt

Paste this at the end of the research conversation. Replace the identity placeholder if it was not already stated.

```text
Turn this into a DOR Packet.

Use our entire conversation to produce one self-contained research handoff for DAWN Open Research. The recipient will not receive the original conversation, so restate all context, reasoning, decisions, constraints, and unresolved questions needed to continue the work.

Rules:
- Separate known observations, external sources, candidate claims, candidate insights, open questions, and proposed probes.
- Treat claims and predicted results as proposed, not as findings.
- Do not turn conversation statements into Evidence or Sources.
- Do not invent citations, DAWN IDs, provenance, experimental results, implementation revisions, artifact availability, infrastructure readiness, or author identity.
- Include a source locator only if it is known; say whether the source was actually checked.
- Include explicit scope, assumptions, limitations, negative outcomes, failure cases, requirements, and reviewable completion criteria.
- Use verified DAWN IDs only if they appeared and were confirmed in the conversation; otherwise provide graph search terms.
- Exclude credentials, secrets, private keys, restricted data, private URLs, personal machine paths, and irrelevant personal information.
- Use null, unknown, or unresolved_ambiguities for missing facts.
- Set privacy to private-local and created_by to "github:<username>" if I supplied that identity; otherwise set created_by to null.
- Return exactly one fenced YAML block and no commentary.

Use these top-level keys and nesting:
dor_packet_version: 1
title: ...
created_at: ...
created_by: ...
privacy: private-local
handoff:
  summary: ...
  motivation: ...
  requested_outcome: ...
  decisions_already_made: []
  constraints: []
  out_of_scope: []
research:
  background: []
  known_observations: []
  open_questions: []
  candidate_claims: []
  candidate_insights: []
  sources: []
  candidate_relations: []
exploration:
  goal: ...
  graph_targets: []
  proposed_probes: []
  requirements:
    capabilities: []
    artifacts: []
    environment: []
    compute: []
  implementation_refs: []
  data_refs: []
  expected_outputs: []
  completion_criteria: ...
  known_limitations: []
canonicalization:
  graph_search_terms: []
  possible_existing_ids: []
  explicit_provenance_assertions: []
  assumptions: []
  unresolved_ambiguities: []
  intake_notes: []
```

## Handoff and intake

Save the YAML block as `.dor/inbox/<slug>.dor.yaml`, then ask Codex:

```text
Read AGENTS.md and ingest .dor/inbox/<slug>.dor.yaml.
```

Codex searches before creating anything, explains reuse and overlap decisions, writes only justified canonical objects and proposed Relations, prepares an Exploration, and runs the resolver when enough executable context exists. Its intake report distinguishes runnable work from missing Probes, capabilities, environments, profiles, artifacts, or provenance. Compute remains a separate, explicit step. Runs preserve execution history; reviewed Evidence is authored separately and then connected back to the graph.
