# DAWN TRC research plan

## Research program

DAWN-SRW investigates language-model computation through persistent reusable operators and state-conditioned selection. The proposed TRC program begins with qualification of the existing reference model, then pursues two parallel research tracks: a shared conditional-space routing architecture (Track A) and analysis of semantic computational geometry and hardware locality in the current architecture (Track B). Track A is an architecture candidate; Track B can start from existing DAWN-SRW and does not depend on Track A succeeding.

## Prior work / feasibility

- [DAWN-SRW GitHub repository](https://github.com/madst0614/DAWN-SRW)
- [DAWN Open Research GitHub repository](https://github.com/madst0614/dawn-open-research)
- TODO: add verified prior Zenodo record
- TODO: add verified public manuscript/results link

The program starts from an existing implementation, project-reported trained models and quantitative results, prior JAX/TPU-oriented work, and public open-research infrastructure rather than a new speculative code base. DOR nevertheless records no grounded Result yet, and the reference checkpoint location, digest and reproducible runtime lock remain qualification blockers; earlier project evidence will not be promoted into a DOR Result without reviewable grounding.

## P0 — generation qualification

The existing `Reference checkpoint language validation` Study (`DAWN-ST-01M3E4R072V5NE73SPQY5GZNHM`) is the qualification gate. Frozen stock zero-shot evaluation provides an integrity and sanity check. Deterministic autoregressive generation is the first execution priority once compute and reproducibility blockers are resolved: exact checkpoint, tokenizer and configuration integrity; a versioned prompt suite; greedy decoding; numerical and repetition checks; repeatability; preserved samples and manifests; and explicit review are required before any Result is authored. Existing quantitative language-model behavior has been explored at project level, but free generation has not been grounded in DOR.

## Track A — shared conditional-space routing

The `Shared conditional-space routing architecture` Study (`DAWN-ST-01M3HVE2DH7NKX400ZHM0ZJMS6`) asks whether model state and operator computational role can be projected into a common low-dimensional coordinate and routed by compatibility there without material loss of language-model quality. The exact state encoder, operator-role representation, projection sharing, compatibility function and dimension remain open pending a pinned implementation audit. A credible test requires small-scale sanity checks followed by matched reference/candidate retraining with controlled data, optimizer, token budget, scale and evaluation, while explicitly reporting unavoidable parameter and FLOP differences. This makes accelerator compute necessary, but no improvement is assumed.

## Track B — semantic computational geometry / hardware locality

The private Packet has already been ingested through the repository's archive-and-trace workflow. Its canonical program reuses existing visibility, logical-locality and sparse-execution Questions and Studies and adds only missing bounded objects. The current Studies are:

- `Conditional compactness and operator visibility` (`DAWN-ST-01M3E4R072RVFWWHQWAZYR59ZX`): effective low-dimensional organization and visibility requirements.
- `Computational geometry and semantic locality` (`DAWN-ST-01M3E4R072JTK7TK826BPZZ098`): implementation-grounded coordinates, functional similarity and causal intervention.
- `Hierarchical computational-address simulation` (`DAWN-ST-01M3HRPC1V7GEEFZRF3F5QXYSY`): ownership, lookup, recall, boundary behavior and fan-out before physical execution.
- `Dynamic computational-index maintenance` (`DAWN-ST-01M3HRPC1VYGRFAWKE4H1A4CPJ`): drift, refresh policy and safe maintenance during training.
- `Physical sparse execution` (`DAWN-ST-01M3E4R072GR45VJ05KXCRXS04`) and `TPU sparse RW execution` (`DAWN-ST-01M3E4R072CEAYSMS6T1AV9MZY`): later realized efficiency and TPU-native evaluation.

Track B begins with the current architecture. If Track A later produces a qualified candidate, equivalent locality Methods may be applied for comparison; this is a later comparison, not a dependency or an asserted Relation.

## Why TPU / TRC

The existing research stack is JAX/TPU-oriented. Track A requires matched retraining and multiple architecture, dimension and ablation runs rather than inference-only inspection. Track B can conserve accelerator allocation through repository audit and CPU/offline index simulation, but later causal, training-trajectory, sparse-kernel and physical-locality tests require TPU-native execution and multi-device measurements. TRC access would make the staged comparisons possible while keeping expensive systems experiments conditional on earlier evidence.

## Compute staging

1. **Stage 1 — reference qualification:** restore and integrity checks, zero-shot smoke evaluation, and deterministic generation qualification on the smallest appropriate TPU profile.
2. **Stage 2 — small-scale architecture validation:** implement Track A sanity models and run matched small-scale training sweeps; in parallel, perform Track B audit and offline geometry/index simulations where possible.
3. **Stage 3 — main-scale evidence:** run justified matched Track A training and the Track B locality analyses that require grounded checkpoints or training trajectories.
4. **Stage 4 — physical locality:** attempt multi-device and TPU-native sparse/local execution only when earlier quality, geometry, recall and causal gates justify it.

Exact TPU types, topology and hours remain to be estimated from pinned implementations and pilot measurements; none are claimed here.

## Expected public outputs

- Canonical DOR Questions, Claims, Methods, Studies, Relations, Runs and grounded Results.
- DAWN-SRW code and configuration updates when scientifically justified and separately reviewed.
- Checkpoints, configurations and logs where licensing, privacy and storage permit.
- A public manuscript or technical report and reproducibility documentation.
- Practical TPU implementation and performance feedback, including negative outcomes.

## Decision gates

- P0 must establish a recoverable, integrity-checked reference and reviewable language behavior before it is used as a comparison anchor.
- Track A advances from sanity scale to main-scale training only if implementation checks and matched pilot behavior justify the expense.
- Track B advances from audit and simulation to causal or physical execution only if coordinates, metrics, retrieval rules and correctness thresholds are grounded.
- Multi-device physical-locality work proceeds only after quality preservation and useful selectivity or recall are demonstrated.
- Failed or negative runs are preserved; no gate automatically creates a Result, supports a Claim or resolves a Question.
