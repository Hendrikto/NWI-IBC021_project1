#!/usr/bin/env python3

"""Tests for your DNS resolver and server"""

import socket
import sys
import unittest
from unittest import TestCase
from argparse import ArgumentParser

from dns.message import Message, Question, Header
from dns.cache import RecordCache
from dns.classes import Class
from dns.name import Name
from dns.resolver import Resolver
from dns.resource import ResourceRecord, ARecordData, CNAMERecordData
from dns.types import Type

PORT = 53
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

    def test_ttl_overwrite(self):
        cache = RecordCache(60)
        record = ResourceRecord(
            name=Name("bonobo.putin"),
            type_=Type.A,
            class_=Class.IN,
            ttl=0,
            rdata=ARecordData("1.0.0.1"),
        )
        cache.add_record(record)
        cache_entry = cache.lookup(Name("bonobo.putin"), Type.A, Class.IN)
        self.assertEqual(cache_entry, record)
        self.assertEqual(cache_entry.ttl, 60)


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

    def test_no_cache_entry(self):
        cache = RecordCache(0)
        resolver = Resolver(5, cache)
        self.assertEqual(
            resolver.gethostbyname("google-public-dns-a.google.com"),
            ("google-public-dns-a.google.com", [], ["8.8.8.8"]),
        )
        self.assertEqual(
            resolver.gethostbyname("google-public-dns-b.google.com"),
            ("google-public-dns-b.google.com", [], ["8.8.4.4"]),
        )


class TestServer(TestCase):
    """Server tests"""

    def test_authority_domain(self):
        question = Question(Name("server1.gumpe"), Type.A, Class.IN)
        header = Header(1337, 0, 1, 0, 0, 0)
        query = Message(header, questions=[question])
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(query.to_bytes(), (SERVER, PORT))
        data = s.recv(512)
        s.close()
        message = Message.from_bytes(data)
        self.assertCountEqual(
            message.answers,
            [
                ResourceRecord(
                    name=Name("server1.gumpe."),
                    type_=Type.A,
                    class_=Class.IN,
                    ttl=0,
                    rdata=ARecordData("10.0.1.5"),
                ),
                ResourceRecord(
                    name=Name("server1.gumpe."),
                    type_=Type.A,
                    class_=Class.IN,
                    ttl=0,
                    rdata=ARecordData("10.0.1.4"),
                ),
            ]
        )

    def test_outside_zone(self):
        question = Question(Name("gaia.cs.umass.edu"), Type.A, Class.IN)
        header = Header(1337, 0, 1, 0, 0, 0)
        header.rd = 1
        query = Message(header, questions=[question])
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(query.to_bytes(), (SERVER, PORT))
        data = s.recv(512)
        s.close()
        message = Message.from_bytes(data)
        self.assertEqual(
            message.answers,
            [
                ResourceRecord(
                    name=Name("gaia.cs.umass.edu"),
                    type_=Type.A,
                    class_=Class.IN,
                    ttl=0,
                    rdata=ARecordData("128.119.245.12")
                ),
            ]
        )

    def test_concurrent_requests(self):
        queries = []
        answers = []
        question = Question(Name("gaia.cs.umass.edu"), Type.A, Class.IN)
        header = Header(1337, 0, 1, 0, 0, 0)
        header.rd = 1
        queries.append(Message(header, questions=[question]))
        answers.append([
            ResourceRecord(
                name=Name("gaia.cs.umass.edu"),
                type_=Type.A,
                class_=Class.IN,
                ttl=0,
                rdata=ARecordData("128.119.245.12")
            ),
        ])
        question = Question(Name("server2.gumpe"), Type.A, Class.IN)
        header = Header(420, 0, 1, 0, 0, 0)
        queries.append(Message(header, questions=[question]))
        answers.append([
            ResourceRecord(
                name=Name("server2.gumpe"),
                type_=Type.A,
                class_=Class.IN,
                ttl=0,
                rdata=ARecordData("10.0.1.7")
            ),
        ])
        header = Header(69, 0, 1, 0, 0, 0)
        question = Question(Name("www.gumpe"), Type.A, Class.IN)
        queries.append(Message(header, questions=[question]))
        answers.append([
            ResourceRecord(
                name=Name("www.gumpe"),
                type_=Type.A,
                class_=Class.IN,
                ttl=0,
                rdata=ARecordData("10.0.1.7")
            ),
            ResourceRecord(
                name=Name("www.gumpe"),
                type_=Type.CNAME,
                class_=Class.IN,
                ttl=0,
                rdata=CNAMERecordData(Name("server2.gumpe"))
            ),
        ])
        sockets = [
            socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            for _ in range(len(queries))
        ]
        for i in range(len(sockets)):
            sockets[i].sendto(queries[i].to_bytes(), (SERVER, PORT))
        responses = []
        for i in range(len(sockets)):
            responses.append(Message.from_bytes(sockets[i].recv(1024)))
        for i in range(len(sockets)):
            sockets[i].close()
        for i in range(len(queries)):
            self.assertCountEqual(responses[i].answers, answers[i])


def run_tests():
    """Run the DNS resolver and server tests"""
    parser = ArgumentParser(description="DNS Tests")
    parser.add_argument("-s", "--server", type=str, default="localhost",
                        help="the address of the server")
    parser.add_argument("-p", "--port", type=int, default=53,
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
