from __future__ import annotations

"""Shared helpers for configuration merging and loading.

These utilities are used by both the ingestion and retrieval pipelines so that
we only maintain one implementation.
"""

from pathlib import Path
from typing import Any, Dict

import yaml

__all__ = ["deep_update", "load_config"]


def deep_update(target: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge *src* into *target* (modifies *target* in-place)."""
    for key, value in src.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            deep_update(target[key], value)
        else:
            target[key] = value
    return target


def load_config(defaults: Dict[str, Any], path: str | Path | None = None) -> Dict[str, Any]:
    """Return a configuration dict by overlaying YAML overrides onto *defaults*.

    Parameters
    ----------
    defaults: Dict[str, Any]
        The base configuration.
    path: str | Path | None
        If provided, the YAML file at *path* is read and merged recursively into
        *defaults*.  Values present in the YAML override the defaults.
    """
    cfg: Dict[str, Any] = defaults.copy()
    if path:
        yaml_path = Path(path).expanduser()
        if yaml_path.is_file():
            with yaml_path.open("r", encoding="utf-8") as fh:
                user_cfg = yaml.safe_load(fh) or {}
            if not isinstance(user_cfg, dict):
                raise ValueError("Top-level YAML content must be a mapping/dict")
            deep_update(cfg, user_cfg)
        else:
            raise FileNotFoundError(yaml_path)
    return cfg
