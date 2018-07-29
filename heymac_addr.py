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


class NibbleIndexedBytes(object):
    """Like a bytes object, but len(), find() and __getitem__() work on the nibbles.
    Even-valued index is the upper nibble (bits 4-7).  Odd index is lower nibble.
    """
    def __init__(self, addr_bytes):
        assert type(addr_bytes) is bytes
        self.data = addr_bytes


    def __getitem__(self, indx):
        b = self.data[indx // 2]
        if indx % 2:
            n = b & 0xF
        else:
            n = b >> 4
        return n


    def __setitem__(self, indx, item):
        if not 0 <= item <= 15:
            raise ValueError

        b = self.data[i // 2]
        if i % 2:
            b &= 0xF0
            b |= item
        else:
            b &= 0x0F
            b |= (item << 4)
        self.data[i // 2] = b
        return item


    def __len__(self,):
        return 2 * len(self.data)


    def find(self, item):
        assert 0 <= item < 16
        for i in range(len(self)):
            if item == self.data[i]:
                return i
        return -1


class HeyMacAddr(object):
    """HeyMac Address type
    Implemented as a byte array, but indexing is done on a nibble basis
    because the nibble delimits the address's rank.
    """
    def __init__(self, addr):
        self.data = NibbleIndexedBytes(addr)
        assert self.is_addr_valid()


    def __len__(self,):
        """Returns the length of the address in bits.
        """
        # four bits per nibble
        return 4 * len(self.data)


    @staticmethod
    def get_nearest_common_ancestor(src, dst):
        """Returns the address of the Nearest Common Ancestor
        which connects the src and dst nodes in a DAG.
        """
        assert len(src) == len(dst)

        differ = False

        # Copy the nibble to the NCA when it is the same in both (LtoR)
        nibbles = bytearray()
        for i in range(len(src)):
            if src.data[i] == dst.data[i]:
                if differ:
                    nibbles.append(0)
                else:
                    nibbles.append(src.data[i])
            else:
                nibbles.append(0)
                differ = True

        # convert array of nibbles to bytes
        nca = bytearray()
        for i in range(len(nibbles) // 2):
            nca.append(nibbles[2 * i + 0])
            nca.append(nibbles[2 * i + 1])

        return HeyMacAddr(nca)


    def is_addr_valid(self,):
        """Returns True if this address meets all critera for a valid HeyMac address.
        Address must be 16 or 64 bits (short or extended).
        A nibble of zero must not be left of (more significant posn) a non-zero.
        """
        valid = True

        # Address must be 16 or 64 bits (short or extended)
        if len(self) not in (16, 64):
            valid = False

        else:
            leftzero = -1
            for i in range(len(self.data)):

                # Save the index of the left-most zero
                if leftzero < 0 and self.data[i] == 0:
                    leftzero = i

                # Everything right of the left-most zero must be a zero
                elif leftzero >= 0 and self.data[i] != 0:
                    valid = False

        return valid


    def get_next_addr(self, dst):
        """Returns the address of the next node on the route to dest.
        Assumes this node should route the packet.
        """
        # No need to assert-check self and dst, get_route_dir() will do that

        route_dir = self.get_route_dir(dst)
        leftzero = self.data.find(0)
        if leftzero == -1:
            leftzero = len(self.data)

        # Upward routes have fewer nonzero digits
        if route_dir == "up":
            next_addr = self.data[:]
            if leftzero % 2:
                next_addr[leftzero] = 0
            else:
                next_addr[leftzero - 1] &= 0xF0

        # Downward routes have more nonzero digits
        elif route_dir == "down":
            next_addr[0:leftzero + 1] = dst.data[0:leftzero + 1]
        return HeyMacAddr(bytes(next_addr))


    @staticmethod
    def get_route(src, dst):
        """Returns the list of addresses from src to dst, inclusive.
        """
        # No need to assert-check src and dst, get_nearest_common_ancestor() will do that
        route = []
        nca = HeyMacAddr.get_nearest_common_ancestor(src, dst)
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


    def get_route_dir(self, dst):
        """Returns the direction to route the packet.
        If this node's address is the dst, routing is done (None).
        If this node's address matches the destination up to
        this node's left-most zero, route down; else route up
        """
        route_dir = "bad"

        if self.data == dst.data:
            route_dir = None
        else:
            # Compare nibbles left-to-right
            for i in range(len(self.data)):

                # We reached this node's left-most zero
                # without any nibble diffs, so dst is a
                # decendant of this node: route down
                if self.data[i] == 0:
                    route_dir = "down"
                    break

                # Nibble diffs before this node's left-most zero,
                # so dst is on a different branch: route up
                if self.data[i] != dst.data[i]:
                    route_dir = "up"
                    break

        assert route_dir != "bad"
        return route_dir


class TestAddrMethods(unittest.TestCase):
    def test_is_addr_valid(self,):
        self.assertTrue(HeyMacAddr(b"\x00\x00").is_addr_valid())
        self.assertTrue(HeyMacAddr((b"\x00\x00\x00\x00\x00\x00\x00\x00")).is_addr_valid())
        self.assertTrue(HeyMacAddr(b"\x10\x00").is_addr_valid())
        self.assertTrue(HeyMacAddr(b"\x10\x00\x00\x00\x00\x00\x00\x00").is_addr_valid())
        self.assertTrue(HeyMacAddr(b"\x1E\xEE").is_addr_valid())
        self.assertTrue(HeyMacAddr(b"\x1F\xFF").is_addr_valid())
        # Bad addresses
        # zero left of non-zero
        with self.assertRaises(AssertionError): HeyMacAddr(b"\x01\x00")
        with self.assertRaises(AssertionError): HeyMacAddr(b"\x00\xFF")
        with self.assertRaises(AssertionError): HeyMacAddr(b"\x01\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): HeyMacAddr(b"\x11\x01\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): HeyMacAddr(b"\x00\x00\x00\x00\x00\x00\x00\x01")
        # addr wrong size
        with self.assertRaises(AssertionError): HeyMacAddr(b"\x00\x00\x00")
        with self.assertRaises(AssertionError): HeyMacAddr(b"\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): HeyMacAddr(b"\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): HeyMacAddr(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00")

    def test_get_nearest_common_ancestor(self,):
        # Happy cases
        self.assertEqual(HeyMacAddr.get_nearest_common_ancestor(b"\x00\x00", b"\x00\x00"), b"\x00\x00")
        self.assertEqual(HeyMacAddr.get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00"), b"\x00\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(HeyMacAddr.get_nearest_common_ancestor(b"\x10\x00", b"\x02\x00\x00\x00"), b"\x00\x00")
        self.assertEqual(HeyMacAddr.get_nearest_common_ancestor(b"\x10\x00\x00\x00\x00\x00\x00\x00", b"\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"), b"\x00\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(HeyMacAddr.get_nearest_common_ancestor(b"\x01\x01\x01\x00", b"\x01\x01\x00\x00"), b"\x01\x01\x00\x00")
        self.assertEqual(HeyMacAddr.get_nearest_common_ancestor(b"\x02\x02\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x02\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"), b"\x02\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(HeyMacAddr.get_nearest_common_ancestor(b"\x01\x01\x01\x00", b"\x01\x0E\x0B\x00"), b"\x10\x00")
        self.assertEqual(HeyMacAddr.get_nearest_common_ancestor(b"\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x01\x0E\x0B\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"), b"\x10\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(HeyMacAddr.get_nearest_common_ancestor(b"\x0A\x01\x02\x03", b"\x0B\x0B\x02\x09"), b"\x00\x00")

        # Bad addresses
        with self.assertRaises(AssertionError): HeyMacAddr.get_nearest_common_ancestor(b"\x10\x00\x00\x00", b"\x00\x00")
        with self.assertRaises(AssertionError): HeyMacAddr.get_nearest_common_ancestor(b"\x10\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): HeyMacAddr.get_nearest_common_ancestor(b"\x00\x00", b"\x10\x00\x00\x00")
        with self.assertRaises(AssertionError): HeyMacAddr.get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00", b"\x10\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): HeyMacAddr.get_nearest_common_ancestor(b"\x00\x00", b"\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): HeyMacAddr.get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): HeyMacAddr.get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00", b"\x00\x00")
        with self.assertRaises(AssertionError): HeyMacAddr.get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): HeyMacAddr.get_nearest_common_ancestor(b"\x00\x00\x00\x01", b"\x00\x00")
        with self.assertRaises(AssertionError): HeyMacAddr.get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01", b"\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): HeyMacAddr.get_nearest_common_ancestor(b"\x00\x00", b"\x00\x00\x00\x01")
        with self.assertRaises(AssertionError): HeyMacAddr.get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01")

    def test_get_next_addr(self,):
        # Happy cases
        self.assertEqual(HeyMacAddr(b"\x00\x00").get_next_addr(HeyMacAddr(b"\x10\x00")), HeyMacAddr(b"\x10\x00"))
        self.assertEqual(HeyMacAddr(b"\x00\x00\x00\x00\x00\x00\x00\x00").get_next_addr(HeyMacAddr(b"\x10\x00\x00\x00\x00\x00\x00\x00")), HeyMacAddr(b"\x10\x00\x00\x00\x00\x00\x00\x00"))
        self.assertEqual(HeyMacAddr(b"\x10\x00").get_next_addr(HeyMacAddr(b"\x00\x00")), HeyMacAddr(b"\x00\x00"))
        self.assertEqual(HeyMacAddr(b"\x10\x00\x00\x00\x00\x00\x00\x00").get_next_addr(HeyMacAddr(b"\x00\x00\x00\x00\x00\x00\x00\x00")), HeyMacAddr(b"\x00\x00\x00\x00\x00\x00\x00\x00"))
        self.assertEqual(HeyMacAddr(b"\x10\x00").get_next_addr(HeyMacAddr(b"\xB0\x00")), HeyMacAddr(b"\x00\x00"))
        self.assertEqual(HeyMacAddr(b"\x10\x00\x00\x00\x00\x00\x00\x00").get_next_addr(HeyMacAddr(b"\xB0\x00\x00\x00\x00\x00\x00\x00")), HeyMacAddr(b"\x00\x00\x00\x00\x00\x00\x00\x00"))
        self.assertEqual(HeyMacAddr(b"\x25\x56").get_next_addr(HeyMacAddr(b"\x99\x53")), HeyMacAddr(b"\x25\x50"))
        self.assertEqual(HeyMacAddr(b"\x25\x55\x55\x55\x55\x55\x55\x56").get_next_addr(HeyMacAddr(b"\x99\x99\x99\x99\x99\x99\x99\x53")), HeyMacAddr(b"\x25\x55\x55\x55\x55\x55\x55\x50"))
        self.assertEqual(HeyMacAddr(b"\x99\x50").get_next_addr(HeyMacAddr(b"\x99\x53")), HeyMacAddr(b"\x99\x53"))
        self.assertEqual(HeyMacAddr(b"\x99\x99\x99\x99\x99\x99\x99\x50").get_next_addr(HeyMacAddr(b"\x99\x99\x99\x99\x99\x99\x99\x53")), HeyMacAddr(b"\x99\x99\x99\x99\x99\x99\x99\x53"))
        # Bad addresses
        with self.assertRaises(AssertionError): HeyMacAddr(b"\x10\x00\x00\x00").get_next_addr(HeyMacAddr(b"\x00\x00"))
        with self.assertRaises(AssertionError): HeyMacAddr(b"\x10\x00\x00\x00\x00\x00\x00\x00").get_next_addr(HeyMacAddr(b"\x00\x00\x00\x00\x00\x00\x00\x00"))
        with self.assertRaises(AssertionError): HeyMacAddr(b"\x00\x00").get_next_addr(HeyMacAddr(b"\x10\x00\x00\x00"))
        with self.assertRaises(AssertionError): HeyMacAddr(b"\x00\x00\x00\x00\x00\x00\x00\x00").get_next_addr(HeyMacAddr(b"\x10\x00\x00\x00\x00\x00\x00\x00"))
        with self.assertRaises(AssertionError): HeyMacAddr(b"\x00\x00").get_next_addr(HeyMacAddr(b"\x00\x00\x00\x00\x00"))
        with self.assertRaises(AssertionError): HeyMacAddr(b"\x00\x00\x00\x00\x00\x00\x00\x00").get_next_addr(HeyMacAddr(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"))
        with self.assertRaises(AssertionError): HeyMacAddr(b"\x00\x00\x00\x00\x00").get_next_addr(HeyMacAddr(b"\x00\x00"))
        with self.assertRaises(AssertionError): HeyMacAddr(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00").get_next_addr(HeyMacAddr(b"\x00\x00\x00\x00\x00\x00\x00\x00"))
        with self.assertRaises(AssertionError): HeyMacAddr(b"\x00\x00\x00\x01").get_next_addr(HeyMacAddr(b"\x00\x00"))
        with self.assertRaises(AssertionError): HeyMacAddr(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01").get_next_addr(HeyMacAddr(b"\x00\x00\x00\x00\x00\x00\x00\x00"))
        with self.assertRaises(AssertionError): HeyMacAddr(b"\x00\x00").get_next_addr(HeyMacAddr(b"\x00\x00\x00\x01"))
        with self.assertRaises(AssertionError): HeyMacAddr(b"\x00\x00\x00\x00\x00\x00\x00\x00").get_next_addr(HeyMacAddr(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01"))

    def _test_get_route(self,):
        # Happy cases
        self.assertEqual(get_route(b"\x00\x00", b"\x00\x00"), [b"\x00\x00"])
        self.assertEqual(get_route(b"\x10\x00", b"\x00\x00"), [b"\x10\x00", b"\x00\x00"])
        self.assertEqual(get_route(b"\x00\x00", b"\x10\x00"), [b"\x00\x00", b"\x10\x00"])
        self.assertEqual(get_route(b"\x01\x01\x00\x00", b"\x10\x00"), [b"\x01\x01\x00\x00", b"\x10\x00"])
        self.assertEqual(get_route(b"\x0A\x00\x00\x00", b"\x0B\x00\x00\x00"), [b"\x0A\x00\x00\x00", b"\x00\x00", b"\x0B\x00\x00\x00"])
        self.assertEqual(get_route(b"\x0A\x01\x02\x03", b"\x0B\x0B\x02\x09"),
                                  [b"\x0A\x01\x02\x03", b"\x0A\x01\x02\x00", b"\x0A\x01\x00\x00", b"\x0A\x00\x00\x00",
                                   b"\x00\x00",
                                   b"\x0B\x00\x00\x00", b"\x0B\x0B\x00\x00", b"\x0B\x0B\x02\x00", b"\x0B\x0B\x02\x09", ])


    def _test_get_route_dir(self,):
        # Happy cases
        self.assertEqual(get_route_dir(b"\x00\x00", b"\x00\x00"), None)
        self.assertEqual(get_route_dir(b"\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00"), None)
        self.assertEqual(get_route_dir(b"\x10\x00", b"\x00\x00"), "up")
        self.assertEqual(get_route_dir(b"\x10\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00"), "up")
        self.assertEqual(get_route_dir(b"\x00\x00", b"\x10\x00"), "down")
        self.assertEqual(get_route_dir(b"\x00\x00\x00\x00\x00\x00\x00\x00", b"\x10\x00\x00\x00\x00\x00\x00\x00"), "down")
        self.assertEqual(get_route_dir(b"\x01\x0E\x01\x00", b"\x0E\x00\x00\x00"), "up")
        self.assertEqual(get_route_dir(b"\x01\x0E\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x0E\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"), "up")
        self.assertEqual(get_route_dir(b"\x0E\x00\x00\x00", b"\x01\x0E\x01\x00"), "up")
        self.assertEqual(get_route_dir(b"\x0E\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x01\x0E\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"), "up")
        self.assertEqual(get_route_dir(b"\x01\x0E\x00\x00", b"\x01\x0E\x01\x00"), "down")
        self.assertEqual(get_route_dir(b"\x01\x0E\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x01\x0E\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"), "down")
        # Bad addresses
        with self.assertRaises(AssertionError): get_route_dir(b"\x10\x00\x00\x00", b"\x00\x00")
        with self.assertRaises(AssertionError): get_route_dir(b"\x10\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_route_dir(b"\x00\x00", b"\x10\x00\x00\x00")
        with self.assertRaises(AssertionError): get_route_dir(b"\x00\x00\x00\x00\x00\x00\x00\x00", b"\x10\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_route_dir(b"\x00\x00", b"\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_route_dir(b"\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_route_dir(b"\x00\x00\x00\x00\x00", b"\x00\x00")
        with self.assertRaises(AssertionError): get_route_dir(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_route_dir(b"\x00\x00\x00\x01", b"\x00\x00")
        with self.assertRaises(AssertionError): get_route_dir(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01", b"\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): get_route_dir(b"\x00\x00", b"\x00\x00\x00\x01")
        with self.assertRaises(AssertionError): get_route_dir(b"\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01")


if __name__ == '__main__':
    unittest.main()
