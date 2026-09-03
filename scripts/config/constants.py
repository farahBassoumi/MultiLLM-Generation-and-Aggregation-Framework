N_CONSISTENCY_RUNS = 3

SLEEP_BETWEEN_CALLS = 0.5

DATA_PATH = "../data/"




GPT54_MINI_CONFIG = {
    "name": "gpt-5.4-mini-2026-03-17",
    "reasoning_effort": "low",
    "provider": "openai",
    "api": "chat",

}

GPT4O_MINI_CONFIG = {
    "name": "gpt-4o-mini-2024-07-18",
    "reasoning_effort": "",
    "provider": "openai",
    "api": "chat",

}

GPT_LUNA_CONFIG = {
    "name": "gpt-5.6-luna",
    "reasoning_effort": "medium",
    "provider": "openai",
    "api": "chat",

}

CONTEXT_REL_CONFIG = {
    "name": "gpt-5.6-luna",
    "reasoning_effort": "low",
    "provider": "openai",
    "api": "chat",

}

DEDUP_CONFIG = {
    "name": "gpt-5.6-luna",
    "reasoning_effort": "medium",
    "provider": "openai",
    "api": "chat",
}

GPT_CODEX_CONFIG = {
    "name": "gpt-5.3-codex",
    "reasoning_effort": "low",
    "provider": "openai",
    "api": "responses",

}

GPT_SOL_CONFIG = {
    "name": "gpt-5.6-sol",
    "reasoning_effort": "low",
    "provider": "openai",
    "api": "chat",

}

GPT_OSS_CONFIG = {
    "name": "openai/gpt-oss-120b",
    "reasoning_effort": "medium",
    "provider": "huggingface",
    "api": "huggingface",
}

MODELS_TO_RUN = [
    "gpt54_mini"
    # "gpt4o_mini",
    # "gpt_luna",
    # "gpt_codex",
    # "gpt_sol",
    # "gpt_oss",
]


VALID_CATEGORIES = {
    "Correctness",
    "Design",
    "Maintainability",
    "Readability",
    "Documentation",
}

GENERATION_MODELS = {
    "gpt54_mini": GPT54_MINI_CONFIG,
    "gpt4o_mini": GPT4O_MINI_CONFIG,
    "gpt_luna": GPT_LUNA_CONFIG,
    "gpt_codex": GPT_CODEX_CONFIG,
    "gpt_sol": GPT_SOL_CONFIG,
    "gpt_oss": GPT_OSS_CONFIG,
}
