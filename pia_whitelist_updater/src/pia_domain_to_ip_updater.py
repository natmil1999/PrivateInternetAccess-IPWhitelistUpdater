import os
import subprocess
import json
import time
import logging
import socket
from pathlib import Path
from typing import Iterable

# Configuration constants
WHITELIST_DOMAINS_FILE: Path = Path(os.path.join(os.path.dirname(__file__), "../resources", "domain_whitelist.txt"))
LOG_FILE: Path = Path(os.path.join(os.path.dirname(__file__), "../logs", "vpn_updater.log"))
DEFAULT_INTERVAL: int = 5
IP_CLEAR_WINDOW_SECONDS: int = 15 * 60

# Cached set of currently bypassed IPs
bypassed_ips: set[str] = set()

# Decrements every update; clears bypassed_ips if counter reaches 0
ip_clear_counter_reset_count: int = 0
ip_clear_counter: int = 0


def start_whitelist_updater(interval: int = DEFAULT_INTERVAL):
    global ip_clear_counter_reset_count, ip_clear_counter

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(),
        ],
    )
    logging.info("Starting VPN IP Whitelist Updater Service")

    # Ensure integer tick count
    ip_clear_counter_reset_count = IP_CLEAR_WINDOW_SECONDS // max(1, interval)
    ip_clear_counter = ip_clear_counter_reset_count

    try:
        while True:
            logging.info("Running IP whitelist update...")
            if ip_clear_counter <= 0:
                ip_clear_counter = ip_clear_counter_reset_count
            ip_clear_counter -= 1

            update_pia_whitelist()
            time.sleep(interval)
    except KeyboardInterrupt:
        logging.info("Service stopped by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise


def parse_domain_input(domain_csv: str) -> set[str]:
    # Split, strip, and ignore empties
    return {d.strip() for d in domain_csv.split(",") if d.strip()}


def read_domain_set() -> set[str]:
    try:
        with WHITELIST_DOMAINS_FILE.open("r") as f:
            return {line.strip() for line in f if line.strip()}
    except FileNotFoundError:
        logging.error(f"Error: {WHITELIST_DOMAINS_FILE} not found")
        return set()


def write_domain_set(domains: Iterable[str]) -> None:
    # Persist sorted for determinism
    with WHITELIST_DOMAINS_FILE.open("w") as f:
        f.write("\n".join(sorted(set(domains))))


def add_domains(domain: str) -> bool:
    """Adds one or more comma-separated domains. Returns True if anything was added."""
    to_add = parse_domain_input(domain)
    if not to_add:
        return False

    existing = read_domain_set()
    new_set = existing | to_add
    has_added = new_set != existing
    if has_added:
        write_domain_set(new_set)
    return has_added


def remove_domains(domain: str) -> bool:
    """Removes one or more comma-separated domains. Returns True if anything was removed."""
    to_remove = parse_domain_input(domain)
    if not to_remove:
        return False

    existing = read_domain_set()
    new_set = existing - to_remove
    has_removed = new_set != existing
    if has_removed:
        write_domain_set(new_set)
    return has_removed


def list_domain_or_ip(should_list_domains: bool) -> set[str]:
    return list_domains() if should_list_domains else list_bypassed_ips()


def list_domains() -> set[str]:
    return read_domain_set()


def list_bypassed_ips() -> set[str]:
    # Return a copy to protect internal state
    return set(bypassed_ips)


def update_pia_whitelist() -> bool:
    """
    Updates IP whitelist and applies PIA settings.
    Returns True on success, False otherwise.
    """
    try:
        if update_ip_whitelist():
            apply_whitelist_settings([create_pia_settings_bypass_json_object(ip) for ip in bypassed_ips])
            return True
    except Exception as e:
        logging.error(f"Failed to apply PIA whitelist settings: {e}")
    return False


def update_ip_whitelist() -> bool:
    """
    Returns True if the IP whitelist was updated, returns False if unchanged.
    """
    global ip_clear_counter

    ips = get_ip_whitelist()

    # Periodic clearing policy
    if ip_clear_counter <= 0:
        if bypassed_ips:
            logging.info("Clearing cached bypassed IPs due to scheduled reset.")
            bypassed_ips.clear()

    if not ips:
        if bypassed_ips:
            logging.warning("No IPs found from domain_whitelist.txt; clearing cached IPs.")
            bypassed_ips.clear()
            return True

    added = ips - bypassed_ips

    if not added:
        logging.info("No new IPs to update.")
        return False
    else:
        logging.info(f"Added IPs: {sorted(added)}")
        bypassed_ips.update(added)
        return True


def get_ip_whitelist() -> set[str]:
    domains = read_domains(str(WHITELIST_DOMAINS_FILE))
    all_ips: set[str] = set()

    for domain in domains:
        ips = get_ips_for_domain(domain)
        if ips:
            all_ips.update(ips)
        else:
            logging.warning(f"No IP addresses found for {domain}")
    return all_ips


def get_ips_for_domain(domain_name: str) -> list[str]:
    try:
        ip_address = socket.gethostbyname_ex(domain_name)
        return ip_address[2]
    except socket.gaierror:
        logging.error(f"Could not resolve the domain name: {domain_name}")
        return []


def read_domains(filename: str) -> list[str]:
    try:
        with open(filename, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logging.error(f"Error: {filename} not found")
        return []


def apply_whitelist_settings(json_list: list):
    payload = json.dumps({"bypassSubnets": json_list}, ensure_ascii=False, sort_keys=True)
    result = subprocess.run(
        ["piactl", "-u", "applysettings", payload],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logging.error(f"piactl -u applysettings failed: {result.stderr.strip()}")
        raise RuntimeError("piactl -u applysettings failed")
    logging.info("PIA whitelist settings applied successfully.")


def create_pia_settings_bypass_json_object(ip: str) -> dict[str, str]:
    # Add '/32', since resolver returns a full IP address and PIA expects CIDR notation
    return {"mode": "exclude", "subnet": f"{ip}/32"}
