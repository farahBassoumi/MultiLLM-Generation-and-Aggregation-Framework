# Comment Generation Pipeline

This repository contains a notebook-based pipeline for generating, deduplicating,
and evaluating code review comments. The pipeline starts from a CSV of code
review examples, enriches each example with pull request metadata and code
context, asks LLMs to generate review comments, merges generated and human
comments, deduplicates similar comments, and finally evaluates comment relevance
with an LLM-as-a-judge step.

The project is currently notebook-first for experimentation, but it also includes
a plain-Python runner that executes ordered notebooks automatically. No workflow
or orchestration framework is used.

## High-Level Pipeline

```text
df_py_first_100.csv
        |
        v
GitHub PR/context reconstruction
        |
        v
LLM context generation
        |
        v
LLM review comment generation
        |
        v
Pre-deduplication merge
        |
        v
LLM-based deduplication
        |
        v
LLM-as-a-judge evaluation
        |
        v
Analysis notebooks and final CSV outputs
```

## Main Functionalities

- Reconstruct pull request metadata from GitHub.
- Identify target files and changed hunks for review examples.
- Generate additional code context around each hunk with an LLM.
- Generate code review comments from patches and reconstructed context.
- Normalize generated comments into a flat tabular dataset.
- Merge generated comments with human comments and patch metadata.
- Deduplicate comments that describe the same underlying issue.
- Synthesize representative comments for duplicate groups.
- Evaluate generated or deduplicated comments with an LLM judge.
- Analyze category distributions, severity distributions, deduplication behavior,
  and relevance scores.

## Repository Structure

```text
.
|-- run_pipeline.py
|-- requirements.txt
|-- README.md
|-- .env
|-- .gitignore
|-- pipeline/
|   |-- __init__.py
|   |-- notebooks.py
|   `-- runner.py
|-- scripts/
|   |-- test_n1.ipynb
|   |-- context_generation_n2.ipynb
|   |-- comment_generation_n3.ipynb
|   |-- pre_deduplication_n4.ipynb
|   |-- deduplication_n5.ipynb
|   |-- running_llm_as_a_judge_n6.ipynb
|   `-- context_reconstruction_n11.ipynb
|-- generated_context_generated_comments/
|   `-- generated_comments_merged_30.csv
|-- deduplicated_comments/
|   |-- generated_deduplicated_comments_30_merged.csv
|   `-- genereated_deduplicated_comments_30_merged_without_categories_or_severities.csv
|-- df_py_first_100.csv
|-- df_first_30_n1_generated_context.csv
|-- df_generated_context_minimal_30.csv
|-- df_results_after_llm_as_judge.csv
|-- df_evaluated_30.csv
|-- analysis_evaluation.ipynb
|-- analysing_deduplication.ipynb
`-- evaluation_generated_vs_gt_comment.ipynb
```

## Important Naming Convention

The automation discovers notebooks in `scripts/` whose filenames end with:

```text
_n<number>.ipynb
```

Examples:

```text
context_generation_n2.ipynb
comment_generation_n3.ipynb
deduplication_n5.ipynb
```

The number controls execution order. A notebook named `something_n2.ipynb` runs
before `something_n3.ipynb`.

Multiple notebooks may use the same number. Notebooks with the same number run
in parallel, and the next number starts only after all notebooks in that group
finish. This is useful for a fork/join step where two notebooks read the same
input CSV, write separate output CSVs, and the following notebook combines both
outputs.

Example:

```text
prepare_input_n1.ipynb
generate_model_a_comments_n2.ipynb
generate_model_b_comments_n2.ipynb
merge_model_outputs_n3.ipynb
deduplication_n4.ipynb
```

In this example, both `n2` notebooks run at the same time. `n3` starts only
after both `n2` notebooks finish.

Current discovered order:

```text
n1  scripts/test_n1.ipynb
n2  scripts/context_generation_n2.ipynb
n3  scripts/comment_generation_n3.ipynb
n4  scripts/pre_deduplication_n4.ipynb
n5  scripts/deduplication_n5.ipynb
n6  scripts/running_llm_as_a_judge_n6.ipynb
n11 scripts/context_reconstruction_n11.ipynb
```

Note: `context_reconstruction_n11.ipynb` currently runs after `n6` because its
filename ends with `n11`. If it is meant to be the first real pipeline step, it
should be renamed to something like `context_reconstruction_n1.ipynb`, and
`test_n1.ipynb` should be moved out of `scripts/` or renamed so it does not end
with `_n1.ipynb`.

## Folder and File Responsibilities

### `run_pipeline.py`

Plain-Python command-line entrypoint for executing the ordered notebooks.

Responsibilities:

- Parse command-line options.
- Discover ordered notebooks from `scripts/`.
- Filter which notebook steps to run.
- Print the execution order.
- Call the notebook execution helper.

Supported options:

```text
--scripts-dir         Choose another notebook directory.
--output-dir          Choose where executed notebook copies are written.
--from-step           Start from a specific notebook number.
--to-step             Stop at a specific notebook number.
--only                Run only specific notebook numbers.
--timeout             Set per-notebook timeout in seconds.
--kernel              Select a Jupyter kernel.
--inplace             Write outputs back into source notebooks.
--continue-on-error   Continue even if one notebook fails.
--dry-run             Print execution order without running notebooks.
```

### `pipeline/`

Small helper package for plain-Python automation.

### `pipeline/notebooks.py`

Contains notebook discovery and filtering logic.

Responsibilities:

- Match notebooks ending in `_n<number>.ipynb`.
- Extract the numeric order.
- Sort notebooks by order.
- Allow duplicate order numbers so matching steps can run in parallel.
- Support partial execution with `--from-step`, `--to-step`, and `--only`.

### `pipeline/runner.py`

Contains notebook execution logic.

Responsibilities:

- Execute notebooks through `jupyter nbconvert --execute`.
- Run notebooks with the same order number in parallel.
- Prefer the active Python environment's Jupyter installation.
- Fall back to a `jupyter` executable on `PATH`.
- Run notebooks from the project root so relative CSV paths keep working.
- Write executed notebook copies to `artifacts/executed_notebooks/` by default.
- Optionally execute notebooks in place.
- Track and print elapsed time for each notebook.

### `scripts/`

Contains the numbered notebooks that make up the runnable pipeline. These
notebooks are still the main source of the project logic.

#### `test_n1.ipynb`

Small test notebook that prints a success message.

Current role:

- Useful for checking that notebook execution works.
- Because it ends with `_n1.ipynb`, it is currently treated as pipeline step 1.

#### `context_reconstruction_n11.ipynb`

Reconstructs pull request metadata and code review context from the original
dataset.

Main operations:

- Load `df_py_first_100.csv`.
- Add or normalize `patch_id` values.
- Load GitHub credentials from `.env`.
- Query GitHub pull request metadata.
- Query changed files for each pull request.
- Find the target file for a dataset hunk.
- Split GitHub patches into individual hunks.
- Add metadata columns such as PR title, changed files, target file, PR hunks,
  and same-file hunks.

Important note:

- This notebook is named `n11`, so the runner executes it after `n6`. Rename it
  to `n1` if it should run first.

#### `context_generation_n2.ipynb`

Generates LLM-produced code context for each patch.

Main operations:

- Load `df_py_first_100.csv`.
- Select the first 30 rows.
- Load OpenRouter configuration from `.env`.
- Build system and user prompts for extracting relevant source context.
- Call the configured LLM through OpenRouter.
- Retry failed LLM calls with backoff.
- Build a dataframe containing `generated_context`.

Expected output or handoff:

- The downstream notebooks expect a file like
  `df_first_30_n1_generated_context.csv`.
- If running from scratch, make sure this notebook saves the generated context
  file expected by `comment_generation_n3.ipynb`.

#### `comment_generation_n3.ipynb`

Generates review comments with an LLM.

Main operations:

- Load `df_first_30_n1_generated_context.csv`.
- Load OpenRouter configuration from `.env`.
- Define valid comment categories and severity labels.
- Build prompts containing PR title, changed files, target file, generated
  context, and code patch.
- Ask the configured LLM to return strict JSON comments.
- Parse generated comments.
- Add comment IDs and generation system metadata.
- Convert nested generated comments into a flat dataframe.
- Save generated comments to
  `generated_context_generated_comments/generated_comments_cohere_30.csv`.
- Inspect merged generated comments and category distributions.

Expected input:

- `df_first_30_n1_generated_context.csv`.

Primary generated output:

- `generated_context_generated_comments/generated_comments_cohere_30.csv`.

#### `pre_deduplication_n4.ipynb`

Prepares generated comments for deduplication.

Main operations:

- Load generated comment CSVs.
- Concatenate one or more model outputs into one dataframe.
- Sort generated comments by `patch_id`.
- Load the dataframe containing human comments, hunks, and generated context.
- Rename `comment` to `generated_comment`.
- Merge generated comments with human comments and patch metadata.
- Save a merged CSV for deduplication.

Expected inputs:

- `generated_context_generated_comments/generated_comments_cohere_30.csv`.
- `df_first_30_n1_generated_context.csv`.

Primary output:

- `generated_context_generated_comments/generated_comments_merged_30.csv`.

#### `deduplication_n5.ipynb`

Groups duplicate or near-duplicate generated review comments.

Main operations:

- Load `generated_context_generated_comments/generated_comments_merged_30.csv`.
- Load OpenRouter configuration from `.env`.
- Group comments by `patch_id`.
- Ask an LLM to group comments that describe the same underlying issue.
- Run multiple consistency passes.
- Use pairwise agreement and union-find to build final clusters.
- Synthesize a representative comment for duplicate groups.
- Create one row per cluster.
- Analyze duplicate group counts, category agreement, severity agreement,
  cluster sizes, and system overlap.

Expected input:

- `generated_context_generated_comments/generated_comments_merged_30.csv`.

Primary output:

- The current checked-in downstream file is
  `deduplicated_comments/generated_deduplicated_comments_30_merged.csv`.
- The notebook also writes checkpoint data to `dedup_checkpoint.json`.

#### `running_llm_as_a_judge_n6.ipynb`

Evaluates generated or deduplicated comments using an LLM judge.

Main operations:

- Load `deduplicated_comments/generated_deduplicated_comments_30_merged.csv`.
- Load `df_first_30_n1_generated_context.csv`.
- Merge generated context and patch information back into deduplicated rows.
- Select the first comment from each deduplicated comment group.
- Build judge prompts using PR metadata, patch, context, and review comment.
- Ask the LLM for a relevance score from 1 to 5.
- Parse strict JSON judge outputs.
- Save partial and final relevance predictions.

Expected inputs:

- `deduplicated_comments/generated_deduplicated_comments_30_merged.csv`.
- `df_first_30_n1_generated_context.csv`.

Primary outputs:

- `df_results_first_left_after_llm_as_judge.csv`.
- `df_results_first_25_after_llm_as_judge.csv`.
- `df_results_after_llm_as_judge.csv`.

### `generated_context_generated_comments/`

Stores generated comment datasets and merged generated-comment data.

Current important file:

- `generated_comments_merged_30.csv`: merged generated comments with patch IDs,
  categories, severities, generation system, human comment, hunk, and generated
  context.

Typical columns:

```text
comment_id
generated_comment
category
generation_system
patch_id
severity
github_commit_url
pr_url
human_comment
hunk
generated_context
```

### `deduplicated_comments/`

Stores deduplicated generated comments and related deduplication outputs.

Current important files:

- `generated_deduplicated_comments_30_merged.csv`: deduplicated clusters with
  comment IDs, comments, generation systems, categories, severities, duplicate
  flags, and synthesis comments.
- `genereated_deduplicated_comments_30_merged_without_categories_or_severities.csv`:
  variant of deduplicated output without category/severity fields.

Typical columns:

```text
patch_id
num_comments
cluster_id
comment_ids
comments
generation_systems
categories
severities
is_duplicate_group
synthesis_comment
```

### Root CSV Files

#### `df_py_first_100.csv`

Initial dataset used by the pipeline.

Observed columns:

```text
old_hunk
oldf
hunk
comment
ids
repo
ghid
old
new
lang
patch_id
```

#### `df_first_30_n1_generated_context.csv`

Context-enriched dataset used by comment generation and evaluation.

Observed columns:

```text
hunk
comment
repo
ghid
pr_title
changed_files
target_file
internal_id
parent_sha
new_sha
pr_url
github_commit_url
patch_id
old_context
generated_context
```

#### `df_generated_context_minimal_30.csv`

Smaller generated-context dataset. It is useful when only `patch_id` and
`generated_context` are needed.

#### `df_results_after_llm_as_judge.csv`

Final or near-final LLM-judge evaluation output.

#### `df_evaluated_30.csv`

Evaluation dataset used by analysis notebooks.

### Analysis Notebooks

These notebooks are not currently part of the automated `scripts/` runner
because they do not follow the `_n<number>.ipynb` naming convention inside
`scripts/`.

#### `analysis_evaluation.ipynb`

Analyzes evaluation results, likely including score distributions and generated
comment quality.

#### `analysing_deduplication.ipynb`

Analyzes deduplication results, duplicate clusters, agreement patterns, and
system overlap.

#### `evaluation_generated_vs_gt_comment.ipynb`

Compares generated comments against ground-truth or human comments.

## Setup

Use Python 3.13, matching the current local environment.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -3.13 -m pip install -r requirements.txt
```

If your activated virtual environment exposes `python`, this also works:

```powershell
python -m pip install -r requirements.txt
```

## Required Environment Variables

Create a `.env` file in the project root. The notebooks currently load values
from `.env`.

Common variables:

```text
GITHUB_TOKEN=...
OPENROUTER_API_KEY=...
OPENROUTER_URL=...
MODEL_NAME=...
SLEEP_BETWEEN_CALLS=1
```

Expected usage:

- `GITHUB_TOKEN`: used when calling GitHub's pull request and pull request files
  APIs.
- `OPENROUTER_API_KEY`: used for LLM calls through OpenRouter.
- `OPENROUTER_URL`: OpenRouter chat completions endpoint.
- `MODEL_NAME`: model identifier used by the notebooks.
- `SLEEP_BETWEEN_CALLS`: pacing between API calls to reduce rate-limit failures.

Do not commit real secrets from `.env`.

## Install Dependencies

```powershell
py -3.13 -m pip install -r requirements.txt
```

Dependencies currently include:

```text
jupyter
nbconvert
ipykernel
pandas
python-dotenv
requests
matplotlib
```

The imports inside notebooks are enough for a reader to understand the code, but
`requirements.txt` is needed so a new environment can install the same runtime
packages.

## Run the Pipeline

Preview the order without executing notebooks:

```powershell
py -3.13 run_pipeline.py --dry-run
```

Run the full discovered pipeline:

```powershell
py -3.13 run_pipeline.py
```

Run from a specific step:

```powershell
py -3.13 run_pipeline.py --from-step 3
```

Run through a specific step:

```powershell
py -3.13 run_pipeline.py --to-step 5
```

Run only selected steps:

```powershell
py -3.13 run_pipeline.py --only 4 5
```

Use a specific kernel:

```powershell
py -3.13 run_pipeline.py --kernel python3
```

Increase the timeout for long LLM/API notebooks:

```powershell
py -3.13 run_pipeline.py --timeout 14400
```

Write execution output back into source notebooks:

```powershell
py -3.13 run_pipeline.py --inplace
```

By default, executed notebook copies are written to:

```text
artifacts/executed_notebooks/
```

This avoids unnecessary notebook output churn in Git.

## Reproducibility Notes

This project has three levels of reproducibility:

1. Notebook-level reproducibility: the logic exists in notebooks and can be
   rerun in order.
2. Environment-level reproducibility: `requirements.txt` documents the required
   Python packages.
3. Data/API reproducibility: external API calls depend on GitHub state,
   OpenRouter availability, selected model behavior, rate limits, and API keys.

Because the pipeline uses LLM calls, outputs may change between runs even when
the same code is used. For stronger reproducibility, keep generated CSV outputs,
record model names, record run dates, and avoid overwriting important result
files without versioning them.

Docker is not required for the current local workflow. It would be useful later
if the pipeline needs CI, deployment, exact OS-level reproducibility, or easier
handoff to another machine.

## Current Caveats

- The automated runner executes notebooks by filename order only.
- `context_reconstruction_n11.ipynb` currently runs after `n6`, not before `n2`.
- `test_n1.ipynb` currently occupies step `n1`.
- Some notebooks expect handoff CSVs that already exist in the project root.
- Some notebooks contain exploratory analysis cells after the main data-writing
  cells.
- Some notebooks rely on variables created by previous cells, so they should be
  executed from top to bottom.
- Full pipeline execution will make real GitHub and OpenRouter API calls.
- LLM outputs can vary between runs and models.

## Recommended Next Cleanup

The current automation is a good intermediate step, but the cleaner long-term
structure would be:

```text
pipeline/
|-- context_reconstruction.py
|-- context_generation.py
|-- comment_generation.py
|-- pre_deduplication.py
|-- deduplication.py
|-- judge.py
`-- config.py
```

Then notebooks can become thin analysis or experiment layers that call functions
from these Python modules. This would reduce hidden notebook state, make testing
easier, and make the pipeline more reliable when run automatically.

## Suggested Development Workflow

1. Prototype prompt and dataframe changes in notebooks.
2. Move stable logic into `pipeline/*.py`.
3. Keep notebook outputs out of Git unless they are intentional artifacts.
4. Save important generated CSVs with clear names.
5. Use `run_pipeline.py --dry-run` before any full run.
6. Run expensive API notebooks selectively with `--only` or `--from-step`.
7. Record model names and dates for important experiments.
