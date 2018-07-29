import unittest

"""HeyMac Address operations
An address is of type bytes in order to be immutable.
In this file, each byte holds only a nibble (4-bits) of address
to make it easier to manipulate each nibble separately.
These operations are meant to show how easy it is to route within a DAG of nodes with HONR addresses.

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


def is_addr_valid(addr):
    """Returns True if the given address meets all critera for a valid address.
    Address must be 4 or 16 nibbles (16 or 64 bits)
    Address values must be nibble-sized
    A zero must not be left (more significant posn) of a non-zero
    """
    assert type(addr) is bytes

    valid = True

    # Address must be 4 or 16 nibbles (16 or 64 bits)
    if len(addr) not in (4, 16):
        valid = False

    else:
        leftzero = -1
        for i in range(len(addr)):

            # All values must be nibble-sized
            if addr[i] >= 16:
                valid = False

            # Save the index of the left-most zero
            if leftzero < 0 and addr[i] == 0:
                leftzero = i
                continue

            # Everything right of the left-most zero must be a zero
            if leftzero >= 0 and addr[i] != 0:
                valid = False

    return valid


def get_nearest_common_ancestor(src, dst):
    """Returns the address of the Nearest Common Ancestor
    which connects the src and dst nodes in a DAG.
    """
    assert is_addr_valid(src)
    assert is_addr_valid(dst)
    assert len(src) == len(dst)

    differ = False

    # Copy the nibble to the NCA when it is the same in both (LtoR)
    nca = bytearray()
    for i in range(len(src)):
        if src[i] == dst[i]:
            if differ:
                nca.append(0)
            else:
                nca.append(src[i])
        else:
            nca.append(0)
            differ = True
    nca = bytes(nca)

    assert is_addr_valid(nca), "NCA: " + str(nca)
    return nca


def get_next_addr(myaddr, dst):
    """Returns the address of the next node on the route to dest.
    Assumes this node should route the packet.
    """
    # No need to assert-check myaddr and dst, get_route_dir() will do that

    route_dir = get_route_dir(myaddr, dst)
    leftzero = myaddr.find(0)
    if leftzero == -1:
        leftzero = len(myaddr)
    next_addr = bytearray(len(myaddr))

    # Upward routes have fewer nonzero digits
    if route_dir == "up":
        next_addr[0:leftzero - 1] = myaddr[0:leftzero - 1]

    # Downward routes have more nonzero digits
    elif route_dir == "down":
        next_addr[0:leftzero + 1] = dst[0:leftzero + 1]
    return bytes(next_addr)


def get_route(src, dst):
    """Returns the sequence of nodes from src to dst, inclusive
    as a list of addresses (bytes of nibbles).
    """
    # No need to assert-check src and dst, get_nearest_common_ancestor() will do that
    route = []
    nca = get_nearest_common_ancestor(src, dst)
    cur = bytearray(src)
    leftzero = cur.find(0)
    if leftzero == -1:
        leftzero = len(src)

    while cur != nca:
        route.append(bytes(cur))
        leftzero -= 1
        cur[leftzero] = 0
    route.append(bytes(nca))
    while cur != dst:
        cur[leftzero] = dst[leftzero]
        route.append(bytes(cur))
        leftzero += 1
    return route


def get_route_dir(myaddr, dst):
    """Returns the direction to route the packet.
    If this node's address is the dst, routing is done (None).
    If this node's address matches the destination up to
    this node's left-most zero, route down; else route up
    """
    assert is_addr_valid(myaddr)
    assert is_addr_valid(dst)
    assert len(myaddr) == len(dst)

    route_dir = "bad"

    if myaddr == dst:
        route_dir = None
    else:
        # Compare nibbles left-to-right
        for i in range(len(myaddr)):

            # We reached this node's left-most zero
            # without any nibble diffs, so dst is a
            # decendant of this node: route down
            if myaddr[i] == 0:
                route_dir = "down"
                break

            # Nibble diffs before this node's left-most zero,
            # so dst is on a different branch: route up
            if myaddr[i] != dst[i]:
                route_dir = "up"
                break

    assert route_dir != "bad"
    return route_dir


class TestAddrMethods(unittest.TestCase):
    def test_is_addr_valid(self,):
        self.assertTrue(is_addr_valid(b"\x00\x00\x00\x00"))
        self.assertTrue(is_addr_valid(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"))
        self.assertTrue(is_addr_valid(b"\x01\x00\x00\x00"))
        self.assertTrue(is_addr_valid(b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"))
        self.assertTrue(is_addr_valid(b"\x01\x0F\x0F\x0F"))
        self.assertTrue(is_addr_valid(b"\x01\x0F\x0F\x0F\x0F\x0F\x0F\x0F\x0F\x0F\x0F\x0F\x0F\x0F\x0F\x0F"))
        # Bad addresses
        # greater than a nibble
        self.assertFalse(is_addr_valid(b"\x00\x00\x00\x10"))
        self.assertFalse(is_addr_valid(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10"))
        # greater than a nibble
        self.assertFalse(is_addr_valid(b"\x10\x00\x00\x00"))
        self.assertFalse(is_addr_valid(b"\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"))
        # zero left of non-zero
        self.assertFalse(is_addr_valid(b"\x00\x01\x00\x00"))
        self.assertFalse(is_addr_valid(b"\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"))
        # addr wrong size
        self.assertFalse(is_addr_valid(b"\x00\x00\x00"))
        self.assertFalse(is_addr_valid(b"\x00\x00\x00\x00\x00"))
        self.assertFalse(is_addr_valid(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"))
        self.assertFalse(is_addr_valid(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"))

    def test_get_nearest_common_ancestor(self,):
        # Happy cases
        self.assertEqual(get_nearest_common_ancestor(b"\x00\x00\x00\x00", b"\x00\x00\x00\x00"), b"\x00\x00\x00\x00")
        self.assertEqual(get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"), b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(get_nearest_common_ancestor(b"\x01\x00\x00\x00", b"\x02\x00\x00\x00"), b"\x00\x00\x00\x00")
        self.assertEqual(get_nearest_common_ancestor(b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"), b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(get_nearest_common_ancestor(b"\x01\x01\x01\x00", b"\x01\x01\x00\x00"), b"\x01\x01\x00\x00")
        self.assertEqual(get_nearest_common_ancestor(b"\x02\x02\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x02\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"), b"\x02\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(get_nearest_common_ancestor(b"\x01\x01\x01\x00", b"\x01\x0E\x0B\x00"), b"\x01\x00\x00\x00")
        self.assertEqual(get_nearest_common_ancestor(b"\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x01\x0E\x0B\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"), b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(get_nearest_common_ancestor(b"\x0A\x01\x02\x03", b"\x0B\x0B\x02\x09"), b"\x00\x00\x00\x00")

        # Bad addresses
        with self.assertRaises(AssertionError): get_nearest_common_ancestor(b"\x10\x00\x00\x00", b"\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_nearest_common_ancestor(b"\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_nearest_common_ancestor(b"\x00\x00\x00\x00", b"\x10\x00\x00\x00")
        with self.assertRaises(AssertionError): get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_nearest_common_ancestor(b"\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_nearest_common_ancestor(b"\x00\x00\x00\x01", b"\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_nearest_common_ancestor(b"\x00\x00\x00\x00", b"\x00\x00\x00\x01")
        with self.assertRaises(AssertionError): get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01")

    def test_get_next_addr(self,):
        # Happy cases
        self.assertEqual(get_next_addr(b"\x00\x00\x00\x00", b"\x01\x00\x00\x00"), b"\x01\x00\x00\x00")
        self.assertEqual(get_next_addr(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"), b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(get_next_addr(b"\x01\x00\x00\x00", b"\x00\x00\x00\x00"), b"\x00\x00\x00\x00")
        self.assertEqual(get_next_addr(b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"), b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(get_next_addr(b"\x01\x00\x00\x00", b"\x0B\x00\x00\x00"), b"\x00\x00\x00\x00")
        self.assertEqual(get_next_addr(b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x0B\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"), b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(get_next_addr(b"\x02\x05\x05\x06", b"\x09\x09\x05\x03"), b"\x02\x05\x05\x00")
        self.assertEqual(get_next_addr(b"\x02\x05\x05\x05\x05\x05\x05\x05\x05\x05\x05\x05\x05\x05\x05\x06", b"\x09\x09\x09\x09\x09\x09\x09\x09\x09\x09\x09\x09\x09\x09\x05\x03"), b"\x02\x05\x05\x05\x05\x05\x05\x05\x05\x05\x05\x05\x05\x05\x05\x00")
        self.assertEqual(get_next_addr(b"\x09\x09\x05\x00", b"\x09\x09\x05\x03"), b"\x09\x09\x05\x03")
        self.assertEqual(get_next_addr(b"\x09\x09\x09\x09\x09\x09\x09\x09\x09\x09\x09\x09\x09\x09\x05\x00", b"\x09\x09\x09\x09\x09\x09\x09\x09\x09\x09\x09\x09\x09\x09\x05\x03"), b"\x09\x09\x09\x09\x09\x09\x09\x09\x09\x09\x09\x09\x09\x09\x05\x03")
        # Bad addresses
        with self.assertRaises(AssertionError): get_next_addr(b"\x10\x00\x00\x00", b"\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_next_addr(b"\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_next_addr(b"\x00\x00\x00\x00", b"\x10\x00\x00\x00")
        with self.assertRaises(AssertionError): get_next_addr(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_next_addr(b"\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_next_addr(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_next_addr(b"\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_next_addr(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_next_addr(b"\x00\x00\x00\x01", b"\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_next_addr(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_next_addr(b"\x00\x00\x00\x00", b"\x00\x00\x00\x01")
        with self.assertRaises(AssertionError): get_next_addr(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01")

    def test_get_route(self,):
        # Happy cases
        self.assertEqual(get_route(b"\x00\x00\x00\x00", b"\x00\x00\x00\x00"), [b"\x00\x00\x00\x00"])
        self.assertEqual(get_route(b"\x01\x00\x00\x00", b"\x00\x00\x00\x00"), [b"\x01\x00\x00\x00", b"\x00\x00\x00\x00"])
        self.assertEqual(get_route(b"\x00\x00\x00\x00", b"\x01\x00\x00\x00"), [b"\x00\x00\x00\x00", b"\x01\x00\x00\x00"])
        self.assertEqual(get_route(b"\x01\x01\x00\x00", b"\x01\x00\x00\x00"), [b"\x01\x01\x00\x00", b"\x01\x00\x00\x00"])
        self.assertEqual(get_route(b"\x0A\x00\x00\x00", b"\x0B\x00\x00\x00"), [b"\x0A\x00\x00\x00", b"\x00\x00\x00\x00", b"\x0B\x00\x00\x00"])
        self.assertEqual(get_route(b"\x0A\x01\x02\x03", b"\x0B\x0B\x02\x09"),
                                  [b"\x0A\x01\x02\x03", b"\x0A\x01\x02\x00", b"\x0A\x01\x00\x00", b"\x0A\x00\x00\x00",
                                   b"\x00\x00\x00\x00",
                                   b"\x0B\x00\x00\x00", b"\x0B\x0B\x00\x00", b"\x0B\x0B\x02\x00", b"\x0B\x0B\x02\x09", ])


    def test_get_route_dir(self,):
        # Happy cases
        self.assertEqual(get_route_dir(b"\x00\x00\x00\x00", b"\x00\x00\x00\x00"), None)
        self.assertEqual(get_route_dir(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"), None)
        self.assertEqual(get_route_dir(b"\x01\x00\x00\x00", b"\x00\x00\x00\x00"), "up")
        self.assertEqual(get_route_dir(b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"), "up")
        self.assertEqual(get_route_dir(b"\x00\x00\x00\x00", b"\x01\x00\x00\x00"), "down")
        self.assertEqual(get_route_dir(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"), "down")
        self.assertEqual(get_route_dir(b"\x01\x0E\x01\x00", b"\x0E\x00\x00\x00"), "up")
        self.assertEqual(get_route_dir(b"\x01\x0E\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x0E\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"), "up")
        self.assertEqual(get_route_dir(b"\x0E\x00\x00\x00", b"\x01\x0E\x01\x00"), "up")
        self.assertEqual(get_route_dir(b"\x0E\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x01\x0E\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"), "up")
        self.assertEqual(get_route_dir(b"\x01\x0E\x00\x00", b"\x01\x0E\x01\x00"), "down")
        self.assertEqual(get_route_dir(b"\x01\x0E\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x01\x0E\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"), "down")
        # Bad addresses
        with self.assertRaises(AssertionError): get_route_dir(b"\x10\x00\x00\x00", b"\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_route_dir(b"\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_route_dir(b"\x00\x00\x00\x00", b"\x10\x00\x00\x00")
        with self.assertRaises(AssertionError): get_route_dir(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_route_dir(b"\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_route_dir(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_route_dir(b"\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_route_dir(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_route_dir(b"\x00\x00\x00\x01", b"\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_route_dir(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_route_dir(b"\x00\x00\x00\x00", b"\x00\x00\x00\x01")
        with self.assertRaises(AssertionError): get_route_dir(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01")


if __name__ == '__main__':
    unittest.main()
