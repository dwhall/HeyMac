#!/usr/bin/env python3
"""
Copyright 2018 Dean Hall.  See LICENSE for details.

HONR: Hierarchically Ordered Numerical Routing

Abstract
--------

HeyMac is comparable to the `IEEE 802.15.4`_ MAC layer and
APv6 is comparable to the 6LoWPAN_ adaptation layer.
HeyMac and APv6 can adapt ideas from the IETF ROLL_ and 6LoWPAN working groups
to solve the problems of ad-hoc node addressing and multi-hop message routing.

HONR is a method of hierarchical addressing similar to HiLow_.
Using HONR, each node may have up to fifteen children.
HONR's numbering method differs from HiLow slightly
to ease algorithm implementations for numbering and routing
as well as to increase the human readability of the addresses.

HONR is a Data Link Layer (layer 2) addressing and routing method
that expects participating nodes to organize into a DAG (Directed Acyclic Graph).
The hierarchically formed addresses according to position in the DAG.
Nodes route messages between up and down along the DAG.
All addresses in the DAG are either two octets or eight octets.
Nodes join and leave the network at any time and the network
has repair and address-reassignment operations.

.. _`IEEE 802.15.4`: https://en.wikipedia.org/wiki/IEEE_802.15.4
.. _ROLL: https://datatracker.ietf.org/wg/roll/about/
.. _6LoWPAN: https://datatracker.ietf.org/wg/6lowpan/charter/
.. _HiLow: https://tools.ietf.org/html/draft-daniel-6lowpan-hilow-hierarchical-routing-01


Addressing
----------

The Root of the network is given the special address zero (0x000).
All non-Root nodes have their address formed as follows:
take the parent's address and replace the left-most-zero nibble
with a non-zero nibble value (decimal 1..15 or hex 1..F).

The nodes that have the Root as their parent (a.k.a. Rank 1 nodes),
have all nibbles except the leftmost set to zero.

Rank 1 Example::

    Parent:     0x0000  (Root)
    Child1:     0x1000
    Child2:     0x2000
    ...         ...
    Child15:    0xF000

Rank 2 nodes have their left nibble set to match
their Rank 1 parent's first nibble and their second-to-left nibble
set to uniquely identify themselves.

Rank 2 Example::

    Parent:     0xA000
    Child1:     0xA100
    Child2:     0xA200
    ...         ...
    Child15:    0xAF00

The HONR numbering method makes address assignment easy and efficient.
Since a node's HONR address is dependent solely on its parent's address,
the parent (and not Root) makes local decisions about address assignment.
This distributes the effort of address assignment and there is no need
for coordination between parent nodes because there is no possibility
of address collision.


Expanse
-------

Networks using two octet HONR addresses may have up to 5 layers (Ranks 0..4),
or eight hops between two maximally distant nodes having Root as their only common ancestor.
Whereas eight octet addressing allows networks to have 17 layers (Ranks 0..16)
or thirty-two hops between two maximally distant nodes.
The remainder of this document only deals with two octet addressing
as eight octet addressing will not be implemented unless necessary.

The HONR address creation method means that an address may not have
a zero-value nibble that is left of a non-zero nibble. This yields::

    sum([15**n for n in range(5)]) = 54241

addresses (including Root) available to use out of 65536 possible.
That's only a 17% loss of address space.

However, a node with no zero-value nibble (a.k.a. a Rank 4 node)
may not assign any node to be its child.  So the HONR numbering system
creates a hard limit to the number of hops in the network.
This tradeoff is acceptable as each hop creates message latency
and it is good to keep latency smaller.


Routing
-------

In a DAG, message routing is either "up" or "down".
Upward routes travel toward the DAG's Root.
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

The HONR numbering method has two features that make routing easy.
First, a node's HONR address is tantamount to
the route from the Root to that node.  For example,
to reach node 0xC59A from Root, the route is::

    0x0000, 0xC000, 0xC500, 0xC590, 0xC59A

Second, when routing from one node to another a simple
up-down route is available.  The route proceeds from the source,
up to the nearest ancestor common to both nodes
and then down to the destination.  Determining the
nearest common ancestor (NCA) address is trivial:

1) Proceed along the address nibbles from left to right.
2) If the source and destination nibbles match, copy that nibble to the NCA.
3) If the source and destination nibbles do not match, the NCA's remaining nibbles are zeros.

Two Hop Example::

    Source:         0xC59A
    Destination:    0xC59F
    NCA:            0xC590

                        0xC590
                        ^       v
    Route:          0xC59A      0xC59F

Six Hop Example::

    Source:         0xC59A
    Destination:    0xC232
    NCA:            0xC000
                                0xC000
                                ^       v
                            0xC500      0xC200
                            ^               v
                        0xC590              0xC230
                        ^                       v
    Route:          0xC59A                      0xC232


Source Code Implementation Details
----------------------------------

External Address:
    All code outside this module uses Python's bytes datatype
    2 or 8 octets in length to represent an address.
    This module's public procedures (lacking a preceding underscore)
    use external addresses for arguments and return values.

Internal Representation:
    This module uses Python's bytearray datatype
    4 or 16 octets in length to represent an address
    so that each nibble of the addressed may be indexed

In this module, variables that end with the letter 'x'
hold an external address; whereas, variables that end with
the letter 'i' hold an internal address.
"""


# Two-octet Root address
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
