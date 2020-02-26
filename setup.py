from setuptools import setup

from ipvanish import __version__

# Get the long description from the README file
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.in", encoding="utf-8") as f:
    install_requires = [k.rstrip() for k in f.readlines()[4:]]

setup(
    name="ipvanish",
    version=__version__,
    description="Simple CLI to handle Ipvanish VPN",
    long_description=long_description,
    author="Galiley",
    author_email="Gal1ley@protonmail.com",
    install_requires=install_requires,
    packages=["ipvanish"],
    entry_points={"console_scripts": "ipvanish=ipvanish.cli:cli"},
)
