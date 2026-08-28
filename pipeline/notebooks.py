from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


NOTEBOOK_ORDER_PATTERN = re.compile(
    r"(?:^|_)n(?P<order>\d+)(?P<stage>[a-z]?)(?:_|\.|$)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class NotebookStep:
    order: int
    stage: str
    path: Path

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def execution_group(self) -> str:
        return f"{self.order}{self.stage}"


def discover_notebooks(scripts_dir: Path) -> list[NotebookStep]:
    if not scripts_dir.exists():
        raise FileNotFoundError(
            f"Scripts directory does not exist: {scripts_dir}")

    steps: list[NotebookStep] = []

    for path in scripts_dir.glob("*.ipynb"):
        match = NOTEBOOK_ORDER_PATTERN.search(path.name)
        if not match:
            continue

        steps.append(
            NotebookStep(
                order=int(match.group("order")),
                stage=match.group("stage") or "",
                path=path,
            )
        )

    print("Found notebooks:")
    for step in steps:
        print(step.order, step.path)

    if not steps:
        raise ValueError(
            f"No ordered notebooks found in {scripts_dir}. "
            "Expected names ending like '_n1.ipynb'."
        )

    steps.sort(
        key=lambda step: (
            step.order,
            step.stage,
            step.name.lower()
        )
    )
    return steps


def filter_notebooks(
    steps: list[NotebookStep],
    from_step: int | None = None,
    to_step: int | None = None,
    only: list[int] | None = None,
    names: list[str] | None = None,
) -> list[NotebookStep]:
    selected = steps

    if names:
        selected = [
            step for step in selected
            if step.name in names
        ]

    elif only:
        wanted = set(only)
        selected = [
            step for step in selected
            if step.order in wanted
        ]

    else:
        if from_step is not None:
            selected = [
                step for step in selected
                if step.order >= from_step
            ]

        if to_step is not None:
            selected = [
                step for step in selected
                if step.order <= to_step
            ]

    if not selected:
        raise ValueError("Notebook filters selected no notebooks.")

    return selected
