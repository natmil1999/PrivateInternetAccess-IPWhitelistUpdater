import subprocess
import json
import time
import logging
import socket

WHITELIST_DOMAINS_FILE = './domain_whitelist.txt'

bypassed_ips = set()    # Cached set of currently bypassed ips

def start_whitelist_updaters(interval: int = 15):
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('../vpn_updater.log'),
            logging.StreamHandler()
        ]
    )

    logging.info("Starting VPN IP Whitelist Updater Service")

    try:
        while True:
            logging.info("Running IP whitelist update...")
            update_ip_whitelist()
            time.sleep(interval)
    except KeyboardInterrupt:
        logging.info("Service stopped by user")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise

def add_domains(domain) -> bool:
    has_added = True
    domains = set()
    domains.update(domain.strip(' ').split(','))
    with open(WHITELIST_DOMAINS_FILE, 'r') as f:
        for line in f:
            if line.strip() == domain:
                has_added = False
            domains.add(line.strip())
    with open(WHITELIST_DOMAINS_FILE, 'w') as f:
        f.write('\n'.join(domains))
    return has_added

def remove_domains(domain) -> bool:
    has_removed = False
    domains = set()
    with (open(WHITELIST_DOMAINS_FILE, 'r') as f):
        for line in f:
            if line.strip() in domain.strip(' ').split(','):
                has_removed = True
            else:
                domains.add(line.strip())
    with open(WHITELIST_DOMAINS_FILE, 'w') as f:
         f.write('\n'.join(domains))
    return has_removed

def list_domain_or_ip(should_list_domains: bool) -> set:
    if should_list_domains:
        return list_domains()
    else:
         return list_bypassed_ips()

def list_domains() -> set:
    domains = set()
    with open(WHITELIST_DOMAINS_FILE, 'r') as f:
        for line in f:
            domains.add(line.strip())
    return domains


def list_bypassed_ips() -> set:
    return bypassed_ips

def update_pia_whitelist() -> bool:
    """
    Reads the JSON file at json_path (or resolves a single JSON file in that directory),
    loads it as a Python object, updates/sets the given key with IPs from ip_file,
    and saves it back.

    Returns True on success, False otherwise.
    """
    if update_ip_whitelist():
        # Update the PIA Settings with the updated IP white-list
        try:
            apply_whitelist_settings([create_pia_settings_bypass_json_object(ip) for ip in bypassed_ips])
        except Exception:
            return False
    return True


"""
Returns True if the IP whitelist was updated, returns False if the ip Whitelist is unchanged.
"""
def update_ip_whitelist() -> bool:
    ips = get_ip_whitelist()
    if bypassed_ips.difference(ips).__sizeof__() == 0:
        logging.info("No new IPs to update")
        return False
    else:
        if not ips:
            logging.warning(f"No IPs found for the domain_whitelist.txt file.")
            bypassed_ips.clear()
            return True
        else:
            if bypassed_ips.difference(ips):
                logging.info(f"Removed IPs: {bypassed_ips.difference(ips)}.")
            if ips.difference(bypassed_ips):
                logging.info(f"Added IPs: {ips.difference(bypassed_ips)}")

            bypassed_ips.clear()
            bypassed_ips.update(ips)
            return True


def get_ip_whitelist() -> set:
    domains = read_domains(WHITELIST_DOMAINS_FILE)
    all_ips = set()

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
        with open(filename, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logging.error(f"Error: {filename} not found")
        return []

def apply_whitelist_settings(json_list: list):
    json_str = json.dumps(json_list, indent=2, ensure_ascii=False, sort_keys=True)
    subprocess.run(['piactl', '-u', 'applysettings', '{"bypassSubnets": ' + json_str + '}'], capture_output=True, text=True)

def create_pia_settings_bypass_json_object(ip: str ) -> dict[str, str]:
    return {
        "mode": "exclude",
        "subnet": ip+"/32"  # Add '/32', since dig returns a full ip address and PIA expects CIDR notation
    }
