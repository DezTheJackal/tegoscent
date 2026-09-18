"""
Importing this package registers every built-in transform into base.REGISTRY.
Drop a new module in this directory, decorate functions with @transform,
add the import below, and the CLI/engine pick it up automatically.
"""

from . import dns_transforms      # noqa: F401
from . import whois_transforms    # noqa: F401
from . import cert_transforms     # noqa: F401
from . import net_transforms      # noqa: F401
from . import social_transforms   # noqa: F401

from .base import transform, transforms_for, all_transforms, REGISTRY  # noqa: F401
