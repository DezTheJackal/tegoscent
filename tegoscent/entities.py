"""
entities.py - TegoScent entity model.

Every node in a TegoScent graph is an Entity subclass. This mirrors Maltego's
concept of typed entities (Domain, IPv4Address, Email, Person, etc.) so that
transforms can be dispatched by input type, and the graph can render each
entity with a distinct icon/color.

Usage:
    d = Domain("example.com")
    d.set_property("registrar", "MarkMonitor Inc.")
"""

from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class Entity:
    """Base class for every OSINT entity (graph node)."""

    TYPE: str = "Entity"
    ICON: str = "circle"
    COLOR: str = "#8a8a8a"

    def __init__(self, value: str, properties: Optional[Dict[str, Any]] = None):
        self.value: str = value
        self.properties: Dict[str, Any] = properties.copy() if properties else {}
        self.notes: list[str] = []

    @property
    def id(self) -> str:
        """Stable, content-addressed node id: TYPE:sha1(value)[:12]."""
        h = hashlib.sha1(self.value.encode("utf-8", "ignore")).hexdigest()[:12]
        return f"{self.TYPE}:{h}"

    def set_property(self, key: str, value: Any) -> None:
        self.properties[key] = value

    def add_note(self, note: str) -> None:
        self.notes.append(note)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.TYPE,
            "value": self.value,
            "properties": self.properties,
            "notes": self.notes,
        }

    def __repr__(self) -> str:
        return f"<{self.TYPE} '{self.value}'>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Entity) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


class Domain(Entity):
    TYPE = "Domain"
    ICON = "globe"
    COLOR = "#3498db"


class IPv4Address(Entity):
    TYPE = "IPv4Address"
    ICON = "server"
    COLOR = "#2ecc71"


class URL(Entity):
    TYPE = "URL"
    ICON = "link"
    COLOR = "#9b59b6"


class EmailAddress(Entity):
    TYPE = "EmailAddress"
    ICON = "mail"
    COLOR = "#e67e22"


class PhoneNumber(Entity):
    TYPE = "PhoneNumber"
    ICON = "phone"
    COLOR = "#e74c3c"


class Person(Entity):
    TYPE = "Person"
    ICON = "user"
    COLOR = "#f1c40f"


class Organization(Entity):
    TYPE = "Organization"
    ICON = "building"
    COLOR = "#1abc9c"


class Username(Entity):
    TYPE = "Username"
    ICON = "at-sign"
    COLOR = "#34495e"


class ASNumber(Entity):
    TYPE = "ASNumber"
    ICON = "network"
    COLOR = "#7f8c8d"


class NetBlock(Entity):
    TYPE = "NetBlock"
    ICON = "grid"
    COLOR = "#95a5a6"


class DNSRecord(Entity):
    TYPE = "DNSRecord"
    ICON = "list"
    COLOR = "#16a085"


class SSLCertificate(Entity):
    TYPE = "SSLCertificate"
    ICON = "lock"
    COLOR = "#c0392b"


class Document(Entity):
    TYPE = "Document"
    ICON = "file-text"
    COLOR = "#8e44ad"


class Hash(Entity):
    TYPE = "Hash"
    ICON = "hash"
    COLOR = "#2c3e50"


class Location(Entity):
    TYPE = "Location"
    ICON = "map-pin"
    COLOR = "#d35400"


class BreachRecord(Entity):
    TYPE = "BreachRecord"
    ICON = "alert-triangle"
    COLOR = "#c0392b"


# Registry used by the CLI to resolve --type strings to classes.
ENTITY_TYPES: Dict[str, type] = {
    cls.TYPE: cls
    for cls in [
        Domain, IPv4Address, URL, EmailAddress, PhoneNumber, Person,
        Organization, Username, ASNumber, NetBlock, DNSRecord,
        SSLCertificate, Document, Hash, Location, BreachRecord,
    ]
}


def make_entity(type_name: str, value: str) -> Entity:
    cls = ENTITY_TYPES.get(type_name)
    if cls is None:
        raise ValueError(
            f"Unknown entity type '{type_name}'. Valid types: {', '.join(ENTITY_TYPES)}"
        )
    return cls(value)
