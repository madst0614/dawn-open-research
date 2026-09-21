# DAWN-SRW infrastructure inventory

Read-only inspection on 2026-09-21. Local checkout HEAD `30165201e68897d75f0586805d321393159550c3`, branch `main`, remote `https://github.com/madst0614/DAWN-SRW.git`, `git status --porcelain` empty. The remote identifies a public repository, but this audit used the local checkout. MIT license is present. There are 557 tracked files and 16 `test_*.py` files. No code or files were changed in that repository.

## Execution inventory

| Area | Verified path and observation | Reuse class |
|---|---|---|
| Python/dependencies | `setup.py` describes an older PyTorch package and reads a missing root `README.md`; `requirements.txt` is broad, `requirements_tpu.txt` uses lower bounds, and `requirements_zero_shot_eval.txt` pins lm-eval 0.4.2, Orbax 0.11.24 and several evaluator dependencies. No complete JAX/TPU lock was found. | E: environment decision and lock needed |
| Configuration | `scripts/train_jax.py::load_config` reads YAML with `yaml.safe_load`; numerous versioned training/evaluation configs exist under `configs/`. | A for pinned references; B for a shared config adapter later |
| Model | `models/dawn_srw_v4172.py` and adjacent versioned JAX models, selected through `scripts/train_jax.py` and `models/version_registry.py`. | C: DAWN model implementation stays in legacy repo |
| Trainer | `scripts/train_jax.py::main` is the canonical large JAX trainer, with version dispatch and optimizer/training loops. | B: generic pieces may be refactored after a scoped need; no bulk migration |
| Checkpoint save/load | `scripts/train_jax.py` uses Orbax CheckpointManager; `scripts/zero_shot_eval_jax.py` resolves a concrete committed step and restores parameters/metadata. `utils/checkpoint.py` is an older PyTorch migration helper. | A for evaluator's pinned Orbax path; E for older PyTorch helper |
| Generation | `dawn/eval/lm_eval_dawn_adapter.py::generate_until` exists; `scripts/legacy/generate_samples.py` is an older generation script. A current standalone fixed-prompt sampling protocol was not verified. | A for adapter reference; E for sample script |
| Validation | `scripts/c4_validation_eval_jax.py` evaluates packed C4 validation on a committed checkpoint; zero-shot evaluator also performs a validation CE cross-check. | A through pinned reference |
| Zero-shot evaluation | `scripts/zero_shot_eval_jax.py` and `dawn/eval/{zero_shot_protocol,lm_eval_dawn_adapter,jax_runtime}.py`; documented in `docs/zero_shot_eval.md`. Six stock tasks: LAMBADA, HellaSwag, PIQA, ARC Easy/Challenge, WinoGrande. Smoke `--limit` is explicitly non-comparable. | A: first local adapter target |
| Analysis | `scripts/analysis/`, `scripts/analyze_train_analysis_pool.py`, interpretability tests and paper configs exist. | B: select a scoped tool after a Probe is specified |
| Logging/metrics | Trainer writes text logs and `metrics_*.jsonl` through `GCSLogger`; evaluator writes summary JSON/CSV, raw results, samples JSONL, manifest and log. | A for native evaluator outputs; B for future normalized artifact ingestion |
| JAX/TPU init | `scripts/train_jax.py::_maybe_initialize_jax_distributed`; evaluator calls it before checkpoint/model setup. Mesh shape is checked against checkpoint metadata. | A via evaluator; no copied runtime code |
| Distributed/multi-host | `jax.distributed.initialize()` with Cloud TPU discovery, `jax.process_index()` barriers and host coordination in trainer/evaluator. | A by reference; multi-host launcher not exposed in v0 |
| Launch scripts | `scripts/launch_zero_shot_eval_tpu_pod.sh`, `scripts/launch_tpu_pod.sh` and other TPU pod scripts. Launchers include machine/project defaults and token options. | B: sanitize and parameterize before public reuse |
| Benchmarks | `scripts/benchmark_srw_tpu.py`, `scripts/profile_paper_compute_support.py`, paper FLOP accounting tools. | B: future systems Probe adapters, not first slice |
| Tests | 16 Python test files include zero-shot protocol, lm-eval adapter/stock tasks, minimal pretraining, operator behavior and interpretability CPU tests. | A as upstream verification, not duplicated here |
| Artifacts | Tracked paper support JSON exists under `assets/paper/`; checkpoint references appear in configs/docs. No local Orbax checkpoint bytes or committed concrete step were found in the checkout. | E: checkpoint identity, access and digest unresolved |

Classes: **A** use through a pinned reference/adapter; **B** migrate or refactor only when needed; **C** model-specific implementation; **D** obsolete; **E** unclear or awaiting a decision. No component was conclusively marked D from this read-only audit.

## Reproducibility and publication risks

- The checkpoint required by the first research Probe was not present locally. Registry/config references do not prove public download access or content identity. Its Artifact is marked `missing` with no invented hash.
- TPU requirements use lower bounds for JAX and related packages. The evaluator pins several dependencies, but the combined runtime is not locked, so the Environment has no lock digest.
- TPU hardware, sharding and checkpoint mesh compatibility have not been validated in this bootstrap. Providers and profile are `experimental`, with no verification Run.
- Many configs and launchers contain hard-coded storage, cloud project or machine paths. Some launchers accept tokens. None of those values were copied into public manifests. Review such files before any migration or publication.
- Remote datasets, GCS checkpoints and cloud services may require access or credentials. Public availability was not independently established.
- The legacy `setup.py` description and missing README make it unsuitable as a reproducible package entrypoint without work. The pinned evaluator script is the narrower entrypoint.
- Existing paper JSON and historical analysis were not converted into Evidence; that requires protocol and provenance review.

No `.env`, credentials, logs, caches, checkpoint bytes, virtual environments, legacy configs, model code or trainer code were migrated.
