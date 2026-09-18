"""
transforms/dns_transforms.py - Domain <-> DNS/IP transforms.

Requires: dnspython (`pip install dnspython`)
"""

from __future__ import annotations
from typing import List

import dns.resolver
import dns.reversename

from ..entities import Domain, IPv4Address, DNSRecord, Entity
from .base import transform


def _resolve(name: str, rtype: str):
    resolver = dns.resolver.Resolver()
    resolver.timeout = 4
    resolver.lifetime = 4
    return resolver.resolve(name, rtype)


@transform("Domain", "domain_to_a_record", "Resolve A records for a domain")
def domain_to_a(entity: Domain, config: dict) -> List[Entity]:
    out: List[Entity] = []
    try:
        for rdata in _resolve(entity.value, "A"):
            out.append(IPv4Address(rdata.address))
    except Exception:
        pass
    return out


@transform("Domain", "domain_to_mx", "Resolve MX records for a domain")
def domain_to_mx(entity: Domain, config: dict) -> List[Entity]:
    out: List[Entity] = []
    try:
        for rdata in _resolve(entity.value, "MX"):
            host = str(rdata.exchange).rstrip(".")
            rec = DNSRecord(f"MX: {host}")
            rec.set_property("preference", rdata.preference)
            rec.set_property("exchange", host)
            out.append(rec)
            out.append(Domain(host))
    except Exception:
        pass
    return out


@transform("Domain", "domain_to_ns", "Resolve NS records for a domain")
def domain_to_ns(entity: Domain, config: dict) -> List[Entity]:
    out: List[Entity] = []
    try:
        for rdata in _resolve(entity.value, "NS"):
            out.append(Domain(str(rdata.target).rstrip(".")))
    except Exception:
        pass
    return out


@transform("Domain", "domain_to_txt", "Resolve TXT records (SPF, DKIM, verification tokens)")
def domain_to_txt(entity: Domain, config: dict) -> List[Entity]:
    out: List[Entity] = []
    try:
        for rdata in _resolve(entity.value, "TXT"):
            txt = b"".join(rdata.strings).decode("utf-8", "ignore")
            rec = DNSRecord(txt[:120])
            rec.set_property("full_value", txt)
            out.append(rec)
    except Exception:
        pass
    return out


@transform("IPv4Address", "ip_to_ptr", "Reverse DNS (PTR) lookup on an IP")
def ip_to_ptr(entity: IPv4Address, config: dict) -> List[Entity]:
    out: List[Entity] = []
    try:
        rev = dns.reversename.from_address(entity.value)
        for rdata in _resolve(str(rev), "PTR"):
            out.append(Domain(str(rdata.target).rstrip(".")))
    except Exception:
        pass
    return out
