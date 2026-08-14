from __future__ import annotations

import argparse
from itertools import groupby
from pathlib import Path

from pipeline.notebooks import discover_notebooks, filter_notebooks
from pipeline.runner import run_notebooks


PROJECT_ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ordered notebooks from scripts/ using plain Python."
    )
    parser.add_argument(
        "--scripts-dir",
        type=Path,
        default=PROJECT_ROOT / "scripts",
        help="Directory containing notebooks named like '*_n1.ipynb'.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "executed_notebooks",
        help="Directory for executed notebook copies.",
    )
    parser.add_argument(
        "--from-step",
        type=int,
        help="Start from this notebook order number.",
    )
    parser.add_argument(
        "--to-step",
        type=int,
        help="Stop at this notebook order number.",
    )
    parser.add_argument(
        "--only",
        type=int,
        nargs="+",
        help="Run only these notebook order numbers.",
    )
    parser.add_argument(
        "--notebooks",
        nargs="+",
        help="Run specific notebook files by name.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=7200,
        help="Per-notebook execution timeout in seconds.",
    )
    parser.add_argument(
        "--kernel",
        help="Jupyter kernel name to use, for example 'python3'.",
    )
    parser.add_argument(
        "--inplace",
        action="store_true",
        help="Write execution outputs back into the source notebooks.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue to later notebooks if one notebook fails.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the notebook order without executing anything.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scripts_dir = args.scripts_dir.resolve()
    output_dir = args.output_dir.resolve()

    steps = discover_notebooks(scripts_dir)
    steps = filter_notebooks(
        steps,
        from_step=args.from_step,
        to_step=args.to_step,
        only=args.only,
        names=args.notebooks,
    )

    print("Notebook execution order:")
    for _, group in groupby(
        steps,
        key=lambda step: step.execution_group
    ):
        group_steps = list(group)
        suffix = " (parallel)" if len(group_steps) > 1 else ""
        for step in group_steps:
            print(
                f"  {step.execution_group}{suffix}: {_display_path(step.path)}"
            )

    if args.dry_run:
        return 0

    results = run_notebooks(
        steps=steps,
        project_root=PROJECT_ROOT,
        output_dir=output_dir,
        timeout=args.timeout,
        kernel=args.kernel,
        inplace=args.inplace,
        continue_on_error=args.continue_on_error,
    )

    print("\nCompleted notebooks:")
    for result in results:
        print(
            f"  n{result.step.order}: {result.step.name} "
            f"({result.elapsed_seconds:.1f}s)"
        )

    return 0


def _display_path(path: Path) -> Path:
    try:
        return path.relative_to(PROJECT_ROOT)
    except ValueError:
        return path


if __name__ == "__main__":
    raise SystemExit(main())
