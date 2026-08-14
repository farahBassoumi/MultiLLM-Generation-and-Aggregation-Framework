from pathlib import Path

from notebooks import discover_notebooks
from runner import run_notebooks


project_root = Path(".").resolve()

scripts_dir = project_root / "scripts"

output_dir = project_root / "executed"


# Find notebooks
steps = discover_notebooks(
    scripts_dir
)


# Keep only n1 for testing
steps = [
    step for step in steps
    if step.order == 1
]


# Execute notebook
results = run_notebooks(
    steps=steps,
    project_root=project_root,
    output_dir=output_dir,
    timeout=300
)


for result in results:
    print(
        f"{result.step.name} finished in "
        f"{result.elapsed_seconds:.2f}s"
    )