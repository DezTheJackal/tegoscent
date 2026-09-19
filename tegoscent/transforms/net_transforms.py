"""
transforms/net_transforms.py - IP -> geolocation / ASN / netblock / Shodan.

Free, keyless sources:
  - ip-api.com          geolocation + ISP/org
  - ipwhois (RDAP/whois) ASN + netblock (pip install ipwhois)

Optional, key-gated:
  - Shodan (pip install shodan) - set SHODAN_API_KEY in config or env.
    Without a key this transform is silently skipped, same as Maltego's
    paid transforms degrade gracefully when a TDS seat lacks entitlement.
"""

from __future__ import annotations
import os
from typing import List

import requests

from ..entities import IPv4Address, Location, ASNumber, NetBlock, Organization, Entity
from .base import transform

IP_API_URL = "http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,lat,lon,isp,org,as,query"


@transform("IPv4Address", "ip_to_geolocation", "Free IP geolocation via ip-api.com")
def ip_to_geolocation(entity: IPv4Address, config: dict) -> List[Entity]:
    out: List[Entity] = []
    try:
        resp = requests.get(IP_API_URL.format(ip=entity.value), timeout=config.get("timeout", 10))
        data = resp.json()
    except Exception:
        return out

    if data.get("status") != "success":
        return out

    loc = Location(f"{data.get('city','?')}, {data.get('country','?')}")
    loc.set_property("lat", data.get("lat"))
    loc.set_property("lon", data.get("lon"))
    loc.set_property("region", data.get("regionName"))
    out.append(loc)

    if data.get("isp"):
        out.append(Organization(data["isp"]))
    if data.get("as"):
        out.append(ASNumber(data["as"]))

    return out


@transform("IPv4Address", "ip_to_asn_netblock", "ASN + netblock ownership via RDAP/whois (ipwhois)")
def ip_to_asn_netblock(entity: IPv4Address, config: dict) -> List[Entity]:
    out: List[Entity] = []
    try:
        from ipwhois import IPWhois  # local import: optional dependency
        obj = IPWhois(entity.value)
        res = obj.lookup_rdap(depth=1)
    except Exception:
        return out

    asn = res.get("asn")
    if asn:
        a = ASNumber(f"AS{asn}")
        a.set_property("asn_description", res.get("asn_description"))
        a.set_property("asn_country_code", res.get("asn_country_code"))
        out.append(a)

    cidr = res.get("network", {}).get("cidr")
    if cidr:
        out.append(NetBlock(cidr))

    org_name = res.get("network", {}).get("name")
    if org_name:
        out.append(Organization(org_name))

    return out


@transform("IPv4Address", "ip_to_shodan", "Shodan host lookup - open ports, banners, CVEs (requires SHODAN_API_KEY)")
def ip_to_shodan(entity: IPv4Address, config: dict) -> List[Entity]:
    out: List[Entity] = []
    api_key = config.get("shodan_api_key") or os.environ.get("SHODAN_API_KEY")
    if not api_key:
        return out  # graceful skip, no key configured

    try:
        import shodan
        api = shodan.Shodan(api_key)
        host = api.host(entity.value)
    except Exception:
        return out

    entity.set_property("open_ports", host.get("ports"))
    entity.set_property("shodan_org", host.get("org"))
    entity.set_property("shodan_os", host.get("os"))

    for item in host.get("data", []):
        product = item.get("product", "")
        port = item.get("port", "?")
        note = f"{port}/tcp {product}".strip()
        entity.add_note(note)

    return out
