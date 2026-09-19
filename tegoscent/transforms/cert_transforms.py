"""
transforms/cert_transforms.py - Certificate-transparency subdomain discovery.

Uses crt.sh (no API key required). This is the free, passive equivalent of
Maltego's paid "ToDomainDNS" / CT-log transforms.
"""

from __future__ import annotations
from typing import List, Set

import requests

from ..entities import Domain, SSLCertificate, Entity
from .base import transform

CRTSH_URL = "https://crt.sh/?q=%25.{domain}&output=json"


@transform("Domain", "domain_to_subdomains_ct", "Enumerate subdomains via crt.sh certificate transparency logs")
def domain_to_subdomains_ct(entity: Domain, config: dict) -> List[Entity]:
    out: List[Entity] = []
    seen: Set[str] = set()
    try:
        resp = requests.get(
            CRTSH_URL.format(domain=entity.value),
            timeout=config.get("timeout", 15),
            headers={"User-Agent": "TegoScent/1.0"},
        )
        resp.raise_for_status()
        rows = resp.json()
    except Exception:
        return out

    for row in rows:
        name_value = row.get("name_value", "")
        for name in name_value.split("\n"):
            name = name.strip().lstrip("*.").lower()
            if name and name not in seen and entity.value in name:
                seen.add(name)
                out.append(Domain(name))

        cert = SSLCertificate(row.get("serial_number", row.get("id", "unknown")))
        cert.set_property("issuer", row.get("issuer_name"))
        cert.set_property("not_before", row.get("not_before"))
        cert.set_property("not_after", row.get("not_after"))
        out.append(cert)

    return out
