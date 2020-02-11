# Ipvanish

## Overview
Simple CLI to handle Ipvanish VPN

## Installation
```bash
pip install --user git+https://github.com/Galiley/ipvanish.git
```

## Usage
```
ipvanish [-h] [-v] [COMMAND] ...
```

## Arguments

### `-h`, `--help`
Show ipvanish cli help message and exit

### `-v`, `--version`
Show ipvanish version then exit

## Commands

### `sync`
Sync ipvanish vpn servers config files

### `connect`
Connect to an ipvanish vpn server

#### Additional arguments
##### `--country COUNTRIES [COUNTRIES ...]`
Filter vpn server by country code
