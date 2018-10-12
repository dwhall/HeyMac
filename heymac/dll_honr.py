#!/usr/bin/env python3
"""
Copyright 2018 Dean Hall.  See LICENSE for details.

Data Link Layer (layer 2) Addressing and Routing.

Terminology

DAG:
    Directed Acyclic Graph

HONR:
    Hierarchically Ordered Numerical Routing

External Address:
    All code outside this module uses Python's
    immutable bytes object, 2 or 8 octets in length
    to represent an address.
    This module's public procedures (lacking a preceding underscore)
    use external addresses for arguments and return values.

Internal Representation:
    This module uses Python's bytearray object
    4 or 16 octets in length to represent an address
    so that each nibble of the addressed may be indexed
    This module's private procedures (having a preceding underscore)
    use external addresses for arguments and return values.

Routing

In a DAG, routing is either "up" or "down".
Upward routes travel toward the DAG's root.
Downward routes travel toward a leaf node.

The Root enjoys the all-zero address: 0000.
The nodes that have the Root as their parent (a.k.a. Rank 1 nodes), have all nibbles set to zero except the leftmost one.
Rank 2 nodes have theif left-most nibble set to match their Rank 1 parent's first nibble
and their second-to-left-most nibble set to uniquely identify themselves.

Root:                       0000
                            |
            +-------+-------+-------+-------+-------+
            |       |       |       |       |       |
Rank 1:     1000    2000    5000    7000    A000    C000
            |                       |               |
            +-------+       +-------+               +
            |       |       |       |               |
Rank 2:     1100    1800    7200    7C00            C500
"""


def _to_internal_repr(addrx):
    """Returns a bytearray twice the length of the given address
    so that each nibble may be indexed
    """
    assert type(addrx) is bytes
    addri = bytearray()
    for b in addrx: addri.extend([b >> 4, b & 0xf])
    return addri


def _to_external_addr(addri):
    """Returns a bytes object half the length of the given address
    to be used outside this module
    """
    assert type(addri) is bytearray
    left = addri[0::2]
    right = addri[1::2]
    return bytes([left[i]<<4 | right[i] for i in range(len(left))])


def get_nearest_common_ancestor(srcx, dstx):
    """Returns the address of the Nearest Common Ancestor
    which connects the src and dst nodes in a DAG
    in internal representation.
    """
    srci = _to_internal_repr(srcx)
    dsti = _to_internal_repr(dstx)
    ncai = _get_nearest_common_ancestor(srci, dsti)
    return _to_external_addr(ncai)

def _get_nearest_common_ancestor(srci, dsti):
    assert _is_addr_valid(srci)
    assert _is_addr_valid(dsti)
    assert len(srci) == len(dsti)

    # Start with all zeros
    ncai = bytearray(len(srci))

    # Copy the nibble to the NCA when it is the same in both (LtoR)
    for i in range(len(srci)):
        if srci[i] == dsti[i]:
            ncai[i] = srci[i]
        else:
            break

    return ncai


def get_route(srcx, dstx):
    """Returns the ideal route from src to dst
    as a list of addresses (external representation)
    """
    srci = _to_internal_repr(srcx)
    dsti = _to_internal_repr(dstx)
    routi = _get_route(srci, dsti)
    return list(map(_to_external_addr, routi))

def _get_route(srci, dsti):
    route = []
    ncai = _get_nearest_common_ancestor(srci, dsti)
    curi = srci
    leftzero = curi.find(0)
    if leftzero == -1:
        leftzero = len(srci)
    while curi != ncai:
        route.append(curi.copy())
        leftzero -= 1
        curi[leftzero] = 0
    route.append(ncai.copy())
    while curi != dsti:
        curi[leftzero] = dsti[leftzero]
        route.append(curi.copy())
        leftzero += 1
    return route


def is_addr_valid(addrx):
    """Returns True if the address is a proper length
    and has a valid form
    (all bytes right of the left-most zero must be zero).
    """
    valid = False
    if type(addrx) is bytes:
        addri = _to_internal_repr(addrx)
        valid = _is_addr_valid(addri)
    return valid

def _is_addr_valid(addri):
    valid = False

    # Must have correct type and a length that equates to 2 or 16 octets
    if type(addri) is bytearray:
        if len(addri) in (4, 16):

            # If no zero is found, the address is valid
            leftzero = addri.find(0)
            if leftzero < 0:
                valid = True

            # All bytes right of the left-most zero must be zero
            else:
                if sum(addri[leftzero:]) == 0:
                    valid = True

    return valid


# NOTE: This function returns False in some cases
# where a node could opportunistically make routing improvements.
# i.e. This function returns True only for simplest route.
def should_route(resx, dstx, locx):
    """Returns True if this node (loc) should route a frame
    that has the given resender and destination addresses.
    In this case, "resender" is the neighbor that transmitted
    this frame to this node.
    NOTE: The source address is not considered because it may be encrypted.
    """
    # Do not route, already at destination
    if dstx == locx:
        return False

    # If the local address follows the resender in the ideal route
    route = get_route(resx, dstx)
    return (resx in route and locx in route
            and route.index(locx) - route.index(resx) == 1)
