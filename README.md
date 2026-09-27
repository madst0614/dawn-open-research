# DAWN Open Research

DAWN Open Research (DOR) is a Git-native framework for recording the epistemic history, grounding, and execution of research. DAWN-SRW is its first research program, not the ontology's template. Git is canonical; websites, indexes, dashboards, and generated views are projections.

## Research grammar

DOR separates four layers that have different meanings:

- **Research activity:** a Study is one bounded unit of research activity.
- **Epistemic core:** Questions, Claims, Methods, Results, and Relations record inquiry and scholarly reasoning.
- **Grounding and research products:** Sources, Artifacts, and Runs anchor or embody research.
- **Execution infrastructure:** repositories, providers, environments, and resource profiles make computational work resolvable and reproducible.

The core questions are:

- **Question — what are we trying to understand?** A structured uncertainty with a rationale, scope, and reviewed resolution status.
- **Claim — what are we asserting, interpreting, or defining?** A reviewable proposition, interpretation, or definition whose epistemic status is tracked separately.
- **Method — how are we investigating it?** A reusable protocol for experimentation, observation, proof, analysis, source criticism, qualitative inquiry, construction, or evaluation.
- **Result — what actually occurred or was derived?** A scoped outcome with limitations, authorship, and grounding in at least one Run, Source, or Artifact.
- **Relation — how does one research object bear on another?** A reviewable scholarly assertion with explicit provenance and review state.
- **Study — what bounded research activity are we conducting?** An organizer for any relevant Questions, Claims, Methods, Results, Artifacts, and Method-specific execution plans.

Research is a graph, not a required `Question → Claim → Method → Result` pipeline. Valid histories include `Method → Result → Question`, `Result → Question → Claim`, `Source → Question`, `Artifact → Question`, and `Claim → Question`. A Study may begin without a Question or Claim.

Accepted evidential Relations assign a supporting, weakening, or contradicting role to a Result, Source, or Claim; there is no separate record kind for that role. A Result never changes a Claim automatically, and support for one Claim never resolves a Question automatically.

## Start here

```bash
dawn validate
dawn status
dawn studies [QUERY]
dawn show <ID>
dawn view <STUDY_ID>
dawn view <STUDY_ID> --mode research
dawn view <STUDY_ID> --mode execution
dawn export <STUDY_ID>
```

Views and exports are deterministic, read-only projections. Research view follows bounded canonical research context. Execution view delegates readiness to the resolver and shows every selected Method plan, provider, environment, profile, Artifact, and blocker.

## From a private idea to grounded research

1. Put conversational context in a private DOR Packet under `.dor/inbox/`. The Packet is not canonical and does not authorize compute.
2. During intake, preserve the original bytes, SHA-256 archive, pre-edit Git identity, and private mapping trace.
3. Search existing objects before creating anything. Reuse equivalent objects and keep new Relations proposed until review.
4. Prepare or update a Study. Keep semantic references separate from its `execution.plans`.
5. Resolve one `Study + Method + Profile` target:

   ```bash
   dawn resolve <STUDY_ID> --method <METHOD_ID> --profile <PROFILE> --json
   ```

   `--method` may be omitted only when exactly one executable Method is unambiguous. Resolution fails closed on ambiguity, missing capabilities, unsafe or incomplete environment locks, invalid Artifacts, incompatible profiles, and unverified provider claims.

6. Run compute only when separately authorized and ready:

   ```bash
   dawn run <STUDY_ID> --method <METHOD_ID> --profile <PROFILE> \
     --implementation-repo <PINNED_CHECKOUT> \
     --artifact <ARTIFACT_ID>=<LOCAL_PATH> \
     --executor github:<username> --limit 32
   ```

   The current executor intentionally supports only the pinned DAWN-SRW zero-shot entrypoint. A Run freezes exact execution provenance and never creates a Result automatically.

7. After reviewing an actual observation or derivation, author a Result with explicit grounding, scope, limitations, and authors. Then propose scholarly Relations describing how it bears on Questions or Claims.

Negative outcomes and failed, cancelled, or invalidated Runs remain part of the record.

## Canonical storage

```text
graph/
  questions/
  claims/
  methods/
  results/
  relations/
  sources/
studies/
runs/
artifacts/
infra/
baselines/
publications/
```

One YAML file stores each persistent object. Strict Pydantic models define canonical shapes, generated JSON Schemas project them, and repository validation checks references, grounding, Relation endpoints, review policy, Claim maturity, execution-plan compatibility, and reproducibility invariants.

Connections and References are human-facing labels for canonical Relation and Source records. Artifacts are first-class research products as well as possible execution inputs or outputs.

## Reproducibility

Reproducibility means traceable grounding sufficient for another researcher to inspect the path from inquiry and Method to Result and Claim. Computational work additionally freezes rerunnable code, configuration, environments, profiles, Artifacts, and digests. Proofs may be grounded in proof Artifacts; historical work in inspectable Sources and analytical Methods; qualitative work in an inspectable procedure and analysis trail subject to privacy constraints.

## Install the local CLI

```powershell
git clone https://github.com/madst0614/dawn-open-research.git
cd dawn-open-research
py -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[test]"
.venv\Scripts\python.exe -m open_research validate
```

The primary command surface is `dawn validate`, `dawn status`, `dawn studies`, `dawn show`, `dawn view`, `dawn export`, `dawn resolve`, `dawn run`, and `dawn id new`.

The canonical graph currently contains ten Studies, twelve open Questions, twelve proposed Claims, and no Results or Runs. The compactness, semantic-locality, static-address, dynamic-index and shared-conditional-routing plans remain blocked by missing implementations or grounded coordinate artifacts, adapters, exact environment locks, and current compute allocation. The reference-checkpoint language Study contains separate zero-shot and autoregressive-generation Methods and plans; only the zero-shot plan has a supported runner entrypoint, and it remains blocked by the missing checkpoint and exact TPU environment lock. DAWN-SRW remains a separately licensed, read-only, pinned dependency.
