from pathlib import Path
import shutil

import pytest
import yaml


SOURCE_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def research_tree(tmp_path):
    root = tmp_path / "program"
    root.mkdir()
    shutil.copy2(SOURCE_ROOT / "program.yaml", root / "program.yaml")
    for directory in ("graph", "studies", "infra", "artifacts", "runs", "baselines", "publications"):
        shutil.copytree(SOURCE_ROOT / directory, root / directory)
    return root


def read_yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_yaml(path, value):
    path.write_text(yaml.safe_dump(value, sort_keys=False, allow_unicode=True), encoding="utf-8")
