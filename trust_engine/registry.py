"""
TrustCloud AI — Validator Registry
Plugin-based registry with dynamic registration and auto-discovery.
"""

import logging
from typing import Dict, List, Optional, Type

from validators.base import BaseValidator

logger = logging.getLogger("trustcloud.registry")


class ValidatorRegistry:
    """
    Central registry for all validators.

    Responsibilities:
    - Register validator classes or instances
    - Auto-discover built-in validators
    - Provide lookup by name
    - Enforce uniqueness (no duplicate names)
    - List all registered validators with metadata
    """

    def __init__(self):
        self._validators: Dict[str, BaseValidator] = {}

    def register(self, validator: BaseValidator) -> None:
        """
        Register a validator instance.

        Raises:
            ValueError: If a validator with the same name is already registered.
        """
        if validator.name in self._validators:
            raise ValueError(
                f"Validator '{validator.name}' is already registered "
                f"(version: {self._validators[validator.name].version}). "
                f"Cannot register duplicate."
            )
        self._validators[validator.name] = validator
        logger.info(
            f"Registered validator: {validator.name} (version={validator.version}, "
            f"weight={validator.default_weight}, inverted={validator.inverted})"
        )

    def register_class(self, cls: Type[BaseValidator]) -> None:
        """Register a validator by class (instantiates it)."""
        self.register(cls())

    def get(self, name: str) -> Optional[BaseValidator]:
        """Get a validator by name. Returns None if not found."""
        return self._validators.get(name)

    def get_many(self, names: List[str]) -> List[BaseValidator]:
        """
        Get multiple validators by name.

        Raises:
            KeyError: If any requested validator name is not registered.
        """
        result = []
        for name in names:
            v = self._validators.get(name)
            if v is None:
                available = list(self._validators.keys())
                raise KeyError(
                    f"Validator '{name}' not found. Available: {available}"
                )
            result.append(v)
        return result

    def all(self) -> List[BaseValidator]:
        """Return all registered validators."""
        return list(self._validators.values())

    def names(self) -> List[str]:
        """Return all registered validator names."""
        return list(self._validators.keys())

    def info(self) -> List[dict]:
        """Return metadata about all registered validators (epistemic model)."""
        return [
            {
                "name": v.name,
                "version": v.version,
                "default_weight": v.default_weight,
                "signal_type": v.signal_type,
                "method_type": v.method_type,
                "inverted": v.inverted,
            }
            for v in self._validators.values()
        ]

    def auto_discover(self) -> None:
        """
        Auto-discover and register all built-in validators.
        Imports from validators package BUILTIN_VALIDATORS list.
        """
        from validators import BUILTIN_VALIDATORS

        for cls in BUILTIN_VALIDATORS:
            try:
                self.register_class(cls)
            except ValueError:
                logger.warning(f"Skipping already-registered validator: {cls.__name__}")

    def __len__(self) -> int:
        return len(self._validators)

    def __contains__(self, name: str) -> bool:
        return name in self._validators
