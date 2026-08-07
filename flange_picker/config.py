"""Nalaganje konfiguracije.

config.yaml je edini vir resnice za konstante in pragove. Ta modul ne vsebuje
privzetih vrednosti - ce kljuc manjka, javi jasno napako namesto tihega ugibanja.
"""

from __future__ import annotations

import copy
import os
from typing import Any, Dict, Optional

import yaml

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")


class ConfigError(KeyError):
    """Manjkajoc ali napacen konfiguracijski kljuc."""


class Config:
    """Tanka ovojnica okoli slovarja s pikovnim dostopom in jasnimi napakami."""

    def __init__(self, data: Dict[str, Any], path: Optional[str] = None):
        self._data = data
        self.path = path

    # -- dostop -----------------------------------------------------------
    def get(self, dotted: str, default: Any = "__raise__") -> Any:
        node: Any = self._data
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                if default == "__raise__":
                    raise ConfigError(
                        f"manjka konfiguracijski kljuc '{dotted}' (datoteka: {self.path})"
                    )
                return default
            node = node[part]
        return node

    def __getitem__(self, dotted: str) -> Any:
        return self.get(dotted)

    def section(self, dotted: str) -> "Config":
        node = self.get(dotted)
        if not isinstance(node, dict):
            raise ConfigError(f"'{dotted}' ni sekcija (datoteka: {self.path})")
        return Config(node, self.path)

    def as_dict(self) -> Dict[str, Any]:
        return copy.deepcopy(self._data)

    def with_overrides(self, overrides: Dict[str, Any]) -> "Config":
        """Vrne novo konfiguracijo z globoko zlitimi popravki."""
        return Config(_deep_merge(copy.deepcopy(self._data), overrides), self.path)

    def set(self, dotted: str, value: Any) -> None:
        parts = dotted.split(".")
        node = self._data
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value


def _deep_merge(base: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def load_config(path: Optional[str] = None, overrides: Optional[Dict[str, Any]] = None) -> Config:
    path = path or DEFAULT_CONFIG_PATH
    if not os.path.exists(path):
        raise ConfigError(f"konfiguracijska datoteka ne obstaja: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"konfiguracija mora biti slovar, dobil {type(data).__name__}")
    cfg = Config(data, path)
    if overrides:
        cfg = cfg.with_overrides(overrides)
    return cfg
