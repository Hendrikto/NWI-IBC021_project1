#!/usr/bin/env python3

"""Tests for your DNS resolver and server"""

import sys
import unittest
from unittest import TestCase
from argparse import ArgumentParser

from dns.cache import RecordCache
from dns.classes import Class
from dns.name import Name
from dns.resolver import Resolver
from dns.resource import ResourceRecord, ARecordData, CNAMERecordData
from dns.types import Type

PORT = 5001
SERVER = "localhost"


class TestResolver(TestCase):
    """Resolver tests"""

    def test_gethostbyname(self):
        resolver = Resolver(5, None)
        self.assertEqual(
            resolver.gethostbyname("google-public-dns-a.google.com"),
            ("google-public-dns-a.google.com", [], ["8.8.8.8"]),
        )
        self.assertEqual(
            resolver.gethostbyname("google-public-dns-b.google.com"),
            ("google-public-dns-b.google.com", [], ["8.8.4.4"]),
        )
        self.assertEqual(
            resolver.gethostbyname("con1.nipr.mil"),
            ("con1.nipr.mil", [], ["199.252.157.234"]),
        )
        self.assertEqual(
            # recommended domain to test
            resolver.gethostbyname("gaia.cs.umass.edu"),
            ("gaia.cs.umass.edu", [], ["128.119.245.12"]),
        )

    def test_gethostbyname_non_existent(self):
        resolver = Resolver(5, None)
        self.assertEqual(
            resolver.gethostbyname("bonobo.putin"),
            ("bonobo.putin", [], [])
        )
        self.assertEqual(
            resolver.gethostbyname("gumpenfisch.net"),
            ("gumpenfisch.net", [], [])
        )
        self.assertEqual(
            resolver.gethostbyname("ThisDomainDoesNotExist.false"),
            ("ThisDomainDoesNotExist.false", [], [])
        )
        self.assertEqual(
            resolver.gethostbyname("JustSoWeHaveMoreThanThree.domains"),
            ("JustSoWeHaveMoreThanThree.domains", [], [])
        )


class TestCache(TestCase):
    """Cache tests"""

    def test_invalid_domain_from_cache(self):
        cache = RecordCache(0)
        record = ResourceRecord(
            name=Name("bonobo.putin"),
            type_=Type.A,
            class_=Class.IN,
            ttl=60,
            rdata=ARecordData("1.0.0.1"),
        )
        cache.add_record(record)
        self.assertEqual(
            cache.lookup(Name("bonobo.putin"), Type.A, Class.IN), record
        )

    def test_expired_cache_entry(self):
        cache = RecordCache(0)
        record = ResourceRecord(
            name=Name("bonobo.putin"),
            type_=Type.A,
            class_=Class.IN,
            ttl=0,
            rdata=ARecordData("1.0.0.1"),
        )
        cache.add_record(record)
        self.assertEqual(
            cache.lookup(Name("bonobo.putin"), Type.A, Class.IN), None
        )


class TestResolverCache(TestCase):
    """Resolver tests with cache enabled"""

    def test_invalid_domain_from_cache(self):
        cache = RecordCache(0)
        resolver = Resolver(5, cache)
        cache.add_record(ResourceRecord(
            name=Name("bonobo.putin"),
            type_=Type.A,
            class_=Class.IN,
            ttl=60,
            rdata=ARecordData("1.0.0.1"),
        ))
        cache.add_record(ResourceRecord(
            name=Name("bonobo.putin"),
            type_=Type.CNAME,
            class_=Class.IN,
            ttl=60,
            rdata=CNAMERecordData(Name("putin.bonobo")),
        ))
        self.assertEqual(
            resolver.gethostbyname("bonobo.putin"),
            ("bonobo.putin", ["putin.bonobo."], ["1.0.0.1"])
        )

    def test_expired_cache_entry(self):
        cache = RecordCache(0)
        resolver = Resolver(5, cache)
        cache.add_record(ResourceRecord(
            name=Name("hw.gumpe"),
            type_=Type.A,
            class_=Class.IN,
            ttl=0,
            rdata=ARecordData("1.0.0.2"),
        ))
        cache.add_record(ResourceRecord(
            name=Name("hw.gumpe"),
            type_=Type.CNAME,
            class_=Class.IN,
            ttl=0,
            rdata=CNAMERecordData(Name("gumpe.hw")),
        ))
        self.assertEqual(
            resolver.gethostbyname("hw.gumpe"),
            ("hw.gumpe", [], [])
        )


class TestServer(TestCase):
    """Server tests"""


def run_tests():
    """Run the DNS resolver and server tests"""
    parser = ArgumentParser(description="DNS Tests")
    parser.add_argument("-s", "--server", type=str, default="localhost",
                        help="the address of the server")
    parser.add_argument("-p", "--port", type=int, default=5001,
                        help="the port of the server")
    args, extra = parser.parse_known_args()
    global PORT, SERVER
    PORT = args.port
    SERVER = args.server

    # Pass the extra arguments to unittest
    sys.argv[1:] = extra

    # Start test suite
    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_tests()
