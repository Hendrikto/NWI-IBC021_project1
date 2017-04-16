#!/usr/bin/env python3

"""A recursive DNS server

This module provides a recursive DNS server. You will have to implement this
server using the algorithm described in section 4.3.2 of RFC 1034.
"""
import socket
from threading import Thread

from dns.message import Message, Header
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
                if zone in Server.catalog.zones:
                    records = Server.catalog.zones[zone].records
                    return records[
                        str(self.domain)[:str(self.domain).rfind(zone)]
                    ]
                else:
                    return

    def run(self):
        """ Run the handler thread"""
        print("Thread started for:", self.data, self.address)
        message = Message.from_bytes(self.data)
        self.domain = message.questions[0].qname
        records = self.lookup_zone()
        header = Header(message.header.ident, 0, 0, 1, 0, 0)
        response = Message(header, answers=records)
        self.sock.sendto(response.to_bytes(), self.address)


class Server:
    """A recursive DNS server"""

    catalog = Catalog()

    def __init__(self, port, caching, ttl):
        """Initialize the server

        Args:
            port (int): port that server is listening on
            caching (bool): server uses resolver with caching if true
            ttl (int): ttl for records (if > 0) of cache
        """
        self.caching = caching
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
