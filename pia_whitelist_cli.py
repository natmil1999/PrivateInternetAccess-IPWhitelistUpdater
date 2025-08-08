import click
from app.pia_whitelist_updater import remove_domains as remove_domain_func, add_domains as add_domain_func, list_domain_or_ip, start_whitelist_updaters

@click.group()
def cli():
    return

@cli.command()
@click.option('--domain', type=str, help='A domain or csv string of domains to add to the whitelist, such as "example.com" or "example.com,example2.com"', default="")
def add(domain: str):
    if add_domain_func(domain):
        click.echo("Domains added to whitelist.")
    else:
        click.echo("No Domains added to whitelist.")

@cli.command()
@click.option('--domain', type=str, help='A domain or csv string of domains to remove from the whitelist, such as "example.com" or "example.com,example2.com"', default="")
def remove(domain: str):
    if remove_domain_func(domain):
        click.echo("Domain removed from whitelist.")
    else:
        click.echo("No Domain removed from whitelist.")

@cli.command()
def list_domains():
    click.echo(list_domain_or_ip(True))

@cli.command()
def list_ips():
    click.echo(list_domain_or_ip(False))

@cli.command()
@click.option('--interval', type=int, help='The number of seconds to wait between updating the set of ips whitelisted for the given domains.', default=15)
def start(interval: int):
    click.echo(start_whitelist_updaters(interval))
