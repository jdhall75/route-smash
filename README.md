route-smash
===========

Quick'n'Dirty prefix generator for use with ExaBGP

### Description

This is a simple python script to generate sequential BGP updates (all /24s).  When combined with an appropriate ExaBGP configuration, route-smash can be used to load test routers and benchmark RIB, FIB and Forwarding-Plane limits.

### Usage

Given the following exabgp configuration:


```
## File: exabgp.conf
neighbor 10.0.5.10 {
    description "Test Router";
    router-id 10.0.0.31;
    local-address 10.0.0.31;
    local-as 65001;
    peer-as 65000;
    process route-smash {
    	run ./route-smash.py;
    }
}
```


### Arguments for route-smash
```
usage: route-smash [-h] [--rfc1918 | --martians] --next-hop NEXT_HOP
                   [--communities COMMUNITIES] --asn ASN [--random-path]
                   [--bogon-path] [--max-path-length MAX_PATH_LENGTH]
```

Only Generate RFC1918 router
`--rfc1918`

Generate routes in the IANA reserved space; mutually exclusive and includes --rfc1918
`--martians`

Set the next-hop
`--next-hop 10.0.0.31`

Comma separated list of communites you want to attach to the update
`--communities 65001:12345,65001:666`

Set the local ASN
`--asn 123`

Generate bogon as-paths or just random as-paths for the announcements
`--random-path`
`--bogon-path`

Set the maximum length the as-path can be
`--max-path-length 10`


and assuming route-smash.py was located in the same directory you would launch with:

```
exabgp exabgp.conf
```
