# Ipvanish

## Overview
Simple CLI to handle Ipvanish VPN

## Installation
```
pip install --user git+https://github.com/Galiley/ipvanish.git
```

## Usage
```
Usage: ipvanish [OPTIONS] COMMAND [ARGS]...

  Manage ipvanish from the cli

Options:
  --help  Show this message and exit.

Commands:
  auth     Configure ipvanish auth credentials
  connect  Connect to an ipvanish vpn server
  info     Display ipvanish vpn server status
  sync     Sync ipvanish vpn servers config files
```

## Commands

* `ipvanish auth --force`  
Override auth credentials if present

* `ipvanish connect --country COUNTRY1[,COUNTRY2,...]`  
Connect to an ipvanish vpn server located in these country

* `ipvanish connect --not --country COUNTRY1[,COUNTRY2,...]`  
Connect to an ipvanish vpn server not located in these country