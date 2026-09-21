"""Conservative, deterministic capability and artifact resolution."""

from hashlib import sha256
from pathlib import Path

from .models import Artifact, Environment, Exploration, InfrastructureProvider, RepositoryRef, ResourceProfile, Run

RANK = {"validated": 0, "available": 1, "experimental": 2}


def _lock_problem(catalog, environment: Environment) -> str | None:
    if not environment.lock_digest or not environment.lockfile:
        return f"environment {environment.id} lacks an exact lockfile and digest"
    relative = Path(environment.lockfile)
    if relative.is_absolute() or ".." in relative.parts:
        return f"environment {environment.id} lockfile path is unsafe"
    lock = (catalog.root / relative).resolve()
    if not lock.is_relative_to(catalog.root.resolve()):
        return f"environment {environment.id} lockfile path is unsafe"
    if not lock.is_file():
        return f"environment {environment.id} lockfile is missing"
    if "sha256:" + sha256(lock.read_bytes()).hexdigest() != environment.lock_digest:
        return f"environment {environment.id} lockfile digest mismatch"
    return None


def _provider_usable(catalog, provider: InfrastructureProvider) -> bool:
    if provider.status not in RANK:
        return False
    if provider.status == "validated":
        return any(isinstance(catalog.objects.get(run_id), Run)
                   and catalog.objects[run_id].status == "completed"
                   and any(frozen.provider_id == provider.id
                           for frozen in catalog.objects[run_id].implementations)
                   for run_id in provider.verification_run_ids)
    return True


def _quality(providers: dict[str, InfrastructureProvider], environment: Environment) -> tuple:
    # Compare the weakest capability first, then environment status and stable ID.
    return (tuple(sorted((RANK[p.status] for p in providers.values()), reverse=True)),
            RANK[environment.status], environment.id)


def resolve(catalog, exploration_id: str, profile_key: str, artifact_paths: dict[str, Path] | None = None) -> dict:
    exploration = catalog.get(exploration_id, Exploration)
    profiles = [profile for profile in catalog.of_type(ResourceProfile)
                if profile.id == profile_key or profile.name == profile_key]
    if len(profiles) != 1:
        raise ValueError(f"unknown or ambiguous profile: {profile_key}")
    profile = profiles[0]
    if exploration.profile_ids and profile.id not in exploration.profile_ids:
        raise ValueError(f"profile {profile.name} is not supported by {exploration.id}")
    artifact_paths = artifact_paths or {}
    unknown_artifacts = set(artifact_paths) - set(exploration.requires.artifacts)
    if unknown_artifacts:
        raise ValueError(f"artifact paths not required by Exploration: {sorted(unknown_artifacts)}")

    capabilities = sorted(set(exploration.requires.capabilities))
    candidates = []
    for environment_id in sorted(profile.environment_ids):
        environment = catalog.objects.get(environment_id)
        if not isinstance(environment, Environment) or environment.status == "broken":
            continue
        selected = {}
        missing = []
        for capability in capabilities:
            providers = [provider for provider in catalog.of_type(InfrastructureProvider)
                         if capability in provider.capabilities
                         and environment_id in provider.environment_ids
                         and profile.id in provider.profile_ids
                         and _provider_usable(catalog, provider)]
            if providers:
                selected[capability] = min(providers, key=lambda p: (RANK[p.status], p.id))
            else:
                missing.append(capability)
        candidates.append((environment, selected, missing, _lock_problem(catalog, environment)))

    viable = [candidate for candidate in candidates if not candidate[2] and not candidate[3]]
    if viable:
        environment, selected, missing, lock_problem = min(
            viable, key=lambda c: _quality(c[1], c[0]))
    elif candidates:
        environment, selected, missing, lock_problem = min(
            candidates, key=lambda c: (len(c[2]) + bool(c[3]), _quality(c[1], c[0])))
    else:
        environment, selected, missing, lock_problem = None, {}, capabilities, "no compatible environment for profile"

    fundamental_blockers = [f"missing compatible capability: {capability}" for capability in missing]
    if lock_problem:
        fundamental_blockers.append(lock_problem)
    if not exploration.entrypoint:
        fundamental_blockers.append("Exploration has no entrypoint")
    if not exploration.entrypoint_probe_id:
        fundamental_blockers.append("Exploration has no executable Probe")

    warnings = []
    if profile.status == "experimental":
        warnings.append(f"profile {profile.id} has not been validated by a Run")
    for provider in {provider.id: provider for provider in selected.values()}.values():
        if provider.status != "validated":
            warnings.append(f"provider {provider.id} is {provider.status}")

    artifacts = []
    local_blockers = []
    public_artifacts = True
    for artifact_id in exploration.requires.artifacts:
        artifact = catalog.objects.get(artifact_id)
        if not isinstance(artifact, Artifact):
            local_blockers.append(f"missing artifact: {artifact_id}")
            artifacts.append({"id": artifact_id, "availability": "missing"})
            public_artifacts = False
            continue
        is_public = artifact.availability == "public" and bool(artifact.uri and artifact.digest)
        public_artifacts &= is_public
        override = artifact_paths.get(artifact_id)
        if override is not None:
            if not override.exists():
                local_blockers.append(f"artifact {artifact_id} path does not exist")
                artifacts.append({"id": artifact_id, "availability": "missing"})
                public_artifacts = False
                continue
            from .runner import hash_path
            digest = hash_path(override)
            if artifact.digest and artifact.digest != digest:
                local_blockers.append(f"artifact {artifact_id} digest mismatch")
                public_artifacts = False
            artifacts.append({"id": artifact_id, "availability": "local", "digest": digest})
        elif is_public:
            artifacts.append({"id": artifact_id, "availability": "public", "digest": artifact.digest,
                              "uri": artifact.uri})
            local_blockers.append(f"artifact {artifact_id} needs a local path; remote retrieval is not implemented")
        else:
            local_blockers.append(f"artifact {artifact_id} is {artifact.availability} or has no digest")
            artifacts.append({"id": artifact_id, "availability": artifact.availability})

    provider_repositories_public = all(
        isinstance(catalog.objects.get(provider.repository_id), RepositoryRef)
        and catalog.objects[provider.repository_id].status == "public"
        for provider in selected.values())
    public_ready = (not fundamental_blockers and public_artifacts
                    and provider_repositories_public
                    and all(provider.status == "validated" for provider in selected.values())
                    and environment is not None and environment.status == "validated"
                    and profile.status == "validated")
    blockers = sorted(set(fundamental_blockers + local_blockers))
    return {
        "exploration_id": exploration.id,
        "profile_id": profile.id,
        "environment_id": environment.id if environment else None,
        "environment_lock_digest": environment.lock_digest if environment else None,
        "providers": [{"capability": cap, "id": provider.id, "status": provider.status,
                       "interface_version": provider.interface_version,
                       "repository_id": provider.repository_id,
                       "revision": catalog.get(provider.repository_id, RepositoryRef).revision}
                      for cap, provider in sorted(selected.items())],
        "artifacts": artifacts,
        "warnings": sorted(set(warnings)),
        "blockers": blockers,
        "ready": not blockers,
        "publicly_reproducible": public_ready,
    }


def readiness(catalog, exploration: Exploration) -> tuple[str, list[str]]:
    if exploration.lifecycle in {"completed", "superseded"}:
        return exploration.lifecycle, []
    if not exploration.profile_ids or not exploration.entrypoint_probe_id or not exploration.entrypoint:
        state = "blocked" if exploration.lifecycle == "blocked" else "draft"
        return state, list(exploration.blockers)
    try:
        plans = [resolve(catalog, exploration.id, profile) for profile in exploration.profile_ids]
    except ValueError as exc:
        return "blocked", [str(exc)]
    if any(plan["publicly_reproducible"] for plan in plans):
        return "public", []
    if any(plan["ready"] for plan in plans):
        return "local", []
    return "blocked", sorted(set(exploration.blockers + [item for plan in plans for item in plan["blockers"]]))
