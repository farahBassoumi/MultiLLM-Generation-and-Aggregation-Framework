from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
import importlib.util
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from itertools import groupby
from pathlib import Path

from .notebooks import NotebookStep


@dataclass(frozen=True)
class RunResult:
    step: NotebookStep
    elapsed_seconds: float


def run_notebooks(
    steps: list[NotebookStep],
    project_root: Path,
    output_dir: Path,
    timeout: int,
    kernel: str | None = None,
    inplace: bool = False,
    continue_on_error: bool = False,
) -> list[RunResult]:
    results: list[RunResult] = []

    if not inplace:
        output_dir.mkdir(parents=True, exist_ok=True)

    if not kernel:
        kernel = ensure_current_python_kernel()

    for _, group in groupby(
        steps,
        key=lambda step: step.execution_group
    ):
        group_steps = list(group)
        if len(group_steps) == 1:
            result = _run_notebook(
                step=group_steps[0],
                project_root=project_root,
                output_dir=output_dir,
                timeout=timeout,
                kernel=kernel,
                inplace=inplace,
                continue_on_error=continue_on_error,
            )
            if result:
                results.append(result)
            continue

        print(
            f"\n[PARALLEL] {group_steps[0].execution_group}: "
            f"running {len(group_steps)} notebooks",
        )

        with ThreadPoolExecutor(max_workers=len(group_steps)) as executor:
            futures = [
                executor.submit(
                    _run_notebook,
                    step=step,
                    project_root=project_root,
                    output_dir=output_dir,
                    timeout=timeout,
                    kernel=kernel,
                    inplace=inplace,
                    continue_on_error=continue_on_error,
                )
                for step in group_steps
            ]

            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

    return results


def _run_notebook(
    step: NotebookStep,
    project_root: Path,
    output_dir: Path,
    timeout: int,
    kernel: str | None,
    inplace: bool,
    continue_on_error: bool,
) -> RunResult | None:
    start_time = time.monotonic()
    command = _build_nbconvert_command(
        step=step,
        project_root=project_root,
        output_dir=output_dir,
        timeout=timeout,
        kernel=kernel,
        inplace=inplace,
    )

    print(
        f"\n[RUN] {step.execution_group}: {step.name}",
        flush=True
    )
    print(f"[CMD] {' '.join(command)}", flush=True)

    completed = subprocess.run(command, cwd=project_root)
    elapsed = time.monotonic() - start_time

    if completed.returncode != 0:
        message = (
            f"Notebook {step.execution_group} failed after {elapsed:.1f}s: "
            f"{step.name}"
        )
        if continue_on_error:
            print(f"[FAIL] {message}", flush=True)
            return None
        raise subprocess.CalledProcessError(completed.returncode, command)

    print(
        f"[OK] {step.execution_group} finished in {elapsed:.1f}s",
        flush=True
    )
    return RunResult(step=step, elapsed_seconds=elapsed)


def ensure_jupyter_available() -> list[str]:
    if importlib.util.find_spec("jupyter"):
        return [sys.executable, "-m", "jupyter"]

    jupyter = shutil.which("jupyter")
    if jupyter:
        return [jupyter]

    raise RuntimeError(
        "Jupyter is required to execute notebooks. Install the project "
        "requirements, then rerun this command."
    )


def _kernel_installed(kernel_name: str) -> bool:
    completed = subprocess.run(
        [*ensure_jupyter_available(), "kernelspec", "list", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return False

    data = json.loads(completed.stdout or "{}")
    return kernel_name in data.get("kernelspecs", {})


def ensure_current_python_kernel(kernel_name: str = "python3.13") -> str:
    if _kernel_installed(kernel_name):
        return kernel_name

    print(
        f"[INFO] Installing Jupyter kernel '{kernel_name}' for {sys.executable}",
        flush=True,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "ipykernel",
            "install",
            "--user",
            "--name",
            kernel_name,
            "--display-name",
            "Python 3.13",
        ],
        check=True,
    )
    return kernel_name


def _build_nbconvert_command(
    step: NotebookStep,
    project_root: Path,
    output_dir: Path,
    timeout: int,
    kernel: str | None,
    inplace: bool,
) -> list[str]:
    command = [
        *ensure_jupyter_available(),
        "nbconvert",
        "--to",
        "notebook",
        "--execute",
        str(_path_for_command(step.path, project_root)),
        # f"--ExecutePreprocessor.cwd={project_root}",
        f"--ExecutePreprocessor.timeout={timeout}",
    ]

    if not kernel:
        kernel = ensure_current_python_kernel()

    if kernel:
        command.append(f"--ExecutePreprocessor.kernel_name={kernel}")

    if inplace:
        command.append("--inplace")
    else:
        command.extend(
            [
                "--output-dir",
                str(output_dir),
                "--output",
                f"{step.path.stem}_executed.ipynb",
            ]
        )

    return command


def _path_for_command(path: Path, project_root: Path) -> Path:
    try:
        return path.relative_to(project_root)
    except ValueError:
        return path
