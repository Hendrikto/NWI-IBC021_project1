#!/usr/bin/env python3

"""A recursive DNS server

This module provides a recursive DNS server. You will have to implement this
server using the algorithm described in section 4.3.2 of RFC 1034.
"""
import socket
import threading
from threading import Thread

from dns.message import Message, Header
from dns.resolver import Resolver
from dns.zone import Catalog


class RequestHandler(Thread):
    """A handler for requests to the DNS server"""

    def __init__(self, sock, data, address):
        """Initialize the handler thread"""
        super().__init__()
        self.daemon = True
        self.sock = sock
        self.data = data
        self.address = address

    def lookup_zone(self):
        """Look for a record in the zone files."""
        for i in range(len(self.domain.labels) + 1):
            zone = ".".join(self.domain.labels[i:]) + "."
            if zone in Server.catalog.zones:
                name = str(self.domain)[:str(self.domain).rfind(zone)]
                if name in Server.catalog.zones[zone].records:
                    return True, Server.catalog.zones[zone].records[name]
                else:
                    return True, None
        return False, None

    def send_response(self, message, records, authoritative):
        """Send a response to some message."""
        if len(records) == 0:
            header = Header(message.header.ident, 0, 0, 0, 0, 0)
            header.rcode = 3
        else:
            header = Header(message.header.ident, 0, 0, len(records), 0, 0)
        header.aa = authoritative  # Authoritative Answer
        header.qr = 1  # Message is Response
        header.rd = message.header.rd  # Recursion desired
        header.ra = 1  # Recursion Available
        response = Message(header, answers=records)
        self.sock.sendto(response.to_bytes(), self.address)

    def run(self):
        """ Run the handler thread"""
        message = Message.from_bytes(self.data)
        self.domain = message.questions[0].qname
        print(threading.current_thread())
        print("\tDomain:", self.domain)
        print("\tAddress:", self.address)
        authoritative, records = self.lookup_zone()
        if records is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            resolver = Resolver(5, Server.cache)
            records = resolver.query_recursive(
                sock, self.domain, Resolver.root_server
            )
            sock.close()
        self.send_response(message, records, authoritative)


class Server:
    """A recursive DNS server"""

    cache=None
    catalog = Catalog()

    def __init__(self, port):
        """Initialize the server

        Args:
            port (int): port that server is listening on
        """
        self.ttl = ttl
        self.port = port
        self.done = False

    def serve(self):
        """Start serving requests"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", self.port))
        while not self.done:
            data, address = self.sock.recvfrom(1024)
            RequestHandler(self.sock, data, address).start()

    def shutdown(self):
        """Shut the server down"""
        self.done = True
        self.sock.close()
