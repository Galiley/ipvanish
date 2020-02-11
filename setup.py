from setuptools import setup

from ipvanish import __version__

# Get the long description from the README file
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="ipvanish",
    version=__version__,
    description="Simple CLI to handle Ipvanish VPN",
    long_description=long_description,
    author="Galiley",
    author_email="Gal1ley@protonmail.com",
    scripts=["bin/ipvanish"],
    install_requires=["requests"],
    packages=["ipvanish"],
)
