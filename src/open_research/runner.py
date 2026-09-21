"""One-run executor and immutable provenance capture for the legacy evaluator."""

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .ids import new_id
from .models import Exploration, InfrastructureProvider, RepositoryRef, Run
from .resolver import resolve
from .store import validate_catalog


def hash_path(path: Path) -> str:
    path = path.resolve()
    if not path.exists():
        raise ValueError(f"missing artifact path: {path}")
    digest = hashlib.sha256()
    files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
    if not files:
        raise ValueError("artifact path contains no files")
    for file in files:
        relative = file.name if path.is_file() else file.relative_to(path).as_posix()
        digest.update(relative.encode("utf-8") + b"\0")
        with file.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True)
    return completed.stdout.strip()


def _git_identity(repo: Path) -> tuple[str, bool]:
    return _git(repo, "rev-parse", "HEAD"), bool(_git(repo, "status", "--porcelain"))


def _write_manifest(path: Path, run: Run) -> None:
    staging = path.with_suffix(".tmp")
    staging.write_text(yaml.safe_dump(run.model_dump(mode="json"), sort_keys=False, allow_unicode=True), encoding="utf-8")
    staging.replace(path)


def execute(catalog, exploration_id: str, profile: str, legacy_repo: Path,
            artifact_paths: dict[str, Path], executor: str, limit: int = 32) -> Run:
    errors = validate_catalog(catalog)
    if errors:
        raise ValueError("cannot execute an invalid research tree: " + "; ".join(errors))
    plan = resolve(catalog, exploration_id, profile, artifact_paths)
    if not plan["ready"]:
        raise ValueError("Run blocked: " + "; ".join(plan["blockers"]))
    exploration = catalog.get(exploration_id, Exploration)
    if exploration.entrypoint != "legacy.zero_shot_eval_jax@1":
        raise ValueError(f"unsupported entrypoint: {exploration.entrypoint}")
    if len(exploration.requires.artifacts) != 1:
        raise ValueError("zero-shot adapter expects one checkpoint artifact")
    legacy_repo = legacy_repo.resolve()
    implementation_revision, implementation_dirty = _git_identity(legacy_repo)
    research_revision, research_dirty = _git_identity(catalog.root)
    if implementation_dirty or research_dirty:
        raise ValueError("exact revision freeze requires clean research and implementation repositories")
    if len({item["repository_id"] for item in plan["providers"]}) != 1:
        raise ValueError("legacy adapter can execute providers from only one implementation repository")
    provider_ids = sorted({item["id"] for item in plan["providers"]})
    frozen_providers = []
    for provider_id in provider_ids:
        provider = catalog.get(provider_id, InfrastructureProvider)
        repo = catalog.get(provider.repository_id, RepositoryRef)
        planned_revision = next(item["revision"] for item in plan["providers"] if item["id"] == provider_id)
        if implementation_revision != repo.revision or planned_revision != repo.revision:
            raise ValueError(f"legacy repository HEAD differs from pinned {repo.revision}")
        frozen_providers.append({"provider_id": provider.id, "interface_version": provider.interface_version,
                                 "repository_id": repo.id, "revision": implementation_revision,
                                 "dirty": implementation_dirty})
    artifact_id = exploration.requires.artifacts[0]
    checkpoint = artifact_paths.get(artifact_id)
    if checkpoint is None:
        raise ValueError("local checkpoint path must be supplied")
    checkpoint = checkpoint.resolve()
    artifact_digest = hash_path(checkpoint)
    run_id = new_id(catalog.program.namespace, "RUN")
    run_dir = catalog.root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "outputs").mkdir()
    config = {"exploration_id": exploration.id, "profile_id": plan["profile_id"],
              "artifact_id": artifact_id, "artifact_digest": artifact_digest,
              "tasks": ["lambada_openai", "hellaswag", "piqa", "arc_easy", "arc_challenge", "winogrande"],
              "limit": limit, "seed": 1234}
    config_bytes = (json.dumps(config, sort_keys=True, separators=(",", ":")) + "\n").encode()
    (run_dir / "config.json").write_bytes(config_bytes)
    command = ["python", "scripts/zero_shot_eval_jax.py", "--init-from", f"artifact:{artifact_id}",
               "--output-dir", "outputs", "--limit", str(limit), "--seed", "1234"]
    now = datetime.now(timezone.utc)
    run = Run(id=run_id, created_by=executor, created_at=now,
              exploration_id=exploration.id, probe_id=exploration.entrypoint_probe_id,
              research_revision=research_revision, research_dirty=research_dirty,
              implementations=frozen_providers, environment_id=plan["environment_id"],
              environment_lock_digest=plan["environment_lock_digest"],
              profile_id=plan["profile_id"],
              hardware_class=f"declared {catalog.get(plan['profile_id']).hardware_class}",
              input_artifacts=[{"artifact_id": artifact_id, "digest": artifact_digest,
                                "location": f"artifact:{artifact_id}"}],
              config_digest="sha256:" + hashlib.sha256(config_bytes).hexdigest(),
              config_path="config.json", seed=1234, command=command,
              executor=executor, started_at=now, status="created")
    manifest = run_dir / "manifest.yaml"
    _write_manifest(manifest, run)
    actual_command = [sys.executable, str(legacy_repo / "scripts" / "zero_shot_eval_jax.py"),
                      "--init-from", str(checkpoint), "--output-dir", str(run_dir / "outputs"),
                      "--limit", str(limit), "--seed", "1234"]
    cache_dir = run_dir / "outputs" / "cache"
    tmp_dir = run_dir / "outputs" / "tmp"
    cache_dir.mkdir()
    tmp_dir.mkdir()
    child_env = os.environ.copy()
    child_env.update({"PYTHONDONTWRITEBYTECODE": "1", "HF_HOME": str(cache_dir),
                      "XDG_CACHE_HOME": str(cache_dir), "TMP": str(tmp_dir), "TEMP": str(tmp_dir)})
    run.status = "running"
    _write_manifest(manifest, run)
    try:
        with (run_dir / "stdout.log").open("w", encoding="utf-8") as stdout, (run_dir / "stderr.log").open("w", encoding="utf-8") as stderr:
            completed = subprocess.run(actual_command, cwd=legacy_repo, env=child_env,
                                       stdout=stdout, stderr=stderr, check=False)
        if completed.returncode:
            run.status = "failed"
            run.error = f"legacy evaluator exited {completed.returncode}; see stderr.log"
        else:
            native_path = run_dir / "outputs" / "run_manifest.json"
            if not native_path.exists():
                run.status = "failed"
                run.error = "legacy evaluator returned success without run_manifest.json"
            else:
                native_bytes = native_path.read_bytes()
                native = json.loads(native_bytes)
                if native.get("dawn_git_commit") != implementation_revision:
                    run.status = "failed"
                    run.error = "legacy evaluator reported a different implementation commit"
                elif native.get("working_tree_clean") is not (not implementation_dirty):
                    run.status = "failed"
                    run.error = "legacy evaluator working-tree state differs from frozen provenance"
                elif native.get("tasks") != config["tasks"] or native.get("limit") != limit or native.get("smoke_test_only") is not True:
                    run.status = "failed"
                    run.error = "legacy evaluator protocol differs from requested smoke config"
                elif not native.get("software_versions") or not native.get("dataset_fingerprints_revisions"):
                    run.status = "failed"
                    run.error = "legacy evaluator manifest lacks software or dataset provenance"
                else:
                    run.status = "completed"
                    run.native_manifest_digest = "sha256:" + hashlib.sha256(native_bytes).hexdigest()
                    run.software_versions = native["software_versions"]
                    run.dataset_provenance = native["dataset_fingerprints_revisions"]
                    run.params_hash = native.get("params_hash")
                    run.hardware_observation = {
                        key: int(native[key]) for key in ("global_device_count", "local_device_count", "host_count")
                        if key in native}
        if hash_path(checkpoint) != artifact_digest:
            run.status = "failed"
            run.error = (run.error + "; " if run.error else "") + "input Artifact changed during execution"
    except KeyboardInterrupt:
        run.status = "cancelled"
        run.error = "execution interrupted"
    except Exception as exc:
        run.status = "failed"
        run.error = f"evaluator or output error: {type(exc).__name__}: {exc}"
    run.ended_at = datetime.now(timezone.utc)
    run.outputs = ["stdout.log", "stderr.log", "outputs"]
    _write_manifest(manifest, run)
    return run
