"""Read and validate the canonical Git tree."""

from dataclasses import dataclass, field
import hashlib
from pathlib import Path

import yaml
from pydantic import ValidationError

from .ids import validate_id
from .models import (
    Artifact,
    Baseline,
    Claim,
    DIRECTORIES,
    InfrastructureProvider,
    Program,
    PublicationManifest,
    Record,
    Relation,
    ResourceProfile,
    Result,
    Run,
    Source,
    Study,
)


SEMANTIC_ENDPOINTS = {
    "answers": {("C", "Q"), ("RES", "Q")},
    "raises": {("C", "Q"), ("RES", "Q")},
    "motivates": {("SRC", "Q")},
    "enables": {("M", "Q"), ("ART", "Q")},
    "investigates": {("M", "Q")},
    "tests": {("M", "C")},
    "supports": {("RES", "C"), ("SRC", "C"), ("C", "C")},
    "weakens": {("RES", "C"), ("SRC", "C"), ("C", "C")},
    "contradicts": {("RES", "C"), ("SRC", "C"), ("C", "C")},
    "refines": {("Q", "Q"), ("C", "C")},
    "generalizes": {("C", "C")},
    "specializes": {("C", "C")},
    "depends_on": {("C", "C")},
}
SEMANTIC = set(SEMANTIC_ENDPOINTS)
PROVENANCE = {"derived_from", "inspired_by", "informed_by", "independently_convergent_with"}
PROVENANCE_KINDS = {"Q", "C", "M", "RES", "SRC", "ART"}


@dataclass
class Catalog:
    root: Path
    program: Program | None = None
    objects: dict[str, Record] = field(default_factory=dict)
    paths: dict[str, Path] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def of_type(self, cls):
        return [obj for obj in self.objects.values() if isinstance(obj, cls)]

    def get(self, object_id: str, cls=None):
        obj = self.objects.get(object_id)
        if obj is None or (cls and not isinstance(obj, cls)):
            raise ValueError(f"missing {cls.__name__ if cls else 'object'}: {object_id}")
        return obj


def _read_yaml(path: Path):
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_catalog(root: Path) -> Catalog:
    root = root.resolve()
    catalog = Catalog(root)
    try:
        catalog.program = Program.model_validate(_read_yaml(root / "program.yaml"))
        validate_id(catalog.program.id, catalog.program.namespace, "PROGRAM")
    except (OSError, ValueError, ValidationError, yaml.YAMLError) as exc:
        catalog.errors.append(f"program.yaml: {exc}")
        return catalog

    for relative, (kind, model) in DIRECTORIES.items():
        directory = root / relative
        files = sorted(directory.glob("*.yaml"))
        if relative == "runs":
            files += sorted(directory.glob("*/manifest.yaml"))
        for path in files:
            try:
                obj = model.model_validate(_read_yaml(path))
                validate_id(obj.id, catalog.program.namespace, kind)
                if obj.id in catalog.objects:
                    raise ValueError(f"duplicate ID also in {catalog.paths[obj.id]}")
                nested_run = relative == "runs" and path.name == "manifest.yaml" and path.parent.name == obj.id
                if path.stem != obj.id and not nested_run:
                    raise ValueError("file name must match object ID")
                catalog.objects[obj.id] = obj
                catalog.paths[obj.id] = path
            except (OSError, ValueError, ValidationError, yaml.YAMLError) as exc:
                catalog.errors.append(f"{path.relative_to(root)}: {exc}")
    return catalog


def validate_catalog(catalog: Catalog) -> list[str]:
    errors = list(catalog.errors)
    if not catalog.program:
        return errors
    ns = catalog.program.namespace

    def check_ref(source: Record, target_id: str, expected=None):
        try:
            validate_id(target_id, ns)
            return catalog.get(target_id, expected)
        except ValueError as exc:
            errors.append(f"{source.id}: {exc}")
            return None

    if catalog.program.default_baseline_id and catalog.program.default_baseline_id not in catalog.objects:
        errors.append("program.yaml: default baseline does not exist")

    for obj in catalog.objects.values():
        if isinstance(obj, Relation):
            source = check_ref(obj, obj.source_id)
            target = check_ref(obj, obj.target_id)
            allowed = SEMANTIC if obj.relation_class == "semantic" else PROVENANCE
            if obj.relation_type not in allowed:
                errors.append(f"{obj.id}: invalid {obj.relation_class} relation type {obj.relation_type}")
            if source and target and obj.source_id == obj.target_id:
                errors.append(f"{obj.id}: Relation endpoints must be distinct")
            if source and target and obj.relation_class == "semantic" and obj.relation_type in SEMANTIC_ENDPOINTS:
                source_kind = validate_id(source.id, ns)
                target_kind = validate_id(target.id, ns)
                if (source_kind, target_kind) not in SEMANTIC_ENDPOINTS[obj.relation_type]:
                    errors.append(f"{obj.id}: invalid endpoints for {obj.relation_type}")
            if source and target and obj.relation_class == "provenance" and obj.relation_type in PROVENANCE:
                source_kind = validate_id(source.id, ns)
                target_kind = validate_id(target.id, ns)
                if source_kind not in PROVENANCE_KINDS or target_kind not in PROVENANCE_KINDS:
                    errors.append(f"{obj.id}: provenance Relations require scholarly endpoints")
            if obj.asserted_at.tzinfo is None:
                errors.append(f"{obj.id}: asserted_at requires timezone")

        elif isinstance(obj, Result):
            for ref in obj.grounding_ids:
                grounding = check_ref(obj, ref)
                if grounding and not isinstance(grounding, (Run, Source, Artifact)):
                    errors.append(f"{obj.id}: invalid Result grounding type for {ref}")

        elif isinstance(obj, Study):
            from .models import Method, Question

            for ref in obj.question_ids:
                check_ref(obj, ref, Question)
            for ref in obj.claim_ids:
                check_ref(obj, ref, Claim)
            for ref in obj.method_ids:
                check_ref(obj, ref, Method)
            for ref in obj.result_ids:
                check_ref(obj, ref, Result)
            for ref in obj.artifact_ids:
                check_ref(obj, ref, Artifact)
            for plan in obj.execution.plans:
                check_ref(obj, plan.method_id, Method)
                for ref in plan.requires.artifacts:
                    check_ref(obj, ref, Artifact)
                    if ref not in obj.artifact_ids:
                        errors.append(f"{obj.id}: execution Artifact {ref} is not listed in artifact_ids")
                for ref in plan.profile_ids:
                    check_ref(obj, ref, ResourceProfile)
                if plan.declared_readiness in {"local", "public"}:
                    from .resolver import resolve

                    resolutions = []
                    for profile_id in plan.profile_ids:
                        try:
                            resolutions.append(
                                resolve(catalog, obj.id, profile_id, method_id=plan.method_id)
                            )
                        except ValueError as exc:
                            errors.append(
                                f"{obj.id}: cannot resolve Method {plan.method_id} "
                                f"with profile {profile_id}: {exc}"
                            )
                    if not plan.profile_ids:
                        errors.append(
                            f"{obj.id}: Method {plan.method_id} declares readiness without a resource profile"
                        )
                    readiness_key = (
                        "ready" if plan.declared_readiness == "local" else "publicly_reproducible"
                    )
                    if resolutions and not any(item[readiness_key] for item in resolutions):
                        errors.append(
                            f"{obj.id}: Method {plan.method_id} declared {plan.declared_readiness} "
                            f"with missing dependencies: {[item['blockers'] for item in resolutions]}"
                        )

        elif isinstance(obj, InfrastructureProvider):
            from .models import Environment, RepositoryRef

            check_ref(obj, obj.repository_id, RepositoryRef)
            for ref in obj.environment_ids:
                check_ref(obj, ref, Environment)
            for ref in obj.profile_ids:
                check_ref(obj, ref, ResourceProfile)
            for ref in obj.verification_run_ids:
                verification = check_ref(obj, ref, Run)
                if verification and verification.status != "completed":
                    errors.append(f"{obj.id}: verification Run must be completed")
                if verification and not any(
                    frozen.provider_id == obj.id for frozen in verification.implementations
                ):
                    errors.append(f"{obj.id}: verification Run does not use this provider")
            if obj.status == "validated" and not obj.verification_run_ids:
                errors.append(f"{obj.id}: validated provider needs verification Run")

        elif isinstance(obj, ResourceProfile):
            from .models import Environment

            for ref in obj.environment_ids:
                check_ref(obj, ref, Environment)

        elif isinstance(obj, Artifact):
            from .models import RepositoryRef

            if obj.repository_id:
                check_ref(obj, obj.repository_id, RepositoryRef)
            if obj.produced_by_run_id:
                check_ref(obj, obj.produced_by_run_id, Run)
            if obj.availability == "public" and not (obj.uri and obj.digest):
                errors.append(f"{obj.id}: public artifact requires URI and digest")

        elif isinstance(obj, Run):
            from .models import Environment, Method, RepositoryRef

            study = check_ref(obj, obj.study_id, Study)
            check_ref(obj, obj.method_id, Method)
            environment = check_ref(obj, obj.environment_id, Environment)
            profile = check_ref(obj, obj.profile_id, ResourceProfile)
            if study and obj.method_id not in study.method_ids:
                errors.append(f"{obj.id}: Method is not part of Study")
            execution_plan = next(
                (plan for plan in study.execution.plans if plan.method_id == obj.method_id),
                None,
            ) if study else None
            if study and not execution_plan:
                errors.append(f"{obj.id}: Run Method has no execution plan in Study")
            if execution_plan and not execution_plan.entrypoint:
                errors.append(f"{obj.id}: Run Method execution plan has no entrypoint")
            if execution_plan and obj.profile_id not in execution_plan.profile_ids:
                errors.append(f"{obj.id}: profile is not supported by Study Method execution plan")
            if profile and environment and environment.id not in profile.environment_ids:
                errors.append(f"{obj.id}: profile/environment incompatibility")
            if environment and (
                not environment.lock_digest
                or obj.environment_lock_digest != environment.lock_digest
            ):
                errors.append(f"{obj.id}: frozen environment lock digest mismatch")
            covered = set()
            for frozen in obj.implementations:
                provider = check_ref(obj, frozen.provider_id, InfrastructureProvider)
                repository = check_ref(obj, frozen.repository_id, RepositoryRef)
                if provider:
                    covered.update(provider.capabilities)
                    if (
                        provider.interface_version != frozen.interface_version
                        or provider.repository_id != frozen.repository_id
                    ):
                        errors.append(f"{obj.id}: frozen provider interface/repository mismatch")
                    if obj.environment_id not in provider.environment_ids or obj.profile_id not in provider.profile_ids:
                        errors.append(f"{obj.id}: provider incompatible with Run environment/profile")
                if repository and frozen.revision != repository.revision:
                    errors.append(f"{obj.id}: frozen provider revision differs from RepositoryRef")
            if execution_plan and set(execution_plan.requires.capabilities) - covered:
                errors.append(f"{obj.id}: Run does not cover all required capabilities")
            for frozen in obj.input_artifacts:
                artifact = check_ref(obj, frozen.artifact_id, Artifact)
                if artifact and artifact.digest and frozen.digest != artifact.digest:
                    errors.append(f"{obj.id}: input Artifact digest differs from registry")
            if execution_plan and set(execution_plan.requires.artifacts) != {
                item.artifact_id for item in obj.input_artifacts
            }:
                errors.append(f"{obj.id}: Run input Artifacts differ from Study Method execution plan")
            for ref in obj.produced_artifact_ids:
                check_ref(obj, ref, Artifact)
            config_relative = Path(obj.config_path)
            if config_relative.is_absolute() or ".." in config_relative.parts:
                errors.append(f"{obj.id}: config_path must be relative to Run directory")
            else:
                config_file = catalog.paths[obj.id].parent / config_relative
                if not config_file.is_file():
                    errors.append(f"{obj.id}: config snapshot is missing")
                elif "sha256:" + hashlib.sha256(config_file.read_bytes()).hexdigest() != obj.config_digest:
                    errors.append(f"{obj.id}: config snapshot digest mismatch")
            if obj.status in {"completed", "failed", "cancelled", "invalidated"} and obj.ended_at is None:
                errors.append(f"{obj.id}: terminal Run requires ended_at")
            if obj.status == "failed" and not obj.error:
                errors.append(f"{obj.id}: failed Run requires error")
            if obj.status == "invalidated" and not obj.invalidation:
                errors.append(f"{obj.id}: invalidated Run requires reason")
            if (
                obj.status == "completed"
                and execution_plan
                and execution_plan.entrypoint == "dawn_srw.zero_shot_eval_jax@1"
            ):
                if not (obj.native_manifest_digest and obj.software_versions and obj.dataset_provenance):
                    errors.append(f"{obj.id}: completed zero-shot Run lacks native software/dataset provenance")

        elif isinstance(obj, Baseline):
            for ref in obj.run_ids:
                check_ref(obj, ref, Run)

        elif isinstance(obj, PublicationManifest):
            for ref in obj.object_ids + obj.run_ids + obj.artifact_ids:
                check_ref(obj, ref)

    for claim in catalog.of_type(Claim):
        if claim.status in {"supported", "robust"} and not any(
            isinstance(rel, Relation)
            and rel.relation_type == "supports"
            and rel.relation_class == "semantic"
            and rel.status == "accepted"
            and rel.target_id == claim.id
            and isinstance(catalog.objects.get(rel.source_id), (Result, Source, Claim))
            for rel in catalog.objects.values()
        ):
            errors.append(
                f"{claim.id}: {claim.status} Claim requires an accepted supporting scholarly Relation"
            )
    return errors
