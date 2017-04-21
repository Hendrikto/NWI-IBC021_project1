#!/usr/bin/env python3

"""A recursive DNS server

This module provides a recursive DNS server. You will have to implement this
server using the algorithm described in section 4.3.2 of RFC 1034.
"""
import socket
import threading
from threading import Thread

from dns.message import Message, Header
from dns.name import Name
from dns.resolver import Resolver
from dns.types import Type
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

    def lookup_zone(self, domain):
        """Look for a record in the zone files."""
        for i in range(len(domain.labels) + 1):
            zone = ".".join(domain.labels[i:]) + "."
            if zone in Server.catalog.zones:
                name = str(domain)[:str(domain).rfind(zone)]
                if name in Server.catalog.zones[zone].records:
                    records = Server.catalog.zones[zone].records[name]
                    for record in records:
                        record.name = domain
                        if record.type_ is Type.CNAME:
                            cname = Name(record.rdata.cname)
                            cname.labels += zone.split(".")[:-1]
                            records += self.lookup_zone(cname)[1]
                    return True, records
                else:
                    return True, None
        return False, None

    def send_response(self, records, authoritative, error=0):
        """Send a response to some message."""
        if not error and len(records) == 0:
            error = 3  # NXDOMAIN (Domain Name not found)
        if error != 0:
            header = Header(self.message.header.ident, 0, 0, 0, 0, 0)
            header.rcode = error
        else:
            header = Header(
                self.message.header.ident, 0, 0, len(records), 0, 0
            )
        header.aa = authoritative  # Authoritative Answer
        header.qr = 1  # Message is Response
        header.rd = self.message.header.rd  # Recursion desired
        header.ra = 1  # Recursion Available
        response = Message(header, answers=records)
        self.sock.sendto(response.to_bytes(), self.address)

    def run(self):
        """ Run the handler thread"""
        try:
            self.message = Message.from_bytes(self.data)
        except:
            self.message = Message(Header(0, 0, 0, 0, 0, 0))
            self.send_response([], False, 1)
            return
        self.domain = self.message.questions[0].qname
        print(threading.current_thread())
        print("\tDomain:", self.domain)
        print("\tAddress:", self.address)
        authoritative, records = self.lookup_zone(self.domain)
        if records is None:
            if self.message.header.rd:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                resolver = Resolver(5, Server.cache)
                records = resolver.query_recursive(
                    sock, self.domain, Resolver.root_server
                )
                sock.close()
            else:
                records = []
        self.send_response(records, authoritative)


class Server:
    """A recursive DNS server"""

    cache = None
    catalog = Catalog()

    def __init__(self, port):
        """Initialize the server

        Args:
            port (int): port that server is listening on
        """
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
