#!/usr/bin/env python3

""" DNS server

This script contains the code for starting a DNS server.
"""

from argparse import ArgumentParser

from dns.cache import RecordCache
from dns.server import Server
from dns.zone import Zone


def run_server():
    parser = ArgumentParser(description="DNS Server")
    parser.add_argument(
        "-c", "--caching", action="store_true",
        help="Enable caching",
    )
    parser.add_argument(
        "-t", "--ttl", metavar="time", type=int, default=0,
        help="TTL value of cached entries (if > 0)",
    )
    parser.add_argument(
        "-p", "--port", type=int, default=53,
        help="Port which server listens on",
    )
    args = parser.parse_args()

    zone = Zone()
    zone.read_master_file("zone")
    Server.catalog.add_zone("gumpe.", zone)

    if args.caching:
        cache = RecordCache(args.ttl)
        cache.read_cache_file()
        Server.cache = cache

    server = Server(args.port, args.ttl)
    try:
        server.serve()
    except KeyboardInterrupt:
        server.shutdown()

    if args.caching:
        cache.write_cache_file()

if __name__ == "__main__":
    run_server()
