"""
engine.py - breadth-first transform execution ("running a machine").

Given one or more seed entities, repeatedly:
  1. Look up every transform registered for each frontier entity's type.
  2. Run them (concurrently - these are network calls) via base.safe_run.
  3. Add resulting entities + provenance edges to the graph.
  4. The results become next depth's frontier.

Loop protection: an (entity_id, transform_name) pair only ever runs once,
so cyclic data (A resolves to B, B reverse-resolves to A) can't spin forever.
"""

from __future__ import annotations
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Iterable, List, Optional, Set, Tuple

from .entities import Entity
from .graph import TegoGraph
from .transforms.base import transforms_for, safe_run

logger = logging.getLogger("tegoscent.engine")


# Named transform chains - the free equivalent of Maltego's "Machines".
# Each is a whitelist of transform names to run, applied at every depth level.
MACHINES: Dict[str, List[str]] = {
    "footprint_l1": [
        "domain_to_a_record", "domain_to_ns", "domain_to_mx",
        "domain_to_subdomains_ct",
    ],
    "footprint_l2": [
        "domain_to_a_record", "domain_to_ns", "domain_to_mx", "domain_to_txt",
        "domain_to_subdomains_ct", "domain_to_whois",
        "ip_to_ptr", "ip_to_geolocation", "ip_to_asn_netblock", "ip_to_shodan",
    ],
    "person_footprint": [
        "email_to_hibp_breaches", "username_to_social_profiles",
        "phone_to_carrier_info",
    ],
    "full_recon": [],  # empty whitelist == run every registered transform
}


class Engine:
    def __init__(self, graph: TegoGraph, config: dict, max_workers: int = 8):
        self.graph = graph
        self.config = config
        self.max_workers = max_workers
        self._ran: Set[Tuple[str, str]] = set()  # (entity_id, transform_name)

    def run(
        self,
        seeds: Iterable[Entity],
        depth: int = 2,
        allowed_transforms: Optional[List[str]] = None,
    ) -> TegoGraph:
        frontier: List[Entity] = [self.graph.add_entity(e) for e in seeds]

        for level in range(depth):
            if not frontier:
                break
            logger.info("=== depth %d/%d, frontier size %d ===", level + 1, depth, len(frontier))
            frontier = self._expand(frontier, allowed_transforms)

        return self.graph

    def _expand(self, frontier: List[Entity], allowed_transforms: Optional[List[str]]) -> List[Entity]:
        jobs: List[Tuple[Entity, dict]] = []
        for entity in frontier:
            for t in transforms_for(entity.TYPE):
                if allowed_transforms and t["name"] not in allowed_transforms:
                    continue
                key = (entity.id, t["name"])
                if key in self._ran:
                    continue
                self._ran.add(key)
                jobs.append((entity, t))

        next_frontier: List[Entity] = []
        if not jobs:
            return next_frontier

        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {
                pool.submit(safe_run, t["fn"], entity, self.config, t["name"]): (entity, t)
                for entity, t in jobs
            }
            for fut in as_completed(futures):
                entity, t = futures[fut]
                results = fut.result()
                for result_entity in results:
                    stored = self.graph.add_entity(result_entity)
                    self.graph.add_link(entity, stored, t["name"])
                    next_frontier.append(stored)

        return next_frontier
