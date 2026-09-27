"""Conservative, deterministic Method-specific execution resolution."""

from hashlib import sha256
from pathlib import Path

from .models import (
    Artifact,
    Environment,
    ExecutionPlan,
    InfrastructureProvider,
    RepositoryRef,
    ResourceProfile,
    Run,
    Study,
)


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
        return any(
            isinstance(catalog.objects.get(run_id), Run)
            and catalog.objects[run_id].status == "completed"
            and any(
                frozen.provider_id == provider.id
                for frozen in catalog.objects[run_id].implementations
            )
            for run_id in provider.verification_run_ids
        )
    return True


def _quality(providers: dict[str, InfrastructureProvider], environment: Environment) -> tuple:
    return (
        tuple(sorted((RANK[provider.status] for provider in providers.values()), reverse=True)),
        RANK[environment.status],
        environment.id,
    )


def select_execution_plan(study: Study, method_id: str | None = None) -> ExecutionPlan:
    """Select one execution plan, failing closed when Method choice is ambiguous."""

    if method_id is not None:
        matches = [plan for plan in study.execution.plans if plan.method_id == method_id]
        if len(matches) != 1:
            if method_id not in study.method_ids:
                raise ValueError(f"Method {method_id} is not part of Study {study.id}")
            raise ValueError(f"Method {method_id} has no execution plan in Study {study.id}")
        return matches[0]

    executable = [plan for plan in study.execution.plans if plan.entrypoint]
    if not executable:
        raise ValueError(
            f"Study {study.id} has no executable Method; pass --method to inspect a planned Method"
        )
    if len(executable) > 1:
        choices = sorted(plan.method_id for plan in executable)
        raise ValueError(
            f"Study {study.id} has ambiguous executable Methods {choices}; pass --method"
        )
    return executable[0]


def resolve(
    catalog,
    study_id: str,
    profile_key: str,
    artifact_paths: dict[str, Path] | None = None,
    method_id: str | None = None,
) -> dict:
    study = catalog.get(study_id, Study)
    execution_plan = select_execution_plan(study, method_id)
    profiles = [
        profile
        for profile in catalog.of_type(ResourceProfile)
        if profile.id == profile_key or profile.name == profile_key
    ]
    if len(profiles) != 1:
        raise ValueError(f"unknown or ambiguous profile: {profile_key}")
    profile = profiles[0]
    if profile.id not in execution_plan.profile_ids:
        raise ValueError(
            f"profile {profile.name} is not supported by Method {execution_plan.method_id} "
            f"in Study {study.id}"
        )

    artifact_paths = artifact_paths or {}
    required_artifacts = execution_plan.requires.artifacts
    unknown_artifacts = set(artifact_paths) - set(required_artifacts)
    if unknown_artifacts:
        raise ValueError(
            f"artifact paths not required by the selected Study Method: {sorted(unknown_artifacts)}"
        )

    capabilities = sorted(set(execution_plan.requires.capabilities))
    candidates = []
    for environment_id in sorted(profile.environment_ids):
        environment = catalog.objects.get(environment_id)
        if not isinstance(environment, Environment) or environment.status == "broken":
            continue
        selected = {}
        missing = []
        for capability in capabilities:
            providers = [
                provider
                for provider in catalog.of_type(InfrastructureProvider)
                if capability in provider.capabilities
                and environment_id in provider.environment_ids
                and profile.id in provider.profile_ids
                and _provider_usable(catalog, provider)
            ]
            if providers:
                selected[capability] = min(
                    providers, key=lambda item: (RANK[item.status], item.id)
                )
            else:
                missing.append(capability)
        candidates.append((environment, selected, missing, _lock_problem(catalog, environment)))

    viable = [candidate for candidate in candidates if not candidate[2] and not candidate[3]]
    if viable:
        environment, selected, missing, lock_problem = min(
            viable, key=lambda item: _quality(item[1], item[0])
        )
    elif candidates:
        environment, selected, missing, lock_problem = min(
            candidates,
            key=lambda item: (len(item[2]) + bool(item[3]), _quality(item[1], item[0])),
        )
    else:
        environment, selected, missing, lock_problem = (
            None,
            {},
            capabilities,
            "no compatible environment for profile",
        )

    fundamental_blockers = [
        f"missing compatible capability: {capability}" for capability in missing
    ]
    if lock_problem:
        fundamental_blockers.append(lock_problem)
    if not execution_plan.entrypoint:
        fundamental_blockers.append(
            f"Method {execution_plan.method_id} has no execution entrypoint"
        )
    fundamental_blockers.extend(execution_plan.blockers)

    warnings = []
    if profile.status == "experimental":
        warnings.append(f"profile {profile.id} has not been validated by a Run")
    for provider in {item.id: item for item in selected.values()}.values():
        if provider.status != "validated":
            warnings.append(f"provider {provider.id} is {provider.status}")

    artifacts = []
    local_blockers = []
    public_artifacts = True
    for artifact_id in required_artifacts:
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
            artifacts.append(
                {
                    "id": artifact_id,
                    "availability": "public",
                    "digest": artifact.digest,
                    "uri": artifact.uri,
                }
            )
            local_blockers.append(
                f"artifact {artifact_id} needs a local path; remote retrieval is not implemented"
            )
        else:
            local_blockers.append(
                f"artifact {artifact_id} is {artifact.availability} or has no digest"
            )
            artifacts.append({"id": artifact_id, "availability": artifact.availability})

    provider_repositories_public = all(
        isinstance(catalog.objects.get(provider.repository_id), RepositoryRef)
        and catalog.objects[provider.repository_id].status == "public"
        for provider in selected.values()
    )
    public_ready = (
        not fundamental_blockers
        and public_artifacts
        and provider_repositories_public
        and all(provider.status == "validated" for provider in selected.values())
        and environment is not None
        and environment.status == "validated"
        and profile.status == "validated"
    )
    blockers = sorted(set(fundamental_blockers + local_blockers))
    return {
        "study_id": study.id,
        "method_id": execution_plan.method_id,
        "entrypoint": execution_plan.entrypoint,
        "profile_id": profile.id,
        "required_capabilities": capabilities,
        "required_artifacts": list(required_artifacts),
        "expected_outputs": list(execution_plan.expected_outputs),
        "declared_readiness": execution_plan.declared_readiness,
        "environment_id": environment.id if environment else None,
        "environment_lock_digest": environment.lock_digest if environment else None,
        "providers": [
            {
                "capability": capability,
                "id": provider.id,
                "status": provider.status,
                "interface_version": provider.interface_version,
                "repository_id": provider.repository_id,
                "revision": catalog.get(provider.repository_id, RepositoryRef).revision,
            }
            for capability, provider in sorted(selected.items())
        ],
        "artifacts": artifacts,
        "warnings": sorted(set(warnings)),
        "blockers": blockers,
        "ready": not blockers,
        "publicly_reproducible": public_ready,
    }


def readiness(catalog, study: Study) -> tuple[str, list[str]]:
    if study.lifecycle in {"completed", "superseded"}:
        return study.lifecycle, []
    if not study.execution.plans:
        state = "blocked" if study.lifecycle == "blocked" else "draft"
        return state, list(study.blockers)

    resolutions = []
    problems = list(study.blockers)
    for execution_plan in study.execution.plans:
        if not execution_plan.profile_ids:
            problems.append(
                f"Method {execution_plan.method_id} has no configured resource profile"
            )
            problems.extend(execution_plan.blockers)
            continue
        for profile_id in execution_plan.profile_ids:
            try:
                resolutions.append(
                    resolve(
                        catalog,
                        study.id,
                        profile_id,
                        method_id=execution_plan.method_id,
                    )
                )
            except ValueError as exc:
                problems.append(str(exc))

    if any(plan["publicly_reproducible"] for plan in resolutions):
        return "public", []
    if any(plan["ready"] for plan in resolutions):
        return "local", []
    problems.extend(item for plan in resolutions for item in plan["blockers"])
    explicitly_blocked = study.lifecycle == "blocked" or any(
        plan.declared_readiness == "blocked" for plan in study.execution.plans
    )
    return ("blocked" if explicitly_blocked else "draft"), sorted(set(problems))
