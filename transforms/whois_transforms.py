"""
transforms/whois_transforms.py - Domain -> WHOIS registration data.

Requires: python-whois (`pip install python-whois`)
"""

from __future__ import annotations
from typing import List

import whois  # python-whois

from ..entities import Domain, Organization, EmailAddress, Entity
from .base import transform


@transform("Domain", "domain_to_whois", "Pull WHOIS registrant/registrar/date data")
def domain_to_whois(entity: Domain, config: dict) -> List[Entity]:
    out: List[Entity] = []
    try:
        w = whois.whois(entity.value)
    except Exception:
        return out

    if not w:
        return out

    entity.set_property("registrar", w.registrar)
    entity.set_property("creation_date", str(w.creation_date))
    entity.set_property("expiration_date", str(w.expiration_date))
    entity.set_property("name_servers", w.name_servers)

    org = getattr(w, "org", None) or getattr(w, "organization", None)
    if org:
        out.append(Organization(str(org)))

    emails = w.emails
    if emails:
        emails = [emails] if isinstance(emails, str) else emails
        for e in emails:
            out.append(EmailAddress(e))

    return out
