# TegoScent

A free, open-source, Maltego-style link-analysis / OSINT tool. Feed it a seed
entity (domain, IP, email, phone, username...), it runs a graph of transforms
against it and everything the transforms find, and renders the result as an
interactive link-analysis graph - the same core workflow as Maltego CE/Pro,
without the license.

Built by DezTheJackal for  engagements: recon, OSINT, footprinting.

## What it does (and doesn't)

TegoScent reimplements Maltego's **architecture** - typed entities, transforms
dispatched by input type, a directed provenance graph, "machines" (saved
transform chains), and interactive graph export - using free/keyless data
sources wherever one exists, and optional API keys for sources that require
them (Shodan, HaveIBeenPwned). It is **not** a clone of Maltego's proprietary
Transform Hub content, CTAS integrations, or commercial data partnerships -
those are Paterva/Maltego IP. Think "Maltego CE, but every transform is one
you can read, and you can add your own in ten lines."

## Install

Tested on Windows, Linux and macOS - pure-Python dependencies only, no
compiled extensions and no OS-specific code paths.

**Linux / macOS** (bash/zsh):
```bash
git clone https://github.com/<your-username>/tegoscent.git
cd tegoscent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .          # optional: gives you the `tegoscent` command
```

**Windows** (PowerShell):
```powershell
git clone https://github.com/<your-username>/tegoscent.git
cd tegoscent
py -3 -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .          # optional: gives you the `tegoscent` command
```
If PowerShell blocks the activation script, run once as admin:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. cmd.exe users activate
with `venv\Scripts\activate.bat` instead.

Without `pip install -e .`, run it as a module on any OS:
`python3 -m tegoscent ...` (Linux/macOS) or `py -m tegoscent ...` (Windows).

Config file location (`~/.tegoscent.json` by default) resolves via
`pathlib.Path.home()`, so it's `~/.tegoscent.json` on Linux/macOS and
`C:\Users\<you>\.tegoscent.json` on Windows automatically - no path editing
needed. Override with `--config <path>` on any platform.

## Quick start

```bash
# Full footprint of a domain, 2 hops deep, interactive graph
tegoscent run Domain example.com --machine footprint_l2 --depth 2 -o recon.html

# Just DNS + CT-log subdomain enum, exported as JSON for scripting
tegoscent run Domain example.com --machine footprint_l1 --format json -o recon.json

# Person-centric OSINT (breach check needs HIBP_API_KEY; profile probe is keyless)
tegoscent run EmailAddress target@example.com --machine person_footprint

# Username -> which of a dozen platforms have that handle
tegoscent run Username someuser --depth 1

# See what's registered
tegoscent list-entities
tegoscent list-transforms
tegoscent list-machines
```

Open the `.html` output in a browser: drag nodes, scroll to zoom, hover a
node for every property a transform attached to it.

## Startup banner

Every run prints a neon cyberpunk logo (cyan → violet → magenta gradient via
24-bit ANSI). Running `tegoscent` with no arguments, or `tegoscent --help`,
also prints a "replace the `<...>` placeholders with your target" quick-start
guide underneath it:

```
 _______ ______ _____  ____   _____  _____ ______ _   _ _______
|__   __|  ____/ ____|/ __ \ / ____|/ ____|  ____| \ | |__   __|
   | |  | |__ | |  __| |  | | (___ | |    | |__  |  \| |  | |
   | |  |  __|| | |_ | |  | |\___ \| |    |  __| | . ` |  | |
   | |  | |___| |__| | |__| |____) | |____| |____| |\  |  | |
   |_|  |______\_____|\____/|_____/ \_____|______|_| \_|  |_|
────────────────────────────────────────────────────────────────
         FREE & OPEN-SOURCE OSINT LINK-ANALYSIS ENGINE
         root@tegoscent:~# initiate_recon --target ???
────────────────────────────────────────────────────────────────

QUICK START

  SYNTAX:
    tegoscent run <ENTITY_TYPE> <TARGET_VALUE> [OPTIONS]

  EXAMPLES  -  replace every <...> placeholder with your real target

    tegoscent run Domain <target-domain.com> --machine footprint_l2 --depth 2 -o report.html
    tegoscent run EmailAddress <target@example.com> --machine person_footprint
    tegoscent run Username <target_handle> --depth 1
    tegoscent run IPv4Address <1.2.3.4> --machine footprint_l2 --format json -o report.json
    tegoscent run PhoneNumber <+15551234567> --machine person_footprint
```

(shown here without color - in a real terminal the logo renders as a cyan →
violet → magenta gradient, placeholders in bold hot pink, section headers in
acid green.)

Color is skipped automatically when output isn't a terminal, or when
`NO_COLOR`/`TEGOSCENT_NO_COLOR` is set (the [no-color.org](https://no-color.org)
convention). To suppress the banner entirely - useful when piping tegoscent's
stdout into another tool or a script - pass `--no-banner` or set
`TEGOSCENT_NO_BANNER=1`.

## API keys (optional)

Set via environment variable or `~/.tegoscent.json`:

| Key | Env var | Unlocks |
|---|---|---|
| Shodan | `SHODAN_API_KEY` | `ip_to_shodan` - open ports/banners/CVEs |
| HaveIBeenPwned | `HIBP_API_KEY` | `email_to_hibp_breaches` |

```json
// ~/.tegoscent.json
{"shodan_api_key": "...", "hibp_api_key": "..."}
```

Transforms without a configured key skip silently - everything else still runs.

## Entity types

`Domain, IPv4Address, URL, EmailAddress, PhoneNumber, Person, Organization,
Username, ASNumber, NetBlock, DNSRecord, SSLCertificate, Document, Hash,
Location, BreachRecord`

## Built-in transforms

| Input | Transform | Source | Key needed |
|---|---|---|---|
| Domain | `domain_to_a_record` / `_mx` / `_ns` / `_txt` | DNS | no |
| Domain | `domain_to_whois` | WHOIS | no |
| Domain | `domain_to_subdomains_ct` | crt.sh CT logs | no |
| IPv4Address | `ip_to_ptr` | reverse DNS | no |
| IPv4Address | `ip_to_geolocation` | ip-api.com | no |
| IPv4Address | `ip_to_asn_netblock` | RDAP (ipwhois) | no |
| IPv4Address | `ip_to_shodan` | Shodan | **yes** |
| Username | `username_to_social_profiles` | 12-site probe | no |
| PhoneNumber | `phone_to_carrier_info` | libphonenumber (offline) | no |
| EmailAddress | `email_to_hibp_breaches` | HIBP v3 | **yes** |

## Writing your own transform

Drop a function in a module under `tegoscent/transforms/`, decorate it, and
import the module from `tegoscent/transforms/__init__.py`:

```python
from ..entities import Domain, Organization
from .base import transform

@transform("Domain", "domain_to_favicon_hash", "Fetch favicon and compute mmh3 hash for Shodan pivoting")
def domain_to_favicon_hash(entity: Domain, config: dict) -> list:
    ...  # return a list of Entity objects, or [] on no data - never raise
```

The engine dispatches by the input's `TYPE` string automatically. No registry
edits needed beyond the one import.

## Architecture

```
tegoscent/
  entities.py     typed graph nodes (Domain, IPv4Address, ...)
  graph.py        TegoGraph: networkx.DiGraph wrapper + JSON/GraphML/CSV export
  transforms/
    base.py       @transform decorator + registry + safe_run (never crashes a run)
    *.py          transform implementations, grouped by data source
  engine.py       breadth-first transform runner + named "machines"
  visualize.py    pyvis interactive HTML graph renderer
  config.py       API key / timeout loading (file > env)
  cli.py          argparse CLI
```

## Platform notes

- **Console output**: `cli.py` reconfigures stdout/stderr to UTF-8 on startup,
  so non-ASCII domain names (IDNs) and Unicode in WHOIS/breach data print
  cleanly even on Windows terminals still defaulting to a legacy codepage.
- **CSV export**: written via Python's `csv` module with `newline=""`, which
  avoids the classic Windows bug where text-mode line-ending translation
  doubles up with the csv writer's own `\r\n` and leaves a blank line after
  every row.
- **Output paths**: `tegoscent run ... -o some/new/folder/report.html` creates
  intermediate directories automatically on any OS (`pathlib`-based, no
  `mkdir -p` shell-out).
- **DNS resolution**: `dnspython` >= 2.6 reads nameserver configuration from
  the Windows registry directly on Windows and from `/etc/resolv.conf` on
  Linux/macOS - no manual resolver setup needed on any platform.
- **No shell-outs**: every transform (DNS, WHOIS, crt.sh, ip-api.com, RDAP,
  Shodan, HIBP, phonenumbers) talks over sockets/HTTPS or a pure-Python
  library. Nothing here calls `nslookup`, `whois`, or any other platform
  binary, so there's no PATH/executable dependency to break between OSes.

## Legal

Use only against systems and identities you're authorized to assess. TegoScent
performs live lookups against third-party services (crt.sh, ip-api.com,
Shodan, HIBP, social platforms) - respect each service's rate limits and
terms of service. Passive OSINT sources (DNS, WHOIS, CT logs) carry different
legal/ethical weight than active probing (the username-existence checks make
live HTTP requests to each platform) - factor that into scope-of-engagement
documentation for client work.

## Contributing

New transforms are the easiest way to contribute - see "Writing your own
transform" above. Open a PR with the new module, its one-line import in
`transforms/__init__.py`, and a row in the transform table above. Bug reports
and issues are welcome on the GitHub issue tracker.

## License

MIT - see [LICENSE](LICENSE). Do whatever you want with it; attribution
appreciated but not required.

