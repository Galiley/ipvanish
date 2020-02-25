import click
import os
import tempfile
import requests
import zipfile
import sys
import glob
import re
import io
import shutil
import traceback
import pprint
import threading
import bs4

from .vpn import IpvanishVPN, IpvanishError

SETTINGS = {
    "IPVANISH_PATH": os.path.expanduser("~/.config/ipvanish"),
    "CONFIG_URL": "https://www.ipvanish.com/software/configs/configs.zip",
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
            try:
                r = requests.get(SETTINGS["CONFIG_URL"], stream=True)
                r.raise_for_status()
                z = zipfile.ZipFile(io.BytesIO(r.content))
                z.extractall(tmpfolder)
                zipfolder = os.listdir(tmpfolder)
                if len(zipfolder) == 0:
                    raise IpvanishError
                else:
                    shutil.rmtree(
                        os.path.join(SETTINGS["IPVANISH_PATH"], "configs"),
                        ignore_errors=True,
                    )
                    shutil.copytree(
                        tmpfolder, os.path.join(SETTINGS["IPVANISH_PATH"], "configs")
                    )
                    click.echo(
                        f"Ipvanish ovpns files downloaded\n{len(zipfolder)-1} servers available"
                    )
            except:
                raise IpvanishError("Failed to update vpn config")
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
    "--force",
    "-f",
    "force",
    is_flag=True,
    default=False,
    help="Override auth credentials if present",
)
def auth(force):
    """Configure ipvanish auth credentials"""
    try:
        if force or not os.path.exists(os.path.join(SETTINGS["IPVANISH_PATH"], "auth")):
            username = click.prompt("Ipvanish's username: ")
            password = click.prompt("Ipvanish's password: ", hide_input=True)
            with open(os.path.join(SETTINGS["IPVANISH_PATH"], "auth"), "w") as auth:
                click.echo(username, file=auth)
                click.echo(password, file=auth)
        # Try to verify username and password
        try:
            check_auth()
        except requests.exceptions.HTTPError:
            raise IpvanishError("Failed to check the auth credentials")
    except IpvanishError as e:
        click.echo(f"[IpvanishError] {e}", file=sys.stderr)
    except Exception:
        click.echo(traceback.print_exc(), file=sys.stderr)


def _get_ipvanish_config_list(countries, is_excluded):
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


def _get_ipvanish_geojson(countries, is_excluded):
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


def _get_vpns(countries, is_excluded):
    config_files = _get_ipvanish_config_list(countries, is_excluded)
    if len(config_files) == 0:
        raise IpvanishError("There is no available server")

    geojson_data = _get_ipvanish_geojson(countries, is_excluded)
    vpns = []
    threads = []
    for config_file in config_files:
        geojson_id = config_file.split(".ovpn")[0].split("/")[-1]
        vpn = IpvanishVPN(config_file, geojson_data.get(geojson_id, {}))
        vpns.append(vpn)
        thread = threading.Thread(target=vpn.ping_server)
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()
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
    if not os.path.exists(os.path.join(SETTINGS["IPVANISH_PATH"], "auth")):
        ctx.forward(auth)
    try:
        vpns = _get_vpns(countries, is_excluded)
        vpns.sort()
        click.echo(pprint.pformat(vpns))
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
    if not os.path.exists(os.path.join(SETTINGS["IPVANISH_PATH"], "auth")):
        ctx.forward(auth)
    try:
        vpns = _get_vpns(countries, is_excluded)
        vpns.sort()
        click.echo(f"Connecting to {vpns[0].server} ...")
        vpns[0].connect()
    except IpvanishError as e:
        click.echo(f"[IpvanishError] {e}", file=sys.stderr)
    except Exception:
        click.echo(traceback.print_exc(), file=sys.stderr)
