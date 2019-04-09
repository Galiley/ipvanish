#!/usr/bin/env python

import threading

def sort_vpn(elem):
    ping = elem.ping
    if ping is None:
        return float("inf")
    return ping

def threaded(fn):
    def run(*k, **kw):
        t = threading.Thread(target=fn, args=k, kwargs=kw)
        t.start()
        return t # <-- this is new!
    return run