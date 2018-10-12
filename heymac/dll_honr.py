#!/usr/bin/env python3
"""
Copyright 2018 Dean Hall.  See LICENSE for details.

HONR: Hierarchically Ordered Numerical Routing

Abstract
--------

HeyMac is comparable to the `IEEE 802.15.4`_ MAC layer and the 6LoWPAN_ data link layer
and is able to re-use ideas from the IETF ROLL_ and 6LoWPAN working groups
to solve the problems of ad-hoc node addressing and multi-hop message routing.

HONR is a method of hierarchical addressing similar to HiLow_
where each node may have up to fifteen children.
HONR's numbering method differs from HiLow slightly to improve
the human readability of the addresses.

.. _`IEEE 802.15.4`: https://en.wikipedia.org/wiki/IEEE_802.15.4
.. _ROLL: https://datatracker.ietf.org/wg/roll/about/
.. _6LoWPAN: https://datatracker.ietf.org/wg/6lowpan/charter/
.. _HiLow: https://tools.ietf.org/html/draft-daniel-6lowpan-hilow-hierarchical-routing-01


Introduction
------------

HONR is a Data Link Layer (layer 2) Addressing and Routing method
that organizes participating nodes into a DAG
by assigning hierarchially formed two or eight octet addresses
and routes messages between nodes by passing the message along the DAG.

Two octet addresses allow networks to have 5 layers (ranks 0..4),
or eight hops between two nodes having only the root as a common ancestor.
Whereas eight octet addressing allows networks to have 17 layers (ranks 0..16)
or thirty-two hops between two maximally-distant nodes.
The remainder of this document only deals with two-octet addressing
as eight-octet addressing will only be implemented if necessary.

The root of the network is given the special address, zero (0x000).
All other addresses are calculated by replacing the left-most-zero
in the parent's address with a value (decimal 1..15 or hex 1..F).
The nodes that have the Root as their parent (a.k.a. Rank 1 nodes),
have all nibbles except the leftmost set to zero.

Rank 1 Example::

    Parent:     0x0000  (root)
    Child1:     0x1000
    Child15:    0xF000

Rank 2 nodes have theif left-most nibble set to match
their Rank 1 parent's first nibble and their second-to-left-most nibble
set to uniquely identify themselves.

Rank 2 Example::

    Parent:     0xA000
    Child1:     0xA100
    Child15:    0xAF00

In a DAG, routing is either "up" or "down".
Upward routes travel toward the DAG's root.
Downward routes travel toward a leaf node.

Example DAG::

    Root:                       0x0000
                                |
                +-------+-------+-------+-------+-------+
                |       |       |       |       |       |
    Rank 1:     0x1000  0x2000  0x5000  0x7000  0xA000  0xC000
                |                       |               |
                +-------+       +-------+               +
                |       |       |       |               |
    Rank 2:     0x1100  0x1800  0x7200  0x7C00          0xC500


Terminology
-----------

DAG:
    Directed Acyclic Graph

Root:
    The logical first node in a DAG to which the first layer of nodes attach.


Software Implementation Details
-------------------------------

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
"""


# Two-octet root address
ROOT2 = b"\x00\x00"


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


def get_parent(addrx):
    """Returns the given address's parent address.
    Returns None if the Root address is given.
    """
    addri = _to_internal_repr(addrx)
    return _get_parent(addri)

def _get_parent(addri):
    if sum(addri) == 0:
        return None
    leftzero = _get_rank(addri)
    addri[leftzero - 1] = 0
    return _to_external_addr(addri)


def get_rank(addrx):
    """Retuns the rank of the given address [integer]
    """
    addri = _to_internal_repr(addrx)
    return _get_rank(addri)

def _get_rank(addri):
    assert _is_addr_valid(addri)
    leftzero = addri.find(0)
    if leftzero == -1:
        leftzero = len(addri)
    return leftzero


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
    curi = srci.copy()
    leftzero = _get_rank(curi)
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
