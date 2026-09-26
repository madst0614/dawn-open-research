# DOR Packet handoff

A DOR Packet carries a research idea from a free-form conversation into DAWN Open Research without requiring the recipient to see the original conversation. It is a rich, self-contained private handoff: enough context to search the graph, resolve overlap, prepare a Study, and state what is runnable or blocked.

A Packet is deliberately not canonical DAWN state. It is not a Question, Study, Claim, Method, Result, Connection, Reference, Run, or infrastructure record. There is no Packet parser, Python model, JSON Schema, or `dawn ingest` command. Codex performs reviewable canonicalization using [AGENTS.md](AGENTS.md).

## Privacy boundary

Save new Packets as `.dor/inbox/<slug>.dor.yaml`. Successful intake preserves exact Packet bytes under `.dor/archive/` and writes a private transformation trace under `.dor/maps/`. Git ignores the entire `.dor/` directory. This is an accident-prevention boundary, not encryption or access control: anyone with filesystem access can read it, and forced staging can override ignore rules.

Do not put credentials, tokens, private keys, restricted data, private URLs, or unnecessary personal information in a Packet or trace. Canonical files must stand on their own and must not depend on any `.dor/` file remaining present.

## What a Packet may preserve

A useful Packet keeps distinctions that matter during canonicalization:

- unresolved questions;
- candidate propositions;
- reusable interpretations;
- experimental or analytical ideas;
- alternative explanations;
- predicted outcomes;
- negative outcomes and failure modes;
- references and whether each was actually checked;
- execution context, implementation leads, data leads, and artifact needs;
- scope, assumptions, uncertainty, constraints, and decisions already made; and
- reviewable completion criteria.

These entries are proposals or context. A candidate proposition is not a finding. An interpretation is not automatically canonical. An experimental idea becomes a Method only when its protocol is adequately specified. A predicted outcome is not a Result. An actual observation becomes a Result only with verified Run or Reference provenance, explicit scope, and limitations. A conversation is never a Reference.

Use `null`, `unknown`, or an explicit unresolved item instead of inventing missing facts. Name a canonical ID only when it was actually verified.

## Recommended Packet format

The format is a human-authored YAML convention rather than a machine-enforced schema. Empty lists are preferable to omitted context when absence matters.

```yaml
dor_packet_version: 1
title: "Short, specific research handoff title"
created_at: "2026-09-26T00:00:00+09:00"
created_by: "github:<username>"
privacy: private-local

handoff:
  summary: |-
    A standalone account of the idea and the reasoning needed to continue it.
  motivation: "Why this is worth investigating."
  requested_outcome: "What useful research state should exist after intake."
  decisions_already_made: []
  constraints: []
  out_of_scope: []

research:
  background: []
  known_observations:
    - statement: "What is believed to have occurred."
      basis: "Where that belief comes from, or unknown."
      scope: "Where it may apply."
      limitations: "Why it is not yet a general Result."
  open_questions:
    - question: "A concrete unresolved knowledge target."
      scope: "Its intended boundary."
  candidate_propositions:
    - statement: "A falsifiable proposed proposition."
      scope: "The bounded domain."
      basis: "Reasoning or source lead, not automatic validation."
  interpretations:
    - statement: "A reusable interpretation or synthesis."
      scope: "Where the interpretation is intended to apply."
      alternatives: []
  experimental_ideas:
    - title: "Potential Method"
      description: "What kind of investigation this is."
      protocol: "Specified steps, or null when not yet specified."
      controls: []
      measurements: []
  alternative_explanations: []
  predicted_outcomes: []
  failure_modes: []
  references:
    - title: "Known title or descriptive label"
      locator: "A real locator, or null"
      checked: false
      relevance: "Why it may matter."
  candidate_connections: []

study:
  goal: "The bounded research goal."
  question_search_terms: []
  claim_search_terms: []
  method_search_terms: []
  requirements:
    capabilities: []
    artifacts: []
    environment: []
    compute: []
  execution_context:
    implementation_refs: []
    data_refs: []
    profile_preferences: []
  expected_outputs: []
  completion_criteria: "How another researcher can judge completion."
  known_limitations: []
  blockers: []

canonicalization:
  possible_existing_ids: []
  explicit_provenance_assertions: []
  assumptions: []
  unresolved_ambiguities: []
  intake_notes: []
```

## Canonicalization rules

Codex maps Packet material conservatively:

```text
candidate proposition            -> Claim with proposition type
reusable interpretation          -> Claim with interpretation type
specified research procedure     -> Method
actual outcome with provenance   -> Result
bounded body of work             -> Study
external information             -> Reference, after locator verification
reviewable bearing or origin     -> proposed Connection
```

Predicted or hypothetical outcomes do not map to Results. Similarity or chronology does not establish intellectual provenance. A Packet's authorship does not establish authorship of every idea it contains.

## Intake trace

Successful intake follows this order:

1. Read the Packet as bytes without changing it.
2. Compute SHA-256 over those exact bytes.
3. Copy it to `.dor/archive/<sha256>.dor.yaml`, or verify an existing archive byte-for-byte.
4. Record repository HEAD and dirty state before canonical edits.
5. Search, canonicalize, validate, and resolve using tracked repository state.
6. Write `.dor/maps/<YYYYMMDDTHHMMSSZ>-<packet-slug>.intake.yaml`.

The trace records private transformation provenance, not scientific truth:

```yaml
dor_intake_trace_version: 1

packet:
  original_path: ".dor/inbox/example.dor.yaml"
  sha256: "sha256:<64 lowercase hex characters>"
  archived_path: ".dor/archive/<64 lowercase hex characters>.dor.yaml"

repository:
  base_revision: "<40-character Git commit>"
  base_dirty: false

canonicalization:
  reused:
    - packet_item: "research.open_questions[0]"
      canonical_ids: ["<QUESTION_ID>"]
      reason: "The existing Question has the same bounded research intent."
  created: []
  updated: []
  deferred:
    - packet_item: "research.background[2]"
      canonical_ids: []
      reason: "Useful context retained privately, but not a distinct canonical object."
  unresolved:
    - packet_item: "research.references[0]"
      canonical_ids: []
      reason: "The supplied locator could not be verified."

studies: ["<STUDY_ID>"]

validation:
  dawn_validate: "valid: <object count> objects"
  tests: "<exact test result or not run with reason>"
  resolver: "<exact readiness summary or not run with reason>"
```

Every mapping item identifies the Packet entry, all canonical IDs it maps to, and the reason for reuse, creation, update, deferral, or unresolved status. Deferred material remains recoverable in the immutable private archive but is intentionally not promoted.

## Copy-paste ChatGPT prompt

Paste this at the end of a research conversation:

```text
Turn this into a DOR Packet for DAWN Open Research.

The recipient will not receive our conversation. Produce a self-contained private-local handoff that restates the context, reasoning, decisions, constraints, and unresolved questions needed to continue.

Keep separate: known observations and their bases; open questions; candidate propositions; reusable interpretations; experimental or analytical ideas; alternative explanations; predicted outcomes; failure modes; references; execution context; requirements; limitations; and completion criteria.

Do not treat a candidate proposition, interpretation, prediction, or conversational report as a finding. Do not call anything a Result without actual Run or checked Reference provenance. Do not turn the conversation into a Reference. Do not invent citations, DAWN IDs, provenance, outcomes, implementation revisions, artifact availability, infrastructure readiness, or author identity.

Exclude secrets, credentials, private keys, restricted data, private URLs, personal machine paths, and irrelevant personal information. Use null, unknown, or unresolved_ambiguities for missing facts. Use only canonical IDs that were explicitly verified in the conversation.

Return exactly one fenced YAML block using the recommended DOR Packet structure from DOR_PACKET.md, and no commentary.
```

Save the YAML as `.dor/inbox/<slug>.dor.yaml`, then ask Codex to read `AGENTS.md` and ingest it. Compute remains a separate, explicit authorization. A Run preserves execution history; a Result is authored separately and then connected to the graph for review.
