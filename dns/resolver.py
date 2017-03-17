#!/usr/bin/env python3

"""DNS Resolver

This module contains a class for resolving hostnames. You will have to
implement things in this module. This resolver will be both used by the DNS
client and the DNS server, but with a different list of servers.
"""

import socket

from dns.classes import Class
from dns.message import Message, Question, Header
from dns.name import Name
from dns.types import Type


class Resolver:
    """DNS resolver"""

    def __init__(self, timeout, caching, ttl):
        """Initialize the resolver

        Args:
            caching (bool): caching is enabled if True
            ttl (int): ttl of cache entries (if > 0)
        """
        self.timeout = timeout
        self.caching = caching
        self.ttl = ttl

    def gethostbyname(self, hostname):
        """Translate a host name to IPv4 address.

        Algorithm in RFC 1034 5.3.3:
            1 See if the answer is in local information, and if so return
              it to the client.
            2 Find the best servers to ask.
            3 Send them queries until one returns a response.
            4 Analyze the response, either:
                a. if the response answers the question or contains a name
                error, cache the data as well as returning it back to
                the client.
                b. if the response contains a better delegation to other
                servers, cache the delegation information, and go to
                step 2.
                c. if the response shows a CNAME and that is not the
                answer itself, cache the CNAME, change the SNAME to the
                canonical name in the CNAME RR and go to step 1.
                d. if the response shows a servers failure or other
                bizarre contents, delete the server from the SLIST and
                go back to step 3.

        Args:
            hostname (str): the hostname to resolve

        Returns:
            (str, [str], [str]): (hostname, aliaslist, ipaddrlist)
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self.timeout)

        # Create and send query
        question = Question(Name(hostname), Type.A, Class.IN)
        header = Header(9001, 0, 1, 0, 0, 0)
        header.qr = 0
        header.opcode = 0
        header.rd = 0 # no recursion desired
        query = Message(header, [question])
        sock.sendto(query.to_bytes(), ("8.8.8.8", 53))

        # Receive response
        data = sock.recv(512)
        response = Message.from_bytes(data)

        # Get data
        aliaslist = []
        ipaddrlist = []
        for answer in response.answers:
            if answer.type_ == Type.A:
                ipaddrlist.append(answer.rdata.address)
            if answer.type_ == Type.CNAME:
                aliaslist.append(hostname)
                hostname = str(answer.rdata.cname)

        return hostname, aliaslist, ipaddrlist
