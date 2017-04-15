#!/usr/bin/env python3

"""Zones of domain name space

See section 6.1.2 of RFC 1035 and section 4.2 of RFC 1034.
Instead of tree structures we simply use dictionaries from domain names to
zones or record sets.

These classes are merely a suggestion, feel free to use something else.
"""
import re

from dns.classes import Class
from dns.name import Name
from dns.resource import ResourceRecord, RecordData, ARecordData, \
    CNAMERecordData
from dns.types import Type


class Catalog:
    """A catalog of zones"""

    def __init__(self):
        """Initialize the catalog"""
        self.zones = {}

    def add_zone(self, name, zone):
        """Add a new zone to the catalog

        Args:
            name (str): root domain name
            zone (Zone): zone
        """
        self.zones[name] = zone


class Zone:
    """A zone in the domain name space"""

    record_re = "^((?:\w+\.?)+)\s+(?:(\d+)\s+)?(?:(\w+)\s+)?(\w+)\s+([\w.]+)"

    def __init__(self):
        """Initialize the Zone """
        self.records = {}

    def add_node(self, name, record_set):
        """Add a record set to the zone

        Args:
            name (str): domain name
            record_set ([ResourceRecord]): resource records
        """
        self.records[name] = record_set

    def read_master_file(self, filename):
        """Read the zone from a master file

        See section 5 of RFC 1035.

        Args:
            filename (str): the filename of the master file
        """
        records = re.finditer(
            Zone.record_re, open(filename, "r").read(), flags=re.MULTILINE
        )
        for r in records:
            domain, ttl, class_, type_, rdata = r.groups()
            record = ResourceRecord(
                name=Name(domain),
                type_=Type[type_],
                class_=Class[class_],
                ttl=int(ttl) if ttl is not None else 0,
                rdata=RecordData.create_from_str(Type[type_], rdata)
            )
            if domain in self.records:
                self.records[domain].append(record)
            else:
                self.records[domain] = [record]
