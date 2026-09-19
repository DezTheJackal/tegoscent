"""
transforms/social_transforms.py - identity-centric OSINT transforms.

Keyless:
  - Username -> social profile existence (Sherlock/WhatsMyName-style probing
    of a curated site list; HTTP status only, no scraping of profile content)
  - PhoneNumber -> carrier/region/line-type (via `phonenumbers`, Google's
    offline libphonenumber port - no API call at all)

Key-gated (graceful skip without a key):
  - EmailAddress -> known breaches (Have I Been Pwned v3)
"""

from __future__ import annotations
import os
from typing import List

import requests

from ..entities import Username, URL, PhoneNumber, Location, Organization, EmailAddress, BreachRecord, Entity
from .base import transform

# A small, curated set of sites to probe for username OSINT. Each entry is
# (site name, URL template, HTTP status code that means "profile exists").
# Extend this list freely - it's the free equivalent of Maltego's paid
# "SocialNet" transform set.
USERNAME_SITES = [
    ("GitHub", "https://github.com/{u}", 200),
    ("GitLab", "https://gitlab.com/{u}", 200),
    ("Reddit", "https://www.reddit.com/user/{u}/about.json", 200),
    ("Instagram", "https://www.instagram.com/{u}/", 200),
    ("Twitter/X", "https://x.com/{u}", 200),
    ("Twitch", "https://www.twitch.tv/{u}", 200),
    ("Keybase", "https://keybase.io/{u}", 200),
    ("HackerNews", "https://news.ycombinator.com/user?id={u}", 200),
    ("Medium", "https://medium.com/@{u}", 200),
    ("DockerHub", "https://hub.docker.com/u/{u}/", 200),
    ("TikTok", "https://www.tiktok.com/@{u}", 200),
    ("Telegram", "https://t.me/{u}", 200),
]


@transform("Username", "username_to_social_profiles", "Probe curated site list for account existence (Sherlock-style)")
def username_to_social_profiles(entity: Username, config: dict) -> List[Entity]:
    out: List[Entity] = []
    timeout = config.get("timeout", 6)
    headers = {"User-Agent": "Mozilla/5.0 (TegoScent OSINT)"}

    for site_name, template, ok_status in USERNAME_SITES:
        url = template.format(u=entity.value)
        try:
            resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        except Exception:
            continue
        if resp.status_code == ok_status:
            found = URL(url)
            found.set_property("site", site_name)
            found.set_property("status_code", resp.status_code)
            out.append(found)

    return out


@transform("PhoneNumber", "phone_to_carrier_info", "Offline carrier/region/line-type lookup via libphonenumber")
def phone_to_carrier_info(entity: PhoneNumber, config: dict) -> List[Entity]:
    out: List[Entity] = []
    try:
        import phonenumbers
        from phonenumbers import carrier, geocoder, number_type
    except ImportError:
        return out

    try:
        parsed = phonenumbers.parse(entity.value, None)
    except Exception:
        return out

    if not phonenumbers.is_valid_number(parsed):
        entity.set_property("valid", False)
        return out

    entity.set_property("valid", True)
    entity.set_property("country_code", parsed.country_code)
    entity.set_property("national_number", parsed.national_number)
    entity.set_property("line_type", str(number_type(parsed)))

    carrier_name = carrier.name_for_number(parsed, "en")
    if carrier_name:
        out.append(Organization(carrier_name))

    region = geocoder.description_for_number(parsed, "en")
    if region:
        out.append(Location(region))

    return out


@transform("EmailAddress", "email_to_hibp_breaches", "Known-breach lookup via HaveIBeenPwned v3 (requires HIBP_API_KEY)")
def email_to_hibp_breaches(entity: EmailAddress, config: dict) -> List[Entity]:
    out: List[Entity] = []
    api_key = config.get("hibp_api_key") or os.environ.get("HIBP_API_KEY")
    if not api_key:
        return out  # graceful skip, no key configured

    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{entity.value}"
    headers = {"hibp-api-key": api_key, "User-Agent": "TegoScent/1.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=config.get("timeout", 10))
    except Exception:
        return out

    if resp.status_code == 404:
        entity.set_property("known_breaches", 0)
        return out
    if resp.status_code != 200:
        return out

    for breach in resp.json():
        rec = BreachRecord(breach.get("Name", "UnknownBreach"))
        rec.set_property("breach_date", breach.get("BreachDate"))
        rec.set_property("data_classes", breach.get("DataClasses"))
        rec.set_property("pwn_count", breach.get("PwnCount"))
        out.append(rec)

    return out
