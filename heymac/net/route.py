"""
Copyright 2018 Dean Hall.  See LICENSE for details.

Routing
-------

Message travel along a DAG is either "up" or "down".
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

Note that the reverse route is also just as simple.
Second, when routing from one node to another a simple
up-down route is available.  The route proceeds from the source,
up to the nearest ancestor common to both nodes
and then down to the destination.  The nearest common
ancestor (NCA) may or may not be the root.  Determining the
nearest common ancestor address is trivial:

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
"""


from . import honr


def get_route(srcx, dstx):
    """Returns the simple up-down route
    from src to dst as a list of addresses
    """
    route = []
    curi = honr.to_internal_repr(srcx)
    dsti = honr.to_internal_repr(dstx)
    ncax = honr.get_nearest_common_ancestor(srcx, dstx)
    ncai = honr.to_internal_repr(ncax)
    leftzero = honr.get_rank(srcx)
    while curi != ncai:
        route.append(honr.to_external_addr(curi))
        leftzero -= 1
        curi[leftzero] = 0
    route.append(ncax)
    while curi != dsti:
        curi[leftzero] = dsti[leftzero]
        route.append(honr.to_external_addr(curi))
        leftzero += 1
    return route


def should_route(resx, dstx, locx):
    """Returns True if this node (loc) should route a frame
    that has the given resender and destination addresses.
    In this case, "resender" is the neighbor that transmitted
    this frame to this node.
    NOTE: The source address is not considered because it may be encrypted.
    NOTE: This function returns True only for the basic up/down route
    which means this function returns False in some cases
    where a node could opportunistically make routing improvements.
    """
    # Do not route, already at destination
    if dstx == locx:
        return False

    # If the local address follows the resender in the ideal route
    route = get_route(resx, dstx)
    return (resx in route and locx in route
            and route.index(locx) - route.index(resx) == 1)
