# DAWN Open Research

DAWN is a Git-native research program studying whether AI computation can become explicit, traceable, causally testable, and eventually selectively executable with physical efficiency. This repository contains its public research graph, executable plans, infrastructure references, schemas, and run provenance. Git is the source of truth; any future website or index is a projection.

The four intended views are **Knowledge** (claims, questions, insights, evidence and sources), **Explore** (work that can be taken on), **Live** (runs and review in progress), and **People** (attributed contributions). In v0, Git and the CLI provide these views. There is no web service or database.

## Quick start

```bash
git clone https://github.com/madst0614/dawn-open-research.git
cd dawn-open-research
python -m venv .venv
# Activate .venv using your shell, then:
python -m pip install -e '.[test]'
dawn status
dawn explore
dawn validate
```

On Windows PowerShell, use `.venv\Scripts\python.exe -m pip install -e ".[test]"` and `.venv\Scripts\dawn.exe` for the last three commands. The repository has no `uv.lock`; a future release can add one after the research runtime is locked.

`dawn show <ID>` shows an object and its relations. `dawn resolve <EXPLORATION_ID> --profile <PROFILE> --json` explains capability, environment, and artifact resolution without executing anything. `dawn id new Q` creates an offline-safe stable ID. `dawn run` is implemented for the pinned legacy zero-shot evaluator, but the first exploration is blocked until a checkpoint and exact TPU environment lock are available. See [first execution path](docs/reproducibility/model.md) and [legacy inventory](docs/migration/dawn-srw-infrastructure-inventory.md).

The seven seeded Explorations are owner-directed research plans, not findings. Claims are proposed hypotheses. There is no seeded Evidence, Run, supported Claim, or baseline. A run never creates Evidence automatically.

## Contribution path

Search existing objects before creating new ones. Add one YAML file per distinct object; generate its ID with `dawn id new <KIND>`. Keep relations separate and state whether they are semantic or intellectual provenance. Add scope to Claims, provenance to Evidence, and exact revisions to Runs. Submit changes through Git review; `dawn validate` and tests are CI gates. [AGENTS.md](AGENTS.md) is the contributor protocol.

The new repository is Apache-2.0. DAWN-SRW remains a separately licensed, pinned implementation dependency; no legacy code was copied here.
