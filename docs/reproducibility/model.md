# Reproducibility and traceable grounding

DOR defines reproducibility broadly as **traceable grounding sufficient for another researcher to independently inspect the path from inquiry and Method to Result and Claim**. Exact rerunnable compute is one important case, not the universal definition.

- Computational research needs pinned code, environment, configuration, providers, resource profile, input Artifact digests, command, and outputs.
- Experimental research needs traceable protocols, materials, observations, instruments, and limitations.
- Mathematics and theoretical work need an inspectable derivation or proof Artifact and any Sources on which it depends.
- Historical and literature-based research need inspectable Sources, source-critical or analytical Methods, and an argument trail.
- Qualitative research needs an inspectable data, procedure, and analysis trail subject to privacy and consent constraints.
- Engineering and design research need the constructed Artifact, design Method, evaluation conditions, and observed outcomes.

## Computational chain

For executable work, the trace is:

`Study + Method + Profile → execution plan → capability resolution → pinned providers → environment lock → input Artifacts → Run → separately authored Result → reviewed Relations`.

Use:

```bash
dawn resolve <STUDY_ID> --method <METHOD_ID> --profile <PROFILE> --json
```

`--method` may be omitted only when the Study has exactly one unambiguous executable Method. The resolver checks the selected Method plan rather than a Study-wide entrypoint. Local readiness requires concrete local Artifact bytes because remote retrieval is not implemented. Public reproducibility additionally requires public Artifacts and validated providers, environment, and profile. Missing capabilities, an entrypoint, an exact environment lock, a profile, or required Artifact bytes fail closed.

`dawn run` requires clean research and implementation checkouts. It creates a new offline Run ID and exclusive directory, writes a hashed configuration snapshot, and freezes:

- the Study and Method;
- the research and implementation revisions;
- provider interface and repository revisions;
- environment identity and lock digest;
- resource profile;
- input Artifact IDs and digests;
- command and seed;
- timestamps, executor, outputs, and terminal status; and
- failure or invalidation reason.

The `artifact:<ID>` token in the recorded command replaces a local path; the byte digest is frozen and checked again after execution. A successful zero-shot Run also captures evaluator software versions, dataset fingerprints, native manifest digest, and observed device counts. Failed, interrupted, and invalidated Runs remain in history.

## Current DAWN-SRW boundary

The supported runner entrypoint is the frozen six-task DAWN-SRW zero-shot evaluator. Its stock tasks are LAMBADA, HellaSwag, PIQA, ARC Easy, ARC Challenge, and WinoGrande. `--limit 32` is a smoke protocol, not a full comparable evaluation.

Autoregressive generation is a second Method and execution plan in the same reference-checkpoint Study. It remains non-executable until prompts, decoding settings, and an adapter are specified. The reference checkpoint and exact TPU environment lock are also missing, so no scientific Run can honestly be produced now. DAWN-SRW remains read-only and pinned as a separately licensed implementation dependency.

## From Run or Source to knowledge

A Run is execution provenance, not a scientific Result. A researcher must review what occurred and author a scoped Result with limitations, authors, and one or more grounding IDs. Grounding may be a Run, Source, or Artifact depending on the research tradition. Negative outcomes use the same rule.

Only a separate, reviewed scholarly Relation states whether a Result, Source, or Claim supports, weakens, or contradicts a Claim. Neither Result creation nor Run completion promotes Claims or resolves Questions.

Publication manifests may freeze selected object IDs, Runs, implementation commits, environment locks, and Artifact hashes. The current release convention is live Git graph → frozen tag or release → archival DOI when available; v1 does not mint a DOI.
