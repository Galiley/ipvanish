import glob
import io
import os
import re
import shutil
import sys
import tempfile
import threading
import traceback
import zipfile

import beautifultable
import bs4
import click
import requests

from .vpn import IpvanishError, IpvanishVPN

SETTINGS = {
    "IPVANISH_PATH": os.path.expanduser("~/.config/ipvanish"),
    "CONFIG_URL": "https://configs.ipvanish.com/configs/configs.zip",
    "GEOJSON_URL": "https://www.ipvanish.com/api/servers.geojson",
    "IPVANISH_ACCOUNT_URL": "https://account.ipvanish.com",
    "CONTEXT": {"help_option_names": ["-h", "--help"]},
}


@click.group(context_settings=SETTINGS["CONTEXT"])
def cli():
    """Manage ipvanish from the cli"""
    if not os.path.exists(SETTINGS["IPVANISH_PATH"]):
        os.mkdir(SETTINGS["IPVANISH_PATH"])


@cli.command(context_settings=SETTINGS["CONTEXT"])
def sync():
    """Sync ipvanish vpn servers config files"""
    try:
        with tempfile.TemporaryDirectory() as tmpfolder:
            r = requests.get(SETTINGS["CONFIG_URL"], stream=True)
            r.raise_for_status()
            z = zipfile.ZipFile(io.BytesIO(r.content))
            z.extractall(tmpfolder)
            zipfolder = os.listdir(tmpfolder)
            if len(zipfolder) == 0:
                raise IpvanishError("Config archive is empty")
            else:
                config_path = os.path.join(SETTINGS["IPVANISH_PATH"], "configs")
                shutil.rmtree(config_path, ignore_errors=True)
                shutil.copytree(tmpfolder, config_path)
                click.echo(
                    f"Ipvanish ovpns files downloaded\n{len(zipfolder)-1} servers available"
                )
    except requests.exceptions.RequestException as e:
        click.echo(f'Failed to fetch the config archive at {SETTINGS["CONFIG_URL"]}')
    except IpvanishError as e:
        click.echo(f"[IpvanishError] {e}", file=sys.stderr)
    except Exception:
        click.echo(traceback.print_exc(), file=sys.stderr)


def check_auth():
    with open(
        os.path.join(SETTINGS["IPVANISH_PATH"], "auth"), "r", encoding="utf-8"
    ) as auth:
        username = auth.readline().rstrip("\n")
        password = auth.readline().rstrip("\n")
    with requests.Session() as s:
        r = s.get(f"{SETTINGS['IPVANISH_ACCOUNT_URL']}/login")
        r.raise_for_status()
        soup = bs4.BeautifulSoup(r.content, "html.parser")
        token = soup.find(id="clientToken").attrs["value"]

        r = s.post(
            f"{SETTINGS['IPVANISH_ACCOUNT_URL']}/validate",
            data={"username": username, "password": password, "clientToken": token},
        )
        r.raise_for_status()


@cli.command(context_settings=SETTINGS["CONTEXT"])
@click.option(
    "--test",
    "-f",
    "test",
    is_flag=True,
    default=False,
    help="Test auth credentials",
)
@click.option(
    "--force",
    "-f",
    "force",
    is_flag=True,
    default=False,
    help="Override auth credentials if present",
)
def auth(force, test):
    """Configure ipvanish auth credentials"""
    try:
        if force or not os.path.exists(os.path.join(SETTINGS["IPVANISH_PATH"], "auth")):
            username = click.prompt("Ipvanish's username: ")
            password = click.prompt("Ipvanish's password: ", hide_input=True)
            with open(os.path.join(SETTINGS["IPVANISH_PATH"], "auth"), "w") as auth:
                click.echo(username, file=auth)
                click.echo(password, file=auth)
        # Try to verify username and password
        if test:
            try:
                check_auth()
            except requests.exceptions.RequestException as e:
                click.echo(f"Failed to test the auth credentials: {e}")
    except IpvanishError as e:
        click.echo(f"[IpvanishError] {e}", file=sys.stderr)
    except Exception:
        click.echo(traceback.print_exc(), file=sys.stderr)


def _get_ipvanish_config_list(countries: list, is_excluded: bool):
    config_list = glob.glob(
        os.path.join(SETTINGS["IPVANISH_PATH"], "configs", "*.ovpn")
    )
    if len(countries) > 0:
        L = []
        regex = r"ipvanish-(" + r"|".join(countries) + r")-"
        for vpn in config_list:
            if is_excluded:
                if re.search(regex, vpn) is None:
                    L.append(os.path.join(SETTINGS["IPVANISH_PATH"], "configs", vpn))
            else:
                if re.search(regex, vpn) is not None:
                    L.append(os.path.join(SETTINGS["IPVANISH_PATH"], "configs", vpn))
        return L
    else:
        return [os.path.join(SETTINGS["IPVANISH_PATH"], vpn) for vpn in config_list]


def _get_ipvanish_geojson(countries: list, is_excluded: bool):
    r = requests.get(SETTINGS["GEOJSON_URL"])
    if r.status_code == 200:
        d = {}
        for geo in r.json():
            if countries:
                if is_excluded:
                    if geo["properties"]["countryCode"] in countries:
                        continue
                else:
                    if not geo["properties"]["countryCode"] in countries:
                        continue
            properties = geo["properties"]
            countryCode = properties["countryCode"]
            if countryCode == "GB":
                countryCode = "UK"
            city = properties["city"].replace(" ", "-")
            hostNameId = properties["hostname"].split(".")[0]
            key = f"ipvanish-{countryCode}-{city}-{hostNameId}"
            d[key] = properties
        return d
    return {}


def _get_vpns(countries: list, is_excluded: bool):
    config_files = _get_ipvanish_config_list(countries, is_excluded)
    if len(config_files) == 0:
        raise IpvanishError("There is no available server")

    geojson_data = _get_ipvanish_geojson(countries, is_excluded)
    vpns = []
    threads = []
    with click.progressbar(
        config_files, label="Retrieving vpn data", show_eta=False
    ) as bar:
        for config_file in bar:
            geojson_id = config_file.split(".ovpn")[0].split("/")[-1]
            vpn = IpvanishVPN(config_file, geojson_data.get(geojson_id, {}))
            vpns.append(vpn)
            thread = threading.Thread(target=vpn.ping_server)
            thread.start()
            threads.append(thread)

        for i, thread in enumerate(threads):
            thread.join()
            bar.update(i)
    return vpns


def process_country(ctx: click.Context, param: click.Parameter, value):
    if not value:
        return []
    countries = value.split(",")
    if "UK" in countries:
        countries.append("GB")
    elif "GB" in countries:
        countries.append("UK")
    return countries


@cli.command(context_settings=SETTINGS["CONTEXT"])
@click.option(
    "--country",
    "countries",
    help="VPN's country code to use",
    default="",
    callback=process_country,
    type=str,
)
@click.option(
    "--not", "is_excluded", help="Filter out country code", is_flag=True, default=False
)
@click.pass_context
def info(ctx: click.Context, countries: list, is_excluded: bool):
    """Display ipvanish vpn server status"""
    try:
        if not os.path.exists(os.path.join(SETTINGS["IPVANISH_PATH"], "auth")):
            raise IpvanishError(
                "Auth credentials not configured. Please run commands auth"
            )
        vpns = _get_vpns(countries, is_excluded)
        vpns.sort()
        table = beautifultable.BeautifulTable(max_width=180)
        table.set_style(beautifultable.STYLE_BOX_ROUNDED)
        table.column_headers = [
            "Server",
            "City",
            "Country",
            "Region",
            "Ping",
            "Capacity",
        ]
        for vpn in vpns:
            table.append_row(
                [vpn.server, vpn.city, vpn.country, vpn.region, vpn.ping, vpn.capacity]
            )
        click.echo(table)
    except IpvanishError as e:
        click.echo(f"[IpvanishError] {e}", file=sys.stderr)
    except Exception:
        click.echo(traceback.print_exc(), file=sys.stderr)


@cli.command(context_settings=SETTINGS["CONTEXT"])
@click.option(
    "--country",
    "countries",
    help="VPN's country code to use",
    default="",
    callback=process_country,
    type=str,
)
@click.option(
    "--not", "is_excluded", help="Filter out country code", is_flag=True, default=False
)
@click.pass_context
def connect(ctx: click.Context, countries: list, is_excluded: bool):
    """Connect to an ipvanish vpn server"""
    try:
        if not os.path.exists(os.path.join(SETTINGS["IPVANISH_PATH"], "auth")):
            raise IpvanishError(
                "Auth credentials not configured. Please run commands auth"
            )
        vpns = _get_vpns(countries, is_excluded)
        vpns.sort()
        click.echo(f"Connecting to {vpns[0]} ...")
        vpns[0].connect()
    except IpvanishError as e:
        click.echo(f"[IpvanishError] {e}", file=sys.stderr)
    except Exception:
        click.echo(traceback.print_exc(), file=sys.stderr)
