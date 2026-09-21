# Reproducibility chain

`Exploration → Probe → capability resolution → pinned provider repositories → environment → resource profile → input artifact digest → Run → Evidence → Claim relation`.

`dawn resolve <X-ID> --profile tpu-v4-8 --json` gives a deterministic plan with exact provider commits. Local execution readiness requires local paths for required artifacts; remote retrieval is not implemented. A separate public-reproducibility flag requires public artifacts and validated infrastructure. Missing capabilities, the executable Probe, entrypoint or hashed environment lockfile block execution. `dawn run` requires clean research and implementation checkouts, then uses a fresh offline Run ID, an exclusive run directory, a hashed config snapshot, pinned Git revisions, provider interface versions and input artifact digests. It records timestamps, executor, command template, outputs, status and failure reason; interrupted runs remain marked cancelled. The `artifact:<ID>` token in the recorded command represents the local path supplied at invocation; its digest is frozen and checked again after execution. This avoids placing a personal machine path in a public manifest. The evaluator's software versions, dataset fingerprints and native manifest digest are copied into the Run manifest after a successful smoke execution. The hardware class remains a declared profile until independently verified. Raw stdout, stderr and evaluator outputs remain local until reviewed.

The first planned executable path is the frozen six-task DAWN-SRW zero-shot evaluator. Its stock tasks are LAMBADA, HellaSwag, PIQA, ARC Easy, ARC Challenge and WinoGrande. `--limit 32` is a smoke test only and is never comparable to a full evaluation. This path does not establish free-form generation behavior; that requires its separately proposed Probe. The current repository has no checkpoint or exact TPU environment lock, so a research smoke Run cannot honestly be produced yet.

After a concrete checkpoint is obtained and its registry record and environment lock are completed, the intended command on a compatible TPU host is:

```bash
dawn run <X-ID> --profile tpu-v4-8 --legacy-repo <PINNED_DAWN_SRW_CHECKOUT> \
  --artifact <CHECKPOINT_ARTIFACT_ID>=<LOCAL_COMMITTED_ORBAX_STEP> \
  --executor github:<username> --limit 32
```

The current IDs are in `explorations/` and `artifacts/registry/`; use `dawn explore` and `dawn show`. The evaluator's own manifest and metrics remain under the Run output directory. A Run alone is execution provenance. To support a Claim, a researcher must write scoped Evidence referring to Run IDs, submit it for review, and add an accepted `supports` Relation. A negative result follows the same path. Invalidations preserve the original Run and reason.

Publication convention: live Git graph → frozen tag/release → archival DOI when available. A future Publication manifest can freeze selected objects, Runs, implementation commits, environment and artifact hashes; v0 does not mint a DOI.
