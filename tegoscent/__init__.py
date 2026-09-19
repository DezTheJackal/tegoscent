"""TegoScent - free, open-source Maltego-style link-analysis / OSINT tool."""

__version__ = "1.0.0"

from .entities import Entity, ENTITY_TYPES, make_entity  # noqa: F401
from .graph import TegoGraph  # noqa: F401
from .engine import Engine, MACHINES  # noqa: F401
