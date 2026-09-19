
"""
config.py - API key / runtime settings loader.

Precedence: CLI flag > config file (~/.tegoscent.json or --config) > env var.
Never hardcode keys; this just centralizes where transforms look for them.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG_PATH = Path.home() / ".tegoscent.json"

ENV_MAP = {
    "shodan_api_key": "SHODAN_API_KEY",
    "hibp_api_key": "HIBP_API_KEY",
    "opencellid_api_key": "OPENCELLID_API_KEY",
}


def load_config(path: str | None = None, timeout: int = 10, max_depth: int = 2) -> Dict[str, Any]:
    cfg: Dict[str, Any] = {"timeout": timeout, "max_depth": max_depth}

    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception as exc:
            print(f"[!] Could not parse config file {config_path}: {exc}")

    for cfg_key, env_key in ENV_MAP.items():
        if not cfg.get(cfg_key) and os.environ.get(env_key):
            cfg[cfg_key] = os.environ[env_key]

    return cfg
