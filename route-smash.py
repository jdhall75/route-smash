#!/usr/bin/env python

## routesmash.py - 29/07/2014
## ben.dale@gmail.com
## Spam a list of generated /24 prefixes
## Use with ExaBGP for load testing

import sys
import time
import ipaddress
import argparse
import random
from typing import List, Union

bogon_ranges = []
valid_as = []

def parse_args():
    parser = argparse.ArgumentParser(prog="route-smash")

    bogon_group = parser.add_mutually_exclusive_group()

    # RFC1918
    bogon_group.add_argument("--rfc1918", action="store_true")
    bogon_group.set_defaults(rfc1918=False)

    # Martians only
    bogon_group.add_argument("--martians", action="store_true")
    bogon_group.set_defaults(martians=False)

    # Public Range
    parser.add_argument("--public-ranges", action="store_true", default=True)

    # next-hop of route
    parser.add_argument(
        "--next-hop", type=str, required=True, help="IP address of next-hop"
    )

    parser.add_argument(
        "--communities",
        type=str,
        required=False,
        help="Comma separated list of BGP communites to add to the announcements",
    )

    parser.add_argument(
        "--asn",
        type=str,
        default=10,
        required=True,
        help="local ASN for the announcement",
    )


    parser.add_argument("--random-path", action="store_true", default=False)
    parser.add_argument("--bogon-path", action="store_true", default=False)
    parser.add_argument("--max-path-length", type=int, default=10)
    parser.add_argument("--load-test", action="store_true", default=False)
    

    return parser.parse_args()


def format_community_list(mylist: list) -> str:
    if isinstance(mylist, list) and len(mylist) > 0:
        return "community [ {} ]".format(" ".join(mylist))

    return ""


def random_as_path(length):
    path = []
    for _ in range(0, length + 1):
        path.insert(0, random.choice(valid_as))

    # make sure we done have loops
    list_set = set(path)
    return list(list_set)


def bogon_as_path(length):
    as_path = random_as_path(length-1)
    pos = random.randint(1, len(as_path))

    as_path.insert(pos, random.choice(bogon_ranges))
    return as_path


def __print_announcement(
    prefix: str,
    next_hop: str,
    communities: List[str],
    as_path: List[str] = [""],
    med: int = 0,
    origin: str = "IGP",
) -> None:
    as_path = [str(asn) for asn in as_path]
    sys.stdout.write(
        "announce attributes origin {origin} as-path [ {as_path} ] med {med} {communities} next-hop {next_hop} nlri {prefix}\n".format(
            origin=origin,
            as_path=" ".join(as_path),
            med=med,
            communities=format_community_list(communities),
            next_hop=next_hop,
            prefix=prefix,
        )
    )
    sys.stdout.flush()


def gen_rfc1918(prefix_len: int = 24):
    """Generate IP subnets in the ranges defined in RFC1918"""
    ranges = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]

    for r in ranges:
        network = ipaddress.ip_network(r)
        for subnet in network.subnets(new_prefix=prefix_len):
            yield str(subnet)


def gen_martians(prefix_len: int = 24):
    """Generate blocks from all the reserved space
    https://www.iana.org/assignments/iana-ipv4-special-registry/iana-ipv4-special-registry.xhtml
    """
    martians = [
        "0.0.0.0/8",
        "0.0.0.0/32",
        "10.0.0.0/8",
        "100.64.0.0/10",
        "127.0.0.0/8",
        "169.254.0.0/16",
        "172.16.0.0/12",
        "192.0.0.0/24",
        "192.0.0.0/29",
        "192.0.0.8/32",
        "192.0.0.9/32",
        "192.0.0.10/32",
        "192.0.0.170/32",
        "192.0.0.171/32",
        "192.0.2.0/24",
        "192.31.196.0/24",
        "192.52.193.0/24",
        "192.88.99.0/24",
        "192.168.0.0/16",
        "192.175.48.0/24",
        "198.18.0.0/15",
        "198.51.100.0/24",
        "203.0.113.0/24",
        "240.0.0.0/4",
        "255.255.255.255/32",
    ]

    for m in martians:
        network = ipaddress.ip_network(m)

        try:
            subnets = network.subnets(new_prefix=prefix_len)
            for subnet in subnets:
                yield str(subnet)

        except ValueError:
            subnets = [network]
            for subnet in subnets:
                yield str(subnet)


def gen_public_routes(number=10, prefix_len: int = 24):

    public_ranges = ["1.0.0.0/8","2.0.0.0/8"]

    prefix = random.choice(public_ranges)
    
    network = ipaddress.ip_network(prefix)

    count = 0
    for subnet in network.subnets(new_prefix=prefix_len):
        yield str(subnet)

        count += 1

        if count == number:
            break


def gen_load_test(prefix_len:int =24):
    network = ipaddress.ip_network('0.0.0.0/0')
    for subnet in network.subnets(new_prefix=prefix_len):
        yield str(subnet)


def main(args):
    if args.bogon_path or args.random_path:
        # RFC7607, 2 to 4 byte ASN migrations, # RFC7300
        bogon_ranges = [0, 23456, 65535, 4294967295]

        # RFC5398
        bogon_ranges.extend(range(64496, 64512))
        bogon_ranges.extend(range(65536, 65552))
        # RFC6996
        bogon_ranges.extend(range(64512, 65535))
        bogon_ranges.extend(range(4200000000, 4294967294))
        # IANA reserved
        bogon_ranges.extend(range(65552, 131071))

        # 1 - 23456, 23457-64495,
        valid_as = list(range(1, 23457))
        valid_as.extend(range(23457, 64496))



    generators = []
    if args.rfc1918:
        generators.append(gen_rfc1918)
    if args.martians:
        generators.append(gen_martians)
    if args.public_ranges:
        generators.append(gen_public_routes)
    if args.load_test:
        generators.clear()
        generators.append(gen_load_test)

    communities = args.communities.split(",")

    for generator in generators:
        for subnet in generator():
            as_path = [args.asn]
            if args.bogon_path:
                length = random.randint(1,args.max_path_length)
                as_path.extend(bogon_as_path(length))
            elif args.random_path:
                length = random.randint(1,args.max_path_length)
                as_path.extend(random_as_path(length))

            ## Back off timer if router is too slow:
            ##time.sleep(0.001)
            __print_announcement(
                subnet, args.next_hop, communities=communities, as_path=as_path
            )


    while True:
        time.sleep(1)


if __name__ == "__main__":
    args = parse_args()
    main(args)
