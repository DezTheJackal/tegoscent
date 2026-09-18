"""
graph.py - the link-analysis graph.

Wraps a networkx.DiGraph so entities become nodes and each transform run
adds a directed, labelled edge from the input entity to every entity it
produced. This is the data structure that visualize.py renders and that
engine.py mutates as transforms run.
"""

from __future__ import annotations
import csv
import json
from typing import Dict, Iterable, List, Optional

import networkx as nx

from .entities import Entity


class TegoGraph:
    def __init__(self) -> None:
        self._g = nx.DiGraph()

    # -- mutation ---------------------------------------------------------

    def add_entity(self, entity: Entity) -> Entity:
        """Add (or merge into) the graph. Returns the canonical stored entity."""
        if self._g.has_node(entity.id):
            existing: Entity = self._g.nodes[entity.id]["entity"]
            existing.properties.update(entity.properties)
            existing.notes.extend(n for n in entity.notes if n not in existing.notes)
            return existing
        self._g.add_node(entity.id, entity=entity)
        return entity

    def add_link(self, src: Entity, dst: Entity, transform: str, label: Optional[str] = None) -> None:
        self.add_entity(src)
        self.add_entity(dst)
        self._g.add_edge(src.id, dst.id, transform=transform, label=label or transform)

    # -- queries ------------------------------------------------------------

    def entities(self) -> List[Entity]:
        return [data["entity"] for _, data in self._g.nodes(data=True)]

    def get(self, entity_id: str) -> Optional[Entity]:
        node = self._g.nodes.get(entity_id)
        return node["entity"] if node else None

    def neighbors_of(self, entity: Entity) -> List[Entity]:
        return [self._g.nodes[n]["entity"] for n in self._g.successors(entity.id)]

    def edge_count(self) -> int:
        return self._g.number_of_edges()

    def node_count(self) -> int:
        return self._g.number_of_nodes()

    def by_type(self, type_name: str) -> List[Entity]:
        return [e for e in self.entities() if e.TYPE == type_name]

    # -- export ---------------------------------------------------------

    def to_json(self) -> str:
        data = {
            "nodes": [e.to_dict() for e in self.entities()],
            "edges": [
                {"source": u, "target": v, **d}
                for u, v, d in self._g.edges(data=True)
            ],
        }
        return json.dumps(data, indent=2, default=str)

    def save_json(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    def save_graphml(self, path: str) -> None:
        # GraphML wants plain attributes; flatten entity/properties into strings.
        export = nx.DiGraph()
        for node_id, data in self._g.nodes(data=True):
            e: Entity = data["entity"]
            export.add_node(
                node_id,
                label=e.value,
                type=e.TYPE,
                properties=json.dumps(e.properties, default=str),
                notes="; ".join(e.notes),
            )
        for u, v, d in self._g.edges(data=True):
            export.add_edge(u, v, transform=d.get("transform", ""), label=d.get("label", ""))
        nx.write_graphml(export, path)

    def save_csv_edgelist(self, path: str) -> None:
        # newline="" is required on Windows: csv.writer does its own line-ending
        # translation, and text-mode "\n" would otherwise get doubled by the
        # platform's own universal-newline translation (blank line per row).
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["source_type", "source_value", "transform", "target_type", "target_value"])
            for u, v, d in self._g.edges(data=True):
                su, sv = self._g.nodes[u]["entity"], self._g.nodes[v]["entity"]
                writer.writerow([su.TYPE, su.value, d.get("transform", ""), sv.TYPE, sv.value])

    @property
    def nx(self) -> nx.DiGraph:
        """Escape hatch to run networkx algorithms (centrality, shortest paths, etc.)."""
        return self._g
