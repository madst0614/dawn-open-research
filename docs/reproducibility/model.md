# Reproducibility chain

`Study → Method → capability resolution → pinned provider repositories → environment → resource profile → input artifact digest → Run → Result → reviewed Connection → Claim`.

`dawn resolve <STUDY_ID> --profile tpu-v4-8 --json` returns a deterministic plan with exact provider commits. Local execution readiness requires local paths for required artifacts; remote retrieval is not implemented. Public reproducibility additionally requires public artifacts and validated providers, environment, and profile. Missing capabilities, the executable Method, entrypoint, exact environment lock, or artifact bytes block execution.

`dawn run` requires clean research and implementation checkouts. It creates a fresh offline Run ID and exclusive directory, writes a hashed configuration snapshot, and freezes Git revisions, provider interface versions, environment identity, profile identity, and input artifact digests. It records timestamps, executor, command template, outputs, status, and failure or invalidation reason. Interrupted Runs remain marked `cancelled`.

The `artifact:<ID>` token in the recorded command represents the local path supplied at invocation; its digest is frozen and checked again after execution. The evaluator's software versions, dataset fingerprints, and native manifest digest are copied into a successful Run. Hardware remains declared by the profile until independently verified. Raw stdout, stderr, and evaluator outputs remain local until reviewed.

The first executable path is the frozen six-task DAWN-SRW zero-shot evaluator. Its stock tasks are LAMBADA, HellaSwag, PIQA, ARC Easy, ARC Challenge, and WinoGrande. `--limit 32` is a smoke test only and is not comparable to a full evaluation. Autoregressive generation has a separate Study and remains non-executable until its own implementation, prompts, and decoding settings are specified.

The repository currently has no checkpoint or exact TPU environment lock, so a scientific Run cannot honestly be produced. After those dependencies are completed, the intended command on a compatible TPU host is:

```bash
dawn run <STUDY_ID> --profile tpu-v4-8 \
  --implementation-repo <PINNED_DAWN_SRW_CHECKOUT> \
  --artifact <CHECKPOINT_ARTIFACT_ID>=<LOCAL_COMMITTED_ORBAX_STEP> \
  --executor github:<username> --limit 32
```

A successful Run records execution provenance but never creates a Result automatically. A researcher reviews the outcome, authors a Result with explicit scope and limitations, and proposes a Connection to each relevant Claim. Negative outcomes follow the same path. Invalidations preserve the original Run and reason.

Publication convention: live Git graph → frozen tag or release → archival DOI when available. A Publication manifest can freeze selected objects, Runs, implementation commits, environment locks, and artifact hashes; v1 does not mint a DOI.
