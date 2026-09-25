# DAWN Open Research

DAWN is a Git-native research program studying whether AI computation can become explicit, traceable, causally testable, and eventually selectively executable with physical efficiency. This repository contains its public research graph, executable plans, infrastructure references, schemas, and run provenance. Git is the source of truth; websites, indexes, and generated status views are projections.

## From an idea to reproducible research

`idea/conversation → private DOR Packet → Codex ingest → Exploration → resolve → compute → Run/Evidence`

A DOR Packet is a private, local handoff document. It carries enough context to continue a research conversation without the original chat, but it is not a canonical research object and is not accepted as a finding. Codex reads the packet, searches the existing graph, reuses overlapping objects, creates only genuinely distinct objects, prepares an Exploration, and reports what is runnable or blocked. The repository's existing Claim (C), Question (Q), Insight (I), Probe (P), Evidence (E), Source (S), Relation (R), Exploration, Run, and resolver semantics remain authoritative.

### 1. Browse what is known and open

```bash
dawn status
dawn explore
dawn show <ID>
```

`dawn status` summarizes open questions, Claim states, Exploration readiness, capabilities, and recent Runs. `dawn explore [QUERY]` lists or filters research plans. `dawn show <ID>` displays one object with its inbound and outbound Relations.

### 2. Bring an idea

Talk freely with ChatGPT, then use the copy-paste prompt in [DOR_PACKET.md](DOR_PACKET.md) to turn the conversation into one self-contained packet. Save it locally, for example:

```text
.dor/inbox/operator-routing.dor.yaml
```

The entire `.dor/` directory is ignored by Git. This reduces accidental publication; it is not encryption, access control, or permission to store credentials.

### 3. Hand the packet to Codex

Ask Codex:

```text
Read AGENTS.md and ingest .dor/inbox/operator-routing.dor.yaml.
```

Ingest is an agent workflow, not a `dawn ingest` command. Codex follows [AGENTS.md](AGENTS.md): it treats packet statements as proposals, searches before creating objects, preserves explicit attribution, adds only reviewable proposed Relations, and never converts a proposed result into Evidence.

### 4. Prepare and resolve an Exploration

The intake connects the idea to the graph and prepares an Exploration with explicit goals, graph context, Probes, requirements, profiles, completion criteria, limitations, and blockers. Resolution is read-only and does not run compute:

```bash
dawn resolve <EXPLORATION_ID> --profile <PROFILE> --json
```

The resolver selects compatible registered providers and checks capabilities, the environment lock, profiles, and artifacts. It reports exact selections and blockers instead of calling unavailable assets or untested hardware ready.

### 5. Compute on suitable infrastructure

Use your own compatible local, GPU, TPU, or TRC compute only after resolution and environment checks. The current `dawn run` implementation is limited to the pinned legacy DAWN-SRW zero-shot evaluator:

```bash
dawn run <EXPLORATION_ID> --profile <PROFILE> \
  --legacy-repo <PINNED_DAWN_SRW_CHECKOUT> \
  --artifact <ARTIFACT_ID>=<LOCAL_PATH> \
  --executor github:<username> --limit 32
```

See [the reproducibility model](docs/reproducibility/model.md) for the exact execution boundary. A successful command records a Run; it does not create Evidence automatically.

### 6. Return reviewed results

Keep every terminal Run and its provenance, including negative, failed, cancelled, or invalidated outcomes. After review, author Evidence with an explicit observation, scope, limitations, and Run or Source provenance. Graph updates and accepted Relations can then support, weaken, contradict, or refine the next round of research.

## Install the local CLI

```bash
git clone https://github.com/madst0614/dawn-open-research.git
cd dawn-open-research
python -m venv .venv
# Activate .venv using your shell, then:
python -m pip install -e '.[test]'
dawn validate
```

On Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[test]"
.venv\Scripts\dawn.exe validate
```

The repository has no `uv.lock`; a future release can add one after the research runtime is locked.

## CLI reference

The implemented command surface is `dawn validate`, `dawn status`, `dawn show <ID>`, `dawn explore [QUERY]`, `dawn resolve`, `dawn run`, and `dawn id new <KIND>`. Run `dawn <COMMAND> --help` for command-specific arguments. Generate offline-safe stable IDs with `dawn id new Q` or the appropriate registered kind.

The four intended views are **Knowledge** (Claims, Questions, Insights, Evidence, and Sources), **Explore** (work that can be taken on), **Live** (Runs and review in progress), and **People** (attributed contributions). In v0, Git and the CLI provide these views. There is no web service or database.

The seven seeded Explorations are owner-directed research plans, not findings. Claims are proposed hypotheses. There is no seeded Evidence, Run, supported Claim, or baseline. The first executable Exploration remains blocked until a checkpoint and exact TPU environment lock are available. See [first execution path](docs/reproducibility/model.md) and [legacy inventory](docs/migration/dawn-srw-infrastructure-inventory.md).

## Contribution path

Search existing objects before creating new ones. Add one YAML file per distinct canonical object; generate its ID with `dawn id new <KIND>`. Keep Relations separate and state whether they are semantic or intellectual provenance. Add scope to Claims, provenance to Evidence, and exact revisions to Runs. Submit changes through Git review; `dawn validate` and tests are CI gates. [AGENTS.md](AGENTS.md) is the contributor protocol.

This repository is Apache-2.0. DAWN-SRW remains a separately licensed, read-only, pinned implementation dependency; no legacy code is copied here.
