try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import os.path

readme = ''
here = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(here, 'README.md')
if os.path.exists(readme_path):
    with open(readme_path, 'rb') as stream:
        readme = stream.read().decode('utf8')

setup(
    long_description=readme,
    name='ipvanish',
    version='1.2.1',
    description='Simple CLI to handle Ipvanish VPN',
    python_requires='==3.*,>=3.8.0',
    author='Galiley',
    author_email='Gal1ley@protonmail.com',
    entry_points={"console_scripts": ["ipvanish = ipvanish.cmd:cli"]},
    packages=['ipvanish'],
    package_dir={"": "."},
    package_data={},
    install_requires=[
        'beautifultable==0.*,>=0.8.0', 'bs4==0.*,>=0.0.1', 'click==8.*,>=8.0.0',
        'requests==2.*,>=2.23.0'
    ],
    extras_require={
        "dev": [
            "black==19.*,>=19.10.0", "pre-commit==2.*,>=2.2.0",
            "pylint==2.*,>=2.4.4"
        ]
    },
)
