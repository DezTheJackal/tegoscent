"""
transforms/base.py - the transform contract.

A transform is: (input entity type) -> list[Entity]. Register one with the
@transform decorator; the engine looks transforms up by the input entity's
TYPE string. This is the same "input type dispatches applicable transforms"
model Maltego uses.
"""

from __future__ import annotations
import logging
from typing import Callable, Dict, List

from ..entities import Entity

logger = logging.getLogger("tegoscent.transforms")

# input_type -> list of (name, function, description)
REGISTRY: Dict[str, List[dict]] = {}


def transform(input_type: str, name: str, description: str = ""):
    """
    Decorator to register a transform function.

    The decorated function must have the signature:
        def fn(entity: Entity, config: dict) -> list[Entity]
    and should never raise on expected failure (no data, timeout, no API key) -
    log and return [] instead, so one bad transform doesn't kill a run.
    """

    def decorator(fn: Callable[[Entity, dict], List[Entity]]):
        REGISTRY.setdefault(input_type, []).append(
            {"name": name, "fn": fn, "description": description}
        )
        return fn

    return decorator


def transforms_for(type_name: str) -> List[dict]:
    return REGISTRY.get(type_name, [])


def all_transforms() -> Dict[str, List[dict]]:
    return REGISTRY


def safe_run(fn, entity: Entity, config: dict, transform_name: str) -> List[Entity]:
    try:
        result = fn(entity, config) or []
        logger.info("transform=%s input=%s -> %d entities", transform_name, entity.value, len(result))
        return result
    except Exception as exc:  # noqa: BLE001 - transforms must not crash a run
        logger.warning("transform=%s input=%s failed: %s", transform_name, entity.value, exc)
        return []
