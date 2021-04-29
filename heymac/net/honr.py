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
Using HONR, each node may have up to fourteen children.
HONR's numbering method differs from HiLow slightly
to ease algorithm implementations for numbering and routing
as well as to increase the human readability of the addresses.

HONR is a network layer addressing method that expects participating nodes
to organize into a DAG (Directed Acyclic Graph).
The addresses are formed according to their position in the DAG.
Nodes route messages up and down along the DAG.
All addresses in the DAG are either two octets or eight octets.
Nodes join and leave the network at any time and the network
has repair and renumbering operations.

.. _`IEEE 802.15.4`: https://en.wikipedia.org/wiki/IEEE_802.15.4
.. _ROLL: https://datatracker.ietf.org/wg/roll/about/
.. _6LoWPAN: https://datatracker.ietf.org/wg/6lowpan/charter/
.. _HiLow: https://tools.ietf.org/html/draft-daniel-6lowpan-hilow-hierarchical-routing-01


Addressing
----------

The Root of the network is given the special address zero (0x0000).
All non-Root nodes form their address as follows:
take the parent's address and replace the left-most zero nibble
with a nibble value 1 through 14 (or hex 1 through E).

The nodes that have the Root as their parent (a.k.a. Rank 1 nodes),
have all nibbles except the leftmost set to zero.

Rank 1 Example::

    Parent:     0x0000  (Root)
    Child1:     0x1000
    Child2:     0x2000
    ...         ...
    Child14:    0xE000

Rank 2 nodes have their left nibble set to match
their Rank 1 parent's first nibble and their second-to-left nibble
set to uniquely identify themselves.

Rank 2 Example::

    Parent:     0xA000
    Child1:     0xA100
    Child2:     0xA200
    ...         ...
    Child14:    0xAE00

The HONR numbering method makes address assignment easy and efficient.
Since a node's HONR address is dependent solely on its parent's address,
the parent (and not Root) makes local decisions about address assignment.
This distributes the effort of address assignment and there is no need
for coordination between parent nodes because there is no possibility
of address collision.

Broadcast
---------

The nibble value fifteen (decimal 15, hex F) designates a broadcast value.
Any node with children may broadcast to all its children by
replacing the node address's left-most zero with the nibble F.
For example, if the node 0xAE00 sends a message to 0xAEF0,
then the nodes (0xAE10, 0xAE20 ... 0xAEE0), if they exist,
accept and process the message.
Furthermore, a node may broadcast more than one step down its DAG
by appending as many fifteen nibbles as allowed.
For example, if the node 0x2000 sends a message to 0x2FF0,
all of 0x2000's Rank 2 children and Rank 3 grandchildren
will receive the message, but the Rank 4 great-grandchildren will not.
The address 0xFFFF is broadcast to all nodes in the network, including Root.

Expanse
-------

Networks using two octet HONR addresses may have up to 5 layers (Ranks 0..4),
or eight hops between two maximally distant nodes
having Root as their only common ancestor.
Whereas eight octet addressing allows networks to have 17 layers (Ranks 0..16)
or thirty-two hops between two maximally distant nodes.
The remainder of this document only deals with two octet addressing
as eight octet addressing will not be implemented unless necessary.

The HONR16 address creation method means that an address may not have
a zero-value nibble that is left of a non-zero nibble.
Also, the nibble value 15 (hex F) is reserved for broadcast
and may not be used in a node's address.  This yields::

    sum([14**n for n in range(5)]) = 41371

addresses (including Root) available to use out of 65536 possible.
That is a 37% loss of address space.

A node with no zero-value nibble (a.k.a. a Rank 4 node)
may not assign any node to be its child.  So the HONR numbering system
creates a hard limit to the number of hops in the network.
This tradeoff is acceptable as each hop creates message latency
and it is good to keep latency smaller.


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

from functools import reduce


# Two-octet Root address
ROOT2 = b"\x00\x00"


def to_internal_repr(addrx):
    """Returns a bytearray twice the length of the given address
    so that each nibble may be indexed
    """
    assert type(addrx) is bytes
    addri = bytearray()
    for b in addrx:
        addri.extend([b >> 4, b & 0xf])
    return addri


def to_external_addr(addri):
    """Returns a bytes object half the length of the given address
    to be used outside this module
    """
    if addri is None:
        return None
    assert type(addri) is bytearray
    left = addri[0::2]
    right = addri[1::2]
    return bytes([left[i] << 4 | right[i] for i in range(len(left))])


def get_nearest_common_ancestor(srcx, dstx):
    """Returns the address of the Nearest Common Ancestor
    which connects the src and dst nodes in a DAG
    in internal representation.
    """
    srci = to_internal_repr(srcx)
    dsti = to_internal_repr(dstx)
    ncai = _get_nearest_common_ancestor(srci, dsti)
    return to_external_addr(ncai)


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
    addri = to_internal_repr(addrx)
    addri = _get_parent(addri)
    return to_external_addr(addri)


def _get_parent(addri):
    if sum(addri) == 0:
        return None
    leftzero = _get_rank(addri)
    addri[leftzero - 1] = 0
    return addri


def get_rank(addrx):
    """Retuns the rank of the given address [integer]
    """
    addri = to_internal_repr(addrx)
    return _get_rank(addri)


def _get_rank(addri):
    assert _is_addr_valid(addri)
    leftzero = addri.find(0)
    if leftzero == -1:
        leftzero = len(addri)
    return leftzero


def is_addr_valid(addrx):
    """Returns True if the address is a proper length
    and has a valid form.
    To have a valid form, all of the following must be true:
    1) all nibbles right of the left-most zero must be zero
    2) all nibbles right of the left-most fifteen must be zero or fifteen
    3) all nibbles right of the right-most fifteen must be zero
    4) all nibbles between the left- and right-most fifteen must be fifteen
    """
    valid = False
    if type(addrx) is bytes:
        addri = to_internal_repr(addrx)
        valid = _is_addr_valid(addri)
    return valid


def _is_addr_valid(addri):
    """Returns True if the address is a proper length
    and has a valid form.
    To have a valid form, all of the following must be true:
    1) all nibbles right of the left-most zero must be zero
    2) if there is a fifteen nibble, all nibbles between
        the left- and right-most fifteen must be fifteen
    3) all nibbles right of the right-most fifteen must be zero
    """
    # Must have correct type and a length that equates to 2 or 8 octets
    if type(addri) is not bytearray or len(addri) not in (4, 16):
        return False

    # If 1) is not true, return false
    left_most_0 = addri.find(0)
    if left_most_0 >= 0 and sum(addri[left_most_0:]) != 0:
        return False

    # If 2) is not true, return false
    left_most_F = addri.find(0xF)
    if left_most_F >= 0:
        right_most_F = addri.rfind(0xF)
        any_is_not_fifteen = reduce(
            _or_func,
            map(_is_not_fifteen, addri[left_most_F:right_most_F]),
            False)
        if any_is_not_fifteen:
            return False

        # If 3) is not true, return false
        if sum(addri[right_most_F + 1:]) != 0:
            return False

    return True


def is_addr_valid_bcast(addrx):
    """Returns True if the address is a proper broadcast address.
    """
    valid = False
    if type(addrx) is bytes:
        addri = to_internal_repr(addrx)
        valid = _is_addr_valid_bcast(addri)
    return valid

def _is_addr_valid_bcast(addri):
    return _is_addr_valid(addri) and 0xF in addri


def is_addr_valid_node(addrx):
    """Returns True if the address is a proper node address (not broadcast).
    """
    valid = False
    if type(addrx) is bytes:
        addri = to_internal_repr(addrx)
        valid = _is_addr_valid_node(addri)
    return valid


def _is_addr_valid_node(addri):
    return _is_addr_valid(addri) and 0xF not in addri


def _is_not_fifteen(x):
    return x != 0xF


def _or_func(x, y):
    return x or y
