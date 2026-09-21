"""Regenerate JSON Schema projections from strict Pydantic models."""

import json
from pathlib import Path

from open_research.models import DIRECTORIES, Program


def main():
    root = Path(__file__).resolve().parent.parent
    destination = root / "schemas"
    destination.mkdir(exist_ok=True)
    classes = {model.__name__: model for _, model in DIRECTORIES.values()}
    classes["Program"] = Program
    for name, model in sorted(classes.items()):
        (destination / f"{name}.schema.json").write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(classes)} schemas")


if __name__ == "__main__":
    main()
