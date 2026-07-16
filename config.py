"""Load CATDOES config.yaml and inject mothra_text_path into sys.path."""

import sys
from pathlib import Path

import yaml

_CONFIG_SEARCH = [
    Path(__file__).resolve().parent / "config.yaml",
    Path("~/.catdoes/config.yaml").expanduser(),
]


def load_config() -> dict:
    """Read the first config.yaml found and inject mothra_text_path into sys.path.

    Returns the config dict (empty dict if no config file found).
    """
    for path in _CONFIG_SEARCH:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            mothra_path = cfg.get("mothra_text_path")
            if mothra_path:
                resolved = str(Path(mothra_path).expanduser().resolve())
                if resolved not in sys.path:
                    sys.path.insert(0, resolved)
            return cfg
    return {}
