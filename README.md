# DAWN Open Research

DAWN is a Git-native research program studying whether AI computation can become explicit, traceable, causally testable, and eventually selectively executable with physical efficiency. Git is the source of truth; websites, indexes, and generated status views are projections.

The research model has five concepts:

- **Question — What do we want to know?** An unresolved knowledge target.
- **Study — What research are we doing?** A bounded unit of work that connects goals, research objects, requirements, and execution.
- **Claim — What do we assert or interpret?** A proposition or reusable interpretation whose maturity is tracked separately from its type.
- **Method — How do we investigate it?** A reusable experiment, benchmark, analysis, proof attempt, simulation, or intervention protocol.
- **Result — What actually came out?** An observed or derived outcome with explicit Run or Reference provenance, scope, and limitations.

These objects form a graph, not a required pipeline. A Claim or Method can be reused by many Studies, a Result can bear on several Claims, and research can begin with any of the five concepts.

Supporting concepts come second:

- **Connections** record reviewable semantic or provenance assertions. A Result supports, weakens, or contradicts a Claim only through an explicit Connection.
- **References** record external provenance such as papers, datasets, repositories, documentation, and benchmarks.
- **Runs** record concrete historical executions.
- **Artifacts** record identifiable inputs and outputs with digests where available.
- **Reproducible infrastructure** resolves capabilities to pinned repositories, environments, and resource profiles without overstating readiness.

## Start here

```bash
dawn status
dawn studies
dawn view <STUDY_ID>
dawn view <STUDY_ID> --mode research
dawn view <STUDY_ID> --mode execution
dawn export <STUDY_ID> > research.dor.yaml
```

`dawn view` is read-only: compact by default, canonically bounded with `--mode research`, and resolver-backed with `--mode execution`. Add `--profile <PROFILE>` to execution mode to inspect one resource profile. `dawn export` writes a self-contained YAML snapshot to standard output; `--json` selects JSON. Neither command creates canonical research state.

## From an idea to reproducible research

`idea/conversation → private DOR Packet → Codex canonicalization → Study → resolve → Run → Result → reviewed Connections → updated Claims and Questions`

### 1. Browse the program

```bash
dawn status
dawn studies [QUERY]
dawn show <ID>
```

`dawn status` summarizes open Questions, Claim states, Study readiness, capabilities, and recent Runs. `dawn studies` lists or filters bounded research. `dawn show` displays one canonical object with its inbound and outbound Connections.

### 2. Bring an idea privately

Use [DOR_PACKET.md](DOR_PACKET.md) to turn a conversation into a self-contained private handoff and save it under `.dor/inbox/`. The whole `.dor/` directory is ignored by Git. That reduces accidental publication; it is not encryption or access control.

The Packet can retain questions, candidate propositions, interpretations, experimental ideas, alternative explanations, predicted outcomes, failure modes, references, and execution context. It is not canonical scientific state. Predicted outcomes are not Results, and a conversation is not a Reference.

### 3. Canonicalize into a Study

Ask Codex to read [AGENTS.md](AGENTS.md) and ingest the Packet. Intake hashes and privately archives the unchanged Packet, records a private mapping trace, searches the graph, reuses overlapping objects, creates only genuinely distinct objects, and keeps new Connections proposed until review.

The resulting Study names explicit Questions, Claims, and Methods along with its goal, requirements, profiles, completion criteria, limitations, and blockers. A Question parent is optional.

### 4. Resolve without running compute

```bash
dawn resolve <STUDY_ID> --profile <PROFILE> --json
```

The resolver selects compatible registered providers and checks capabilities, the environment lock, profiles, and artifacts. It reports exact selections and blockers. Missing assets, incomplete locks, and unverified hardware remain blocked.

### 5. Execute on suitable infrastructure

The current `dawn run` adapter is intentionally narrow: it invokes the pinned DAWN-SRW zero-shot evaluator without copying that implementation into this repository.

```bash
dawn run <STUDY_ID> --profile <PROFILE> \
  --implementation-repo <PINNED_DAWN_SRW_CHECKOUT> \
  --artifact <ARTIFACT_ID>=<LOCAL_PATH> \
  --executor github:<username> --limit 32
```

A Run freezes the research revision, implementation revision, environment, profile, configuration, input digests, timestamps, executor, status, outputs, and failure or invalidation information. Creating a Run never creates a Result automatically.

### 6. Author and connect Results

After reviewing an actual execution or a reviewable external Reference, author a scoped Result with explicit provenance and limitations. Add a proposed Connection describing how it bears on a Claim. Only an accepted supporting Result Connection permits a Claim to be marked `supported` or `robust`; the mere presence of a Result never changes Claim status.

Negative, failed, cancelled, and invalidated outcomes remain part of the history.

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

Connections and References are the human-facing names for internal Relation and Source records. One YAML file stores each persistent object. Strict Pydantic models define the canonical shapes, generated JSON Schemas project them, and cross-object validation fails closed.

## Install the local CLI

```powershell
git clone https://github.com/madst0614/dawn-open-research.git
cd dawn-open-research
py -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[test]"
.venv\Scripts\dawn.exe validate
```

The implemented command surface is `dawn validate`, `dawn status`, `dawn studies [QUERY]`, `dawn show <ID>`, `dawn view <ID>`, `dawn export <ID>`, `dawn resolve <STUDY_ID>`, `dawn run <STUDY_ID>`, and `dawn id new <KIND>`.

The eight seeded Studies are owner-directed research plans, not findings. The language-behavior frontier uses separate zero-shot and autoregressive-generation Studies because each requires its own execution entrypoint. All four seeded Claims are proposed. There are no seeded Results or Runs. The executable zero-shot Study remains blocked until a concrete checkpoint and exact TPU environment lock are available.

Search before creating research objects, preserve explicit attribution, keep semantic and intellectual provenance distinct, and run the full test suite plus `dawn validate` before submitting a change. DAWN-SRW remains a separately licensed, read-only, pinned implementation dependency; no implementation code is copied here.
