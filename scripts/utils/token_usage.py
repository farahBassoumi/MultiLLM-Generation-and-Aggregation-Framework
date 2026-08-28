# utils/token_usage.py

import json
from datetime import datetime
from pathlib import Path


def create_usage_stats():
    return {
        "prompt_tokens": 0,
        "reasoning_tokens": 0,
        "total_tokens": 0,
        "num_calls": 0,
    }


def update_usage(usage_stats, usage):
    """
    Accumulate token usage for one model execution.
    """

    u = usage.model_dump()

    usage_stats["prompt_tokens"] += u.get(
        "prompt_tokens", 0
    )

    usage_stats["total_tokens"] += u.get(
        "total_tokens", 0
    )

    usage_stats["reasoning_tokens"] += (
        u.get("completion_tokens_details", {})
         .get("reasoning_tokens", 0)
    )

    usage_stats["num_calls"] += 1

def save_token_usage_log(
    usage_stats,
    model_name,
    task_name,
    execution_duration,
    additional_stats=None,
    log_file="../logs/token_usage_insights_logs.json",
):
    usage_log = {
        "task": task_name,
        "timestamp": datetime.now().isoformat(),
        "model_name": model_name,
        "num_calls": usage_stats["num_calls"],
        "prompt_tokens": usage_stats["prompt_tokens"],
        "reasoning_tokens": usage_stats["reasoning_tokens"],
        "total_tokens": usage_stats["total_tokens"],
        "execution_duration_seconds": round(
            execution_duration, 3
        ),
    }

    if additional_stats:
        usage_log.update(additional_stats)

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(log_path, "r") as f:
            logs = json.load(f)

    except (FileNotFoundError, json.JSONDecodeError):
        logs = []

    logs.append(usage_log)

    with open(log_path, "w") as f:
        json.dump(logs, f, indent=4)

    print(f"Token usage saved to {log_path}")